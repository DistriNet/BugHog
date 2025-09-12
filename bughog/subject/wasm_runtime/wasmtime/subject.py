from bughog.parameters import SubjectConfiguration
from bughog.subject.wasm_runtime.subject import WasmRuntime
from bughog.subject.wasm_runtime.wasmtime.executable import WasmtimeExecutable
from bughog.subject.wasm_runtime.wasmtime.state_oracle import WasmtimeStateOracle
from bughog.version_control.state.base import State


class WasmtimeSubject(WasmRuntime):
    @property
    def name(self) -> str:
        return 'wasmtime'

    def get_availability(self) -> dict:
        return {
            'name': 'wasmtime',
            'min_version': 1,
            'max_version': self.state_oracle.get_most_recent_major_release_version()
        }

    @property
    def _state_oracle_class(self) -> type[WasmtimeStateOracle]:
        return WasmtimeStateOracle

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> WasmtimeExecutable:
        return WasmtimeExecutable(subject_configuration, state)
