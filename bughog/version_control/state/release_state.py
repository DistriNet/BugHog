from typing import Literal, Optional

from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.base import ShallowState, State
from bughog.version_control.state.commit_state import CommitState
from bughog.version_control.state_not_found import StateNotFound
from bughog.version_control.version import Version


class ReleaseState(State):
    def __init__(
        self,
        oracle: StateOracle,
        release_version: Version,
        index: int | None = None,
        commit_nb: int | None = None,
        commit_id: str | None = None,
    ):
        super().__init__(oracle)
        self.release_version = release_version
        self._index = index if index is not None else release_version.major
        if commit_nb is None or commit_id is None:
            self._commit_nb, self.commit_id = self.oracle.find_commit_of_release(self.release_version)
        else:
            self._commit_nb = commit_nb
            self.commit_id = commit_id

    @property
    def name(self) -> str:
        return f'v_{str(self.release_version)}'

    @property
    def type(self) -> Literal['release']:
        return 'release'

    @property
    def index(self) -> int:
        return self._index

    @property
    def commit_nb(self) -> int:
        return self._commit_nb

    @property
    def commit_url(self) -> Optional[str]:
        return None

    def has_public_executable(self) -> bool:
        return self.oracle.has_public_release_executable(self.release_version)

    def get_executable_source_urls(self) -> list[str]:
        return self.oracle.get_release_executable_urls(self.release_version)

    def convert_to_commit_state(self) -> CommitState:
        try:
            return CommitState(self.oracle, commit_nb=self.commit_nb)
        except StateNotFound:
            offset = 1
            while True:
                for neighbor in (self.commit_nb - offset, self.commit_nb + offset):
                    try:
                        return CommitState(self.oracle, commit_nb=neighbor)
                    except StateNotFound:
                        continue
                offset += 1

    def to_shallow_state(self) -> ShallowState:
        return ShallowState('release', self.release_version, self.commit_nb, self.commit_id)

    def __str__(self):
        return f'ReleaseState(version: {self.release_version}, rev: {self.commit_nb})'

    def __repr__(self):
        return f'ReleaseState(version: {self.release_version}, rev: {self.commit_nb})'

    def __hash__(self) -> int:
        return hash((self.type, self.release_version))
