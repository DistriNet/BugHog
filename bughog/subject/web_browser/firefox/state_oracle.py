from typing import Literal

from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service


class FirefoxStateOracle(StateOracle):
    # @Cache.cache_in_db('web_browser', 'firefox')
    def find_commit_nb(self, commit_id: str) -> int:
        return bughog_service.find_commit_nb('firefox', commit_id)

    # @Cache.cache_in_db('web_browser', 'firefox')
    def find_commit_id(self, commit_nb: int) -> str | None:
        return bughog_service.find_commit_id('firefox', commit_nb)

    # @Cache.cache_in_db('web_browser', 'firefox')
    def find_commit_of_release(self, release_version: int) -> tuple[int, str]:
        return bughog_service.find_version_commit('firefox', release_version)

    def get_oldest_supported_release_version(self) -> int:
        return 20

    def get_most_recent_major_release_version(self) -> int:
        return bughog_service.find_latest_major_version('firefox')

    @Cache.cache_in_db('web_browser', 'firefox')
    def has_public_executable(self, state_index: int, state_type: Literal['release', 'commit']) -> bool:
        match state_type:
            case 'release':
                return True
            case 'commit':
                return bughog_service.find_commit_executable_info('firefox', state_index) is not None

    def get_executable_download_urls(self, state_index: int, state_type: Literal['release', 'commit']) -> list[str]:
        match state_type:
            case 'release':
                return [
                    f'https://ftp.mozilla.org/pub/firefox/releases/{state_index}.0/linux-x86_64/en-US/firefox-{state_index}.0.tar.bz2',
                    f'https://ftp.mozilla.org/pub/firefox/releases/{state_index}.0/linux-x86_64/en-US/firefox-{state_index}.0.tar.xz',
                ]
            case 'commit':
                info = bughog_service.find_commit_executable_info('firefox', state_index)
                if info is None:
                    raise AttributeError(f"Could not find binary url for '{state_index}'")
                binary_base_url = info['base_url']
                app_version = info['app_version']
                return [
                    f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.bz2',
                    f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.xz',
                ]

    def get_nearest_commit_with_executable(self, target_commit_nb: int, lower_bound: int, upper_bound: int) -> int | None:
        NotImplementedError()

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        if commit_id is None:
            return None
        return f'https://hg.mozilla.org/releases/mozilla-release/rev/{commit_id}'
