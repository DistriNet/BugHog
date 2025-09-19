from __future__ import annotations

import logging
from typing import Optional

from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.base import ShallowState, State

logger = logging.getLogger(__name__)


class CommitState(State):
    def __init__(self, oracle: StateOracle, commit_id: Optional[str] = None, commit_nb: Optional[int] = None):
        super().__init__(oracle)
        if commit_id is None and commit_nb is None:
            raise ValueError('A state must be initialized with either a commit id or commit number.')

        self.commit_id = commit_id if commit_id is not None else self.oracle.find_commit_id(commit_nb)
        self._commit_nb = commit_nb if commit_nb is not None else self.oracle.find_commit_nb(commit_id)

        if self.commit_id is not None and not self.oracle.is_valid_commit_id(self.commit_id):
            raise ValueError(f"Invalid commit id '{self.commit_id}'.")
        if self._commit_nb is not None and not self.oracle.is_valid_commit_nb(self._commit_nb):
            raise ValueError(f"Invalid commit number '{self._commit_nb}'.")

    @staticmethod
    def get_name(index: int) -> str:
        return f'c_{index}'

    @property
    def type(self) -> str:
        return 'commit'

    @property
    def index(self) -> int:
        return self._commit_nb

    @property
    def commit_nb(self) -> int:
        return self._commit_nb

    @property
    def commit_url(self) -> Optional[str]:
        return self.oracle.get_commit_url(self.commit_nb, self.commit_id)

    def to_dict(self) -> dict:
        fields = {
            'type': self.type,
            'commit_nb': self.commit_nb,
            'commit_id': self.commit_id,
            'commit_url': self.commit_url,
        }
        return {k: v for k, v in fields.items() if v is not None}

    def has_public_executable(self) -> bool:
        return self.oracle.has_public_commit_executable(self.commit_nb)

    def get_executable_source_urls(self) -> list[str]:
        return self.oracle.get_commit_executable_download_urls(self.commit_nb)

    def to_shallow_state(self) -> ShallowState:
        return ShallowState(
            'commit',
            None,
            self.commit_nb,
            self.commit_id
        )

    def __str__(self):
        return f'CommitState(number: {self.commit_nb}, id: {self.commit_id})'

    def __repr__(self):
        return f'CommitState(number: {self.commit_nb}, id: {self.commit_id})'
