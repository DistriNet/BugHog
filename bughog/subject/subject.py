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
from bughog.parameters import ExperimentParameters, SubjectConfiguration
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

    @abstractmethod
    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> Executable:
        """
        Creates and returns an executable object based on the given subject configuration and state.
        """
        pass

    @staticmethod
    @abstractmethod
    def create_simulation(executable: Executable, context: Folder, params: ExperimentParameters) -> Simulation:
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
    @abstractmethod
    def state_oracle(self) -> StateOracle:
        """
        Creates and returns the state oracle associated with this subject.
        """
        pass

    @property
    def assets_folder_path(self) -> str:
        """
        Returns the paths of the assets folder associated with this subject.
        """
        return os.path.join('/app/subject', self.type, self.name)

    def get_availability(self) -> dict[str, str | int | list[str]]:
        earliest_version = self.state_oracle.get_earliest_supported_release_version()
        latest_version = self.state_oracle.get_latest_supported_release_version()

        if earliest_version.major != 0 and latest_version.major != 0:
            earliest_major_version = earliest_version.major
            latest_major_version = latest_version.major
            available_versions = [
                str(version) for version in list(range(earliest_major_version, latest_major_version + 1))
            ]
        else:
            earliest_major_version = earliest_version.base_version
            latest_major_version = latest_version.base_version
            available_versions = [str(version) for version in self.state_oracle.get_all_available_release_versions()]

        earliest_commit_number = self.state_oracle.find_commit_of_release(earliest_version)[0]
        latest_commit_number = self.state_oracle.find_commit_of_release(latest_version)[0]
        return {
            'name': self.name,
            'min_version': earliest_major_version,
            'max_version': latest_major_version,
            'min_commit': earliest_commit_number,
            'max_commit': latest_commit_number,
            'available_versions': available_versions,
        }
