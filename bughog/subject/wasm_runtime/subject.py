from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.collectors.logs import LogCollector
from bughog.evaluation.file_structure import Folder
from bughog.parameters import EvaluationParameters
from bughog.subject.executable import Executable
from bughog.subject.subject import Subject
from bughog.subject.wasm_runtime.simulation import WasmRuntimeSimulation


class WasmRuntime(Subject):
    @property
    def type(self) -> str:
        return 'wasm_runtime'

    @staticmethod
    def create_simulation(executable: Executable, context: Folder, params: EvaluationParameters) -> WasmRuntimeSimulation:
        return WasmRuntimeSimulation(executable, context, params)

    @staticmethod
    def create_result_collector() -> Collector:
        return Collector([LogCollector()])
