import requests
from bci.version_control.revision_parser.chromium_parser import ChromiumRevisionParser
from bci.version_control.states.revisions.base import BaseRevision
from bci.database.mongo.mongodb import MongoDB

PARSER = ChromiumRevisionParser()


class ChromiumRevision(BaseRevision):

    def __init__(self, revision_id: str = None, revision_number: int = None, parents=None, children=None):
        super().__init__(revision_id, revision_number, parents=parents, children=children)

    @property
    def browser_name(self):
        return 'chromium'

    def has_online_binary(self):
        cached_binary_available_online = MongoDB.has_binary_available_online('chromium', self)
        if cached_binary_available_online is not None:
            return cached_binary_available_online
        url = f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{self._revision_number}%2Fchrome-linux.zip'
        req = requests.get(url)
        has_binary_online = req.status_code == 200
        MongoDB.store_binary_availability_online_cache('chromium', self, has_binary_online)
        return has_binary_online

    def get_online_binary_url(self):
        return "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/%s%%2F%s%%2Fchrome-%s.zip?alt=media" % ('Linux_x64', self._revision_number, 'linux')

    def _fetch_revision_id(self) -> str:
        if state := MongoDB.get_complete_state_dict_from_binary_availability_cache(self):
            return state['revision_id']
        return PARSER.get_rev_id(self._revision_number)

    def _fetch_revision_number(self) -> int:
        if state := MongoDB.get_complete_state_dict_from_binary_availability_cache(self):
            return state['revision_number']
        return PARSER.get_rev_number(self._revision_id)
