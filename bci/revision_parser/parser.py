from abc import abstractmethod


class RevisionParser:

    @abstractmethod
    def get_rev_id(self, rev_nb: int):
        pass

    @abstractmethod
    def get_rev_number(self, rev_id: str):
        pass
