from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from flatten_dict import flatten
from gridfs import GridFS
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError

from bci.evaluations.logic import (
    DatabaseParameters,
    EvaluationParameters,
    PlotParameters,
    TestParameters,
    TestResult,
)
from bci.version_control.state_result_factory import StateResultFactory
from bci.version_control.states.state import State

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
    binary_cache_limit = 0

    binary_availability_collection_names = {
        'chromium': 'chromium_binary_availability',
        'firefox': 'firefox_central_binary_availability',
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
        logger.info(f'Binary cache limit set to {db_params.binary_cache_limit}')
        # Force connection to check whether MongoDB server is reachable
        try:
            self.client.server_info()
            self._db = self.client[db_params.database_name]
            logger.info('Connected to database!')
        except ServerSelectionTimeoutError as e:
            logger.info('A timeout occurred while attempting to establish connection.', exc_info=True)
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

        for collection_name in ['chromium_binary_availability']:
            if collection_name not in self._db.list_collection_names():
                self._db.create_collection(collection_name)

        # Binary cache
        if 'fs.files' not in self._db.list_collection_names():
            # Create the 'fs.files' collection with indexes
            self._db.create_collection('fs.files')
            self._db['fs.files'].create_index(
                ['state_type', 'browser_name', 'state_index', 'relative_file_path'], unique=True
            )
        if 'fs.chunks' not in self._db.list_collection_names():
            # Create the 'fs.chunks' collection with zstd compression
            self._db.create_collection(
                'fs.chunks', storageEngine={'wiredTiger': {'configString': 'block_compressor=zstd'}}
            )
            self._db['fs.chunks'].create_index(['files_id', 'n'], unique=True)

        # Revision cache
        if 'firefox_binary_availability' not in self._db.list_collection_names():
            self._db.create_collection('firefox_binary_availability')
            self._db['firefox_binary_availability'].create_index([('revision_number', ASCENDING)])
            self._db['firefox_binary_availability'].create_index(['node'])

    def get_collection(self, name: str, create_if_not_found: bool = False) -> Collection:
        if self._db is None:
            raise ServerException('Database server does not have a database')
        if name not in self._db.list_collection_names():
            if create_if_not_found:
                return self._db.create_collection(name)
            else:
                raise ServerException(f"Could not find collection '{name}'")
        return self._db[name]

    def get_all_collection_names_for_browser(self, browser_name: str) -> list[str]:
        """
        Returns all collections associated with the given browser.
        """
        if self._db is None:
            raise ServerException('Database server does not have a database')
        return self._db.list_collection_names(filter={'name': {'$regex': rf'^.+_{browser_name}$'}})

    @property
    def gridfs(self) -> GridFS:
        if self._db is None:
            raise ServerException('Database server does not have a database')
        return GridFS(self._db)

    def store_result(self, result: TestResult):
        """
        Upserts the result.
        """
        browser_config = result.params.browser_configuration
        eval_config = result.params.evaluation_configuration
        collection = self.__get_data_collection(result.params)
        query = {
            'browser_automation': eval_config.automation,
            'browser_version': result.browser_version,
            'binary_origin': result.binary_origin,
            'padded_browser_version': result.padded_browser_version,
            'browser_config': browser_config.browser_setting,
            'cli_options': browser_config.cli_options,
            'extensions': browser_config.extensions,
            'state': result.params.state.to_dict(),
            'mech_group': result.params.mech_group
        }
        if result.driver_version:
            query['driver_version'] = result.driver_version

        if browser_config.browser_name == 'firefox':
            build_id = self.get_build_id_firefox(result.params.state)
            if build_id is None:
                query['artisanal'] = True
                query['build_id'] = 'artisanal'
            else:
                query['build_id'] = build_id
        update = {
            '$set': {
                'results': result.data,
                'dirty': result.is_dirty,
                'ts': str(datetime.now(timezone.utc).replace(microsecond=0)),
            }
        }
        collection.update_one(query, update, upsert=True)

    def get_result(self, params: TestParameters) -> Optional[TestResult]:
        collection = self.__get_data_collection(params)
        query = self.__to_test_query(params)
        document = collection.find_one(query)
        if document:
            return params.create_test_result_with(
                document['browser_version'], document['binary_origin'], document['results'], document['dirty']
            )
        else:
            logger.error(f'Could not find document for query {query}')
            return None

    def has_result(self, params: TestParameters) -> bool:
        collection = self.__get_data_collection(params)
        query = self.__to_test_query(params)
        nb_of_documents = collection.count_documents(query)
        return nb_of_documents > 0

    def get_evaluated_states(
        self, params: EvaluationParameters, boundary_states: Optional[tuple[State, State]], result_factory: StateResultFactory, dirty: Optional[bool]=None
    ) -> list[State]:
        collection = self.get_collection(params.database_collection, create_if_not_found=True)
        query = {
            'browser_config': params.browser_configuration.browser_setting,
            'mech_group': params.evaluation_range.mech_group,
            'state.browser_name': params.browser_configuration.browser_name,
            'results': {'$exists': True},
            'state.type': 'version' if params.evaluation_range.only_release_revisions else 'revision',
        }
        if boundary_states is not None:
            query['state.revision_number'] = {
                '$gte': boundary_states[0].revision_nb,
                '$lte': boundary_states[1].revision_nb,
            }
        if params.browser_configuration.extensions:
            query['extensions'] = {
                '$size': len(params.browser_configuration.extensions),
                '$all': params.browser_configuration.extensions,
            }
        else:
            query['extensions'] = []
        if params.browser_configuration.cli_options:
            query['cli_options'] = {
                '$size': len(params.browser_configuration.cli_options),
                '$all': params.browser_configuration.cli_options,
            }
        else:
            query['cli_options'] = []
        if dirty is not None:
            query['dirty'] = dirty
        cursor = collection.find(query)
        states = []
        for doc in cursor:
            state = State.from_dict(doc['state'])
            state.result = result_factory.get_result(doc['results'])
            states.append(state)
        return states

    def __to_test_query(self, params: TestParameters) -> dict:
        query = {
            'state': params.state.to_dict(),
            'browser_automation': params.evaluation_configuration.automation,
            'browser_config': params.browser_configuration.browser_setting,
            'mech_group': params.mech_group,
        }
        if len(params.browser_configuration.extensions) > 0:
            query['extensions'] = {
                '$size': len(params.browser_configuration.extensions),
                '$all': params.browser_configuration.extensions,
            }
        else:
            query['extensions'] = []
        if len(params.browser_configuration.cli_options) > 0:
            query['cli_options'] = {
                '$size': len(params.browser_configuration.cli_options),
                '$all': params.browser_configuration.cli_options,
            }
        else:
            query['cli_options'] = []
        return query

    def __get_data_collection(self, test_params: TestParameters) -> Collection:
        collection_name = test_params.database_collection
        return self.get_collection(collection_name, create_if_not_found=True)

    def get_binary_availability_collection(self, browser_name: str):
        collection_name = self.binary_availability_collection_names[browser_name]
        return self.get_collection(collection_name, create_if_not_found=True)

    # Caching of online binary availability

    def has_binary_available_online(self, browser: str, state: State):
        collection = self.get_binary_availability_collection(browser)
        document = collection.find_one({'state': state.to_dict()})
        if document is None:
            return None
        return document['binary_online']

    def get_stored_binary_availability(self, browser):
        collection = MongoDB().get_binary_availability_collection(browser)
        result = collection.find(
            {'binary_online': True},
            {
                '_id': False,
                'state': True,
            },
        )
        if browser == 'firefox':
            result.sort('build_id', -1)
        return result

    def get_complete_state_dict_from_binary_availability_cache(self, state: State) -> Optional[dict]:
        collection = MongoDB().get_binary_availability_collection(state.browser_name)
        # We have to flatten the state dictionary to ignore missing attributes.
        state_dict = {'state': state.to_dict()}
        query = flatten(state_dict, reducer='dot')
        document = collection.find_one(query)
        if document is None:
            return None
        return document['state']

    def store_binary_availability_online_cache(
        self, browser: str, state: State, binary_online: bool, url: Optional[str] = None
    ):
        collection = MongoDB().get_binary_availability_collection(browser)
        collection.update_one(
            {'state': state.to_dict()},
            {
                '$set': {
                    'state': state.to_dict(),
                    'binary_online': binary_online,
                    'url': url,
                    'ts': str(datetime.now(timezone.utc).replace(microsecond=0)),
                }
            },
            upsert=True,
        )

    def get_build_id_firefox(self, state: State):
        collection = MongoDB().get_binary_availability_collection('firefox')

        result = collection.find_one({'state': state.to_dict()}, {'_id': False, 'build_id': 1})
        # Result can only be None if the binary associated with the state_id is artisanal:
        # This state_id will not be included in the binary_availability_collection and not have a build_id.
        if result is None or len(result) == 0:
            return None
        return result['build_id']

    def get_documents_for_plotting(self, params: PlotParameters, releases: bool = False) -> list:
        collection = self.get_collection(params.database_collection, create_if_not_found=True)
        query = {
            'mech_group': params.mech_group,
            'browser_config': params.browser_config,
            'state.type': 'version' if releases else 'revision',
            'extensions': {'$size': len(params.extensions) if params.extensions else 0},
            'cli_options': {'$size': len(params.cli_options) if params.cli_options else 0},
        }
        if params.extensions:
            query['extensions']['$all'] = params.extensions
        if params.cli_options:
            query['cli_options']['$all'] = params.cli_options
        if params.revision_number_range:
            query['state.revision_number'] = {
                '$gte': params.revision_number_range[0],
                '$lte': params.revision_number_range[1],
            }
        elif params.major_version_range:
            query['padded_browser_version'] = {
                '$gte': str(params.major_version_range[0]).zfill(4),
                '$lte': str(params.major_version_range[1] + 1).zfill(4),
            }

        docs = collection.aggregate(
            [
                {'$match': query},
                {'$project': {'_id': False, 'state': True, 'browser_version': True, 'dirty': True, 'results': True}},
                {'$sort': {'rev_nb': 1}},
            ]
        )
        return list(docs)

    def remove_datapoint(self, params: TestParameters) -> None:
        collection = self.get_collection(params.database_collection)
        query = self.__to_test_query(params)
        collection.delete_one(query)

    def remove_all_data_from_collection(self, collection_name: str) -> None:
        collection = self.get_collection(collection_name)
        collection.delete_many({})

    def get_info(self) -> dict:
        if self.client and self.client.address:
            return {'type': 'mongo', 'host': self.client.address[0], 'connected': True}
        else:
            return {'type': 'mongo', 'host': None, 'connected': False}

    def get_previous_cli_options(self, params: dict) -> list[str]:
        """
        Returns a list of all cli options used for the browser defined in the given parameter dictionary.
        """
        if browser_name := params.get('browser_name', None):
            collection_names = self.get_all_collection_names_for_browser(browser_name)
            previous_cli_options = []
            for name in collection_names:
                # Appartently simply asking for a set of distinct arrays requires a complicated pipeline in MongoDB,
                # so we'll use Python logic.
                cursor = self.get_collection(name).find(
                    {'cli_options': {'$exists': True, '$not': {'$size': 0}}}, {'_id': False, 'cli_options': True}
                )
                # We convert to tuples because they are, in contract to lists, hashable.
                cli_options_list = set(' '.join(doc['cli_options']) for doc in cursor)
                if cli_options_list:
                    previous_cli_options.extend(list(filter(lambda x: x not in previous_cli_options, cli_options_list)))
            previous_cli_options.sort()
            return previous_cli_options
        else:
            logger.warning('Could not find browser name in parameters, returning empty list')
            return []


class ServerException(Exception):
    pass
