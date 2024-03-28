import re

import bci.version_control.repository.online.chromium as chromium_repo
import bci.version_control.repository.online.firefox as firefox_repo

from bci.evaluations.logic import BrowserConfiguration, EvaluationRange
from bci.version_control.repository.repository import Repository
from bci.version_control.states.revisions.chromium import ChromiumRevision
from bci.version_control.states.revisions.firefox import FirefoxRevision
from bci.version_control.states.state import State
from bci.version_control.states.versions.chromium import ChromiumVersion
from bci.version_control.states.versions.firefox import FirefoxVersion


def create_state_collection(browser_config: BrowserConfiguration, eval_range: EvaluationRange) -> list[State]:
    if eval_range.only_release_revisions:
        return __create_version_collection(browser_config, eval_range)
    else:
        return __create_revision_collection(browser_config, eval_range)


def __create_version_collection(browser_config: BrowserConfiguration, eval_range: EvaluationRange) -> list[State]:
    if not eval_range.major_version_range:
        raise ValueError('A major version range is required for creating a version collection')
    lower_version = eval_range.major_version_range[0]
    upper_version = eval_range.major_version_range[1]

    match browser_config.browser_name:
        case 'chromium':
            state_class = ChromiumVersion
        case 'firefox':
            state_class = FirefoxVersion
        case _:
            raise ValueError(f'Unknown browser name: {browser_config.browser_name}')

    return [
        state_class(version)
        for version in range(lower_version, upper_version + 1)
    ]


def __create_revision_collection(browser_config: BrowserConfiguration, eval_range: EvaluationRange) -> list[State]:
    if eval_range.major_version_range:
        repo = __get_repo(browser_config)
        lower_revision_nb = repo.get_release_revision_number(eval_range.major_version_range[0])
        upper_revision_nb = repo.get_release_revision_number(eval_range.major_version_range[1])
    else:
        lower_revision_nb, upper_revision_nb = eval_range.revision_number_range

    match browser_config.browser_name:
        case 'chromium':
            state_class = ChromiumRevision
        case 'firefox':
            state_class = FirefoxRevision
        case _:
            raise ValueError(f'Unknown browser name: {browser_config.browser_name}')

    return [
        state_class(revision_number=rev_nb)
        for rev_nb in range(lower_revision_nb, upper_revision_nb + 1)
    ]


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
            return chromium_repo
        case 'firefox':
            return firefox_repo
        case _:
            raise ValueError(f'Unknown browser name: {browser_config.browser_name}')
