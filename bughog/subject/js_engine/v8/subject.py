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
    def _state_oracle_class(self) -> type[V8StateOracle]:
        return V8StateOracle

    def get_availability(self) -> dict:
        """
        Returns availability data (minimum and maximu, release versions, and configuration options) of the subject.
        """
        return {
            'name': 'v8',
            'min_version': 6,
            'max_version': self.state_oracle.get_most_recent_major_release_version()
        }

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> V8Executable:
        return V8Executable(subject_configuration, state)
