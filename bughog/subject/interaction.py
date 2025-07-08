from abc import ABC, abstractmethod

from bughog.subject.executable import Executable

class Interaction(ABC):

    def __init__(self, executable: Executable, script: list[str], params: ExperimentParameters) -> None:
        self.executable = executable
        self.script = script
        self.params = params

    def execute(self) -> None:
        self._do_experiment()
        self._do_sanity_check()

    @abstractmethod
    def _do_experiment(self) -> None:
        pass

    @abstractmethod
    def _do_sanity_check(self) -> None:
        pass
