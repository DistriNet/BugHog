from __future__ import annotations

import base64
import os
import pickle
from abc import ABC, abstractmethod
from typing import Optional

from bughog.evaluation.experiment_result import ExperimentResult
from bughog.subject.state_oracle import StateOracle


class State(ABC):
    def __init__(self, oracle: StateOracle):
        self.oracle = oracle
        self.result_variables: Optional[set[tuple[str, str]]] = None

    def has_dirty_result(self) -> bool:
        """
        Returns whether this state has a dirty result.

        :returns bool: True if this state has a result, which is dirty.
        """
        return self.result_variables is not None and ExperimentResult.poc_is_dirty(self.result_variables)

    def has_dirty_or_no_result(self) -> bool:
        """
        Returns whether this state has no result or a dirty result.

        :returns bool: True if this state has no result, or a dirty result.
        """
        return self.result_variables is None or ExperimentResult.poc_is_dirty(self.result_variables)

    def has_same_outcome(self, other: State) -> bool:
        """
        Returns whether this and the given other state share the same result outcome.

        :returns bool: True if states are both reproduced, not reproduced, or dirty.
        """
        if self.result_variables is None or other.result_variables is None:
            return False
        else:
            return ExperimentResult.poc_is_reproduced(self.result_variables) == ExperimentResult.poc_is_reproduced(other.result_variables) and ExperimentResult.poc_is_dirty(self.result_variables) == ExperimentResult.poc_is_dirty(other.result_variables)

    @property
    def name(self) -> str:
        return self.get_name(self.index)

    @staticmethod
    @abstractmethod
    def get_name(index: int) -> str:
        pass

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def index(self) -> int:
        """
        The index of the element in the sequence.
        """
        pass

    @property
    @abstractmethod
    def commit_nb(self) -> int:
        pass

    @property
    @abstractmethod
    def commit_url(self) -> Optional[str]:
        pass

    def serialize(self) -> str:
        """
        Returns a dictionary representation of the state.
        """
        pickled_bytes = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
        return base64.b64encode(pickled_bytes).decode('ascii')

    @staticmethod
    def deserialize(pickled_str: str) -> State:
        pickled_bytes = base64.b64decode(pickled_str)
        return pickle.loads(pickled_bytes)

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @staticmethod
    def from_dict(subject_type: str, subject_name: str, data: dict) -> State:
        from bughog.subject import factory
        from bughog.version_control.state.commit.base import CommitState
        from bughog.version_control.state.release.base import ReleaseState

        subject_class = factory.get_subject(subject_type, subject_name)
        oracle = subject_class.state_oracle
        match data['type']:
            case 'commit':
                return CommitState(oracle, commit_nb=data.get('commit_nb'), commit_id=data.get('commit_id'))
            case 'release':
                return ReleaseState(oracle, release_version=data['major_version'])
            case _:
                raise Exception(f'Unknown state type: {data["type"]}')

    def has_available_executable(self) -> bool:
        return self.has_local_executable() or self.has_publicly_available_executable()

    def get_local_executable_folder_path(self) -> str:
        return self.oracle.get_local_executable_folder_path(self.name)

    def has_local_executable(self) -> bool:
        return os.path.isdir(self.get_local_executable_folder_path())

    @abstractmethod
    def has_publicly_available_executable(self) -> bool:
        pass

    @abstractmethod
    def get_executable_source_urls(self) -> list[str]:
        """
        Returns a list of URLs where the associated binary can potentially be downloaded from.
        """
        pass

    def get_previous_and_next_state_with_executable(self) -> tuple[State, State]:
        raise NotImplementedError(f'This function is not implemented for {self}')

    def __repr__(self) -> str:
        return f'State(index={self.index})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return False
        return self.index == other.index

    def __hash__(self) -> int:
        return hash(self.index)
