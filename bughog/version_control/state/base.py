from __future__ import annotations

import base64
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional

from bughog.evaluation.experiment_result import ExperimentResult
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.version import Version


@dataclass(frozen=True)
class ShallowState:
    type: str
    version: Version | None
    commit_nb: int | None
    commit_id: str | None

    def to_dict(self) -> dict:
        # 'major_version' is always written (e.g. 120 for Chromium, 0 for Servo).
        # 'version' is additionally written when the major version is 0 (e.g. 0.1.1 for Servo),
        # since major_version alone is insufficient to identify the release in that case.
        fields = {
            'type': self.type,
            'major_version': self.version.major if self.version is not None else None,
            'version': str(self.version) if self.version is not None and self.version.major == 0 else None,
            'commit_nb': self.commit_nb,
            'commit_id': self.commit_id,
        }
        return {k: v for k, v in fields.items() if v is not None}


class State(ABC):
    def __init__(self, oracle: StateOracle):
        super().__init__()
        self.oracle = oracle
        self.result_variables: Optional[set[tuple[str, str]]] = None
        self.result_attempt: int | None

    def has_result(self) -> bool:
        """
        Returns whether this state has a result.

        :returns bool: True if this state has a result.
        """
        return self.result_variables is not None

    def has_dirty_result(self) -> bool:
        """
        Returns whether this state has a dirty result.

        :returns bool: True if this state has a result, which is dirty.
        """
        return self.has_result() and ExperimentResult.poc_is_dirty(self.result_variables)

    def has_same_outcome(self, other: State) -> bool:
        """
        Returns whether this and the given other state share the same result outcome.

        :returns bool: True if states are both reproduced, not reproduced, or dirty.
        """
        if not self.has_result() or not other.has_result():
            return False
        else:
            return ExperimentResult.poc_is_reproduced(self.result_variables) == ExperimentResult.poc_is_reproduced(
                other.result_variables
            ) and ExperimentResult.poc_is_dirty(self.result_variables) == ExperimentResult.poc_is_dirty(
                other.result_variables
            )

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def type(self) -> Literal['release', 'commit']:
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
        return self.to_shallow_state().to_dict()

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
        return self.oracle.has_artisanal_executable(self.index, self.type)

    def get_artisanal_executable_folder(self) -> str | None:
        return self.oracle.get_artisanal_executable_folder(self.index, self.type)

    def find_nearest_state_with_executable(self, boundaries: tuple[State, State], inclusive: bool) -> int | None:
        if inclusive:
            lower_index = boundaries[0].index
            upper_index = boundaries[1].index
        else:
            lower_index = boundaries[0].index + 1
            upper_index = boundaries[1].index - 1

        return self.oracle.get_nearest_state_with_executable(self.index, lower_index, upper_index, self.type)

    @abstractmethod
    def to_shallow_state(self) -> ShallowState:
        pass

    def __repr__(self) -> str:
        if not self.has_result():
            status = 'PENDING'
        elif self.has_dirty_result():
            status = 'DIRTY'
        else:
            status = 'CLEAN'
        return f'State(index={self.index}, status={status})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return False
        return self.__hash__() == other.__hash__()
