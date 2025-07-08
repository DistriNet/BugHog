import logging
import os
import re

from bughog import cli
from bughog.subject.webbrowser.binary.artisanal_manager import ArtisanalBuildManager
from bughog.subject.webbrowser.binary.binary import BrowserBinary
from bughog.version_control.states.base import State

logger = logging.getLogger('bci')

EXECUTABLE_NAME = 'firefox'
BIN_FOLDER_PATH = '/app/browser/binaries/firefox'
EXTENSION_FOLDER_PATH = '/app/browser/extensions/firefox'


class FirefoxBinary(BrowserBinary):
    def __init__(self, state: State):
        super().__init__(state)

    # @property
    # def executable_name(self) -> str:
    #     return 'firefox'

    # @property
    # def browser_name(self) -> str:
    #     return 'firefox'

    # @property
    # def bin_folder_path(self) -> str:
    #     return BIN_FOLDER_PATH

    # def configure_binary(self) -> None:
    #     binary_folder = os.path.dirname(self.get_potential_bin_path())
    #     cli.execute_and_return_status(f'chmod -R a+x {binary_folder}')
    #     cli.execute_and_return_status(f'chmod -R a+w {binary_folder}')
    #     # Add policy.json to prevent updating. (this measure is effective from version 60)
    #     # https://github.com/mozilla/policy-templates/blob/master/README.md
    #     # (For earlier versions, the prefs.js file is used)
    #     distributions_path = os.path.join(binary_folder, 'distribution')
    #     os.makedirs(distributions_path, exist_ok=True)
    #     policies_path = os.path.join(distributions_path, 'policies.json')
    #     with open(policies_path, 'a') as file:
    #         file.write('{ "policies": { "DisableAppUpdate": true } }')

    # def _get_version(self):
    #     if (bin_path := self.get_bin_path()) is None:
    #         raise AttributeError(f'Binary not available for {self.browser_name} {self.state}')
    #     command = './firefox --version'
    #     output = cli.execute_and_return_output(command, cwd=os.path.dirname(bin_path))
    #     match = re.match(r'Mozilla Firefox (?P<version>[0-9]+)\.[0-9]+.*', output)
    #     if match:
    #         return match.group('version')
    #     raise AttributeError("Could not determine version of binary at '%s'. Version output: %s" % (bin_path, output))

    @staticmethod
    def get_artisanal_manager() -> ArtisanalBuildManager:
        return BrowserBinary._get_artisanal_manager(BIN_FOLDER_PATH, EXECUTABLE_NAME)
