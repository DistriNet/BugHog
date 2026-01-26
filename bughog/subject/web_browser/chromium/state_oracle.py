import logging
import re
from typing import Literal

import requests

from bughog import util
from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service

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

    # @Cache.cache_in_db('web_browser', 'chromium')
    def find_commit_of_release(self, release_version: int) -> tuple[int, str]:
        return bughog_service.find_version_commit('chromium', release_version, has_public_executable=True)

    def get_most_recent_major_release_version(self) -> int:
        return bughog_service.find_latest_major_version('chromium')

    # @Cache.cache_in_db('web_browser', 'chromium')
    def has_public_executable(self, state_index: int, state_type: Literal['release', 'commit']) -> bool:
        match state_type:
            case 'release':
                # TODO: make more efficient (by possibly adding to bughog service)
                commit_nb, _ = bughog_service.find_version_commit('chromium', state_index, has_public_executable=True)
                executable_info = bughog_service.find_commit_executable_info('chromium', commit_nb)
                if executable_info is None:
                    return self.has_public_executable(commit_nb, 'commit')
                return True
            case 'commit':
                url = f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{state_index}%2Fchrome-linux.zip'
                req = requests.get(url)
                has_binary_online = req.status_code == 200
                # TODO: caching at factory
                return has_binary_online

    # @Cache.cache_in_db('web_browser', 'chromium')
    def get_executable_download_urls(self, state_index: int, state_type: Literal['release', 'commit']) -> list[str]:
        match state_type:
            case 'release':
                # TODO: make more efficient (by possibly adding to bughog service)
                commit_nb, _ = bughog_service.find_version_commit('chromium', state_index, has_public_executable=True)
                return self.get_executable_download_urls(commit_nb, 'commit')
            case 'commit':
                return [f'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{state_index}%2Fchrome-linux.zip?alt=media']

    def get_nearest_commit_with_executable(self, target_commit_nb: int, lower_bound: int, upper_bound: int) -> int | None:
        NotImplementedError()

    # Commit state functions

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        if commit_id is None:
            return None
        return f'https://chromium.googlesource.com/chromium/src/+/{commit_id}'
