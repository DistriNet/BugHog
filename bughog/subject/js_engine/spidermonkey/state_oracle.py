from typing import Literal

import requests

from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service


class SpiderMonkeyStateOracle(StateOracle):
    """
    State oracle for SpiderMonkey (Mozilla's JavaScript engine / JS shell).

    SpiderMonkey is developed as part of mozilla-central and shares its
    commit numbering with Firefox.
    """

    # Commit / revision logic

    @Cache.cache_in_db('web_browser', 'firefox')
    def find_commit_nb(self, commit_id: str) -> int:
        return bughog_service.find_commit_nb('firefox', commit_id)

    @Cache.cache_in_db('web_browser', 'firefox')
    def find_commit_id(self, commit_nb: int) -> str | None:
        return bughog_service.find_commit_id('firefox', commit_nb)

    @Cache.cache_in_db('web_browser', 'firefox')
    def find_commit_of_release(self, release_version: int) -> tuple[int, str]:
        return bughog_service.find_version_commit('firefox', release_version)

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        if commit_id is None:
            return None
        return f'https://hg.mozilla.org/mozilla-central/rev/{commit_id}'

    def get_oldest_supported_release_version(self) -> int:
        return 20

    def get_most_recent_major_release_version(self) -> int:
        return bughog_service.find_latest_major_version('firefox')

    def get_most_recent_commit_nb(self) -> int:
        return bughog_service.find_latest_commit_info('firefox').get('nb')

    # Public executables

    @Cache.cache_in_db('js_engine', 'spidermonkey')
    def has_public_executable(self, state_index: int, state_type: Literal['release', 'commit']) -> bool:
        match state_type:
            case 'release':
                commit_nb = self.find_commit_of_release(state_index)[0]
                return self.has_public_executable(commit_nb, 'commit')
            case 'commit':
                return bughog_service.find_commit_executable_info('firefox', state_index) is not None

    def get_nearest_commit_with_executable(
        self, target_commit_nb: int, lower_bound: int, upper_bound: int
    ) -> int | None:
        NotImplementedError()

    @Cache.cache_in_db('js_engine', 'spidermonkey')
    def get_executable_download_urls(self, state_index: int, state_type: Literal['release', 'commit']) -> list[str]:
        match state_type:
            case 'release':
                commit_nb = self.find_commit_of_release(state_index)[0]
                return self.get_executable_download_urls(commit_nb, 'commit')
            case 'commit':
                info = bughog_service.find_commit_executable_info('firefox', state_index)
                if info is None:
                    raise AttributeError(f"Could not find binary url for '{state_index}'")
                binary_base_url = info['base_url']
                return [
                    f'{binary_base_url}jsshell-linux-x86_64.zip',
                    f'{binary_base_url}jsshell-linux-x86_64.tar.xz',
                ]
