from __future__ import annotations

from abc import abstractmethod, abstractproperty


class EvaluationResult:
    BuildUnavailable = "build unavailable"
    Error = "error"
    Positive = "positive"
    Negative = "negative"
    Undefined = "undefined"


class State:

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def browser_name(self):
        pass

    @abstractmethod
    def to_dict(self):
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

    # @classmethod
    # def create_state_list(cls, evaluation_targets, revision_numbers) -> list:
    #     states = []
    #     ancestor_state = cls(revision_number=revision_numbers[0])
    #     descendant_state = cls(revision_number=revision_numbers[len(revision_numbers) - 1])

    #     states.append(ancestor_state)
    #     prev_state = ancestor_state
    #     for i in range(1, len(revision_numbers) - 1):
    #         revision_number = revision_numbers[i]
    #         curr_state = cls(revision_number=revision_number)
    #         curr_state.add_parent(prev_state)
    #         states.append(curr_state)
    #         prev_state = curr_state
    #         if evaluation_targets is None or revision_number in evaluation_targets:
    #             curr_state.set_as_evaluation_target()

    #     descendant_state.add_parent(prev_state)
    #     states.append(descendant_state)
    #     return states
