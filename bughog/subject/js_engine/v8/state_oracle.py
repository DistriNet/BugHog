import logging
import re

import requests

from bughog import util
from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.revision_parser import github

logger = logging.getLogger(__name__)


class V8StateOracle(StateOracle):
    """
    State oracle for V8.

    More information:
    - https://v8.dev/docs/version-numbers
    - https://commondatastorage.googleapis.com/v8-asan/index.html
    """

    @Cache.cache_in_db("js_engine", "v8")
    def find_commit_nb(self, commit_id: str) -> int:
        return github.find_commit_nb("v8", "v8", commit_id)

    @Cache.cache_in_db("js_engine", "v8")
    def find_commit_id(self, commit_nb: int) -> str:
        return github.find_commit_id("v8", "v8", commit_nb)

    @Cache.cache_in_db("js_engine", "v8")
    def find_commit_nb_of_release(self, release_version: int) -> int:
        commit_id = self.find_commit_id_of_release(release_version)
        return self.find_commit_nb(commit_id)

    @Cache.cache_in_db("js_engine", "v8")
    def find_commit_id_of_release(self, release_version: int) -> str:
        all_release_tags = self.__get_all_release_tags()
        major_release_tag = self.__get_earliest_tag_with_major(all_release_tags, release_version)
        return github.find_commit_id_from_tag("v8", "v8", major_release_tag)

    def get_most_recent_major_release_version(self) -> int:
        all_release_tags = self.__get_all_release_tags()
        major_versions = set(int(tag.split('.')[0]) for tag in all_release_tags)
        return max(major_versions)


    # Release state functions

    @Cache.cache_in_db("js_engine", "v8")
    def has_publicly_available_release_executable(self, major_version: int) -> bool:
        for url in self.get_release_executable_download_urls(major_version):
            resp = requests.head(url)
            if resp.status_code == 200:
                return True
        return False

    @Cache.cache_in_db("js_engine", "v8")
    def get_release_executable_download_urls(self, major_version: int) -> list[str]:
        commit_nb = self.find_commit_nb_of_release(major_version)
        return self.get_commit_executable_download_urls(commit_nb)


    # Public commits

    def get_commit_url(self, commit_nb: int, commit_id: str) -> str:
        return f'https://chromium.googlesource.com/v8/v8/+/{commit_id}'

    def has_publicly_available_commit_executable(self, commit_nb: int) -> bool:
        for url in self.get_commit_executable_download_urls(commit_nb):
            resp = requests.head(url)
            if resp.status_code == 200:
                return True
        return False

    def get_commit_executable_download_urls(self, commit_nb: int) -> list[str]:
        # Debug:
        return [
            f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-debug%2Fasan-linux-debug-v8-component-{commit_nb}.zip?alt=media',
            f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-debug%2Fd8-asan-linux-debug-v8-component-{commit_nb}.zip?alt=media'
        ]
        # Release
        # return [f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-release%2Fd8-linux-release-v8-component-{commit_nb}.zip?alt=media']

    @staticmethod
    @Cache.cache_in_db("js_engine", "v8", ttl=24)
    def __get_all_release_tags() -> list[str]:
        url = "https://chromium.googlesource.com/v8/v8.git/+refs"
        html = util.request_html(url).decode()
        all_tags = re.findall(r'/refs/tags/(\d+(?:\.\d+)+)', html)
        pattern = re.compile(r"^\d+\.\d+\.\d+$")
        return [tag for tag in all_tags if pattern.match(tag)]

    @staticmethod
    def __get_earliest_tag_with_major(all_release_tags: list[str], major_release: int) -> str:
        pattern = re.compile(r"^\d+\.\d+\.\d+$")
        # Filter tags matching x.y.z format and starting with the given major
        filtered_tags = [tag for tag in all_release_tags if pattern.match(tag) and tag.startswith(f"{major_release}.")]
        if not filtered_tags:
            Exception(f'Could not find earliest tag for {major_release}.')

        def version_tuple(tag):
            return tuple(int(x) for x in tag.split("."))

        sorted_tags = sorted(filtered_tags, key=version_tuple)
        return sorted_tags[0]
