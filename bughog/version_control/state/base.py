from __future__ import annotations

import base64
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from bughog.evaluation.experiment_result import ExperimentResult
from bughog.subject.state_oracle import StateOracle


@dataclass(frozen=True)
class ShallowState:
    type: str
    major_version: int|None
    commit_nb: int|None
    commit_id: str|None

    @property
    def dict(self) -> dict:
        fields = {
            'type': self.type,
            'major_version': self.major_version,
            'commit_nb': self.commit_nb,
            'commit_id': self.commit_id,
        }
        return {k: v for k, v in fields.items() if v is not None}


class State(ABC):
    def __init__(self, oracle: StateOracle):
        super().__init__()
        self.oracle = oracle
        self.result_variables: Optional[set[tuple[str, str]]] = None

    def has_dirty_result(self) -> bool:
        """
        Returns whether this state has a dirty result.

        :returns bool: True if this state has a result, which is dirty.
        """
        return ExperimentResult.poc_is_dirty(self.result_variables)

    def has_dirty_or_no_result(self) -> bool:
        """
        Returns whether this state has no result or a dirty result.

        :returns bool: True if this state has no result, or a dirty result.
        """
        return ExperimentResult.poc_is_dirty(self.result_variables)

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

    def to_dict(self) -> dict:
        return self.to_shallow_state().dict

    @staticmethod
    def from_dict(subject_type: str, subject_name: str, data: dict) -> State:
        from bughog.subject import factory
        from bughog.version_control.state.commit_state import CommitState
        from bughog.version_control.state.release_state import ReleaseState

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
        return self.has_artisanal_executable() or self.has_public_executable()

    @abstractmethod
    def has_public_executable(self) -> bool:
        pass

    @abstractmethod
    def get_executable_source_urls(self) -> list[str]:
        """
        Returns a list of URLs where the associated binary can potentially be downloaded from.
        """
        pass

    def has_artisanal_executable(self) -> bool:
        return self.oracle.has_artisanal_executable(self.name)

    def get_artisanal_executable_folder(self) -> str:
        return self.oracle.get_artisanal_executable_folder(self.name)

    def get_previous_and_next_state_with_executable(self) -> tuple[State, State]:
        raise NotImplementedError(f'This function is not implemented for {self}')

    @abstractmethod
    def to_shallow_state(self) -> ShallowState:
        pass

    def __repr__(self) -> str:
        return f'State(index={self.index})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return False
        return self.index == other.index

    def __hash__(self) -> int:
        return hash(self.index)
