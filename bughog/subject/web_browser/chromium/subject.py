import logging

from bughog.parameters import SubjectConfiguration
from bughog.subject.state_oracle import StateOracle
from bughog.subject.web_browser.chromium.executable import ChromiumExecutable
from bughog.subject.web_browser.chromium.state_oracle import ChromiumStateOracle
from bughog.subject.web_browser.state_cache import PublicBrowserStateCache
from bughog.subject.web_browser.subject import WebBrowser
from bughog.version_control.state.base import State

logger = logging.getLogger(__name__)


class Chromium(WebBrowser):
    @property
    def name(self) -> str:
        return 'chromium'

    @property
    def _state_oracle_class(self) -> type[StateOracle]:
        return ChromiumStateOracle

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> ChromiumExecutable:
        return ChromiumExecutable(subject_configuration, state)

    def get_availability(self) -> dict:
        most_recent_major_version = PublicBrowserStateCache.get_most_recent_major_version('chromium')
        return {'name': 'chromium', 'min_version': 20, 'max_version': most_recent_major_version}
