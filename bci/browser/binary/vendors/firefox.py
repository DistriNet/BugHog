import logging
import os
import re

from bci import cli
from bci.browser.binary.artisanal_manager import ArtisanalBuildManager
from bci.browser.binary.binary import Binary
from bci.version_control.states.state import State

logger = logging.getLogger('bci')

EXECUTABLE_NAME = 'firefox'
BIN_FOLDER_PATH = '/app/browser/binaries/firefox'
EXTENSION_FOLDER_PATH = '/app/browser/extensions/firefox'


class FirefoxBinary(Binary):
    def __init__(self, state: State):
        super().__init__(state)

    @property
    def executable_name(self) -> str:
        return "firefox"

    @property
    def browser_name(self) -> str:
        return "firefox"

    @property
    def bin_folder_path(self) -> str:
        return BIN_FOLDER_PATH

    def configure_binary(self) -> None:
        binary_folder = os.path.dirname(self.get_potential_bin_path())
        cli.execute_and_return_status(f'chmod -R a+x {binary_folder}')
        cli.execute_and_return_status(f'chmod -R a+w {binary_folder}')
        # Add policy.json to prevent updating. (this measure is effective from version 60)
        # https://github.com/mozilla/policy-templates/blob/master/README.md
        # (For earlier versions, the prefs.js file is used)
        distributions_path = os.path.join(binary_folder, 'distribution')
        os.makedirs(distributions_path, exist_ok=True)
        policies_path = os.path.join(distributions_path, 'policies.json')
        with open(policies_path, 'a') as file:
            file.write('{ "policies": { "DisableAppUpdate": true } }')

    def _get_version(self):
        if (bin_path := self.get_bin_path()) is None:
            raise AttributeError(f"Binary not available for {self.browser_name} {self.state}")
        command = "./firefox --version"
        output = cli.execute_and_return_output(command, cwd=os.path.dirname(bin_path))
        match = re.match(r'Mozilla Firefox (?P<version>[0-9]+)\.[0-9]+.*', output)
        if match:
            return match.group("version")
        raise AttributeError(
            "Could not determine version of binary at '%s'. Version output: %s" % (bin_path, output))

    def get_driver_version(self, browser_version):
        if browser_version not in self.browser_version_to_driver_version.keys():
            raise AttributeError(
                "Could not determine driver version associated with Firefox version %s" % browser_version)
        return self.browser_version_to_driver_version[browser_version]

    @staticmethod
    def list_downloaded_binaries() -> list[dict[str, str]]:
        return Binary._list_downloaded_binaries(BIN_FOLDER_PATH)

    @staticmethod
    def get_artisanal_manager() -> ArtisanalBuildManager:
        return Binary._get_artisanal_manager(BIN_FOLDER_PATH, EXECUTABLE_NAME)

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
