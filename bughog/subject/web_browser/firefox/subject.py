from bughog.parameters import SubjectConfiguration
from bughog.subject.state_oracle import StateOracle
from bughog.subject.web_browser.firefox.executable import FirefoxExecutable
from bughog.subject.web_browser.firefox.state_oracle import FirefoxStateOracle
from bughog.subject.web_browser.state_cache import PublicBrowserStateCache
from bughog.subject.web_browser.subject import WebBrowser
from bughog.version_control.state.base import State


class Firefox(WebBrowser):
    @property
    def name(self) -> str:
        return 'firefox'

    @property
    def _state_oracle_class(self) -> type[StateOracle]:
        return FirefoxStateOracle

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> FirefoxExecutable:
        return FirefoxExecutable(subject_configuration, state)

    def get_availability(self) -> dict:
        max_version = PublicBrowserStateCache.get_most_recent_major_version('firefox')
        return {
            'name': 'firefox',
            'min_version': 20,
            'max_version': max_version,
        }
