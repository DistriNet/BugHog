import logging
import re
from typing import Literal

import requests

from bughog import util
from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service, github

logger = logging.getLogger(__name__)


class V8StateOracle(StateOracle):
    """
    State oracle for V8.

    More information:
    - https://v8.dev/docs/version-numbers
    - https://commondatastorage.googleapis.com/v8-asan/index.html
    """

    # Commit / revision logic

    @Cache.cache_in_db('js_engine', 'v8')
    def find_commit_nb(self, commit_id: str) -> int:
        return bughog_service.find_commit_nb('v8', commit_id)

    @Cache.cache_in_db('js_engine', 'v8')
    def find_commit_id(self, commit_nb: int) -> str | None:
        return bughog_service.find_commit_id('v8', commit_nb)

    @Cache.cache_in_db('js_engine', 'v8')
    def find_commit_of_release(self, release_version: int) -> tuple[int, str]:
        # TODO: make more efficient (possibly by adding functionality to bughog service)
        all_release_tags = self.__get_all_release_tags()
        major_release_tag = self._get_earliest_tag_with_major(all_release_tags, release_version)
        commit_id = github.find_commit_id_from_tag('v8', 'v8', major_release_tag)
        commit_nb = self.find_commit_nb(commit_id)
        return commit_nb, commit_id

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        if commit_id is None:
            return None
        return f'https://chromium.googlesource.com/v8/v8/+/{commit_id}'

    # Public executables

    def get_most_recent_major_release_version(self) -> int:
        all_release_tags = self.__get_all_release_tags()
        major_versions = set(int(tag.split('.')[0]) for tag in all_release_tags)
        return max(major_versions)

    @Cache.cache_in_db('js_engine', 'v8')
    def has_public_executable(self, state_index: int, state_type: Literal['release', 'commit']) -> bool:
        for url in self.get_executable_download_urls(state_index, state_type):
            resp = requests.head(url, allow_redirects=True)
            if resp.status_code == 200:
                return True
        return False

    def get_nearest_commit_with_executable(
        self, target_commit_nb: int, lower_bound: int, upper_bound: int
    ) -> int | None:
        NotImplementedError()

    @Cache.cache_in_db('js_engine', 'v8')
    def get_executable_download_urls(self, state_index: int, state_type: Literal['release', 'commit']) -> list[str]:
        match state_type:
            case 'release':
                commit_nb = self.find_commit_of_release(state_index)[0]
                return self.get_executable_download_urls(commit_nb, 'commit')
            case 'commit':
                # Debug:
                return [
                    f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-debug%2Fasan-linux-debug-v8-component-{state_index}.zip?alt=media',
                    f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-debug%2Fd8-asan-linux-debug-v8-component-{state_index}.zip?alt=media',
                ]
                # Release
                # return [f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-release%2Fd8-linux-release-v8-component-{state_index}.zip?alt=media']

    @staticmethod
    @Cache.cache_in_db('js_engine', 'v8', ttl=24)
    def __get_all_release_tags() -> list[str]:
        url = 'https://chromium.googlesource.com/v8/v8.git/+refs'
        html = util.request_html(url).decode()
        all_tags = re.findall(r'/refs/tags/(\d+(?:\.\d+)+)', html)
        pattern = re.compile(r'^\d+\.\d+\.\d+$')
        return [tag for tag in all_tags if pattern.match(tag)]
