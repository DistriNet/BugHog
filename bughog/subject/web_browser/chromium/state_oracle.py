import logging
import re

import requests

from bughog import util
from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.subject.web_browser.state_cache import PublicBrowserStateCache

logger = logging.getLogger(__name__)

REV_ID_BASE_URL = 'https://chromium.googlesource.com/chromium/src/+/'
REV_NUMBER_BASE_URL = 'http://crrev.com/'


class ChromiumStateOracle(StateOracle):
    @Cache.cache_in_db('web_browser', 'chromium')
    def find_commit_nb(self, commit_id: str) -> int:
        url = f'{REV_ID_BASE_URL}{commit_id}'
        html = util.request_html(url).decode()
        commit_nb = self._parse_commit_nb_from_googlesource(html)
        if commit_nb is None:
            logger.error(f"Could not parse commit number on '{url}'")
            raise AttributeError(f"Could not parse commit number on '{url}'")
        assert re.match(r'[0-9]{1,7}', commit_nb)
        return int(commit_nb)

    @Cache.cache_in_db('web_browser', 'chromium')
    def find_commit_id(self, commit_nb: int) -> str:
        try:
            final_url = util.request_final_url(f'{REV_NUMBER_BASE_URL}{commit_nb}')
        except util.ResourceNotFound:
            logger.warning(f"Could not find commit id for commit number '{commit_nb}'")
            return None
        rev_id = final_url[-40:]
        assert re.match(r'[a-z0-9]{40}', rev_id)
        return rev_id

    @Cache.cache_in_db('web_browser', 'chromium')
    def find_commit_nb_of_release(self, release_version: int) -> int:
        return PublicBrowserStateCache.get_release_commit_nb('chromium', release_version)

    @Cache.cache_in_db('web_browser', 'chromium')
    def find_commit_id_of_release(self, release_version: int) -> str:
        return PublicBrowserStateCache.get_release_commit_id('chromium', release_version)

    def get_most_recent_major_release_version(self) -> int:
        return PublicBrowserStateCache.get_most_recent_major_version('chromium')

    # Release state functions

    @Cache.cache_in_db('web_browser', 'chromium')
    def has_public_release_executable(self, major_version: int) -> bool:
        # TODO: check cache at factory
        commit_nb = PublicBrowserStateCache.get_release_commit_nb('chromium', major_version)
        return self.has_public_commit_executable(commit_nb)

    @Cache.cache_in_db('web_browser', 'chromium')
    def get_release_executable_download_urls(self, major_version: int) -> list[str]:
        commit_nb = PublicBrowserStateCache.get_release_commit_nb('chromium', major_version)
        return self.get_commit_executable_download_urls(commit_nb)

    # Commit state functions

    def get_commit_url(self, commit_nb: int, commit_id: str) -> str:
        return f'https://chromium.googlesource.com/chromium/src/+/{commit_id}'

    @Cache.cache_in_db('web_browser', 'chromium')
    def has_public_commit_executable(self, commit_nb: int) -> bool:
        url = f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{commit_nb}%2Fchrome-linux.zip'
        req = requests.get(url)
        has_binary_online = req.status_code == 200
        # TODO: caching at factory
        return has_binary_online

    def get_commit_executable_download_urls(self, commit_nb: int) -> list[str]:
        return [f'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{commit_nb}%2Fchrome-linux.zip?alt=media']
