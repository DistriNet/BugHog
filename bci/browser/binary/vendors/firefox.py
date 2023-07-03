import logging
import os
import re
import shutil
import tarfile

import requests

from bci import cli, util
from bci.browser.binary.artisanal_manager import ArtisanalBuildManager
from bci.browser.binary.binary import Binary
from bci.version_control.states.firefox import (BINARY_AVAILABILITY_MAPPING,
                                                REVISION_NUMBER_MAPPING)
from bci.version_control.states.state import State

logger = logging.getLogger('bci')

EXECUTABLE_NAME = 'firefox'
BIN_FOLDER_PATH = '/app/browser/binaries/firefox'
EXTENSION_FOLDER_PATH = '/app/browser/extensions/firefox'


class FirefoxBinary(Binary):

    def __init__(self, state: State):
        super().__init__(state)

    def get_release_tag(self, version):
        return self.repo.get_release_tag(version)

    @property
    def executable_name(self) -> str:
        return "firefox"

    @property
    def browser_name(self) -> str:
        return "firefox"

    @property
    def bin_folder_path(self) -> str:
        return BIN_FOLDER_PATH

    @staticmethod
    def has_available_binary_online(state: State) -> bool:
        if state._revision_id:
            return state._revision_id in BINARY_AVAILABILITY_MAPPING
        if state._revision_number:
            return str(state._revision_number) in REVISION_NUMBER_MAPPING

    def download_binary(self):
        rev_id = self.state.revision_id
        rev_number = self.state.revision_number

        if self.only_releases:
            binary_url = f'https://ftp.mozilla.org/pub/firefox/releases/{self.version}.0/linux-x86_64/en-US/firefox-{self.version}.0.tar.bz2'
        else:
            # binary_url = MongoDB.get_binary_url("firefox", changeset_id)
            binary_base_url = BINARY_AVAILABILITY_MAPPING[rev_id]["files_url"]
            app_version = BINARY_AVAILABILITY_MAPPING[rev_id]["app_version"]
            binary_url = f"{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.bz2"
        logger.debug(f'Downloading {rev_number} from \'{binary_url}\'')
        tar_file_path = f'/tmp/{rev_number}/archive.tar.bz2'
        if os.path.exists(os.path.dirname(tar_file_path)):
            shutil.rmtree(os.path.dirname(tar_file_path))
        os.makedirs(os.path.dirname(tar_file_path))
        with requests.get(binary_url, stream=True) as req:
            with open(tar_file_path, 'wb') as file:
                shutil.copyfileobj(req.raw, file)
        with tarfile.open(tar_file_path, "r:bz2") as tar_ref:
            tar_ref.extractall(os.path.dirname(tar_file_path))
        bin_path = self.get_potential_bin_path()
        os.makedirs(os.path.dirname(bin_path), exist_ok=True)
        unzipped_folder_path = os.path.join(os.path.dirname(tar_file_path), "firefox")
        util.safe_move_dir(unzipped_folder_path, os.path.dirname(bin_path))
        cli.execute_and_return_status("chmod -R a+x %s" % os.path.dirname(bin_path))
        cli.execute_and_return_status("chmod -R a+w %s" % os.path.dirname(bin_path))
        # Remove temporary files in /tmp/COMMIT_POS
        shutil.rmtree(os.path.dirname(tar_file_path))
        # Add policy.json to prevent updating. (this measure is effective from version 60)
        # https://github.com/mozilla/policy-templates/blob/master/README.md
        # (For earlier versions, the prefs.js file is used)
        distributions_path = os.path.join(os.path.dirname(bin_path), "distribution")
        os.makedirs(distributions_path, exist_ok=True)
        policies_path = os.path.join(distributions_path, "policies.json")
        with open(policies_path, "a") as file:
            file.write('{ "policies": { "DisableAppUpdate": true } }')

    def _get_version(self):
        bin_path = self.get_bin_path()
        command = "./firefox --version"
        output = cli.execute_and_return_output(command, cwd=os.path.dirname(bin_path))
        match = re.match(r'Mozilla Firefox (?P<version>[0-9]+)\.[0-9]+.*', output)
        if match:
            return match.group("version")
        raise AttributeError(
            "Could not determine version of binary at '%s'. Version output: %s" % (bin_path, output))

    def get_driver_path(self, browser_version):
        driver_version = self.get_driver_version(browser_version)
        driver_path = os.path.join(self.driver_folder_path, driver_version)
        if os.path.exists(driver_path):
            return driver_path
        raise AttributeError("Could not find appropriate driver for Firefox %s" % browser_version)

    def get_driver_version(self, browser_version):
        if browser_version not in self.browser_version_to_driver_version.keys():
            raise AttributeError(
                "Could not determine driver version associated with Firefox version %s" % browser_version)
        return self.browser_version_to_driver_version[browser_version]

    @staticmethod
    def list_downloaded_binaries() -> list[dict[str, str]]:
        return Binary.list_downloaded_binaries(BIN_FOLDER_PATH)

    @staticmethod
    def get_artisanal_manager() -> ArtisanalBuildManager:
        return Binary.get_artisanal_manager(BIN_FOLDER_PATH, EXECUTABLE_NAME)

    browser_version_to_driver_version = {
        '84': "0.28.0",
        '83': "0.28.0",
        '82': "0.27.0",
        '81': "0.27.0",
        '80': "0.27.0",
        '79': "0.27.0",
        '78': "0.27.0",
        '77': "0.27.0",
        '76': "0.27.0",
        '75': "0.27.0",
        '74': "0.27.0",
        '73': "0.27.0",
        '72': "0.27.0",
        '71': "0.27.0",
        '70': "0.27.0",
        '69': "0.27.0",
        '68': "0.26.0",
        '67': "0.26.0",
        '66': "0.26.0",
        '65': "0.25.0",
        '64': "0.26.0",
        '63': "0.26.0",
        '62': "0.26.0",
        '61': "0.26.0",
        '60': "0.26.0",
        '59': "0.25.0",
        '58': "0.20.1",
        '57': "0.20.1",
        '56': "0.19.1",
        '55': "0.20.1",
        '54': "0.17.0",
        '53': "0.16.1",
        '52': "0.15.0",
        '51': "0.15.0",
        '50': "0.15.0"
    }
