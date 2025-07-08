import os
import re

from bughog import cli
from bughog.parameters import SubjectConfiguration
from bughog.subject.webbrowser.executable import BrowserExecutable
from bughog.version_control.states.base import State


class FirefoxExecutable(BrowserExecutable):
    def __init__(self, config: SubjectConfiguration, state: State) -> None:
        super().__init__(config, state)

    @property
    def executable_name(self) -> str:
        return 'firefox'

    def _get_version(self):
        command = './firefox --version'
        output = cli.execute_and_return_output(command, cwd=self.executable_folder)
        match = re.match(r'Mozilla Firefox (?P<version>[0-9]+)\.[0-9]+.*', output)
        if match:
            return match.group('version')
        raise AttributeError(f"Could not determine version of binary at '{self.executable_name}'.")

    def _configure_executable(self):
        binary_folder = self.executable_folder
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
