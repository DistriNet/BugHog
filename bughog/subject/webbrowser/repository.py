from abc import abstractmethod


class Repository:

    @abstractmethod
    def is_tag(self, tag) -> bool:
        pass

    @abstractmethod
    def get_release_tag(self, version) -> str:
        pass

    @abstractmethod
    def get_revision_id(self, revision_number: int) -> str:
        pass

    @abstractmethod
    def get_revision_number(self, revision_id: str) -> int:
        pass

    @abstractmethod
    def get_release_revision_number(self, major_release_version: int) -> int:
        pass
