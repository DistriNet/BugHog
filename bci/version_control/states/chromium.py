from bci.revision_parser.chromium_parser import ChromiumRevisionParser
from bci.version_control.states.state import State

PARSER = ChromiumRevisionParser()


class ChromiumState(State):

    def __init__(self, revision_id: str = None, revision_number: int = None, parents=None, children=None):
        super().__init__(revision_id, revision_number, parents=parents, children=children)

    @property
    def browser_name(self):
        return 'chromium'

    def _fetch_revision_id(self) -> str:
        return PARSER.get_rev_id(self._revision_number)

    def _fetch_revision_number(self) -> int:
        return PARSER.get_rev_number(self._revision_id)
