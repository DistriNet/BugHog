from abc import abstractmethod


class BaseCollector:
    def __init__(self) -> None:
        self.data = {}

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def parse_data(self):
        pass
