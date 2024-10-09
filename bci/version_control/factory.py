from __future__ import annotations

from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import EvaluationParameters
from bci.evaluations.outcome_checker import OutcomeChecker
from bci.version_control.states.revisions.chromium import ChromiumRevision
from bci.version_control.states.revisions.firefox import FirefoxRevision
from bci.version_control.states.state import State
from bci.version_control.states.versions.chromium import ChromiumVersion
from bci.version_control.states.versions.firefox import FirefoxVersion


class StateFactory:
    def __init__(
            self,
            eval_params: EvaluationParameters,
            outcome_checker: OutcomeChecker,
            boundary_indices: tuple[int, int] | None = None)-> None:
        '''
        Create a state factory object with the given evaluation parameters and boundary indices.

        :param eval_params: The evaluation parameters.
        :param boundary_indices: The boundary indices that will overwrite the range defined by eval_params.
        '''
        self.eval_params = eval_params
        self.outcome_checker = outcome_checker
        self.boundary_indices = boundary_indices

    def create_state(self, index: int) -> State:
        """
        Create a state object associated with the given index.
        """
        eval_range = self.eval_params.evaluation_range
        if eval_range.major_version_range:
            return self.__create_version_state(index)
        elif eval_range.revision_number_range:
            return self.__create_revision_state(index)
        else:
            raise ValueError("No evaluation range specified")

    def create_boundary_states(self) -> tuple[State, State]:
        """
        Create the boundary state objects for the evaluation range.
        """
        eval_range = self.eval_params.evaluation_range
        if eval_range.major_version_range:
            if self.boundary_indices:
                return tuple(self.create_state(index) for index in self.boundary_indices)
            else:
                return tuple(self.create_state(index) for index in eval_range.major_version_range)
        elif eval_range.revision_number_range:
            if self.boundary_indices:
                return tuple(self.create_state(index) for index in self.boundary_indices)
            else:
                return tuple(self.create_state(index) for index in eval_range.revision_number_range)
        else:
            raise ValueError("No evaluation range specified")

    def create_evaluated_states(self) -> list[State]:
        """
        Create evaluated state objects within the evaluation range where the result is fetched from the database.
        """
        db = MongoDB.get_instance()
        return db.get_evaluated_states(self.eval_params, self.outcome_checker)

    def create_sibling_factory(self, boundary_indices: tuple[int, int]) -> StateFactory:
        """
        Create a sibling factory object with the same evaluation parameters.
        """
        return StateFactory(self.eval_params, boundary_indices)

    def __create_version_state(self, index: int) -> State:
        """
        Create a version state object associated with the given index.
        """
        browser_config = self.eval_params.browser_configuration
        match browser_config.browser_name:
            case "chromium":
                return ChromiumVersion(index)
            case "firefox":
                return FirefoxVersion(index)
            case _:
                raise ValueError(f"Unknown browser name: {browser_config.browser_name}")

    def __create_revision_state(self, index: int) -> State:
        """
        Create a revision state object associated with the given index.
        """
        browser_config = self.eval_params.browser_configuration
        match browser_config.browser_name:
            case "chromium":
                return ChromiumRevision(revision_number=index)
            case "firefox":
                return FirefoxRevision(revision_number=index)
            case _:
                raise ValueError(f"Unknown browser name: {browser_config.browser_name}")
