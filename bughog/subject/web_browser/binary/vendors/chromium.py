import logging
import os
import re

from bughog import cli, util
from bughog.database.mongo.executable_cache import ExecutableCache
from bughog.subject.web_browser.binary.artisanal_manager import ArtisanalBuildManager
from bughog.subject.web_browser.binary.binary import BrowserBinary
from bughog.version_control.states.base import State

logger = logging.getLogger(__name__)

EXECUTABLE_NAME = 'chrome'
BIN_FOLDER_PATH = '/app/browser/binaries/chromium'
EXTENSION_FOLDER_PATH = '/app/browser/extensions/chromium'


class ChromiumBinary(BrowserBinary):
    def __init__(self, state: State):
        super().__init__(state)

    # def save_browser_binary(self, binary_file):
    #     binary_file.save(self.get_bin_path())

    # @property
    # def executable_name(self) -> str:
    #     return EXECUTABLE_NAME

    # @property
    # def browser_name(self) -> str:
    #     return 'chromium'

    # @property
    # def bin_folder_path(self) -> str:
    #     return BIN_FOLDER_PATH

    # Downloadable binaries

    # def configure_binary(self):
    #     binary_folder = os.path.dirname(self.get_potential_bin_path())
    #     self.__remove_unnecessary_files(binary_folder)
    #     cli.execute_and_return_status(f'chmod -R a+x {binary_folder}')

    # def __remove_unnecessary_files(self, binary_folder_path: str) -> None:
    #     """
    #     Remove binary files that are not necessary for default usage of the browser.
    #     This is to improve performance, especially when caching binary files.

    #     :param binary_folder_path: Path to the folder where the binary files are stored.
    #     """
    #     locales_folder_path = os.path.join(binary_folder_path, 'locales')
    #     if os.path.isdir(locales_folder_path):
    #         util.remove_all_in_folder(locales_folder_path, except_files=['en-GB.pak', 'en-US.pak'])

    # def _get_version(self) -> str:
    #     command = './chrome --version'
    #     if bin_path := self.get_bin_path():
    #         output = cli.execute_and_return_output(command, cwd=os.path.dirname(bin_path))
    #     else:
    #         ExecutableCache.remove_executable_files(self.state)
    #         raise AttributeError(f'Could not get binary path for {self.state}')
    #     match = re.match(r'Chromium (?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', output)
    #     if match:
    #         return match.group('version')
    #     raise AttributeError("Could not determine version of binary at '%s'. Version output: %s" % (bin_path, output))

    @staticmethod
    def get_artisanal_manager() -> ArtisanalBuildManager:
        return BrowserBinary._get_artisanal_manager(BIN_FOLDER_PATH, EXECUTABLE_NAME)
