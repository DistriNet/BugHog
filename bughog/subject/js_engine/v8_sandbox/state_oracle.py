import logging
from typing import Literal

from bughog.subject.js_engine.v8.state_oracle import V8StateOracle
from bughog.version_control.conversion import bughog_service

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

    def has_public_executable(self, state_index: int, state_type: Literal['release', 'commit']) -> bool:
        return False

    def get_executable_download_urls(self, state_index: int, state_type: Literal['release', 'commit']) -> list[str]:
        raise Exception('Only artisanal executables are available.')
