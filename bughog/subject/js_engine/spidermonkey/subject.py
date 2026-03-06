from bughog.parameters import SubjectConfiguration
from bughog.subject.js_engine.spidermonkey.executable import SpiderMonkeyExecutable
from bughog.subject.js_engine.spidermonkey.state_oracle import SpiderMonkeyStateOracle
from bughog.subject.js_engine.subject import JsEngine
from bughog.version_control.state.base import State


class SpiderMonkeySubject(JsEngine):
    @property
    def name(self) -> str:
        return 'spidermonkey'

    @property
    def _state_oracle_class(self) -> type[SpiderMonkeyStateOracle]:
        return SpiderMonkeyStateOracle

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> SpiderMonkeyExecutable:
        return SpiderMonkeyExecutable(subject_configuration, state)
