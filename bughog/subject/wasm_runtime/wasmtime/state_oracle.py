import re

from bughog.database.mongo.cache import Cache
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service, github
from bughog.version_control.version import Version


class WasmtimeStateOracle(StateOracle):
    """
    State oracle for Wasmtime.
    """

    def __init__(self, subject_type: str, subject_name: str) -> None:
        super().__init__(subject_type, subject_name, only_artisanal=True)

    @Cache.cache_in_db('wasm_runtime', 'wasmtime')
    def find_commit_nb(self, commit_id: str) -> int:
        return bughog_service.find_commit_nb('wasmtime', commit_id)

    @Cache.cache_in_db('wasm_runtime', 'wasmtime')
    def find_commit_id(self, commit_nb: int) -> str | None:
        return bughog_service.find_commit_id('wasmtime', commit_nb)

    @Cache.cache_in_db('wasm_runtime', 'wasmtime')
    def find_commit_of_release(self, release_version: Version) -> tuple[int, str]:
        # TODO: make more efficient, possibly by adding functionality to bughog service
        all_release_tags = self.__get_all_release_tags()
        major_release_tag = self._get_earliest_tag_version_match(all_release_tags, release_version)
        commit_id = github.find_commit_id_from_tag('bytecodealliance', 'wasmtime', major_release_tag)
        commit_nb = self.find_commit_nb(commit_id)
        return commit_nb, commit_id

    def get_earliest_supported_release_version(self) -> Version:
        return Version('1')

    def get_latest_supported_release_version(self) -> Version:
        all_release_tags = self.__get_all_release_tags()
        versions = [self.get_full_version_from_release_tag(tag) for tag in all_release_tags]
        return max(versions)

    @staticmethod
    @Cache.cache_in_db('wasm_runtime', 'wasmtime', ttl=24)
    def __get_all_release_tags() -> list[str]:
        all_tags = github.get_all_tags('bytecodealliance', 'wasmtime')
        pattern = re.compile(r'^v\d+\.\d+\.\d+$')
        return [tag for tag in all_tags if pattern.match(tag)]

    """
    Online executables
    """

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        if commit_id is None:
            return None
        return f'https://github.com/bytecodealliance/wasmtime/commit/{commit_id}'

    def has_public_release_executable(self, version: Version) -> bool:
        return False

    def has_public_commit_executable(self, commit_nb: int) -> bool:
        return False

    def get_release_executable_urls(self, version: Version) -> list[str]:
        return []

    def get_commit_executable_urls(self, commit_nb: int) -> list[str]:
        return []

    def get_nearest_commit_with_executable(
        self, target_commit_nb: int, lower_bound: int, upper_bound: int
    ) -> int | None:
        NotImplementedError()
