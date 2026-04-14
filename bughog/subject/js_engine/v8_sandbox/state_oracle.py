import logging

from bughog.subject.js_engine.v8.state_oracle import V8StateOracle
from bughog.version_control.conversion import bughog_service
from bughog.version_control.version import Version

logger = logging.getLogger(__name__)


class V8SandboxStateOracle(V8StateOracle):
    """
    State oracle for V8.

    More information:
    - https://v8.dev/docs/version-numbers
    - https://commondatastorage.googleapis.com/v8-asan/index.html
    """

    def __init__(self, subject_type: str, subject_name: str) -> None:
        # There are no public executables, only artisanal.
        super().__init__(subject_type, subject_name, only_artisanal=True)

    def get_most_recent_commit_nb(self) -> int:
        """
        We override this method because we want to call the API for v8, not v8_sandbox.
        """
        return bughog_service.find_latest_commit_info('v8').get('nb')

    def has_public_release_executable(self, version: Version) -> bool:
        return False

    def has_public_commit_executable(self, commit_nb: int) -> bool:
        return False

    def get_release_executable_urls(self, version: Version) -> list[str]:
        raise Exception('Only artisanal executables are available.')

    def get_commit_executable_urls(self, commit_nb: int) -> list[str]:
        raise Exception('Only artisanal executables are available.')
