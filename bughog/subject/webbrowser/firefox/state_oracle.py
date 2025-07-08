from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.subject.webbrowser.state_cache import PublicBrowserStateCache


class FirefoxStateOracle(StateOracle):

    @Cache.cache_in_db('webbrowser', 'firefox')
    def find_commit_nb(self, commit_id: str) -> int:
        return PublicBrowserStateCache.firefox_get_commit_number(commit_id)

    @Cache.cache_in_db('webbrowser', 'firefox')
    def find_commit_id(self, commit_nb: int) -> str:
        return PublicBrowserStateCache.firefox_get_commit_id(commit_nb)

    @Cache.cache_in_db('webbrowser', 'firefox')
    def has_publicly_available_release_executable(self, major_version: int) -> bool:
        return True

    def get_release_executable_download_urls(self, major_version: int) -> list[str]:
        return [
            f'https://ftp.mozilla.org/pub/firefox/releases/{major_version}.0/linux-x86_64/en-US/firefox-{major_version}.0.tar.bz2',
            f'https://ftp.mozilla.org/pub/firefox/releases/{major_version}.0/linux-x86_64/en-US/firefox-{major_version}.0.tar.xz',
        ]

    @Cache.cache_in_db('webbrowser', 'firefox')
    def has_publicly_available_commit_executable(self, commit_nb: int) -> bool:
        return PublicBrowserStateCache.firefox_has_executable_for(commit_nb=commit_nb)

    def get_commit_executable_download_urls(self, commit_nb: int) -> list[str]:
        commit_id = self.find_commit_id(commit_nb)
        result = PublicBrowserStateCache.firefox_get_executable_info(commit_id)
        if result is None:
            raise AttributeError(f"Could not find binary url for '{commit_nb}'")
        binary_base_url = result['files_url']
        app_version = result['app_version']
        return [
            f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.bz2',
            f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.xz',
        ]
