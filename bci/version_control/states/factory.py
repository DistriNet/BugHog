from bci.version_control.states.chromium import ChromiumState
from bci.version_control.states.firefox import FirefoxState
from bci.version_control.states.state import State


def create_state(browser_name: str, revision_id: str = None, revision_number: int = None, parents=None, children=None) -> State:
    if browser_name == 'chromium':
        return ChromiumState(revision_id, revision_number, parents, children)
    elif browser_name == 'firefox':
        return FirefoxState(revision_id, revision_number, parents, children)
    else:
        raise Exception(f'Unknown browser: {browser_name}')


def to_dict(state: State) -> dict:
    return {
        'revision_id': state.revision_id,
        'revision_number': state.revision_number,
        'browser_name': state.browser_name
    }


def from_dict(data: dict) -> State:
    return create_state(data['browser_name'], revision_id=data['revision_id'], revision_number=data['revision_number'])
