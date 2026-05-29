from bughog.subject.js_engine.v8_sandbox.subject import V8SandboxSubject
from bughog.subject.js_engine.v8_sandbox_noasan.executable import V8SandboxNoAsanExecutable
from bughog.parameters import SubjectConfiguration
from bughog.subject.js_engine.v8.executable import V8Executable
from bughog.version_control.state.base import State


 
class V8SandboxNoAsanSubject(V8SandboxSubject):

    @property
    def name(self) -> str:
        return 'v8_sandbox_noasan'
    
    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> V8Executable:
        return V8SandboxNoAsanExecutable(subject_configuration, state)
