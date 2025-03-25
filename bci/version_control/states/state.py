from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class StateCondition(Enum):
    """
    The condition of a state.
    """

    # This state has been evaluated and the result is available.
    COMPLETED = 0
    # The evaluation of this state has failed.
    FAILED = 1
    # The evaluation of this state is in progress.
    IN_PROGRESS = 2
    # The evaluation of this state has not started yet.
    PENDING = 3
    # This state is not available.
    UNAVAILABLE = 4


@dataclass(frozen=True)
class StateResult:
    requests: list[dict[str, str]]
    request_vars: list[dict[str, str]]
    log_vars: list[dict[str, str]]
    is_dirty: bool
    reproduced: bool

    def has_same_outcome(self, other: StateResult) -> bool:
        """
        Returns whether this and the given other result share the same outcome.

        :returns bool: True if both state results are reproduced, not reproduced, or are both dirty.
        """
        return self.is_dirty == other.is_dirty and self.reproduced == other.reproduced

    def __repr__(self) -> str:
        return f'StateResult(reproduced={self.reproduced}, dirty={self.is_dirty})'


class State:
    def __init__(self):
        self.result: Optional[StateResult] = None
        self.unavailable = False
        self.failed_by_error = False

    @property
    def condition(self) -> StateCondition:
        if self.result is None:
            return StateCondition.PENDING
        elif self.failed_by_error:
            return StateCondition.FAILED
        elif self.unavailable:
            return StateCondition.UNAVAILABLE
        elif self.result.is_dirty:
            return StateCondition.FAILED
        else:
            return StateCondition.COMPLETED

    def has_dirty_result(self) -> bool:
        """
        Returns whether this state has a dirty result.

        :returns bool: True if this state has a result, which is dirty.
        """
        return self.result is not None and self.result.is_dirty

    def has_dirty_or_no_result(self) -> bool:
        """
        Returns whether this state has no result or a dirty result.

        :returns bool: True if this state has no result, or a dirty result.
        """
        return self.result is None or self.result.is_dirty

    def has_same_outcome(self, other: State) -> bool:
        """
        Returns whether this and the given other state share the same result outcome.

        :returns bool: True if states are both reproduced, not reproduced, or dirty.
        """
        if self.result is None or other.result is None:
            return False
        else:
            return self.result.has_same_outcome(other.result)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def browser_name(self) -> str:
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
    def revision_nb(self) -> int:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @staticmethod
    def from_dict(data: dict) -> State:
        from bci.version_control.states.revisions.base import BaseRevision
        from bci.version_control.states.versions.base import BaseVersion

        match data['type']:
            case 'revision':
                return BaseRevision.from_dict(data)
            case 'version':
                return BaseVersion.from_dict(data)
            case _:
                raise Exception(f'Unknown state type: {data["type"]}')

    @abstractmethod
    def has_online_binary(self) -> bool:
        pass

    @abstractmethod
    def get_online_binary_url(self) -> str:
        pass

    def has_available_binary(self) -> bool:
        if self.condition == StateCondition.UNAVAILABLE:
            return False
        else:
            has_available_binary = self.has_online_binary()
            if not has_available_binary:
                self.unavailable = True
            return has_available_binary

    def get_previous_and_next_state_with_binary(self) -> tuple[State, State]:
        raise NotImplementedError(f'This function is not implemented for {self}')

    def __repr__(self) -> str:
        return f'State(index={self.index})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return False
        return self.index == other.index

    def __hash__(self) -> int:
        return hash((self.index, self.browser_name))
