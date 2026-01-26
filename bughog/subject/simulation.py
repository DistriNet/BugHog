import time
from abc import ABC, abstractmethod

from bughog.evaluation.file_structure import Folder
from bughog.parameters import EvaluationParameters
from bughog.subject.executable import Executable


class Simulation(ABC):
    def __init__(self, executable: Executable, context: Folder, params: EvaluationParameters) -> None:
        self.executable = executable
        self.context = context
        self.params = params

    @property
    @abstractmethod
    def supported_commands(self) -> list[str]:
        pass

    @abstractmethod
    def do_sanity_check(self):
        """
        Performs a sanity check on the associated executable.
        A successful sanity check will cause the collector to collect {'sanity_check': 'ok'}.

        Implementing this method is optional in cases where the sanity check is done as part of a proof of concept.
        """
        pass

    @abstractmethod
    def report_simulation_error(self, message: str):
        pass

    def sleep(self, duration: str):
        time.sleep(float(duration))
