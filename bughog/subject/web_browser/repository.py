from abc import abstractmethod


class Repository:

    @abstractmethod
    def is_tag(self, tag) -> bool:
        pass

    @abstractmethod
    def get_release_tag(self, version) -> str:
        pass

    @abstractmethod
    def get_commit_id(self, commit_nb: int) -> str:
        pass

    @abstractmethod
    def get_commit_nb(self, commit_id: str) -> int:
        pass

    @abstractmethod
    def get_release_commit_nb(self, major_release_version: int) -> int:
        pass
