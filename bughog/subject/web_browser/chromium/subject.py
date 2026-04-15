from bughog.parameters import SubjectConfiguration
from bughog.subject.web_browser.chromium.executable import ChromiumExecutable
from bughog.subject.web_browser.chromium.state_oracle import ChromiumStateOracle
from bughog.subject.web_browser.subject import WebBrowser
from bughog.version_control.state.base import State


class Chromium(WebBrowser):
    @property
    def name(self) -> str:
        return 'chromium'

    @property
    def state_oracle(self) -> ChromiumStateOracle:
        return ChromiumStateOracle(self.type, self.name)

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> ChromiumExecutable:
        return ChromiumExecutable(subject_configuration, state)
