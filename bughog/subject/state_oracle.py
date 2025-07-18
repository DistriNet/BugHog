import os
import re
from abc import ABC, abstractmethod
from typing import Optional


class StateOracle(ABC):

    def __init__(self, subject_type, subject_name) -> None:
        self.subject_type = subject_type
        self.subject_name = subject_name

    @abstractmethod
    def find_commit_nb(self, commit_id: str) -> int:
        pass

    @abstractmethod
    def find_commit_id(self, commit_nb: int) -> str:
        pass

    @abstractmethod
    def find_commit_nb_of_release(self, release_version: int) -> int:
        pass

    @abstractmethod
    def find_commit_id_of_release(self, release_version: int) -> str:
        pass

    def get_local_executable_folder_path(self, state_name: str) -> str:
        return os.path.join('/app/subject/', self.subject_type, self.subject_name, state_name)

    def has_local_executable(self, state_name: str) -> bool:
        return os.path.isdir(self.get_local_executable_folder_path(state_name))

    @staticmethod
    def is_valid_commit_id(commit_id: str) -> bool:
        """
        Checks if a revision id is valid.
        A valid revision id is a 40 character long string containing only lowercase letters and numbers.
        """
        return re.match(r'[a-z0-9]{40}', commit_id) is not None

    @staticmethod
    def is_valid_commit_nb(commit_nb: int) -> bool:
        """
        Checks if a revision number is valid.
        A valid revision number is a positive integer.
        """
        return re.match(r'[0-9]{1,7}', str(commit_nb)) is not None


    # Public releases

    @abstractmethod
    def has_publicly_available_release_executable(self, major_version: int) -> bool:
        pass

    @abstractmethod
    def get_release_executable_download_urls(self, major_version: int) -> list[str]:
        pass

    @abstractmethod
    def get_most_recent_major_release_version(self) -> int:
        pass


    # Public commits

    @abstractmethod
    def get_commit_url(self, commit_nb, commit_id) -> str:
        pass

    @abstractmethod
    def has_publicly_available_commit_executable(self, commit_nb: int) -> bool:
        pass

    @abstractmethod
    def get_commit_executable_download_urls(self, commit_nb: int) -> list[str]:
        pass


    # Helper functions

    @staticmethod
    def _parse_commit_nb_from_googlesource(html: str) -> Optional[str]:
        matches = re.findall(r"refs\/heads\/(?:master|main)\@\{\#([0-9]{1,7})\}", html)
        if matches:
            return matches[0]
        matches = re.findall(r"svn.chromium.org\/chrome\/trunk\/src\@([0-9]{1,7}) ", html)
        if matches:
            return matches[0]
        return None
