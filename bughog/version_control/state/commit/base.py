from __future__ import annotations

import logging
from typing import Optional

from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.base import State

logger = logging.getLogger(__name__)


class CommitState(State):
    def __init__(self, oracle: StateOracle, commit_id: Optional[str] = None, commit_nb: Optional[int] = None):
        super().__init__(oracle)
        if commit_id is None and commit_nb is None:
            raise AttributeError('A state must be initiliazed with either a revision id or revision number')

        self._commit_id = commit_id
        self._commit_nb = commit_nb
        self._fetch_missing_data()

        if self._commit_id is not None and not self.oracle.is_valid_commit_id(self._commit_id):
            raise AttributeError(f"Invalid revision id '{self._commit_id}' for state '{self}'")

        if self._commit_nb is not None and not self.oracle.is_valid_commit_nb(self._commit_nb):
            raise AttributeError(f"Invalid revision number '{self._commit_nb}' for state '{self}'")

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

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'commit_nb': self._commit_nb,
            'commit_id': self._commit_id,
        }

    def _has_commit_id(self) -> bool:
        return self._commit_id is not None

    def _has_commit_nb(self) -> bool:
        return self._commit_nb is not None

    def _fetch_missing_data(self) -> None:
        """
        States are initialized with either a revision id or revision number.
        This method attempts to fetch other data to complete this state object.
        """
        # TODO: solve with oracle
        # # First check if the missing data is available in the cache
        # if self._commit_id and self._commit_nb:
        #     return
        # if state := MongoDB().get_complete_state_dict_from_binary_availability_cache(self):
        #     if self._commit_id is None:
        #         self._commit_id = state.get('revision_id', None)
        #     if self._commit_nb is None:
        #         self._commit_nb = state.get('revision_number', None)
        # # If not, fetch the missing data from the parser
        # if self._commit_id is None:
        #     self._commit_id = self.oracle.find_commit_id(self.commit_nb)
        # if self._commit_nb is None:
        #     self._commit_nb = self.oracle.find_commit_nb(self._commit_id)

    def has_publicly_available_executable(self) -> bool:
        return self.oracle.has_publicly_available_commit_executable(self.commit_nb)

    def get_executable_source_urls(self) -> list[str]:
        return self.oracle.get_commit_executable_download_urls(self.commit_nb)

    def __str__(self):
        return f'CommitState(number: {self._commit_nb}, id: {self._commit_id})'

    def __repr__(self):
        return f'CommitState(number: {self._commit_nb}, id: {self._commit_id})'
