from typing import Optional

from bci.util import request_json
from bci.version_control.states.revisions.base import BaseRevision

BINARY_AVAILABILITY_URL = 'https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/firefox_binary_availability.json'
REVISION_NUMBER_MAPPING_URL = 'https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/firefox_revision_nb_to_id.json'

BINARY_AVAILABILITY_MAPPING = request_json(BINARY_AVAILABILITY_URL)['data']
REVISION_NUMBER_MAPPING = request_json(REVISION_NUMBER_MAPPING_URL)['data']


class FirefoxRevision(BaseRevision):
    def __init__(
        self, revision_id: Optional[str] = None, revision_nb: Optional[int] = None, major_version: Optional[int] = None
    ):
        super().__init__(revision_id=revision_id, revision_nb=revision_nb)
        self.major_version = major_version

    @property
    def browser_name(self) -> str:
        return 'firefox'

    def has_online_binary(self) -> bool:
        if self._revision_id:
            return self._revision_id in BINARY_AVAILABILITY_MAPPING
        if self._revision_nb:
            return str(self._revision_nb) in REVISION_NUMBER_MAPPING
        raise AttributeError('Cannot check binary availability without a revision id or revision number')

    def get_online_binary_url(self) -> str:
        binary_base_url = BINARY_AVAILABILITY_MAPPING[self._revision_id]['files_url']
        app_version = BINARY_AVAILABILITY_MAPPING[self._revision_id]['app_version']
        binary_url = f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.bz2'
        return binary_url

    def _fetch_missing_data(self):
        if self._revision_id is None:
            self._revision_id = REVISION_NUMBER_MAPPING.get(str(self._revision_nb), None)
        if self._revision_nb is None:
            binary_data = BINARY_AVAILABILITY_MAPPING.get(self._revision_id, None)
            if binary_data is not None:
                self._revision_nb = binary_data.get('revision_number')
