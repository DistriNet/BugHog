import os
import re
from abc import ABC, abstractmethod
from typing import Optional


class StateOracle(ABC):
    def __init__(self, subject_type, subject_name, only_artisanal=False) -> None:
        self.subject_type = subject_type
        self.subject_name = subject_name
        self._only_artisanal = only_artisanal

    # Commit / revision logic

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

    @abstractmethod
    def get_commit_url(self, commit_nb: int, commit_id: str) -> str:
        pass

    @abstractmethod
    def get_most_recent_major_release_version(self) -> int:
        pass

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

    @staticmethod
    def get_full_version_from_release_tag(release_tag: str) -> str|None:
        if match := re.search(r'\d+\.\d+\.\d+', release_tag):
            return match[0]
        return None

    # Public executables

    @abstractmethod
    def has_public_release_executable(self, major_version: int) -> bool:
        pass

    @abstractmethod
    def get_release_executable_download_urls(self, major_version: int) -> list[str]:
        pass

    @abstractmethod
    def has_public_commit_executable(self, commit_nb: int) -> bool:
        pass

    @abstractmethod
    def get_commit_executable_download_urls(self, commit_nb: int) -> list[str]:
        pass

    # Artisanal executables

    def get_artisanal_executable_folder(self, state_name: str) -> str:
        return f'/app/subject/{self.subject_type}/executables/{self.subject_name}/{state_name}'

    def has_artisanal_executable(self, state_name: str) -> bool:
        executable_folder = self.get_artisanal_executable_folder(state_name)
        return os.path.isdir(executable_folder)

    # Helper functions

    @staticmethod
    def _parse_commit_nb_from_googlesource(html: str) -> Optional[str]:
        matches = re.findall(r'refs\/heads\/(?:master|main)\@\{\#([0-9]{1,7})\}', html)
        if matches:
            return matches[0]
        matches = re.findall(r'svn.chromium.org\/chrome\/trunk\/src\@([0-9]{1,7}) ', html)
        if matches:
            return matches[0]
        return None

    @staticmethod
    def _get_earliest_tag_with_major(all_release_tags: list[str], major_release: int) -> str:
        candidates = []
        for tag in all_release_tags:
            v = StateOracle.get_full_version_from_release_tag(tag)
            if v is None or not v.startswith(f"{major_release}."):
                continue
            parts = tuple(int(p) for p in v.split('.'))
            candidates.append((parts, tag))

        if not candidates:
            raise ValueError(f"Could not find earliest tag for major {major_release}.")

        candidates.sort()
        return candidates[0][1]
