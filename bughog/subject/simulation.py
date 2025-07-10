import time
from abc import ABC, abstractmethod

from bughog.parameters import EvaluationParameters
from bughog.subject.executable import Executable


class Simulation(ABC):
    def __init__(self, executable: Executable, params: EvaluationParameters) -> None:
        self.executable = executable
        self.params = params

    @property
    @abstractmethod
    def supported_commands(self) -> list[str]:
        pass

    @abstractmethod
    def do_sanity_check(self):
        pass

    def sleep(self, duration: str):
        time.sleep(float(duration))
