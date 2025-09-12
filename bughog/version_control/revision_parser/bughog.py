import logging

from pymongo import UpdateOne

from bughog import util
from bughog.database.mongo.mongodb import MongoDB

DB_COLLECTION = 'commit_pos'
SUPPORTED_SUBJECTS = [
    'wasmtime'
]
logger = logging.getLogger(__name__)


def update_commit_pos_data() -> None:
    logger.info('Collecting commit position data...')
    collection = MongoDB().get_collection(DB_COLLECTION, create_if_not_found=True)
    for subject in SUPPORTED_SUBJECTS:
        # Fetch commit position - commit hash pairs
        url = f'https://bughog.distrinet-research.be/{subject}_commit_pos.json'
        resp = util.request_json(url)
        if isinstance(resp, list):
            raise Exception('A list was returned, but a dictionary was expected')
        positions = resp.get('positions', [])

        # Fetch base commit positions of version / release branches
        url = f'https://bughog.distrinet-research.be/{subject}_version_tag_base_pos.json'
        resp = util.request_json(url)
        if isinstance(resp, list):
            raise Exception('A list was returned, but a dictionary was expected')
        base_positions = resp.get('version_tag_base_positions', [])

        ops = []
        for pos in positions:
            if common_entry := list(filter(lambda x: x['base_commit_pos_id'] == pos['hash'], base_positions)):
                version_tag = common_entry[0]['tag']
            else:
                version_tag = None
            ops.append(
                UpdateOne(
                    {'pos': pos['pos']},
                    {
                        '$set': {
                            'hash': pos['hash'],
                            'subject': subject,
                            'version_tag_of_forked_release_branch': version_tag,
                        },
                    },
                    upsert=True,
                )
            )
        collection.bulk_write(ops, ordered=False)
    logger.info('Commit position data collection finished!')


def get_commit_nb(subject: str, commit_id: str) -> int:
    collection = MongoDB().get_collection(DB_COLLECTION)
    result = collection.find_one({
        'subject': subject,
        'hash': commit_id,
    })
    if result is not None:
        return result.get('pos', None)
    raise Exception(f'Could not find commit pos of {commit_id}')


def get_commit_id(subject: str, commit_nb: int) -> str:
    collection = MongoDB().get_collection(DB_COLLECTION)
    result = collection.find_one({
        'subject': subject,
        'pos': commit_nb,
    })
    if result is not None:
        return result.get('hash', None)
    raise Exception(f'Could not find commit hash of {commit_nb}')


def get_commit_id_of_release(subject: str, release_tag: str) -> str:
    collection = MongoDB().get_collection(DB_COLLECTION)
    result = collection.find_one({
        'subject': subject,
        'version_tag_of_forked_release_branch': release_tag,
    })
    if result is not None:
        return result.get('hash', None)
    raise Exception(f'Could not find commit hash of {release_tag}')

