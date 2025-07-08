from abc import abstractmethod
from typing import Optional


class RevisionParser:
    @abstractmethod
    def get_revision_id(self, revision_nb: int) -> Optional[str]:
        pass

    @abstractmethod
    def get_revision_nb(self, revision_id: str) -> Optional[int]:
        pass
