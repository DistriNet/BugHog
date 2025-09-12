import re

from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.revision_parser import bughog, github


class WasmtimeStateOracle(StateOracle):
    """
    State oracle for Wasmtime.
    """

    @Cache.cache_in_db('wasm_runtime', 'wasmtime')
    def find_commit_nb(self, commit_id: str) -> int:
        return bughog.get_commit_nb('wasmtime', commit_id)

    @Cache.cache_in_db('wasm_runtime', 'wasmtime')
    def find_commit_id(self, commit_nb: int) -> str:
        return bughog.get_commit_id('wasmtime', commit_nb)

    @Cache.cache_in_db('wasm_runtime', 'wasmtime')
    def find_commit_nb_of_release(self, release_version: int) -> int:
        commit_id = self.find_commit_id_of_release(release_version)
        return self.find_commit_nb(commit_id)

    @Cache.cache_in_db('wasm_runtime', 'wasmtime')
    def find_commit_id_of_release(self, release_version: int) -> str:
        all_release_tags = self.__get_all_release_tags()
        major_release_tag = self._get_earliest_tag_with_major(all_release_tags, release_version)
        return bughog.get_commit_id_of_release('wasmtime', major_release_tag)

    def get_most_recent_major_release_version(self) -> int:
        all_release_tags = self.__get_all_release_tags()
        truncated_tags = [self.get_full_version_from_release_tag(tag) for tag in all_release_tags]
        major_versions = set(int(tag.split('.')[0]) for tag in truncated_tags if tag is not None)
        return max(major_versions)

    @staticmethod
    @Cache.cache_in_db('wasm_runtime', 'wasmtime', ttl=24)
    def __get_all_release_tags() -> list[str]:
        all_tags = github.get_all_tags('bytecodealliance', 'wasmtime')
        pattern = re.compile(r'^v\d+\.\d+\.\d+$')
        return [tag for tag in all_tags if pattern.match(tag)]

    """
    Online executables
    """

    def get_commit_url(self, commit_nb: int, commit_id: str) -> str:
        return f'https://github.com/bytecodealliance/wasmtime/commit/{commit_id}'

    def has_public_release_executable(self, major_version: int) -> bool:
        return False

    def get_release_executable_download_urls(self, major_version: int) -> list[str]:
        return []

    def has_public_commit_executable(self, commit_nb: int) -> bool:
        return False

    def get_commit_executable_download_urls(self, commit_nb: int) -> list[str]:
        raise Exception('Only artisanal executables are available.')
