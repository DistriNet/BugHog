from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.collectors.logs import LogCollector
from bughog.evaluation.file_structure import Folder
from bughog.parameters import EvaluationParameters
from bughog.subject.executable import Executable
from bughog.subject.js_engine.simulation import JSEngineSimulation
from bughog.subject.subject import Subject


class JsEngine(Subject):
    @property
    def type(self) -> str:
        return 'js_engine'

    @staticmethod
    def create_simulation(executable: Executable, context: Folder, params: EvaluationParameters) -> JSEngineSimulation:
        return JSEngineSimulation(executable, context, params)

    @staticmethod
    def create_result_collector() -> Collector:
        return Collector([LogCollector()])
