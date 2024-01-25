from bci.version_control.states.state import State
from bci.util import request_json

BINARY_AVAILABILITY_URL = "https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/firefox_binary_availability.json"
REVISION_NUMBER_MAPPING_URL = "https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/firefox_revision_nb_to_id.json"

BINARY_AVAILABILITY_MAPPING = request_json(BINARY_AVAILABILITY_URL)["data"]
REVISION_NUMBER_MAPPING = request_json(REVISION_NUMBER_MAPPING_URL)["data"]


class FirefoxState(State):

    def __init__(self, revision_id: str = None, revision_number: str = None, parents=None, children=None, version: int = None):
        super().__init__(revision_id=revision_id, revision_number=revision_number, parents=parents, children=children)
        self.version = version

    @property
    def browser_name(self):
        return 'firefox'

    def _fetch_revision_id(self) -> str:
        return REVISION_NUMBER_MAPPING.get(str(self._revision_number), None)

    def _fetch_revision_number(self) -> int:
        binary_data = BINARY_AVAILABILITY_MAPPING.get(self._revision_id, None)
        if binary_data is not None:
            return binary_data.get('revision_number')
        else:
            return None
