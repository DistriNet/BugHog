from bughog.parameters import SubjectConfiguration
from bughog.subject.js_engine.subject import JsEngine
from bughog.subject.js_engine.v8_sandbox_testing.executable import V8SandboxTestingExecutable
from bughog.subject.js_engine.v8_sandbox_testing.state_oracle import V8SandboxTestingStateOracle
from bughog.version_control.state.base import State


class V8SandboxTestingSubject(JsEngine):
    @property
    def name(self) -> str:
        return 'v8_sandbox_testing'

# Test Docker build cached
    @property
    def state_oracle(self) -> V8SandboxTestingStateOracle:
        return V8SandboxTestingStateOracle(self.type, self.name)

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> V8SandboxTestingExecutable:
        return V8SandboxTestingExecutable(subject_configuration, state)
