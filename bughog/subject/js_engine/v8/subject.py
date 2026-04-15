from bughog.parameters import SubjectConfiguration
from bughog.subject.js_engine.subject import JsEngine
from bughog.subject.js_engine.v8.executable import V8Executable
from bughog.subject.js_engine.v8.state_oracle import V8StateOracle
from bughog.version_control.state.base import State


class V8Subject(JsEngine):
    @property
    def name(self) -> str:
        return 'v8'

    @property
    def state_oracle(self) -> V8StateOracle:
        return V8StateOracle(self.type, self.name)

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> V8Executable:
        return V8Executable(subject_configuration, state)
