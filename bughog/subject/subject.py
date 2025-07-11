"""
This module provides abstract base classes for subjects, states and executables.

All classes should be implemented by newly added subjects.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

from bughog.evaluation.collectors.collector import Collector
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
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def _state_oracle_class(self) -> type[StateOracle]:
        pass

    @abstractmethod
    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> Executable:
        pass

    @staticmethod
    @abstractmethod
    def get_availability() -> dict:
        """
        Returns availability data (minimum and maximu, release versions, and configuration options) of the subject.
        """
        pass

    @staticmethod
    @abstractmethod
    def create_simulation(executable: Executable, params: EvaluationParameters) -> Simulation:
        pass

    @staticmethod
    @abstractmethod
    def create_result_collector() -> Collector:
        pass

    @property
    def state_oracle(self) -> StateOracle:
        return self._state_oracle_class(self.type, self.name)

    @property
    def assets_folder_path(self) -> str:
        return os.path.join('/app/subject', self.type, self.name)
