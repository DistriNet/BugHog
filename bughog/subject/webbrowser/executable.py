from abc import abstractmethod
from bughog import util
from bughog.parameters import SubjectConfiguration
from bughog.subject.executable import Executable
from bughog.version_control.states.base import State


class BrowserExecutable(Executable):
    PROFILE_STORAGE_FOLDER = '/app/subject/webbrowser/profiles'
    PROFILE_EXECUTION_FOLDER = '/tmp/profiles'

    def __init__(self, config: SubjectConfiguration, state: State) -> None:
        super().__init__(config, state)

    @abstractmethod
    def get_navigation_sleep_duration(self) -> int:
        pass

    @abstractmethod
    def get_open_console_hotkey(self) -> list[str]:
        pass

    def __fetch_binary(self):
        self.binary.fetch_binary()

    def __remove_binary(self):
        self.binary.remove_bin_folder()

    def __prepare_execution_folder(self):
        path = self.__get_execution_folder_path()
        util.copy_folder(self.binary.get_bin_folder_path(), path)
