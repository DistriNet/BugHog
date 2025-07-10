from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.base import State
from bughog.version_control.state.commit.base import CommitState


class ReleaseState(State):
    def __init__(self, oracle: StateOracle, release_version: int):
        super().__init__(oracle)
        self.release_version = release_version
        self._commit_nb = self.__get_commit_nb()
        self._commit_id = self._get_commit_id()

    def __get_commit_nb(self) -> int:
        return self.oracle.find_commit_nb_of_release(self.release_version)

    def _get_commit_id(self) -> str:
        return self.oracle.find_commit_id_of_release(self.release_version)

    @staticmethod
    def get_name(index: int) -> str:
        return f'v_{index}'
    @property
    def type(self) -> str:
        return 'version'

    @property
    def index(self) -> int:
        return self.release_version

    @property
    def commit_nb(self) -> int:
        return self._commit_nb

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'major_version': self.index,
            'commit_nb': self.commit_nb,
            'commit_id': self._commit_id,
        }

    # @staticmethod
    # def from_dict(data: dict) -> State:
    #     from bughog.version_control.state.release.chromium import ChromiumVersion
    #     from bughog.version_control.state.release.firefox import FirefoxVersion

    #     match data['browser_name']:
    #         case 'chromium':
    #             state = ChromiumVersion(major_version=data['major_version'])
    #         case 'firefox':
    #             state = FirefoxVersion(major_version=data['major_version'])
    #         case _:
    #             raise Exception(f'Unknown browser: {data["browser_name"]}')
    #     return state

    def has_publicly_available_executable(self) -> bool:
        return self.oracle.has_publicly_available_release_executable(self.release_version)

    def get_executable_source_urls(self) -> list[str]:
        return self.oracle.get_release_executable_download_urls(self.release_version)

    def convert_to_commit_state(self) -> CommitState:
        return CommitState(self.oracle, commit_nb=self.commit_nb)

    def __str__(self):
        return f'VersionState(version: {self.release_version}, rev: {self._commit_nb})'

    def __repr__(self):
        return f'VersionState(version: {self.release_version}, rev: {self._commit_nb})'
