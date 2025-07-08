"""
This module provides abstract base classes for subjects, states and executables.

All classes should be implemented by newly added subjects.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.commit.base import CommitState
from bughog.version_control.state.release.base import ReleaseState

logger = logging.getLogger(__name__)


class Subject(ABC):
    """
    Abstract base class representing an evaluation target.

    The Subject class defines the interface and common functionality for any suibject that can be evaluated.
    """

    @staticmethod
    @abstractmethod
    def type() -> str:
        pass

    @staticmethod
    @abstractmethod
    def name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def state_oracle() -> type[StateOracle]:
        pass

    @staticmethod
    @abstractmethod
    def release_state_class() -> type[ReleaseState]:
        pass

    @staticmethod
    @abstractmethod
    def commit_state_class() -> type[CommitState]:
        pass

    @property
    def assets_folder_path(self) -> str:
        return os.path.join('/app/subject', self.type(), self.name())

    @staticmethod
    @abstractmethod
    def get_availability() -> dict:
        """
        Returns availability data (minimum and maximu, release versions, and configuration options) of the subject.
        """
        pass
