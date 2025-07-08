from abc import ABC, abstractmethod


class StateOracle(ABC):

    @abstractmethod
    def find_commit_nb(self, commit_id: str) -> int:
        pass

    @abstractmethod
    def find_commit_id(self, commit_nb: int) -> str:
        pass

    @abstractmethod
    def has_publicly_available_release_executable(self, major_version: int) -> bool:
        pass

    @abstractmethod
    def get_release_executable_download_urls(self, major_version: int) -> list[str]:
        pass

    @abstractmethod
    def has_publicly_available_commit_executable(self, commit_nb: int) -> bool:
        pass

    @abstractmethod
    def get_commit_executable_download_urls(self, commit_nb: int) -> list[str]:
        pass
