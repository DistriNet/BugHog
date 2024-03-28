from bci.util import request_json
from bci.version_control.states.revisions.base import BaseRevision

BINARY_AVAILABILITY_URL = "https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/firefox_binary_availability.json"
REVISION_NUMBER_MAPPING_URL = "https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/firefox_revision_nb_to_id.json"

BINARY_AVAILABILITY_MAPPING = request_json(BINARY_AVAILABILITY_URL)["data"]
REVISION_NUMBER_MAPPING = request_json(REVISION_NUMBER_MAPPING_URL)["data"]


class FirefoxRevision(BaseRevision):

    def __init__(self, revision_id: str = None, revision_number: str = None, parents=None, children=None, version: int = None):
        super().__init__(revision_id=revision_id, revision_number=revision_number, parents=parents, children=children)
        self.version = version

    @property
    def browser_name(self):
        return 'firefox'

    def has_online_binary(self) -> bool:
        if self._revision_id:
            return self._revision_id in BINARY_AVAILABILITY_MAPPING
        if self._revision_number:
            return str(self._revision_number) in REVISION_NUMBER_MAPPING

    def get_online_binary_url(self) -> str:
        binary_base_url = BINARY_AVAILABILITY_MAPPING[self.revision_id]["files_url"]
        app_version = BINARY_AVAILABILITY_MAPPING[self.revision_id]["app_version"]
        binary_url = f"{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.bz2"
        return binary_url

    def _fetch_revision_id(self) -> str:
        return REVISION_NUMBER_MAPPING.get(str(self._revision_number), None)

    def _fetch_revision_number(self) -> int:
        binary_data = BINARY_AVAILABILITY_MAPPING.get(self._revision_id, None)
        if binary_data is not None:
            return binary_data.get('revision_number')
        else:
            return None
