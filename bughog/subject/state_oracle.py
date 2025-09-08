import os
import re
from abc import ABC, abstractmethod
from typing import Optional


class StateOracle(ABC):
    def __init__(self, subject_type, subject_name) -> None:
        self.subject_type = subject_type
        self.subject_name = subject_name

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
    def get_commit_url(self, commit_nb, commit_id) -> str:
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

    # Public executables

    @abstractmethod
    def get_most_recent_major_release_version(self) -> int:
        pass

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
        return f'/app/subject/executables/{self.subject_type}/{self.subject_name}/{state_name}'

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
        pattern = re.compile(r'^\d+\.\d+\.\d+$')
        # Filter tags matching x.y.z format and starting with the given major
        filtered_tags = [tag for tag in all_release_tags if pattern.match(tag) and tag.startswith(f'{major_release}.')]
        if not filtered_tags:
            Exception(f'Could not find earliest tag for {major_release}.')

        def version_tuple(tag):
            return tuple(int(x) for x in tag.split('.'))

        sorted_tags = sorted(filtered_tags, key=version_tuple)
        return sorted_tags[0]
