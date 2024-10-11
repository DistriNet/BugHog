from abc import abstractmethod

from bci.version_control.states.state import State


class BaseVersion(State):
    def __init__(self, major_version: int):
        super().__init__()
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
    @abstractmethod
    def browser_name(self) -> str:
        pass

    @property
    def index(self) -> int:
        return self.major_version

    @property
    def revision_nb(self) -> int:
        return self._revision_nb

    def to_dict(self, make_complete: bool = True) -> dict:
        return {
            'type': 'version',
            'browser_name': self.browser_name,
            'major_version': self.major_version,
            'revision_id': self._revision_id,
            'revision_number': self._revision_nb,
        }

    @staticmethod
    def from_dict(data: dict) -> State:
        from bci.version_control.states.versions.chromium import ChromiumVersion
        from bci.version_control.states.versions.firefox import FirefoxVersion

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

    def __str__(self):
        return f'VersionState(version: {self.major_version}, rev: {self._revision_nb})'

    def __repr__(self):
        return f'VersionState(version: {self.major_version}, rev: {self._revision_nb})'
