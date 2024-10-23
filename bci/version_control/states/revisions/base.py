import logging
import re
from abc import abstractmethod
from typing import Optional

from bci.version_control.states.state import State

logger = logging.getLogger(__name__)


class BaseRevision(State):
    def __init__(self, revision_id: Optional[str] = None, revision_nb: Optional[int] = None):
        super().__init__()
        if revision_id is None and revision_nb is None:
            raise AttributeError('A state must be initiliazed with either a revision id or revision number')

        self._revision_id = revision_id
        self._revision_nb = revision_nb
        self._fetch_missing_data()

        if self._revision_id is not None and not self._is_valid_revision_id(self._revision_id):
            raise AttributeError(f"Invalid revision id '{self._revision_id}' for state '{self}'")

        if self._revision_nb is not None and not self._is_valid_revision_number(self._revision_nb):
            raise AttributeError(f"Invalid revision number '{self._revision_nb}' for state '{self}'")

    @property
    @abstractmethod
    def browser_name(self) -> str:
        pass

    @property
    def name(self) -> str:
        return f'{self._revision_nb}'

    @property
    def type(self) -> str:
        return 'revision'

    @property
    def index(self) -> int:
        return self._revision_nb

    @property
    def revision_nb(self) -> int:
        return self._revision_nb

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the state.
        """
        state_dict = {'type': self.type, 'browser_name': self.browser_name}
        if self._revision_id:
            state_dict['revision_id'] = self._revision_id
        if self._revision_nb:
            state_dict['revision_number'] = self._revision_nb
        return state_dict

    @staticmethod
    def from_dict(data: dict) -> State:
        from bci.version_control.states.revisions.chromium import ChromiumRevision
        from bci.version_control.states.revisions.firefox import FirefoxRevision

        match data['browser_name']:
            case 'chromium':
                state = ChromiumRevision(revision_id=data.get('revision_id', None), revision_nb=data['revision_number'])
            case 'firefox':
                state = FirefoxRevision(revision_id=data.get('revision_id', None), revision_nb=data['revision_number'])
            case _:
                raise Exception(f'Unknown browser: {data["browser_name"]}')
        return state

    def _has_revision_id(self) -> bool:
        return self._revision_id is not None

    def _has_revision_number(self) -> bool:
        return self._revision_nb is not None

    @abstractmethod
    def _fetch_missing_data(self):
        pass

    def _is_valid_revision_id(self, revision_id: str) -> bool:
        """
        Checks if a revision id is valid.
        A valid revision id is a 40 character long string containing only lowercase letters and numbers.
        """
        return re.match(r'[a-z0-9]{40}', revision_id) is not None

    def _is_valid_revision_number(self, revision_number: int) -> bool:
        """
        Checks if a revision number is valid.
        A valid revision number is a positive integer.
        """
        return re.match(r'[0-9]{1,7}', str(revision_number)) is not None

    def __str__(self):
        return f'RevisionState(number: {self._revision_nb}, id: {self._revision_id})'

    def __repr__(self):
        return f'RevisionState(number: {self._revision_nb}, id: {self._revision_id})'
