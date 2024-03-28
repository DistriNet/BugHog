from abc import abstractmethod
import re
from bci.version_control.states.state import State


class BaseRevision(State):

    def __init__(self, revision_id: str = None, revision_number: int = None, parents=None, children=None):
        super().__init__()
        self._revision_id = None
        self._revision_number = None
        if revision_id is None and revision_number is None:
            raise Exception('A state must be initiliazed with either a revision id or revision number')
        if revision_id is not None:
            self.revision_id = revision_id
        if revision_number is not None:
            self.revision_number = revision_number
        self.parents = [] if parents is None else parents
        self.children = [] if children is None else children
        self.result = []
        self.evaluation_target = False

    @property
    @abstractmethod
    def browser_name(self):
        pass

    @property
    def name(self):
        return f'{self.revision_number}'

    def to_dict(self) -> dict:
        return {
            'type': 'revision',
            'browser_name': self.browser_name,
            'revision_id': self.revision_id,
            'revision_number': self.revision_number
        }

    @staticmethod
    def from_dict(data: dict) -> State:
        from bci.version_control.states.revisions.chromium import ChromiumRevision
        from bci.version_control.states.revisions.firefox import FirefoxRevision
        match data['browser_name']:
            case 'chromium':
                return ChromiumRevision(
                    revision_id=data['revision_id'], revision_number=data['revision_number']
                )
            case 'firefox':
                return FirefoxRevision(
                    revision_id=data['revision_id'], revision_number=data['revision_number']
                )
            case _:
                raise Exception(f'Unknown browser: {data["browser_name"]}')

    def _has_revision_id(self) -> bool:
        return self._revision_id is not None

    def _has_revision_number(self) -> bool:
        return self._revision_number is not None

    @abstractmethod
    def _fetch_revision_id(self) -> str:
        pass

    @abstractmethod
    def _fetch_revision_number(self) -> int:
        pass

    @property
    def revision_id(self) -> str:
        if self._revision_id is None:
            self.revision_id = self._fetch_revision_id()
        return self._revision_id

    @revision_id.setter
    def revision_id(self, value: str):
        assert value is not None
        assert re.match(r'[a-z0-9]{40}', value), f'\'{value}\' is not a valid revision id'
        self._revision_id = value

    @property
    def revision_number(self) -> int:
        if self._revision_number is None:
            self.revision_number = self._fetch_revision_number()
        return self._revision_number

    @revision_number.setter
    def revision_number(self, value: int):
        assert value is not None
        assert re.match(r'[0-9]{1,7}', str(value)),  f'\'{value}\' is not a valid revision number'
        self._revision_number = value

    def add_parent(self, new_parent):
        if not self.is_parent(new_parent):
            self.parents.append(new_parent)
        if not new_parent.is_child(self):
            new_parent.add_child(self)

    def add_child(self, new_child):
        if not self.is_child(new_child):
            self.children.append(new_child)
        if not new_child.is_parent(self):
            new_child.add_parent(self)

    def is_parent(self, parent):
        return parent in self.parents

    def is_child(self, child):
        return child in self.children

    def __str__(self):
        return f'RevisionState(id: {self._revision_id}, number: {self._revision_number})'

    def __repr__(self):
        return f'RevisionState(id: {self._revision_id}, number: {self._revision_number})'
