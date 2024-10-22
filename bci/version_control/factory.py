from __future__ import annotations

from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import EvaluationParameters
from bci.evaluations.outcome_checker import OutcomeChecker
from bci.version_control.states.revisions.chromium import ChromiumRevision
from bci.version_control.states.revisions.firefox import FirefoxRevision
from bci.version_control.states.state import State
from bci.version_control.states.versions.base import BaseVersion
from bci.version_control.states.versions.chromium import ChromiumVersion
from bci.version_control.states.versions.firefox import FirefoxVersion


class StateFactory:
    def __init__(self, eval_params: EvaluationParameters, outcome_checker: OutcomeChecker) -> None:
        """
        Create a state factory object with the given evaluation parameters and boundary indices.

        :param eval_params: The evaluation parameters.
        """
        self.__eval_params = eval_params
        self.__outcome_checker = outcome_checker
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
                first_state = first_state.convert_to_revision()
                last_state = last_state.convert_to_revision()
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
        return MongoDB().get_evaluated_states(self.__eval_params, self.boundary_states, self.__outcome_checker)

    def __create_version_state(self, index: int) -> BaseVersion:
        """
        Create a version state object associated with the given index.
        """
        browser_config = self.__eval_params.browser_configuration
        match browser_config.browser_name:
            case 'chromium':
                return ChromiumVersion(index)
            case 'firefox':
                return FirefoxVersion(index)
            case _:
                raise ValueError(f'Unknown browser name: {browser_config.browser_name}')

    def __create_revision_state(self, index: int) -> State:
        """
        Create a revision state object associated with the given index.
        """
        browser_config = self.__eval_params.browser_configuration
        match browser_config.browser_name:
            case 'chromium':
                return ChromiumRevision(revision_nb=index)
            case 'firefox':
                return FirefoxRevision(revision_nb=index)
            case _:
                raise ValueError(f'Unknown browser name: {browser_config.browser_name}')
