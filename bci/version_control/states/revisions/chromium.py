from typing import Optional

import requests

from bci.database.mongo.mongodb import MongoDB
from bci.version_control.revision_parser.chromium_parser import ChromiumRevisionParser
from bci.version_control.states.revisions.base import BaseRevision

PARSER = ChromiumRevisionParser()


class ChromiumRevision(BaseRevision):
    def __init__(self, revision_id: Optional[str] = None, revision_nb: Optional[int] = None):
        super().__init__(revision_id, revision_nb)

    @property
    def browser_name(self):
        return 'chromium'

    def has_online_binary(self) -> bool:
        cached_binary_available_online = MongoDB().has_binary_available_online('chromium', self)
        if cached_binary_available_online is not None:
            return cached_binary_available_online
        url = f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{self._revision_nb}%2Fchrome-linux.zip'
        req = requests.get(url)
        has_binary_online = req.status_code == 200
        MongoDB().store_binary_availability_online_cache('chromium', self, has_binary_online)
        return has_binary_online

    def get_online_binary_url(self):
        return (
            'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/%s%%2F%s%%2Fchrome-%s.zip?alt=media'
            % ('Linux_x64', self._revision_nb, 'linux')
        )

    def _fetch_missing_data(self) -> None:
        """
        States are initialized with either a revision id or revision number.
        This method attempts to fetch other data to complete this state object.
        """
        # First check if the missing data is available in the cache
        if self._revision_id and self._revision_nb:
            return
        if state := MongoDB().get_complete_state_dict_from_binary_availability_cache(self):
            if self._revision_id is None:
                self._revision_id = state.get('revision_id', None)
            if self._revision_nb is None:
                self._revision_nb = state.get('revision_number', None)
        # If not, fetch the missing data from the parser
        if self._revision_id is None:
            self._revision_id = PARSER.get_revision_id(self._revision_nb)
        if self._revision_nb is None:
            self._revision_nb = PARSER.get_revision_nb(self._revision_id)
