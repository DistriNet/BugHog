from abc import ABC

from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.collectors.requests import RequestCollector
from bughog.parameters import EvaluationParameters
from bughog.subject.subject import Subject
from bughog.subject.executable import Executable
from bughog.subject.webbrowser.interaction.simulation import BrowserSimulation


class Browser(Subject, ABC):
    def __init__(self) -> None:
        super().__init__()

    @property
    def type(self):
        return 'webbrowser'

    @staticmethod
    def create_simulation(executable: Executable, params: EvaluationParameters) -> BrowserSimulation:
        return BrowserSimulation(executable, params)

    @staticmethod
    def create_result_collector() -> Collector:
        return Collector([RequestCollector()])
