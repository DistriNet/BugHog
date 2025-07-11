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
        major_versions = [int(tag.split('.')[0]) for tag in all_release_tags]
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

    def has_publicly_available_commit_executable(self, commit_nb: int) -> bool:
        for url in self.get_commit_executable_download_urls(commit_nb):
            resp = requests.head(url)
            if resp.status_code == 200:
                return True
        return False

    def get_commit_executable_download_urls(self, commit_nb: int) -> list[str]:
        return [f'https://www.googleapis.com/download/storage/v1/b/v8-asan/o/linux-release%2Fd8-linux-release-v8-component-{commit_nb}.zip?alt=media']


    @staticmethod
    def __get_all_release_tags() -> list[str]:
        url = "https://chromium.googlesource.com/v8/v8.git/+refs"
        html = util.request_html(url).decode()

        tags_section = html.split("<h3>Tags</h3>", 1)
        if len(tags_section) < 2:
            return []
        ul_start = tags_section[1].find("<ul>")
        ul_end = tags_section[1].find("</ul>", ul_start)
        if ul_start == -1 or ul_end == -1:
            return []
        ul_html = tags_section[1][ul_start:ul_end]
        all_tags = re.findall(r'<li><a href="[^"]+">([^<]+)</a></li>', ul_html)
        pattern = re.compile(r"^\d+\.\d+\.\d+$")
        return [tag for tag in all_tags if pattern.match(tag)]

    @staticmethod
    def __get_earliest_tag_with_major(all_release_tags: list[str], major_release: int) -> str:
        pattern = re.compile(r"^\d+\.\d+\.\d+$")
        # Filter tags matching x.y.z format and starting with the given major
        filtered_tags = [tag for tag in all_release_tags if pattern.match(tag) and tag.startswith(f"{major_release}.")]
        if not filtered_tags:
            return None

        def version_tuple(tag):
            return tuple(int(x) for x in tag.split("."))

        sorted_tags = sorted(filtered_tags, key=version_tuple)
        return sorted_tags[0]
