import re

from bci.evaluations.logic import BrowserConfiguration, EvaluationRange
from bci.version_control.repository.online.chromium import OnlineChromiumRepo
from bci.version_control.repository.online.firefox import OnlineFirefoxRepo
from bci.version_control.repository.repository import Repository
from bci.version_control.states.chromium import ChromiumState
from bci.version_control.states.firefox import FirefoxState
from bci.version_control.states.state import State


def get_state_list(browser_config: BrowserConfiguration, eval_range: EvaluationRange) -> list[State]:
    if eval_range.major_version_range:
        repo = __get_repo(browser_config)
        if eval_range.only_release_revisions:
            short_lower_version = __get_short_version(eval_range.major_version_range[0])
            short_upper_version = __get_short_version(eval_range.major_version_range[1])
            return [
                __create_state(browser_config, repo.get_release_revision_number(version))
                for version in range(short_lower_version, short_upper_version + 1)
            ]
        else:
            lower_revision_nb = repo.get_release_revision_number(eval_range.major_version_range[0])
            upper_revision_nb = repo.get_release_revision_number(eval_range.major_version_range[1])
    else:
        lower_revision_nb, upper_revision_nb = eval_range.revision_number_range
    return [__create_state(browser_config, rev_nb) for rev_nb in range(lower_revision_nb, upper_revision_nb + 1)]


def __get_short_version(version: str) -> int:
    if '.' not in version:
        return int(version)
    if re.match(r'^[0-9]+$', version):
        return int(version)
    if re.match(r'^[0-9]+(\.[0-9]+)+$', version):
        return int(version.split(".")[0])
    raise AttributeError(f'Could not convert version \'{version}\' to short version')


def __get_repo(browser_config: BrowserConfiguration) -> Repository:
    match browser_config.browser_name:
        case 'chromium':
            return OnlineChromiumRepo()
        case 'firefox':
            return OnlineFirefoxRepo()
        case _:
            raise ValueError(f'Unknown browser name: {browser_config.browser_name}')


def __create_state(browser_config: BrowserConfiguration, revision_number: int) -> State:
    match browser_config.browser_name:
        case 'chromium':
            return ChromiumState(revision_number=revision_number)
        case 'firefox':
            return FirefoxState(revision_number=revision_number)
        case _:
            raise ValueError(f'Unknown browser name: {browser_config.browser_name}')
