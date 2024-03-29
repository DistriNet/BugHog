from __future__ import annotations

import logging
from abc import ABC
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ServerSelectionTimeoutError

from bci.evaluations.logic import DatabaseConnectionParameters, PlotParameters, TestParameters, TestResult, WorkerParameters
from bci.version_control.states.state import State

logger = logging.getLogger(__name__)

# pylint: disable=global-statement
CLIENT = None
DB = None


class MongoDB(ABC):
    instance = None

    binary_availability_collection_names = {
        "chromium": "chromium_binary_availability",
        "firefox": "firefox_central_binary_availability"
    }

    def __init__(self):
        self.client = CLIENT
        self.db = DB

    @classmethod
    def get_instance(cls) -> MongoDB:
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

    @staticmethod
    def connect(db_connection_params: DatabaseConnectionParameters):
        global CLIENT, DB
        assert db_connection_params is not None

        CLIENT = MongoClient(
            host=db_connection_params.host,
            port=27017,
            username=db_connection_params.username,
            password=db_connection_params.password,
            authsource=db_connection_params.database_name,
            retryWrites=False,
            serverSelectionTimeoutMS=10000)
        # Force connection to check whether MongoDB server is reachable
        try:
            CLIENT.server_info()
            DB = CLIENT[db_connection_params.database_name]
            logger.info("Connected to database!")
        except ServerSelectionTimeoutError as e:
            logger.info("A timeout occurred while attempting to establish connection.", exc_info=True)
            raise ServerException from e

        # Initialize collections
        MongoDB.__initialize_collections()

    @staticmethod
    def disconnect():
        global CLIENT, DB
        CLIENT.close()
        CLIENT = None
        DB = None

    @staticmethod
    def __initialize_collections():
        for collection_name in [
            'chromium_binary_availability',
            'firefox_central_binary_availability'
        ]:
            if collection_name not in DB.list_collection_names():
                DB.create_collection(collection_name)

    def get_collection(self, name: str):
        if name not in DB.list_collection_names():
            logger.info(f'Collection \'{name}\' does not exist, creating it...')
            DB.create_collection(name)
        return DB[name]

    def store_result(self, result: TestResult):
        browser_config = result.params.browser_configuration
        eval_config = result.params.evaluation_configuration
        collection = self.__get_data_collection(result.params)
        document = {
            'browser_automation': eval_config.automation,
            'browser_version': result.browser_version,
            'binary_origin': result.binary_origin,
            'padded_browser_version': result.padded_browser_version,
            'browser_config': browser_config.browser_setting,
            'cli_options': browser_config.cli_options,
            'extensions': browser_config.extensions,
            'state': result.params.state.to_dict(),
            'mech_group': result.params.mech_group,
            'results': result.data,
            'dirty': result.is_dirty,
            'ts': str(datetime.now(timezone.utc).replace(microsecond=0))
        }
        if result.driver_version:
            document["driver_version"] = result.driver_version

        if browser_config.browser_name == "firefox":
            build_id = self.get_build_id_firefox(result.params.state)
            if build_id is None:
                document["artisanal"] = True
                document["build_id"] = "artisanal"
            else:
                document["build_id"] = build_id

        collection.insert_one(document)

    def get_result(self, params: TestParameters) -> TestResult:
        collection = self.__get_data_collection(params)
        query = self.__to_query(params)
        document = collection.find_one(query)
        if document:
            return params.create_test_result_with(
                document['browser_version'],
                document['binary_origin'],
                document['results'],
                document['dirty']
            )
        else:
            logger.error(f'Could not find document for query {query}')

    def has_result(self, params: TestParameters) -> bool:
        collection = self.__get_data_collection(params)
        query = self.__to_query(params)
        nb_of_documents = collection.count_documents(query)
        return nb_of_documents > 0

    def has_all_results(self, params: WorkerParameters) -> bool:
        for test_params in map(params.create_test_params_for, params.mech_groups):
            if not self.has_result(test_params):
                return False
        return True

    def __to_query(self, params: TestParameters) -> dict:
        query = {
            'state': params.state.to_dict(),
            'browser_automation': params.evaluation_configuration.automation,
            'browser_config': params.browser_configuration.browser_setting,
            'mech_group': params.mech_group
        }
        if len(params.browser_configuration.extensions) > 0:
            query['extensions'] = {
                '$size': len(params.browser_configuration.extensions),
                '$all': params.browser_configuration.extensions
            }
        else:
            query['extensions'] = []
        if len(params.browser_configuration.cli_options) > 0:
            query['cli_options'] = {
                '$size': len(params.browser_configuration.cli_options),
                '$all': params.browser_configuration.cli_options
            }
        else:
            query['cli_options'] = []
        return query

    def __get_data_collection(self, test_params: TestParameters) -> Collection:
        collection_name = test_params.database_collection
        if collection_name not in self.db.list_collection_names():
            return self.db.create_collection(collection_name)
        return self.db[collection_name]

    @staticmethod
    def get_binary_availability_collection(browser_name: str):
        collection_name = MongoDB.binary_availability_collection_names[browser_name]
        if collection_name not in DB.list_collection_names():
            raise AttributeError("Collection '%s' not found in database" % collection_name)
        return DB[collection_name]

    # Caching of online binary availability

    @staticmethod
    def has_binary_available_online(browser: str, state: State):
        collection = MongoDB.get_binary_availability_collection(browser)
        document = collection.find_one({'state': state.to_dict()})
        if document is None:
            return None
        return document["binary_online"]

    @staticmethod
    def get_stored_binary_availability(browser):
        collection = MongoDB.get_binary_availability_collection(browser)
        result = collection.find(
            {
                "binary_online": True
            },
            {
                "_id": False,
                "state": True,
            }
        )
        if browser == "firefox":
            result.sort('build_id', -1)
        return result

    @staticmethod
    def store_binary_availability_online_cache(browser: str, state: State, binary_online: bool, url: str = None):
        collection = MongoDB.get_binary_availability_collection(browser)
        collection.update_one(
            {
                'state': state.to_dict()
            },
            {
                "$set":
                {
                    'state': state.to_dict(),
                    'binary_online': binary_online,
                    'url': url,
                    'ts': str(datetime.now(timezone.utc).replace(microsecond=0))
                }
            },
            upsert=True
        )

    @staticmethod
    def get_build_id_firefox(state: State):
        collection = MongoDB.get_binary_availability_collection("firefox")

        result = collection.find_one({
            "state": state.to_dict()
        }, {
            "_id": False,
            "build_id": 1
        })
        # Result can only be None if the binary associated with the state_id is artisanal:
        # This state_id will not be included in the binary_availability_collection and not have a build_id.
        if result is None or len(result) == 0:
            return None
        return result["build_id"]

    def get_documents_for_plotting(self, params: PlotParameters, releases: bool = False):
        collection = self.get_collection(params.database_collection)
        query = {
            'mech_group': params.mech_group,
            'browser_config': params.browser_config,
            'state.type': 'version' if releases else 'revision'
        }
        query['extensions'] = {
            '$size': len(params.extensions) if params.extensions else 0
        }
        if params.extensions:
            query['extensions']['$all'] = params.extensions
        query['cli_options'] = {
            '$size': len(params.cli_options) if params.cli_options else 0
        }
        if params.cli_options:
            query['cli_options']['$all'] = params.cli_options
        if params.revision_number_range:
            query['state.revision_number'] = {
                '$gte': params.revision_number_range[0],
                '$lte': params.revision_number_range[1]
            }
        elif params.major_version_range:
            query['padded_browser_version'] = {
                '$gte': str(params.major_version_range[0]).zfill(4),
                '$lte': str(params.major_version_range[1] + 1).zfill(4)
            }

        docs = collection.aggregate([
            {
                '$match': query
            },
            {
                '$project': {
                    '_id': False,
                    'state': True,
                    'browser_version': True,
                    'dirty': True,
                    'results': True
                }
            },
            {
                '$sort': {
                    'rev_nb': 1
                }
            }
        ])
        return list(docs)

    @staticmethod
    def get_info() -> dict:
        if CLIENT and CLIENT.address:
            return {
                'type': 'mongo',
                'host': CLIENT.address[0],
                'connected': True
            }
        else:
            return {
                'type': 'mongo',
                'host': None,
                'connected': False
            }


class ServerException(Exception):
    pass
