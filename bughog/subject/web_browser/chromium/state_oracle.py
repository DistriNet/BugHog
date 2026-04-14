import logging
import re

import requests

from bughog import util
from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service
from bughog.version_control.version import Version

logger = logging.getLogger(__name__)

REV_ID_BASE_URL = 'https://chromium.googlesource.com/chromium/src/+/'
REV_NUMBER_BASE_URL = 'http://crrev.com/'


class ChromiumStateOracle(StateOracle):
    @Cache.cache_in_db('web_browser', 'chromium')
    def find_commit_nb(self, commit_id: str) -> int:
        # First use bughog service.
        try:
            return bughog_service.find_commit_nb('chromium', commit_id)
        except Exception:
            pass

        # If not found, use googlesource.
        url = f'{REV_ID_BASE_URL}{commit_id}'
        html = util.request_html(url).decode()
        commit_nb = self._parse_commit_nb_from_googlesource(html)
        if commit_nb is None:
            logger.error(f"Could not parse commit number on '{url}'")
            raise AttributeError(f"Could not parse commit number on '{url}'")
        assert re.match(r'[0-9]{1,7}', commit_nb)
        return int(commit_nb)

    @Cache.cache_in_db('web_browser', 'chromium')
    def find_commit_id(self, commit_nb: int) -> str | None:
        # First use bughog service.
        if commit_id := bughog_service.find_commit_id('chromium', commit_nb):
            return commit_id

        # If not found, use crrev.com.
        try:
            final_url = util.request_final_url(f'{REV_NUMBER_BASE_URL}{commit_nb}')
        except util.ResourceNotFound:
            return None
        commit_id = final_url[-40:]
        assert re.match(r'[a-z0-9]{40}', commit_id)
        return commit_id

    def get_earliest_supported_release_version(self) -> Version:
        return Version('20')

    # @Cache.cache_in_db('web_browser', 'chromium')
    def has_public_commit_executable(self, commit_nb: int) -> bool:
        url = f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{commit_nb}%2Fchrome-linux.zip'
        req = requests.get(url)
        # TODO: caching at factory
        return req.status_code == 200

    # @Cache.cache_in_db('web_browser', 'chromium')
    def get_release_executable_urls(self, version: Version) -> list[str]:
        # TODO: make more efficient (by possibly adding to bughog service)
        commit_nb, _ = bughog_service.find_version_info('chromium', version, has_public_executable=True)
        return self.get_commit_executable_urls(commit_nb)

    # @Cache.cache_in_db('web_browser', 'chromium')
    def get_commit_executable_urls(self, commit_nb: int) -> list[str]:
        return [
            f'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{commit_nb}%2Fchrome-linux.zip?alt=media'
        ]

    def get_nearest_commit_with_executable(
        self, target_commit_nb: int, lower_bound: int, upper_bound: int
    ) -> int | None:
        NotImplementedError()

    # Commit state functions

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        if commit_id is None:
            return None
        return f'https://chromium.googlesource.com/chromium/src/+/{commit_id}'
