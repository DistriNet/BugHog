import concurrent.futures
import datetime
import logging
import os
import time
from typing import Optional

import gridfs

from bci.database.mongo.mongodb import MongoDB
from bci.version_control.states.state import State

logger = logging.getLogger(__name__)


class BinaryCache:
    """
    The binary cache is used to store and fetch binary files from the database.
    """

    @staticmethod
    def fetch_binary_files(binary_executable_path: str, state: State) -> bool:
        """
        Fetches the binary files from the database and stores them in the directory of the given path.

        :param binary_executable_path: The path to store the executable binary file.
        :param state: The state of the binary.
        :return: True if the binary was fetched, False otherwise.
        """
        if MongoDB.binary_cache_limit <= 0:
            return False

        files_collection = MongoDB().get_collection('fs.files')

        query = {
            'file_type': 'binary',
            'browser_name': state.browser_name,
            'state_type': state.type,
            'state_index': state.index,
        }
        if files_collection.count_documents(query) == 0:
            return False
        # Update access count and last access timestamp
        files_collection.update_many(
            query,
            {'$inc': {'access_count': 1}, '$set': {'last_access_ts': datetime.datetime.now()}},
        )
        binary_folder_path = os.path.dirname(binary_executable_path)
        if not os.path.exists(binary_folder_path):
            os.mkdir(binary_folder_path)

        def write_from_db(file_path: str, grid_file_id: str) -> None:
            grid_file = fs.get(grid_file_id)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as file:
                file.write(grid_file.read())
            os.chmod(file_path, 0o744)

        grid_cursor = files_collection.find(query)
        fs = MongoDB().gridfs
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for grid_doc in grid_cursor:
                file_path = os.path.join(binary_folder_path, grid_doc['relative_file_path'])
                grid_file_id = grid_doc['_id']
                executor.submit(write_from_db, file_path, grid_file_id)

        executor.shutdown(wait=True)
        elapsed_time = time.time() - start_time
        logger.debug(f'Fetched cached binary in {elapsed_time:.2f}s')
        return True

    @staticmethod
    def store_binary_files(binary_executable_path: str, state: State) -> bool:
        """
        Stores the files in the folder of the given path in the database.

        :param binary_executable_path: The path to the binary executable.
        :param state: The state of the binary.
        :return: True if the binary was stored, False otherwise.
        """
        if MongoDB.binary_cache_limit <= 0:
            return False

        while BinaryCache.__count_cached_binaries() >= MongoDB.binary_cache_limit:
            if BinaryCache.__count_cached_binaries(state_type='revision') <= 0:
                # There are only version binaries in the cache, which will never be removed
                return False
            BinaryCache.__remove_least_used_revision_binary_files()

        fs = MongoDB().gridfs
        binary_folder_path = os.path.dirname(binary_executable_path)
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for root, _, files in os.walk(binary_folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as file:
                        executor.submit(
                            fs.put,
                            file.read(),
                            file_type='binary',
                            browser_name=state.browser_name,
                            state_type=state.type,
                            state_index=state.index,
                            relative_file_path=os.path.relpath(file_path, binary_folder_path),
                            access_count=0,
                            last_access_ts=datetime.datetime.now(),
                        )
            executor.shutdown(wait=True)
        elapsed_time = time.time() - start_time
        logger.debug(f'Stored binary in {elapsed_time:.2f}s')
        return True

    @staticmethod
    def __count_cached_binaries(state_type: Optional[str] = None) -> int:
        """
        Counts the number of cached binaries in the database.

        :param state_type: The type of the state.
        :return: The number of cached binaries.
        """
        files_collection = MongoDB().get_collection('fs.files')
        if state_type:
            query = {'file_type': 'binary', 'state_type': state_type}
        else:
            query = {'file_type': 'binary'}
        return len(files_collection.find(query).distinct('state_index'))

    @staticmethod
    def __remove_least_used_revision_binary_files() -> None:
        """
        Removes the least used revision binary files from the database.
        """
        fs = MongoDB().gridfs
        files_collection = MongoDB().get_collection('fs.files')

        grid_cursor = files_collection.find(
            {'file_type': 'binary', 'state_type': 'revision'},
            sort=[('access_count', 1), ('last_access_ts', 1)],
        )
        for state_doc in grid_cursor:
            state_index = state_doc['state_index']
            for grid_doc in files_collection.find({'state_index': state_index, 'state_type': 'revision'}):
                fs.delete(grid_doc['_id'])
            break
