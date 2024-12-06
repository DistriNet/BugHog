import logging
from typing import Optional

from pymongo import ASCENDING, DESCENDING

from bci.database.mongo.mongodb import MongoDB

logger = logging.getLogger(__name__)


class RevisionCache:
    @staticmethod
    def store_firefox_binary_availability(data: dict) -> None:
        values = list(data.values())
        collection = MongoDB().get_collection('firefox_binary_availability')

        if (n := len(values)) == collection.count_documents({}):
            logger.debug(f'Revision Cache was not updated ({n} documents).')
            return

        collection.delete_many({})
        collection.insert_many(values)
        logger.info(f'Revision Cache was updated ({len(values)} documents).')

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
