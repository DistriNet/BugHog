from bughog.subject.state_oracle import StateOracle
from bughog.version_control.conversion import bughog_service
from bughog.version_control.version import Version


class ServoStateOracle(StateOracle):
    def find_commit_nb(self, commit_id: str) -> int:
        return bughog_service.find_commit_nb(self.subject_name, commit_id)

    def find_commit_id(self, commit_nb: int) -> str | None:
        return bughog_service.find_commit_id(self.subject_name, commit_nb)

    def get_earliest_supported_release_version(self) -> Version:
        return Version('0.0.1')

    def has_public_commit_executable(self, commit_nb: int) -> bool:
        return bughog_service.find_commit_executable_info(self.subject_name, commit_nb) is not None

    def get_release_executable_urls(self, version: Version) -> list[str]:
        version_info = bughog_service.find_version_info(self.subject_name, version, has_public_executable=True)
        if version_info is None:
            return []
        base_url = version_info.get('executable_info', {}).get('base_url')
        assets = version_info.get('executable_info', {}).get('assets', [])
        if base_url is None or 'servo-x86_64-linux-gnu.tar.gz' not in assets:
            return []
        return [base_url + 'servo-x86_64-linux-gnu.tar.gz']

    def get_commit_executable_urls(self, commit_nb: int) -> list[str]:
        commit_info = bughog_service.find_commit_executable_info(self.subject_name, commit_nb)
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
        return f'https://github.com/servo/servo/commit/{commit_id}'
