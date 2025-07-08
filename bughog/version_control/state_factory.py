from __future__ import annotations

from bughog.database.mongo.mongodb import MongoDB
from bughog.parameters import EvaluationParameters
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.base import State
from bughog.version_control.state.commit.base import CommitState
from bughog.version_control.state.release.base import ReleaseState


class StateFactory:
    def __init__(self, state_oracle: StateOracle, eval_params: EvaluationParameters) -> None:
        """
        Create a state factory object with the given evaluation parameters and boundary indices.

        :param eval_params: The evaluation parameters.
        """
        self.__oracle = state_oracle
        self.__eval_params = eval_params
        self.boundary_states = self.__create_boundary_states()

    def create_state(self, index: int) -> State:
        """
        Create a state object associated with the given index.
        The given index represents:
        - A major version number if `self.eval_params.evaluation_range.major_version_range` is True.
        - A revision number otherwise.

        :param index: The index of the state.
        """
        eval_range = self.__eval_params.evaluation_range
        if eval_range.only_release_revisions:
            return self.__create_version_state(index)
        else:
            return self.__create_revision_state(index)

    def __create_boundary_states(self) -> tuple[State, State]:
        """
        Create the boundary state objects for the evaluation range.
        """
        eval_range = self.__eval_params.evaluation_range
        if eval_range.major_version_range:
            first_state = self.__create_version_state(eval_range.major_version_range[0])
            last_state = self.__create_version_state(eval_range.major_version_range[1])
            if not eval_range.only_release_revisions:
                first_state = first_state.convert_to_commit_state()
                last_state = last_state.convert_to_commit_state()
            return first_state, last_state
        elif eval_range.revision_number_range:
            if eval_range.only_release_revisions:
                raise ValueError('Release revisions are not allowed in this evaluation range')
            return (
                self.__create_revision_state(eval_range.revision_number_range[0]),
                self.__create_revision_state(eval_range.revision_number_range[1]),
            )
        else:
            raise ValueError('No evaluation range specified')

    def create_evaluated_states(self) -> list[State]:
        """
        Create evaluated state objects within the evaluation range where the result is fetched from the database.
        """
        return MongoDB().get_evaluated_states(self.__eval_params, self.boundary_states, self.__state_result_factory)

    def __create_version_state(self, index: int) -> ReleaseState:
        """
        Create a version state object associated with the given index.
        """
        return self.__subject.release_state_class(self.__oracle, index)

    def __create_revision_state(self, index: int) -> CommitState:
        """
        Create a revision state object associated with the given index.
        """
        return self.__subject.commit_state_class(self.__oracle, index)
