from bughog.parameters import SubjectConfiguration
from bughog.subject.state_oracle import StateOracle
from bughog.subject.web_browser.servo.executable import ServoExecutable
from bughog.subject.web_browser.servo.state_oracle import ServoStateOracle
from bughog.subject.web_browser.subject import WebBrowser
from bughog.version_control.state.base import State


class Servo(WebBrowser):
    @property
    def name(self) -> str:
        return 'servo'

    @property
    def _state_oracle_class(self) -> type[StateOracle]:
        return ServoStateOracle

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> ServoExecutable:
        return ServoExecutable(subject_configuration, state)
