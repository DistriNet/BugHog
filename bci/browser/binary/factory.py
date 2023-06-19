from bci.browser.binary.binary import Binary
from bci.browser.binary.vendors.chromium import ChromiumBinary
from bci.browser.binary.vendors.firefox import FirefoxBinary
from bci.version_control.states.state import State


def list_downloaded_binaries(browser):
    return __get_class(browser).list_downloaded_binaries()


def list_artisanal_binaries(browser):
    return __get_class(browser).list_artisanal_binaries()


def update_artisanal_binaries(browser):
    return __get_class(browser).get_artisanal_manager().update()


def download_online_binary(browser, revision_number):
    return __get_class(browser).download_online_binary(revision_number)


def binary_is_available(state: State) -> bool:
    return __has_available_binary_online(state) or __has_available_binary_artisanal(state)


def __has_available_binary_online(state: State) -> bool:
    return __get_class(state.browser_name).has_available_binary_online(state)


def __has_available_binary_artisanal(state: State) -> bool:
    return __get_class(state.browser_name).get_artisanal_manager().has_artisanal_binary_for(state)


def get_binary(state: State) -> Binary:
    return __get_object(state.browser_name, state)


def __get_class(browser_name: str) -> Binary.__class__:
    match browser_name:
        case 'chromium':
            return ChromiumBinary
        case 'firefox':
            return FirefoxBinary
        case _:
            raise ValueError(f'Unknown browser {browser_name}')


def __get_object(browser_name: str, state: State) -> Binary:
    match browser_name:
        case 'chromium':
            return ChromiumBinary(state)
        case 'firefox':
            return FirefoxBinary(state)
        case _:
            raise ValueError(f'Unknown browser {browser_name}')
