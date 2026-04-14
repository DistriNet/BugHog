from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service
from bughog.version_control.version import Version


class FirefoxStateOracle(StateOracle):
    # @Cache.cache_in_db('web_browser', 'firefox')
    def find_commit_nb(self, commit_id: str) -> int:
        return bughog_service.find_commit_nb('firefox', commit_id)

    # @Cache.cache_in_db('web_browser', 'firefox')
    def find_commit_id(self, commit_nb: int) -> str | None:
        return bughog_service.find_commit_id('firefox', commit_nb)

    def get_earliest_supported_release_version(self) -> Version:
        return Version('20.0')

    @Cache.cache_in_db('web_browser', 'firefox')
    def has_public_release_executable(self, version: Version) -> bool:
        return True

    @Cache.cache_in_db('web_browser', 'firefox')
    def has_public_commit_executable(self, commit_nb: int) -> bool:
        return bughog_service.find_commit_executable_info('firefox', commit_nb) is not None

    def get_release_executable_urls(self, version: Version) -> list[str]:
        return [
            f'https://ftp.mozilla.org/pub/firefox/releases/{version}.0/linux-x86_64/en-US/firefox-{version}.0.tar.bz2',
            f'https://ftp.mozilla.org/pub/firefox/releases/{version}.0/linux-x86_64/en-US/firefox-{version}.0.tar.xz',
        ]

    def get_commit_executable_urls(self, commit_nb: int) -> list[str]:
        info = bughog_service.find_commit_executable_info('firefox', commit_nb)
        if info is None:
            raise AttributeError(f"Could not find binary url for '{commit_nb}'")
        binary_base_url = info['base_url']
        app_version = info['app_version']
        return [
            f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.bz2',
            f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.xz',
        ]

    def get_nearest_commit_with_executable(
        self, target_commit_nb: int, lower_bound: int, upper_bound: int
    ) -> int | None:
        NotImplementedError()

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        if commit_id is None:
            return None
        return f'https://hg.mozilla.org/releases/mozilla-release/rev/{commit_id}'
