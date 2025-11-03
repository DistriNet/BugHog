from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from gridfs import GridFS
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError

from bughog.evaluation.experiment_result import ExperimentResult
from bughog.parameters import (
    DatabaseParameters,
    EvaluationParameters,
    SubjectConfiguration,
)
from bughog.version_control.state.base import ShallowState, State

logger = logging.getLogger(__name__)


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


@singleton
class MongoDB:
    instance = None
    executable_cache_limit = 0

    binary_availability_collection_names = {
        "chromium": "chromium_binary_availability",
        "firefox": "firefox_binary_availability",
    }

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def connect(self, db_params: DatabaseParameters) -> None:
        assert db_params is not None

        self.client = MongoClient(
            host=db_params.host,
            port=27017,
            username=db_params.username,
            password=db_params.password,
            authsource=db_params.database_name,
            retryWrites=False,
            serverSelectionTimeoutMS=10000,
        )
        self.binary_cache_limit = db_params.binary_cache_limit
        logger.info(f"Binary cache limit set to {db_params.binary_cache_limit}")
        # Force connection to check whether MongoDB server is reachable
        try:
            self.client.server_info()
            self._db = self.client[db_params.database_name]
            logger.info("Connected to database!")
        except ServerSelectionTimeoutError as e:
            logger.info("A timeout occurred while attempting to establish connection.", exc_info=True)
            raise ServerException from e

        # Initialize collections
        self.__initialize_collections()

    def disconnect(self):
        if self.client:
            self.client.close()
        self.client = None
        self._db = None

    def __initialize_collections(self):
        if self._db is None:
            raise

        for collection_name in ["chromium_binary_availability"]:
            if collection_name not in self._db.list_collection_names():
                self._db.create_collection(collection_name)

        # Binary cache
        if "fs.files" not in self._db.list_collection_names():
            # Create the 'fs.files' collection with indexes
            self._db.create_collection("fs.files")
            self._db["fs.files"].create_index(["state_type", "subject_type", "subject_name", "state_name"], unique=True)
        if "fs.chunks" not in self._db.list_collection_names():
            # Create the 'fs.chunks' collection with zstd compression
            self._db.create_collection("fs.chunks", storageEngine={"wiredTiger": {"configString": "block_compressor=zstd"}})
            self._db["fs.chunks"].create_index(["files_id", "n"], unique=True)

        # Commit cache
        if "firefox_binary_availability" not in self._db.list_collection_names():
            self._db.create_collection("firefox_binary_availability")
            self._db["firefox_binary_availability"].create_index([("revision_number", ASCENDING)])
            self._db["firefox_binary_availability"].create_index(["node"])
        if "firefox_release_base_revs" not in self._db.list_collection_names():
            self._db.create_collection("firefox_release_base_revs")
        if "chromium_release_base_revs" not in self._db.list_collection_names():
            self._db.create_collection("chromium_release_base_revs")
        if "commit_pos" not in self._db.list_collection_names():
            self._db.create_collection("commit_pos")
            self._db["commit_pos"].create_index([("pos", ASCENDING), ("subject")])
            self._db["commit_pos"].create_index([("hash"), ("subject")])
            self._db["commit_pos"].create_index([("version_tag_of_forked_release_branch"), ("subject")])


    def get_collection(self, name: str, create_if_not_found: bool = False) -> Collection:
        if self._db is None:
            raise ServerException("Database server does not have a database")
        if name not in self._db.list_collection_names():
            if create_if_not_found:
                return self._db.create_collection(name)
            else:
                raise ServerException(f"Could not find collection '{name}'")
        return self._db[name]

    def get_cache_collection(self, subject_type: str) -> Collection:
        if self._db is None:
            raise ServerException("Database server does not have a database")
        collection_name = f"{subject_type}_cache"
        if collection_name not in self._db.list_collection_names():
            return self._db.create_collection(collection_name)
        return self._db[collection_name]

    @property
    def gridfs(self) -> GridFS:
        if self._db is None:
            raise ServerException("Database server does not have a database")
        return GridFS(self._db)

    def store_result(self, eval_params: EvaluationParameters, result: ExperimentResult):
        """
        Upserts the result.
        """
        subject_config = eval_params.subject_configuration
        eval_params = eval_params
        collection = self.__get_data_collection(eval_params)
        query = {
            "subject_version": result.executable_version,
            "executable_origin": result.executable_origin,
            "padded_subject_version": result.padded_subject_version,
            "subject_config": subject_config.subject_setting,
            "cli_options": subject_config.cli_options,
            "extensions": subject_config.extensions,
            "state": result.state,
            "project": eval_params.evaluation_range.project_name,
            "experiment": eval_params.evaluation_range.experiment_name,
        }
        # if browser_config.subject_name == 'firefox':
        #     build_id = self.get_build_id_firefox(result.params.state)
        #     if build_id is None:
        #         query['artisanal'] = True
        #         query['build_id'] = 'artisanal'
        #     else:
        #         query['build_id'] = build_id
        update = {
            "$set": {
                "result.raw": result.raw_results,
                "result.variables": [list(item) for item in result.result_variables],
                "dirty": result.is_dirty,
                "ts": str(datetime.now(timezone.utc).replace(microsecond=0)),
            }
        }
        collection.update_one(query, update, upsert=True)

    def get_result(self, params: EvaluationParameters, state: ShallowState) -> Optional[ExperimentResult]:
        collection = self.__get_data_collection(params)
        query = self.__to_experiment_query(params, state)
        doc = collection.find_one(query)
        if doc:
            return ExperimentResult(
                doc["executable_version"],
                doc["executable_origin"],
                doc["state"],
                doc["result"]["raw"],
                set(tuple(item) for item in doc["result"]["variables"]),
                doc["dirty"],
            )
        else:
            logger.error(f"Could not find document for query {query}.")
            return None

    def has_result(self, params: EvaluationParameters, state: ShallowState) -> bool:
        collection = self.__get_data_collection(params)
        query = self.__to_experiment_query(params, state)
        nb_of_documents = collection.count_documents(query)
        return nb_of_documents > 0

    def get_evaluated_states(
        self,
        params: EvaluationParameters,
        boundary_states: Optional[tuple[State, State]],
        dirty: Optional[bool] = None,
    ) -> list[State]:
        collection = self.__get_data_collection(params)
        query = {
            "subject_config": params.subject_configuration.subject_setting,
            "experiment": params.evaluation_range.experiment_name,
            "result": {"$exists": True},
            "state.type": "release" if params.evaluation_range.only_release_commits else "commit",
        }
        if boundary_states is not None:
            query["state.commit_nb"] = {
                "$gte": boundary_states[0].commit_nb,
                "$lte": boundary_states[1].commit_nb,
            }
        if params.subject_configuration.extensions:
            query["extensions"] = {
                "$size": len(params.subject_configuration.extensions),
                "$all": params.subject_configuration.extensions,
            }
        else:
            query["extensions"] = []
        if params.subject_configuration.cli_options:
            query["cli_options"] = {
                "$size": len(params.subject_configuration.cli_options),
                "$all": params.subject_configuration.cli_options,
            }
        else:
            query["cli_options"] = []
        if dirty is not None:
            query["dirty"] = dirty
        cursor = collection.find(query)
        states = []
        for doc in cursor:
            subject_type = params.subject_configuration.subject_type
            subject_name = params.subject_configuration.subject_name
            state = State.from_dict(subject_type, subject_name, doc["state"])
            state.result_variables = set(tuple(item) for item in doc["result"]["variables"])
            states.append(state)
        return states

    def __to_experiment_query(self, params: EvaluationParameters, state: ShallowState) -> dict:
        state_query = {'state.' + k: v for k, v in state.dict.items()}
        query = {
            "subject_config": params.subject_configuration.subject_setting,
            "experiment": params.evaluation_range.experiment_name,
        }
        query.update(state_query)
        if len(params.subject_configuration.extensions) > 0:
            query["extensions"] = {
                "$size": len(params.subject_configuration.extensions),
                "$all": params.subject_configuration.extensions,
            }
        else:
            query["extensions"] = []
        if len(params.subject_configuration.cli_options) > 0:
            query["cli_options"] = {
                "$size": len(params.subject_configuration.cli_options),
                "$all": params.subject_configuration.cli_options,
            }
        else:
            query["cli_options"] = []
        return query

    def __get_data_collection(self, eval_params: EvaluationParameters) -> Collection:
        """
        Returns the data collection, of which the name is formatted as '{subject_type}_{subject_name}'.
        """
        collection_name = f"{eval_params.subject_configuration.subject_type}_{eval_params.subject_configuration.subject_name}"
        return self.get_collection(collection_name, create_if_not_found=True)

    def get_binary_availability_collection(self, subject_config: SubjectConfiguration) -> Collection:
        collection_name = f"{subject_config.subject_type}_executable_availability"
        return self.get_collection(collection_name, create_if_not_found=True)

    # Caching of online executable availability

    def get_stored_binary_availability(self, subject_config: SubjectConfiguration):
        collection = MongoDB().get_binary_availability_collection(subject_config)
        result = collection.find(
            {"executable_online": True},
            {
                "_id": False,
                "state": True,
            },
        )
        if subject_config.subject_name == "firefox":
            result.sort("build_id", -1)
        return result

    def get_documents_for_plotting(self, params: EvaluationParameters, releases: bool = False) -> list:
        collection = self.__get_data_collection(params)

        evaluation_range = params.evaluation_range
        subject_config = params.subject_configuration

        query = {
            "project": evaluation_range.project_name,
            "experiment": evaluation_range.experiment_name,
            "subject_config": subject_config.subject_setting,
            "state.type": "release" if releases else "commit",
            "extensions": {"$size": len(subject_config.extensions) if subject_config.extensions else 0},
            "cli_options": {"$size": len(subject_config.cli_options) if subject_config.cli_options else 0},
        }
        if subject_config.extensions:
            query["extensions"]["$all"] = subject_config.extensions
        if subject_config.cli_options:
            query["cli_options"]["$all"] = subject_config.cli_options
        if evaluation_range.commit_nb_range:
            query["state.commit_nb"] = {
                "$gte": evaluation_range.commit_nb_range[0],
                "$lte": evaluation_range.commit_nb_range[1],
            }
        elif evaluation_range.major_version_range:
            query["padded_subject_version"] = {
                "$gte": str(evaluation_range.major_version_range[0]).zfill(4),
                "$lte": str(evaluation_range.major_version_range[1] + 1).zfill(4),
            }
        docs = collection.aggregate(
            [
                {"$match": query},
                {"$project": {"_id": False, "state": True, "subject_version": True, "dirty": True, "result.variables": True}},
                {"$sort": {"state.commit_nb": 1}},
            ]
        )
        return list(docs)

    def remove_datapoint(self, params: EvaluationParameters, state: ShallowState) -> None:
        collection = self.__get_data_collection(params)
        query = self.__to_experiment_query(params, state)
        count = collection.delete_one(query)
        if count.deleted_count == 0:
            logger.error(f'Could not remove datapoint for {state}.')
        else:
            logger.debug(f'Removed datapoint for {state}.')

    def remove_all_data_for(self, params_list: list[EvaluationParameters]) -> None:
        for params in params_list:
            collection = self.__get_data_collection(params)
            collection.delete_many({
                'project': params.evaluation_range.project_name,
                'experiment': params.evaluation_range.experiment_name,
            })

    def remove_all_data_from_collection(self, collection_name: str) -> None:
        collection = self.get_collection(collection_name)
        collection.delete_many({})

    def get_info(self) -> dict:
        if self.client and self.client.address:
            return {"type": "mongo", "host": self.client.address[0], "connected": True}
        else:
            return {"type": "mongo", "host": None, "connected": False}

    # def get_previous_cli_options(self, params: dict) -> list[str]:
    #     """
    #     Returns a list of all cli options used for the browser defined in the given parameter dictionary.
    #     """
    #     previous_cli_options = []
    #     collection = self.__get_data_collection(params)
    #     cursor = collection.find(
    #         {'cli_options': {'$exists': True, '$not': {'$size': 0}}}, {'_id': False, 'cli_options': True}
    #     )
    #     # We convert to tuples because they are, in contrast to lists, hashable.
    #     cli_options_list = set(' '.join(doc['cli_options']) for doc in cursor)
    #     if cli_options_list:
    #         previous_cli_options.extend(list(filter(lambda x: x not in previous_cli_options, cli_options_list)))
    #     previous_cli_options.sort()
    #     return previous_cli_options


class ServerException(Exception):
    pass
