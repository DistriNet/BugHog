import logging
import os
import re
import shutil
import zipfile

import requests

from bci import cli, util
from bci.browser.binary.artisanal_manager import ArtisanalBuildManager
from bci.browser.binary.binary import Binary
from bci.database.mongo.mongodb import MongoDB
from bci.version_control.states.state import State

logger = logging.getLogger('bci')

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

    # def get_full_version(self, version: int):
        # if re.match(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        #     return version + ".0"
        # if re.match(r'[0-9]+', version):
        #     return self.repo.get_release_tag(version)
        # if re.match(r'[0-9]{2}', version):
        #     return self.full_versions[version] + ".0"
        # raise AttributeError("Could not convert version '%i' to full version" % version)
        # return self.repo.get_release_tag(version)

    # Downloadable binaries

    @staticmethod
    def has_available_binary_online(state: State) -> bool:
        cached_binary_available_online = MongoDB.has_binary_available_online('chromium', state)
        if cached_binary_available_online is not None:
            return cached_binary_available_online
        url = f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{state.revision_number}%2Fchrome-linux.zip'
        req = requests.get(url)
        has_binary_online = req.status_code == 200
        MongoDB.store_binary_availability_online_cache('chromium', state, has_binary_online)
        return has_binary_online

    def download_binary(self):
        rev_number = self.state.revision_number

        if self.has_available_binary_locally():
            logger.debug(f'{self.rev_number} was already downloaded ({self.get_bin_path()})')
            return
        url = \
            "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/%s%%2F%s%%2Fchrome-%s.zip?alt=media"\
            % ('Linux_x64', rev_number, 'linux')
        logger.info(f'Downloading {rev_number} from \'{url}\'')
        zip_file_path = f'/tmp/{rev_number}/archive.zip'
        if os.path.exists(os.path.dirname(zip_file_path)):
            shutil.rmtree(os.path.dirname(zip_file_path))
        os.makedirs(os.path.dirname(zip_file_path))
        with requests.get(url, stream=True) as req:
            with open(zip_file_path, 'wb') as file:
                shutil.copyfileobj(req.raw, file)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(zip_file_path))
        bin_path = self.get_potential_bin_path()
        os.makedirs(os.path.dirname(bin_path), exist_ok=True)
        unzipped_folder_path = os.path.join(os.path.dirname(zip_file_path), "chrome-linux")
        util.safe_move_dir(unzipped_folder_path, os.path.dirname(bin_path))
        cli.execute_and_return_status("chmod -R a+x %s" % os.path.dirname(bin_path))
        # Remove temporary files in /tmp/COMMIT_POS
        shutil.rmtree(os.path.dirname(zip_file_path))

    def _get_version(self) -> str:
        bin_path = self.get_bin_path()
        command = "./chrome --version"
        output = cli.execute_and_return_output(command, cwd=os.path.dirname(bin_path))
        match = re.match(r'Chromium (?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', output)
        if match:
            return match.group("version")
        raise AttributeError("Could not determine version of binary at '%s'. Version output: %s" % (bin_path, output))

    def get_driver_path(self, full_browser_version):
        driver_version = self.get_driver_version(full_browser_version)
        driver_path = os.path.join(DRIVER_FOLDER_PATH, driver_version)
        if os.path.exists(driver_path):
            return driver_path
        raise AttributeError("Could not find appropriate driver for Chromium %s" % full_browser_version)

    def get_driver_version(self, browser_version):
        short_browser_version = browser_version.split('.')[0]
        if short_browser_version not in self.browser_version_to_driver_version.keys():
            raise AttributeError("Could not determine driver version associated with Chromium version %s" % browser_version)
        return self.browser_version_to_driver_version[short_browser_version]

    @staticmethod
    def list_downloaded_binaries() -> list[dict[str, str]]:
        return Binary.list_downloaded_binaries(BIN_FOLDER_PATH)

    @staticmethod
    def get_artisanal_manager() -> ArtisanalBuildManager:
        return Binary.get_artisanal_manager(BIN_FOLDER_PATH, EXECUTABLE_NAME)

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
