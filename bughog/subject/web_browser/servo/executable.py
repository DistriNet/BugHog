import re

from bughog import cli
from bughog.parameters import SubjectConfiguration
from bughog.subject.web_browser.executable import BrowserExecutable
from bughog.version_control.state.base import State


class ServoExecutable(BrowserExecutable):
    def __init__(self, config: SubjectConfiguration, state: State) -> None:
        super().__init__(config, state)
        self._profile_path = None

    @property
    def executable_name(self) -> str:
        return 'servo'

    def _get_version(self) -> str:
        command = f'./{self.executable_name} --version'
        output = cli.execute_and_return_output(command, cwd=self.staging_folder)
        match = re.search(r'Servo (?P<version>[0-9]+\.[0-9]+\.[0-9]+(-\w+)?)', output)
        if match:
            return match.group('version')
        raise AttributeError(f"Could not determine version of executable at '{self.executable_name}'.")

    def _optimize_for_storage(self) -> None:
        pass

    def _configure_executable(self) -> None:
        cli.execute_and_return_status(f'chmod -R a+x {self.staging_folder}')

    @property
    def post_experiment_sleep_duration(self) -> int:
        return 1

    @property
    def open_console_hotkey(self) -> list[str]:
        """
        This is not implemented, but we simply ignore the command in the interaction script.
        """
        return []

    @property
    def supported_options(self) -> list[str]:
        return []

    def _get_cli_command(self) -> list[str]:
        return [self.executable_path, '--ignore-certificate-errors']

    def _prepare_profile_folder(self):
        pass

    def _remove_profile_folder(self):
        pass
