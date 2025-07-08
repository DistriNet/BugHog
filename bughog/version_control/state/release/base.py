from abc import abstractmethod

from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.base import State


class ReleaseState(State):
    def __init__(self, oracle: StateOracle, major_version: int):
        super().__init__(oracle)
        self.major_version = major_version
        self._revision_nb = self._get_rev_nb()
        self._revision_id = self._get_rev_id()

    @abstractmethod
    def _get_rev_nb(self) -> int:
        pass

    @abstractmethod
    def _get_rev_id(self) -> str:
        pass

    @property
    def name(self) -> str:
        return f'v_{self.major_version}'

    @property
    def type(self) -> str:
        return 'version'

    @property
    def index(self) -> int:
        return self.major_version

    @property
    def commit_nb(self) -> int:
        return self._revision_nb

    def to_dict(self, make_complete: bool = True) -> dict:
        return {
            'type': self.type,
            'browser_name': self.browser_name,
            'major_version': self.major_version,
            'revision_id': self._revision_id,
            'revision_number': self._revision_nb,
        }

    @staticmethod
    def from_dict(data: dict) -> State:
        from bughog.version_control.states.versions.chromium import ChromiumVersion
        from bughog.version_control.states.versions.firefox import FirefoxVersion

        match data['browser_name']:
            case 'chromium':
                state = ChromiumVersion(major_version=data['major_version'])
            case 'firefox':
                state = FirefoxVersion(major_version=data['major_version'])
            case _:
                raise Exception(f'Unknown browser: {data["browser_name"]}')
        return state

    @abstractmethod
    def convert_to_revision(self) -> State:
        pass

    def has_publicly_available_executable(self) -> bool:
        return self.oracle.has_publicly_available_release_executable(self.major_version)

    def get_executable_source_urls(self) -> list[str]:
        return self.oracle.get_release_executable_download_urls(self.major_version)

    def __str__(self):
        return f'VersionState(version: {self.major_version}, rev: {self._revision_nb})'

    def __repr__(self):
        return f'VersionState(version: {self.major_version}, rev: {self._revision_nb})'
