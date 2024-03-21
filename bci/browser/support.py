import dataclasses

import bci.version_control.repository.online.chromium as chromium_repo
import bci.version_control.repository.online.firefox as firefox_repo

from bci.browser.configuration import chromium, firefox


def get_chromium_support() -> dict:
    return {
        'name': 'chromium',
        'min_version': 20,
        'max_version': chromium_repo.get_most_recent_major_version(),
        'options': [dataclasses.asdict(option) for option in chromium.SUPPORTED_OPTIONS]
    }

def get_firefox_support() -> dict:
    return {
        'name': 'firefox',
        'min_version': 20,
        'max_version': firefox_repo.get_most_recent_major_version(),
        'options': [dataclasses.asdict(option) for option in firefox.SUPPORTED_OPTIONS]
    }
