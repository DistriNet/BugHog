from bughog.parameters import SubjectConfiguration
from bughog.subject.wasm_runtime.subject import WasmRuntime
from bughog.subject.wasm_runtime.wasmtime.executable import WasmtimeExecutable
from bughog.subject.wasm_runtime.wasmtime.state_oracle import WasmtimeStateOracle
from bughog.version_control.state.base import State


class WasmtimeSubject(WasmRuntime):
    @property
    def name(self) -> str:
        return 'wasmtime'

    @property
    def state_oracle(self) -> WasmtimeStateOracle:
        return WasmtimeStateOracle(self.type, self.name)

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> WasmtimeExecutable:
        return WasmtimeExecutable(subject_configuration, state)
