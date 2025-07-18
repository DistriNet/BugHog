from abc import ABC

from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.collectors.requests import RequestCollector
from bughog.evaluation.file_structure import Folder
from bughog.parameters import EvaluationParameters
from bughog.subject.executable import Executable
from bughog.subject.subject import Subject
from bughog.subject.web_browser.interaction.simulation import BrowserSimulation


class WebBrowser(Subject, ABC):
    def __init__(self) -> None:
        super().__init__()

    @property
    def type(self):
        return 'web_browser'

    @staticmethod
    def create_simulation(executable: Executable, context: Folder, params: EvaluationParameters) -> BrowserSimulation:
        return BrowserSimulation(executable, context, params)

    @staticmethod
    def create_result_collector() -> Collector:
        return Collector([RequestCollector()])
