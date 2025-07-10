import concurrent.futures
import datetime
import logging
import os
import time
from typing import Optional

from bughog.database.mongo.mongodb import MongoDB
from bughog.parameters import SubjectConfiguration

logger = logging.getLogger(__name__)


class ExecutableCache:
    """
    The executable cache is used to store and fetch executable files from the database.
    """

    @staticmethod
    def fetch_executable_files(subject_config: SubjectConfiguration, state_name: str, executable_folder_path: str) -> bool:
        """
        Fetches the executable files from the database and stores them in the directory of the given path.

        :param executable_path: The path to store the executable files.
        :param state: The state of the executable.
        :return: True if the executable was fetched, False otherwise.
        """
        if MongoDB().executable_cache_limit <= 0:
            return False

        files_collection = MongoDB().get_collection('fs.files')

        query = {
            'file_type': 'executable',
            'subject_type': subject_config.subject_type,
            'subject_name': subject_config.subject_name,
            'state_name': state_name,
        }
        if files_collection.count_documents(query) == 0:
            return False
        # Update access count and last access timestamp
        files_collection.update_many(
            query,
            {'$inc': {'access_count': 1}, '$set': {'last_access_ts': datetime.datetime.now()}},
        )
        if not os.path.exists(executable_folder_path):
            os.mkdir(executable_folder_path)

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
                file_path = os.path.join(executable_folder_path, grid_doc['relative_file_path'])
                grid_file_id = grid_doc['_id']
                executor.submit(write_from_db, file_path, grid_file_id)

        executor.shutdown(wait=True)
        elapsed_time = time.time() - start_time
        logger.debug(f'Fetched cached executable in {elapsed_time:.2f}s')
        return True

    @staticmethod
    def store_executable_files(subject_config: SubjectConfiguration, state_name: str, executable_folder_path: str):
        """
        Stores the files in the folder of the given path in the database.

        :param subject_config: The evaluation subject configuration.
        :param state: The state of the executable.
        :param executable_path: The path to the executable.
        :return: True if the executable was stored, False otherwise.
        """
        if MongoDB().executable_cache_limit <= 0:
            return False

        while ExecutableCache.__count_cached_executables() >= MongoDB().executable_cache_limit:
            if ExecutableCache.__count_cached_executables(state_type='commit') <= 0:
                # There are only version binaries in the cache, which will never be removed
                return False
            ExecutableCache.__remove_least_used_commit_executable_files()

        logger.debug(f'Caching executable files for {state_name}...')
        fs = MongoDB().gridfs

        last_access_ts = datetime.datetime.now()

        def store_file(file_path: str) -> None:
            # Max chunk size is 16 MB (meta-data included)
            chunk_size = 1024 * 1024 * 15
            with open(file_path, 'rb') as file:
                file_id = fs.new_file(
                    file_type='executable',
                    subject_type=subject_config.subject_type,
                    subject_name=subject_config.subject_name,
                    state_name=state_name,
                    relative_file_path=os.path.relpath(file_path, executable_folder_path),
                    access_count=0,
                    last_access_ts=last_access_ts,
                    chunk_size=chunk_size,
                )
                while chunk := file.read(chunk_size):
                    file_id.write(chunk)
            file_id.close()

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for root, _, files in os.walk(executable_folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    future = executor.submit(store_file, file_path)
                    futures.append(future)
            logger.debug(f'Number of files to cache: {len(futures)}')
            executor.shutdown(wait=True)

            futures_with_exception = [future for future in futures if future.exception() is not None]
            if futures_with_exception:
                logger.error(
                    (
                        f'Something went wrong caching executable files for {state_name}, '
                        'Removing possibly imcomplete executable files from cache.'
                    ),
                    exc_info=futures_with_exception[0].exception(),
                )
                ExecutableCache.__remove_commit_executable_files(state_name)
                logger.debug(f'Removed possibly incomplete cached executable files for {state_name}.')
            else:
                elapsed_time = time.time() - start_time
                logger.debug(f'Stored executable in {elapsed_time:.2f}s')

    @staticmethod
    def remove_executable_files(state_name) -> None:
        ExecutableCache.__remove_commit_executable_files(state_name)

    @staticmethod
    def __count_cached_executables(state_type: Optional[str] = None) -> int:
        """
        Counts the number of cached binaries in the database.

        :param state_type: The type of the state.
        :return: The number of cached binaries.
        """
        files_collection = MongoDB().get_collection('fs.files')
        if state_type:
            query = {'file_type': 'executable', 'state_type': state_type}
        else:
            query = {'file_type': 'executable'}
        return len(files_collection.find(query).distinct('state_index'))

    @staticmethod
    def __remove_least_used_commit_executable_files() -> None:
        """
        Removes the least used commit executable files from the database.
        """
        files_collection = MongoDB().get_collection('fs.files')

        grid_cursor = files_collection.find(
            {'file_type': 'executable', 'state_type': 'commit'},
            sort=[('access_count', 1), ('last_access_ts', 1)],
        )
        for state_doc in grid_cursor:
            state_name = state_doc['state_name']
            ExecutableCache.__remove_commit_executable_files(state_name)
            break

    @staticmethod
    def __remove_commit_executable_files(state_name: str) -> None:
        """
        Removes the executable files associated with the parameters.
        """
        fs = MongoDB().gridfs
        files_collection = MongoDB().get_collection('fs.files')

        for grid_doc in files_collection.find({'state_name': state_name}):
            fs.delete(grid_doc['_id'])
