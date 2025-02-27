from __future__ import annotations

import os
import subprocess
from abc import abstractmethod

import bci.browser.binary.factory as binary_factory
from bci import util
from bci.browser.automation.terminal import TerminalAutomation
from bci.browser.binary.binary import Binary
from bci.browser.configuration.profile import remove_profile_execution_folder
from bci.evaluations.logic import BrowserConfiguration, EvaluationConfiguration
from bci.version_control.states.state import State

EXECUTION_PARENT_FOLDER = '/tmp'


class Browser:
    process: subprocess.Popen | None

    def __init__(
        self, browser_config: BrowserConfiguration, eval_config: EvaluationConfiguration, binary: Binary
    ) -> None:
        self.browser_config = browser_config
        self.process = None
        self.eval_config = eval_config
        self.binary = binary
        self.state = binary.state
        self._profile_path = None

    @property
    def version(self) -> str:
        return self.binary.version

    def get_binary_origin(self) -> str:
        return self.binary.origin

    def visit(self, url: str):
        match self.eval_config.automation:
            case 'terminal':
                args = self._get_terminal_args()
                TerminalAutomation.visit_url(url, args, self.eval_config.seconds_per_visit)
            case _:
                raise AttributeError('Not implemented')

    def open(self, url: str) -> None:
        args = self._get_terminal_args()
        args.append(url)
        self.process = TerminalAutomation.open_browser(args)

    def terminate(self):
        if self.process is None:
            return

        TerminalAutomation.terminate_browser(self.process, self._get_terminal_args())
        self.process = None

    def pre_evaluation_setup(self):
        self.__fetch_binary()

    def post_evaluation_cleanup(self):
        self.__remove_binary()

    def pre_test_setup(self):
        self.__prepare_execution_folder()

    def post_test_cleanup(self):
        self.__remove_execution_folder()

    def pre_try_setup(self):
        self._prepare_profile_folder()

    def post_try_cleanup(self):
        self.__remove_profile_folder()
        self.__empty_downloads_folder()

    def __fetch_binary(self):
        self.binary.fetch_binary()

    def __remove_binary(self):
        self.binary.remove_bin_folder()

    def __prepare_execution_folder(self):
        path = self.__get_execution_folder_path()
        util.copy_folder(self.binary.get_bin_folder_path(), path)

    @abstractmethod
    def _prepare_profile_folder(self):
        pass

    def __remove_execution_folder(self):
        util.rmtree(self.__get_execution_folder_path())

    def __remove_profile_folder(self):
        if self._profile_path is None:
            return
        remove_profile_execution_folder(self._profile_path)
        self._profile_path = None

    def __empty_downloads_folder(self):
        download_folder = '/root/Downloads'
        util.remove_all_in_folder(download_folder)

    def __get_execution_folder_path(self) -> str:
        return os.path.join(EXECUTION_PARENT_FOLDER, str(self.state.name))

    def _get_executable_file_path(self) -> str:
        return os.path.join(self.__get_execution_folder_path(), self.binary.executable_name)

    @abstractmethod
    def _get_terminal_args(self) -> list[str]:
        pass

    @abstractmethod
    def get_navigation_sleep_duration(self) -> int:
        pass

    @abstractmethod
    def get_open_console_hotkey(self) -> list[str]:
        pass

    @staticmethod
    def get_browser(
        browser_config: BrowserConfiguration, eval_config: EvaluationConfiguration, state: State
    ) -> Browser:
        from bci.browser.configuration.chromium import Chromium
        from bci.browser.configuration.firefox import Firefox

        binary = binary_factory.get_binary(state)

        if browser_config.browser_name == 'chromium':
            return Chromium(browser_config, eval_config, binary)
        elif browser_config.browser_name == 'firefox':
            return Firefox(browser_config, eval_config, binary)
        else:
            raise AttributeError('Not implemented')
