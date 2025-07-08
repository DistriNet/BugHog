from __future__ import annotations

import base64
import pickle
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional

from bughog.subject.state_oracle import StateOracle


@dataclass(frozen=True)
class StateResult:
    requests: list[dict[str, str]]
    logs: list[str]
    result_vars: list[dict[str, str]]
    is_dirty: bool
    reproduced: bool

    def has_same_outcome(self, other: StateResult) -> bool:
        """
        Returns whether this and the given other result share the same outcome.

        :returns bool: True if both state results are reproduced, not reproduced, or are both dirty.
        """
        return self.is_dirty == other.is_dirty and self.reproduced == other.reproduced

    def from_dict(result: dict) -> StateResult:
        return StateResult(
            result['requests'],
            result
        )

    def __repr__(self) -> str:
        return f'StateResult(reproduced={self.reproduced}, dirty={self.is_dirty})'


class State:
    def __init__(self, oracle: StateOracle):
        self.oracle = oracle
        self.result_variables: Optional[State]

    # def has_dirty_result(self) -> bool:
    #     """
    #     Returns whether this state has a dirty result.

    #     :returns bool: True if this state has a result, which is dirty.
    #     """
    #     return self.result is not None and self.result.is_dirty

    # def has_dirty_or_no_result(self) -> bool:
    #     """
    #     Returns whether this state has no result or a dirty result.

    #     :returns bool: True if this state has no result, or a dirty result.
    #     """
    #     return self.result is None or self.result.is_dirty

    # def has_same_outcome(self, other: State) -> bool:
    #     """
    #     Returns whether this and the given other state share the same result outcome.

    #     :returns bool: True if states are both reproduced, not reproduced, or dirty.
    #     """
    #     if self.result is None or other.result is None:
    #         return False
    #     else:
    #         return self.result.has_same_outcome(other.result)

    @property
    @abstractmethod
    def name(self) -> str:
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

    @abstractmethod
    def to_parameters(self) -> StateParameters:
        pass

    @classmethod
    def from_parameters(cls, oracle: StateOracle, params: StateParameters) -> State:
        from bughog.version_control.states.revisions.base import CommitState
        from bughog.version_control.states.versions.base import ReleaseState

        if params.type == 'release':
            return ReleaseState(oracle, params.version_or_commit)
        elif params.type == 'commit':
            return CommitState(oracle, commit_nb=params.version_or_commit)
        else:
            raise ValueError('Unknown state type')

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
        
        subject_class = factory.get_subject_class(subject_type, subject_name)
        oracle = subject_class.state_oracle
        match data['type']:
            case 'commit':
                state_class = subject_class.commit_state_class
                return state_class(oracle, commit_nb=data.get('commit_nb'), commit_id=data.get('commit_id'))
            case 'release':
                state_class = subject_class.release_state_class
                return state_class(oracle, release_version=data['release_version'])
            case _:
                raise Exception(f'Unknown state type: {data["type"]}')

    @abstractmethod
    def has_executable_online(self) -> bool:
        pass

    @abstractmethod
    def has_publicly_available_executable(self) -> bool:
        pass

    @abstractmethod
    def get_executable_source_urls(self) -> list[str]:
        """
        Returns a list of URLs where the associated binary can potentially be downloaded from.
        """
        pass

    def get_previous_and_next_state_with_binary(self) -> tuple[State, State]:
        raise NotImplementedError(f'This function is not implemented for {self}')

    def __repr__(self) -> str:
        return f'State(index={self.index})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return False
        return self.index == other.index

    def __hash__(self) -> int:
        return hash((self.index, self.subject.name))
