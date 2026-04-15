import logging
import re

import requests

from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.util import http
from bughog.version_control.conversion import bughog_service, github
from bughog.version_control.version import Version

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
    def find_commit_of_release(self, release_version: Version) -> tuple[int, str]:
        # TODO: make more efficient (possibly by adding functionality to bughog service)
        all_release_tags = self.__get_all_release_tags()
        major_release_tag = self._get_earliest_tag_version_match(all_release_tags, release_version)
        commit_id = github.find_commit_id_from_tag('v8', 'v8', major_release_tag)
        commit_nb = self.find_commit_nb(commit_id)
        return commit_nb, commit_id

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        if commit_id is None:
            return None
        return f'https://chromium.googlesource.com/v8/v8/+/{commit_id}'

    # Public executables

    def get_earliest_supported_release_version(self) -> Version:
        return Version('6')

    def get_latest_supported_release_version(self) -> Version:
        all_release_tags = self.__get_all_release_tags()
        versions = list(Version(tag.split('.')[0]) for tag in all_release_tags)
        return max(versions)

    @Cache.cache_in_db('js_engine', 'v8')
    def has_public_release_executable(self, version: Version) -> bool:
        for url in self.get_release_executable_urls(version):
            resp = requests.head(url, allow_redirects=True)
            if resp.status_code == 200:
                return True
        return False

    @Cache.cache_in_db('js_engine', 'v8')
    def has_public_commit_executable(self, commit_nb: int) -> bool:
        for url in self.get_commit_executable_urls(commit_nb):
            resp = requests.head(url, allow_redirects=True)
            if resp.status_code == 200:
                return True
        return False

    def get_nearest_commit_with_executable(
        self, target_commit_nb: int, lower_bound: int, upper_bound: int
    ) -> int | None:
        NotImplementedError()

    @Cache.cache_in_db('js_engine', 'v8')
    def get_release_executable_urls(self, version: Version) -> list[str]:
        commit_nb = self.find_commit_of_release(version)[0]
        return self.get_commit_executable_urls(commit_nb)

    @Cache.cache_in_db('js_engine', 'v8')
    def get_commit_executable_urls(self, commit_nb: int) -> list[str]:
        # Debug:
        return [
            f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-debug%2Fasan-linux-debug-v8-component-{commit_nb}.zip?alt=media',
            f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-debug%2Fd8-asan-linux-debug-v8-component-{commit_nb}.zip?alt=media',
        ]
        # Release
        # return [f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-release%2Fd8-linux-release-v8-component-{commit_nb}.zip?alt=media']

    @staticmethod
    @Cache.cache_in_db('js_engine', 'v8', ttl=24)
    def __get_all_release_tags() -> list[str]:
        url = 'https://chromium.googlesource.com/v8/v8.git/+refs'
        html = http.request_html(url).decode()
        all_tags = re.findall(r'/refs/tags/(\d+(?:\.\d+)+)', html)
        pattern = re.compile(r'^\d+\.\d+\.\d+$')
        return [tag for tag in all_tags if pattern.match(tag)]
