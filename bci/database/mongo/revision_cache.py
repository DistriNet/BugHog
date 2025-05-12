import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from pymongo import ASCENDING, DESCENDING

from bci import util
from bci.database.mongo.mongodb import MongoDB

logger = logging.getLogger(__name__)

BASE_URL = 'https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/'


class RevisionCache:

    @staticmethod
    def update() -> None:
        def safe_request_json_and_update(collection_name: str, transform=lambda x: x):
            url = BASE_URL + collection_name + '.json'
            try:
                result = util.request_json(url)['data']
                if result is not None:
                    RevisionCache.__update_collection(collection_name, transform(result))
            except util.ResourceNotFound:
                logger.warning(f'Could not update revision cache with resource at {url}')

        executor = ThreadPoolExecutor()
        executor.submit(safe_request_json_and_update, 'firefox_binary_availability', transform=lambda x: list(x.values()))
        executor.submit(safe_request_json_and_update, 'firefox_revision_nb_to_id', transform=lambda x: list(x))
        executor.submit(safe_request_json_and_update, 'firefox_release_base_revs')
        executor.submit(safe_request_json_and_update, 'chromium_release_base_revs')
        executor.shutdown(wait=False)

    @staticmethod
    def __update_collection(collection_name: str, data: list) -> None:
        collection = MongoDB().get_collection(collection_name)
        if (n := len(data)) == collection.count_documents({}):
            logger.debug(f'{collection_name} is still up-to-date ({n} documents).')
        else:
            collection.delete_many({})
            collection.insert_many(data)
            logger.info(f'{collection_name} is updated ({len(data)} documents).')

    @staticmethod
    def firefox_get_revision_number(revision_id: str) -> int:
        collection = MongoDB().get_collection('firefox_binary_availability')
        result = collection.find_one({'revision_id': revision_id}, {'revision_number': 1})
        if result is None or 'revision_number' not in result:
            raise AttributeError(f"Could not find 'revision_number' in {result}")
        return result['revision_number']

    @staticmethod
    def firefox_has_binary_for(revision_nb: Optional[int], revision_id: Optional[str]) -> bool:
        collection = MongoDB().get_collection('firefox_binary_availability')
        if revision_nb:
            result = collection.find_one({'revision_number': revision_nb})
        elif revision_id:
            result = collection.find_one({'revision_number': revision_nb})
        else:
            raise AttributeError('No revision number or id was provided')
        return result is not None

    @staticmethod
    def firefox_get_binary_info(revision_id: str) -> Optional[dict]:
        collection = MongoDB().get_collection('firefox_binary_availability')
        return collection.find_one({'node': revision_id}, {'files_url': 1, 'app_version': 1})

    @staticmethod
    def firefox_get_previous_and_next_revision_nb_with_binary(revision_nb: int) -> tuple[Optional[int], Optional[int]]:
        collection = MongoDB().get_collection('firefox_binary_availability')

        previous_revision_nbs = collection.find({'revision_number': {'$lt': revision_nb}}).sort(
            {'revision_number': DESCENDING}
        )
        previous_document = next(previous_revision_nbs, None)

        next_revision_nbs = collection.find({'revision_number': {'$gt': revision_nb}}).sort(
            {'revision_number': ASCENDING}
        )
        next_document = next(next_revision_nbs, None)

        return (
            previous_document['revision_number'] if previous_document else None,
            next_document['revision_number'] if next_document else None,
        )

    @staticmethod
    def firefox_get_revision_id(revision_nb: int) -> Optional[str]:
        collection = MongoDB().get_collection('firefox_revision_nb_to_id')
        data = collection.find_one({})
        if data is None:
            return None
        return data.get(revision_nb, None)

    @staticmethod
    def __get_release_base_rev_collection(browser: str) -> str:
        match browser:
            case 'chromium':
                return 'chromium_release_base_revs'
            case 'firefox':
                return 'firefox_release_base_revs'
            case _:
                raise AttributeError(f'Could not get collection for browser {browser}')

    @staticmethod
    def is_tag(browser: str, tag: str) -> bool:
        collection = MongoDB().get_collection(RevisionCache.__get_release_base_rev_collection(browser))
        n = collection.count_documents({'release_tag': tag})
        return n > 0

    @staticmethod
    def get_release_tag(browser: str, major_release_version: int) -> str:
        collection = MongoDB().get_collection(RevisionCache.__get_release_base_rev_collection(browser))
        if doc := collection.find_one({'major_version': major_release_version}):
            return doc['release_tag']
        raise AttributeError(f"Could not find release tag associated with version '{major_release_version}'")

    @staticmethod
    def get_release_revision_number(browser: str, major_release_version: int) -> int:
        collection = MongoDB().get_collection(RevisionCache.__get_release_base_rev_collection(browser))
        if doc := collection.find_one({'major_version': major_release_version}):
            return doc['revision_number']
        raise AttributeError(f"Could not find major release version '{major_release_version}'")

    @staticmethod
    def get_release_revision_id(browser: str, major_release_version: int) -> int:
        collection = MongoDB().get_collection(RevisionCache.__get_release_base_rev_collection(browser))
        if doc := collection.find_one({'major_version': major_release_version}):
            return doc['revision_id']
        raise AttributeError(f"Could not find major release version '{major_release_version}'")

    @staticmethod
    def get_most_recent_major_version(browser:str) -> int:
        collection = MongoDB().get_collection(RevisionCache.__get_release_base_rev_collection(browser))
        if doc := collection.find_one(sort=[('major_version', -1)]):
            return doc['major_version']
        raise AttributeError("Could not find most recent major release version")
