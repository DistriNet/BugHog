from typing import Literal

from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service


class ServoStateOracle(StateOracle):
    def find_commit_nb(self, commit_id: str) -> int:
        return bughog_service.find_commit_nb(self.subject_name, commit_id)

    def find_commit_id(self, commit_nb: int) -> str | None:
        return bughog_service.find_commit_id(self.subject_name, commit_nb)

    def find_commit_of_release(self, release_version: int) -> tuple[int, str]:
        return bughog_service.find_version_commit(self.subject_name, release_version)

    def get_oldest_supported_release_version(self) -> int:
        return 0

    def get_most_recent_major_release_version(self) -> int:
        return bughog_service.find_latest_major_version(self.subject_name)

    def has_public_executable(self, state_index: int, state_type: Literal['release', 'commit']) -> bool:
        match state_type:
            case 'release':
                # For now, only support commits.
                return False
            case 'commit':
                return bughog_service.find_commit_executable_info(self.subject_name, state_index) is not None

    def get_executable_download_urls(self, state_index: int, state_type: Literal['release', 'commit']) -> list[str]:
        match state_type:
            case 'release':
                # For now, only support commits.
                return []
            case 'commit':
                commit_info = bughog_service.find_commit_executable_info(self.subject_name, state_index)
                if commit_info is None:
                    return []
                return [commit_info['base_url'] + 'servo-latest.tar.gz']

    def get_nearest_commit_with_executable(
        self, target_commit_nb: int, lower_bound: int, upper_bound: int
    ) -> int | None:
        commit_info = bughog_service.find_nearest_commit_with_executable(
            self.subject_name, target_commit_nb, lower_bound, upper_bound
        )
        return commit_info.get('nb') if commit_info else None

    def get_commit_url(self, commit_nb: int, commit_id: str | None) -> str | None:
        commit_info = bughog_service.find_commit_info(self.subject_name, commit_nb)
        return commit_info.get('url') if commit_info else None
