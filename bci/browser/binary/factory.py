from bci.browser.binary.binary import Binary
from bci.browser.binary.vendors.chromium import ChromiumBinary
from bci.browser.binary.vendors.firefox import FirefoxBinary
from bci.version_control.states.state import State


def get_binary(state: State) -> Binary:
    return __get_object(state)


def __get_object(state: State) -> Binary:
    match state.browser_name:
        case 'chromium':
            return ChromiumBinary(state)
        case 'firefox':
            return FirefoxBinary(state)
        case _:
            raise ValueError(f'Unknown browser {state.browser_name}')
