import re
from bughog import cli
from bughog.subject.executable import Executable


class V8Executable(Executable):

    @property
    def executable_name(self) -> str:
        return 'd8'

    @property
    def navigation_sleep_duration(self) -> int:
        return 0

    @property
    def open_console_hotkey(self) -> list[str]:
        raise NotImplementedError()

    def _configure_executable(self):
        """
        Configures the downloaded executable folder after download and extraction, but before it is cached or used.
        This function should be idempotent.
        """
        cli.execute('chmod u+x d8', cwd=self.temporary_storage_folder, ignore_error=False)

    @property
    def supported_options(self) -> list[str]:
        return []

    def _get_version(self) -> str:
        command = './d8 -e "print(\'V8 version: \' + version())"'
        output = cli.execute_and_return_output(command, cwd=self.staging_folder)
        match = re.match(r'V8 version: (?P<version>[0-9]+\.[0-9]+\.[0-9]+)', output)
        if match:
            return match.group('version')
        raise AttributeError(f"Could not determine version of executable at '{self.executable_name}'.")

    def _get_cli_command(self) -> list[str]:
        return [self.executable_path] + self._runtime_flags

    def pre_evaluation_setup(self):
        self.fetch()

    def post_evaluation_cleanup(self):
        self.remove()

    def pre_experiment_setup(self):
        self.stage()

    def post_experiment_cleanup(self):
        self.unstage()

    def pre_try_setup(self):
        pass

    def post_try_cleanup(self):
        pass
