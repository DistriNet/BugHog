from abc import ABC

from bughog.subject.base import Subject


class Browser(Subject, ABC):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def type():
        return 'webbrowser'

