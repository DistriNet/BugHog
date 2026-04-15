from bughog.parameters import SubjectConfiguration
from bughog.subject.web_browser.firefox.executable import FirefoxExecutable
from bughog.subject.web_browser.firefox.state_oracle import FirefoxStateOracle
from bughog.subject.web_browser.subject import WebBrowser
from bughog.version_control.state.base import State


class Firefox(WebBrowser):
    @property
    def name(self) -> str:
        return 'firefox'

    @property
    def state_oracle(self) -> FirefoxStateOracle:
        return FirefoxStateOracle(self.type, self.name)

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> FirefoxExecutable:
        return FirefoxExecutable(subject_configuration, state)
