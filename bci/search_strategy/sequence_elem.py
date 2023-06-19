from enum import Enum

import bci.browser.binary.factory as binary_factory
from bci.version_control.states.state import State


class ElemState(Enum):
    INITIALIZED = 0
    UNAVAILABLE = 1
    IN_PROGRESS = 2
    ERROR = 3
    DONE = 4


class SequenceElem:

    def __init__(self, index: int, value: State, state: ElemState = ElemState.INITIALIZED, outcome: bool = None) -> None:
        self.value = value
        self.index = index
        if state == ElemState.DONE and outcome is None:
            raise AttributeError("Every sequence element that has been evaluated should have an outcome")
        self.state = state
        self.outcome = outcome

    def is_available(self) -> bool:
        return binary_factory.binary_is_available(self.value)

    def update_outcome(self, outcome: bool):
        if self.state == ElemState.DONE:
            raise AttributeError(f"Outcome was already set to DONE for {repr(self)}")
        if outcome is None:
            self.state = ElemState.ERROR
        self.state = ElemState.DONE
        self.outcome = outcome

    def get_deep_copy(self, index=None):
        if index is not None:
            return SequenceElem(index, self.value, state=self.state, outcome=self.outcome)
        else:
            return SequenceElem(self.index, self.value, state=self.state, outcome=self.outcome)

    def __repr__(self) -> str:
        return f"{str(self.value)}: {self.state}"
