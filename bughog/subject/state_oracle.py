import re
from abc import ABC, abstractmethod
from typing import Literal, Optional

from bughog.subject.artisanal_executable_manager import artisanal_executable_manager
from bughog.version_control.conversion import bughog_service
from bughog.version_control.version import Version


class StateOracle(ABC):
    def __init__(self, subject_type, subject_name, only_artisanal=False) -> None:
        self.subject_type = subject_type
        self.subject_name = subject_name
        self.only_artisanal = only_artisanal

    # Commit / revision logic

    @abstractmethod
    def find_commit_nb(self, commit_id: str) -> int:
        pass

    @abstractmethod
    def find_commit_id(self, commit_nb: int) -> str | None:
        pass

    def find_commit_of_release(self, release_version: Version) -> tuple[int, str]:
        version_info = bughog_service.find_version_info(self.subject_name, release_version)
        return version_info.get('commit_info', {}).get('nb'), version_info.get('commit_info', {}).get('id')

    @abstractmethod
    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        pass

    @abstractmethod
    def get_earliest_supported_release_version(self) -> Version:
        pass

    def get_latest_supported_release_version(self) -> Version:
        return bughog_service.find_latest_major_version(self.subject_name)

    def get_all_available_release_versions(self) -> list[Version]:
        versions = [
            Version(v)
            for version_info in bughog_service.find_all_versions(self.subject_name)
            if (v := version_info.get('version')) is not None
        ]
        versions.sort()
        return versions

    def get_most_recent_commit_nb(self) -> int:
        return bughog_service.find_latest_commit_info(self.subject_name)['nb']

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
    def get_full_version_from_release_tag(release_tag: str) -> Version | None:
        if match := re.search(r'\d+\.\d+(?:\.\d+)*(?:-\w+)?', release_tag):
            try:
                return Version(match[0])
            except Exception:
                return None
        return None

    """
    Executables
    """

    def get_nearest_state_with_executable(
        self, state_index: int, lower_bound: int, upper_bound: int, state_type: Literal['release', 'commit']
    ) -> int | None:
        nearest_with_public_executable = self.get_nearest_state_with_public_executable(
            state_index, lower_bound, upper_bound, state_type
        )
        nearest_with_artisanal_executable = artisanal_executable_manager.get_nearest_state_with_artisanal_executable(
            self.subject_type, self.subject_name, state_type, state_index, lower_bound, upper_bound
        )

        if nearest_with_public_executable is not None and nearest_with_artisanal_executable is not None:
            if abs(state_index - nearest_with_public_executable) < abs(state_index - nearest_with_artisanal_executable):
                return nearest_with_public_executable
            else:
                return nearest_with_artisanal_executable

        if nearest_with_public_executable is not None:
            return nearest_with_public_executable
        elif nearest_with_artisanal_executable is not None:
            return nearest_with_artisanal_executable
        else:
            return None

    # Public executables

    def has_public_release_executable(self, version: Version) -> bool:
        return bughog_service.find_version_info(self.subject_name, version, has_public_executable=True) is not None

    @abstractmethod
    def has_public_commit_executable(self, commit_nb: int) -> bool:
        pass

    @abstractmethod
    def get_release_executable_urls(self, version: Version) -> list[str]:
        pass

    @abstractmethod
    def get_commit_executable_urls(self, commit_nb: int) -> list[str]:
        pass

    def get_nearest_state_with_public_executable(
        self, state_index: int, lower_bound: int, upper_bound: int, state_type: Literal['release', 'commit']
    ) -> int | None:
        if self.only_artisanal:
            return None

        if state_type == 'commit':
            commit_info = bughog_service.find_nearest_commit_with_executable(
                self.subject_name, state_index, lower_bound, upper_bound
            )
            if commit_info is None:
                return None
            return commit_info.get('nb')
        elif state_type == 'release':
            # Every version within the absolute lower and upper bound should be available.
            return state_index
        else:
            raise ValueError(f'Unknown state type: {state_type}')

    # Artisanal executables

    def count_artisanal_executables(self, state_type: Literal['release', 'commit']) -> int:
        return artisanal_executable_manager.count_executables(self.subject_type, self.subject_name, state_type)

    def get_artisanal_executable_folder(self, state_index: int, state_type: Literal['release', 'commit']) -> str | None:
        return artisanal_executable_manager.get_executable_folder(
            self.subject_type, self.subject_name, state_type, state_index
        )

    def has_artisanal_executable(self, state_index: int, state_type: Literal['release', 'commit']) -> bool:
        executable_folder = self.get_artisanal_executable_folder(state_index, state_type)
        return executable_folder is not None

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
    def _get_earliest_tag_version_match(all_release_tags: list[str], release_version: Version) -> str:
        candidates = []
        for tag in all_release_tags:
            v = StateOracle.get_full_version_from_release_tag(tag)
            if v is not None and release_version.matches(v):
                candidates.append((v, tag))

        if not candidates:
            raise ValueError(f'Could not find earliest tag for {release_version}.')

        candidates.sort()
        return candidates[0][1]
