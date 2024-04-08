from abc import abstractmethod, abstractproperty

from bci.version_control.states.state import State


class BaseVersion(State):

    def __init__(self, major_version: int):
        super().__init__()
        self.major_version = major_version
        self._rev_nb = self._get_rev_nb()
        self._rev_id = self._get_rev_id()

    @abstractmethod
    def _get_rev_nb(self):
        pass

    @abstractmethod
    def _get_rev_id(self):
        pass

    @property
    def name(self):
        return f'v_{self.major_version}'

    @abstractproperty
    def browser_name(self):
        pass

    def to_dict(self, make_complete: bool = True) -> dict:
        return {
            'type': 'version',
            'browser_name': self.browser_name,
            'major_version': self.major_version,
            'revision_id': self._rev_id,
            'revision_number': self._rev_nb
        }

    @staticmethod
    def from_dict(data: dict) -> State:
        from bci.version_control.states.versions.chromium import \
            ChromiumVersion
        from bci.version_control.states.versions.firefox import FirefoxVersion
        match data['browser_name']:
            case 'chromium':
                return ChromiumVersion(
                    major_version=data['major_version']
                )
            case 'firefox':
                return FirefoxVersion(
                    major_version=data['major_version']
                )
            case _:
                raise Exception(f'Unknown browser: {data["browser_name"]}')

    def __str__(self):
        return f'VersionState(version: {self.major_version}, rev: {self._rev_nb})'

    def __repr__(self):
        return f'VersionState(version: {self.major_version}, rev: {self._rev_nb})'
