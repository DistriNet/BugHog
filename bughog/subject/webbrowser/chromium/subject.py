import logging

from bughog.parameters import SubjectConfiguration
from bughog.subject.state_oracle import StateOracle
from bughog.subject.webbrowser.chromium import repo
from bughog.subject.webbrowser.chromium.executable import ChromiumExecutable
from bughog.subject.webbrowser.chromium.state_oracle import ChromiumStateOracle
from bughog.subject.webbrowser.subject import Browser
from bughog.version_control.state.base import State

logger = logging.getLogger(__name__)


class Chromium(Browser):
    @property
    def name(self) -> str:
        return 'chromium'

    @property
    def _state_oracle_class(self) -> type[StateOracle]:
        return ChromiumStateOracle

    def create_executable(self, subject_configuration: SubjectConfiguration, state: State) -> ChromiumExecutable:
        return ChromiumExecutable(subject_configuration, state)

    @staticmethod
    def get_availability() -> dict:
        return {'name': 'chromium', 'min_version': 20, 'max_version': repo.get_most_recent_major_version()}
