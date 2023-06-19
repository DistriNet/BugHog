from __future__ import annotations

from abc import abstractmethod
import re


class EvaluationResult:
    BuildUnavailable = "build unavailable"
    Error = "error"
    Positive = "positive"
    Negative = "negative"
    Undefined = "undefined"


class State:

    def __init__(self, revision_id: str = None, revision_number: int = None, parents=None, children=None):
        self._revision_id = None
        self._revision_number = None
        if revision_id is None and revision_number is None:
            raise Exception('A state must be initiliazed with either a revision id or revision number')
        if revision_id is not None:
            self.revision_id = revision_id
        if revision_number is not None:
            self.revision_number = revision_number
        self.parents = [] if parents is None else parents
        self.children = [] if children is None else children
        self.result = []
        self.evaluation_target = False

    @property
    @abstractmethod
    def browser_name(self):
        pass

    def _has_revision_id(self) -> bool:
        return self._revision_id is not None

    def _has_revision_number(self) -> bool:
        return self._revision_number is not None

    @abstractmethod
    def _fetch_revision_id(self) -> str:
        pass

    @abstractmethod
    def _fetch_revision_number(self) -> int:
        pass

    @property
    def revision_id(self) -> str:
        if self._revision_id is None:
            self.revision_id = self._fetch_revision_id()
        return self._revision_id

    @revision_id.setter
    def revision_id(self, value: str):
        assert value is not None
        assert re.match(r'[a-z0-9]{40}', value), f'\'{value}\' is not a valid revision id'
        self._revision_id = value

    @property
    def revision_number(self) -> int:
        if self._revision_number is None:
            self.revision_number = self._fetch_revision_number()
        return self._revision_number

    @revision_number.setter
    def revision_number(self, value: int):
        assert value is not None
        assert re.match(r'[0-9]{1,7}', str(value)),  f'\'{value}\' is not a valid revision number'
        self._revision_number = value

    def add_parent(self, new_parent):
        if not self.is_parent(new_parent):
            self.parents.append(new_parent)
        if not new_parent.is_child(self):
            new_parent.add_child(self)

    def add_child(self, new_child):
        if not self.is_child(new_child):
            self.children.append(new_child)
        if not new_child.is_parent(self):
            new_child.add_parent(self)

    def is_parent(self, parent):
        return parent in self.parents

    def is_child(self, child):
        return child in self.children

    def is_evaluation_target(self):
        return self.evaluation_target

    def set_as_evaluation_target(self):
        self.evaluation_target = True

    def set_evaluation_outcome(self, outcome: bool):
        if outcome:
            self.result = EvaluationResult.Positive
        else:
            self.result = EvaluationResult.Negative

    def set_evaluation_build_unavailable(self):
        self.result = EvaluationResult.BuildUnavailable

    def set_evaluation_error(self, error_message):
        self.result = error_message

    @property
    def build_unavailable(self):
        return self.result == EvaluationResult.BuildUnavailable

    @property
    def result_undefined(self):
        return len(self.result) == 0

    @classmethod
    def create_state_list(cls, evaluation_targets, revision_numbers) -> list:
        states = []
        ancestor_state = cls(revision_number=revision_numbers[0])
        descendant_state = cls(revision_number=revision_numbers[len(revision_numbers) - 1])

        states.append(ancestor_state)
        prev_state = ancestor_state
        for i in range(1, len(revision_numbers) - 1):
            revision_number = revision_numbers[i]
            curr_state = cls(revision_number=revision_number)
            curr_state.add_parent(prev_state)
            states.append(curr_state)
            prev_state = curr_state
            if evaluation_targets is None or revision_number in evaluation_targets:
                curr_state.set_as_evaluation_target()

        descendant_state.add_parent(prev_state)
        states.append(descendant_state)
        return states

    def __str__(self):
        return f'Revision(id: {self._revision_id}, number: {self._revision_number})'

    def __repr__(self):
        return f'Revision(id: {self._revision_id}, number: {self._revision_number})'
