from bughog.parameters import SubjectConfiguration
from bughog.subject.js_engine.subject import JsEngine
from bughog.subject.js_engine.v8.executable import V8Executable
from bughog.subject.js_engine.v8_sandbox.state_oracle import V8SandboxStateOracle
from bughog.version_control.state.base import State


class V8SandboxSubject(JsEngine):
    @property
    def name(self) -> str:
        return 'v8_sandbox'

    @property
    def state_oracle(self) -> V8SandboxStateOracle:
        return V8SandboxStateOracle(self.type, self.name)

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> V8Executable:
        return V8Executable(subject_configuration, state)
