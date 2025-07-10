from abc import abstractmethod

from bughog import util
from bughog.parameters import SubjectConfiguration
from bughog.subject.executable import Executable
from bughog.version_control.state.base import State


class BrowserExecutable(Executable):
    PROFILE_STORAGE_FOLDER = '/app/subject/webbrowser/profiles'
    PROFILE_EXECUTION_FOLDER = '/tmp/profiles'

    def __init__(self, config: SubjectConfiguration, state: State) -> None:
        super().__init__(config, state)

    @property
    @abstractmethod
    def navigation_sleep_duration(self) -> int:
        pass

    @property
    @abstractmethod
    def open_console_hotkey(self) -> list[str]:
        pass

    @abstractmethod
    def _prepare_profile_folder(self):
        pass

    @abstractmethod
    def _remove_profile_folder(self):
        pass

    def __empty_downloads_folder(self):
        download_folder = '/root/Downloads'
        util.remove_all_in_folder(download_folder)

    def pre_evaluation_setup(self):
        self.fetch()

    def post_evaluation_cleanup(self):
        self.remove()

    def pre_experiment_setup(self):
        self.stage()

    def post_experiment_cleanup(self):
        self.unstage()

    def pre_try_setup(self):
        self._prepare_profile_folder()

    def post_try_cleanup(self):
        self._remove_profile_folder()
        self.__empty_downloads_folder()
