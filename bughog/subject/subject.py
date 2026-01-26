"""
This module provides abstract base classes for subjects, states and executables.

All classes should be implemented by newly added subjects.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.file_structure import Folder
from bughog.parameters import EvaluationParameters, SubjectConfiguration
from bughog.subject.executable import Executable
from bughog.subject.simulation import Simulation
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.base import State

logger = logging.getLogger(__name__)


class Subject(ABC):
    """
    Abstract base class representing an evaluation target.

    The Subject class defines the interface and common functionality for any suibject that can be evaluated.
    """

    @property
    @abstractmethod
    def type(self) -> str:
        """
        Returns the evaluation subject type.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the evaluation subject name.
        """
        pass

    @property
    @abstractmethod
    def _state_oracle_class(self) -> type[StateOracle]:
        """
        Returns the state oracle class associated with this subject.
        """
        pass

    @abstractmethod
    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> Executable:
        """
        Creates and returns an executable object based on the given subject configuration and state.
        """
        pass

    @abstractmethod
    def get_availability(self) -> dict:
        """
        Returns availability data (supported minimum and maximum release version) of this subject.
        """
        pass

    @staticmethod
    @abstractmethod
    def create_simulation(executable: Executable, context: Folder, params: EvaluationParameters) -> Simulation:
        """
        Creates and returns the simulation object based on the given executable, experiment context and eval params.
        """
        pass

    @staticmethod
    @abstractmethod
    def create_result_collector() -> Collector:
        """
        Creates and returns the result collector.
        """
        pass

    @property
    def state_oracle(self) -> StateOracle:
        """
        Creates and returns the state oracle associated with this subject.
        """
        return self._state_oracle_class(self.type, self.name)

    @property
    def assets_folder_path(self) -> str:
        """
        Returns the paths of the assets folder associated with this subject.
        """
        return os.path.join('/app/subject', self.type, self.name)
