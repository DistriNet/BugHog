import logging
import os
import re

from bci import cli, util
from bci.browser.binary.artisanal_manager import ArtisanalBuildManager
from bci.browser.binary.binary import Binary
from bci.database.mongo.binary_cache import BinaryCache
from bci.version_control.states.state import State

logger = logging.getLogger(__name__)

EXECUTABLE_NAME = 'chrome'
BIN_FOLDER_PATH = '/app/browser/binaries/chromium'
EXTENSION_FOLDER_PATH = '/app/browser/extensions/chromium'


class ChromiumBinary(Binary):
    def __init__(self, state: State):
        super().__init__(state)

    def save_browser_binary(self, binary_file):
        binary_file.save(self.get_bin_path())

    @property
    def executable_name(self) -> str:
        return EXECUTABLE_NAME

    @property
    def browser_name(self) -> str:
        return "chromium"

    @property
    def bin_folder_path(self) -> str:
        return BIN_FOLDER_PATH

    # Downloadable binaries

    def configure_binary(self):
        binary_folder = os.path.dirname(self.get_potential_bin_path())
        self.__remove_unnecessary_files(binary_folder)
        cli.execute_and_return_status(f'chmod -R a+x {binary_folder}')

    def __remove_unnecessary_files(self, binary_folder_path: str) -> None:
        """
        Remove binary files that are not necessary for default usage of the browser.
        This is to improve performance, especially when caching binary files.

        :param binary_folder_path: Path to the folder where the binary files are stored.
        """
        locales_folder_path = os.path.join(binary_folder_path, 'locales')
        if os.path.isdir(locales_folder_path):
            util.remove_all_in_folder(locales_folder_path, except_files=['en-GB.pak', 'en-US.pak'])

    def _get_version(self) -> str:
        command = "./chrome --version"
        if bin_path := self.get_bin_path():
            output = cli.execute_and_return_output(command, cwd=os.path.dirname(bin_path))
        else:
            BinaryCache.remove_binary_files(self.state)
            raise AttributeError(f'Could not get binary path for {self.state}')
        match = re.match(r'Chromium (?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', output)
        if match:
            return match.group("version")
        raise AttributeError("Could not determine version of binary at '%s'. Version output: %s" % (bin_path, output))

    @staticmethod
    def list_downloaded_binaries() -> list[dict[str, str]]:
        return Binary._list_downloaded_binaries(BIN_FOLDER_PATH)

    @staticmethod
    def get_artisanal_manager() -> ArtisanalBuildManager:
        return Binary._get_artisanal_manager(BIN_FOLDER_PATH, EXECUTABLE_NAME)

    browser_version_to_driver_version = {
        '88': "88.0.4324.96",
        '87': "87.0.4280.88",
        '86': "86.0.4240.22",
        '85': "85.0.4183.87",
        '84': "84.0.4147.30",
        '83': "83.0.4103.39",
        '82': "81.0.4044.69",  # No chromium driver released for 82
        '81': "81.0.4044.69",
        '80': "80.0.3987.16",  # 80.0.3987.16 80.0.3987.106
        '79': "79.0.3945.36",
        '78': "78.0.3904.11",
        '77': "77.0.3865.40",
        '76': "76.0.3809.126",
        '75': "75.0.3770.8",
        '74': "74.0.3729.6",
        '73': "73.0.3683.68",
        '72': "72.0.3626.7",
        '71': "71.0.3578.80",
        '70': "70.0.3538.97",
        '69': "2.42.591071",
        '68': "2.41.578700",
        '67': "2.40.565383",
        '66': "2.38.552522",
        '65': "2.37.544315",
        '64': "2.36.540471",
        '63': "2.35.528139",
        '62': "2.34.522913",
        '61': "2.33.506092",
        '60': "2.32.498513",
        '59': "2.31.488763",  # From here on not working
        '58': "2.29.461571",
        '57': "2.29.461571",
        '56': "2.29.461571",
        '55': "2.27.440175",
        '54': "2.23.409687",
        '53': "2.23.409687",  # Based on Selenoid https://aerokube.com/images/latest/
        '52': "2.23.409687",  # Based on Selenoid
        '51': "2.22.397932",  # Tried also with 2.21 and 2.23, to no avail
        '50': "2.22.397932",  # Based on Selenoid
        '49': "2.21.371461",  # Based on Selenoid
        '48': "2.21.371461",
        '47': "2.21.371461",
        '46': "2.20.353124",
        '45': "2.20.353124",
        '44': "2.19.346067",
        '43': "2.19.346067",
        '42': "2.18.343837",
        '41': "2.18.343837",
        '40': "2.18.343837",
    }
