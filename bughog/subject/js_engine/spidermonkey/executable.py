import re

from bughog import cli
from bughog.subject.executable import Executable


class SpiderMonkeyExecutable(Executable):
    @property
    def executable_name(self) -> str:
        return 'js'

    @property
    def post_experiment_sleep_duration(self) -> int:
        return 0

    @property
    def open_console_hotkey(self) -> list[str]:
        raise NotImplementedError()

    def _optimize_for_storage(self) -> None:
        pass

    def _configure_executable(self):
        cli.execute('chmod u+x js', cwd=self.staging_folder, ignore_error=False)

    @property
    def supported_options(self) -> list[str]:
        return []

    def _get_version(self) -> str:
        command = './js --version'
        output = cli.execute_and_return_output(command, cwd=self.staging_folder)
        match = re.search(r'JavaScript-C(\d+\.\d+(?:\.\d+)?)', output)
        if match:
            return match.group(1)
        raise AttributeError(f"Could not determine version of executable at '{self.executable_name}'.")

    def _get_cli_command(self) -> list[str]:
        return [self.executable_path] + self._runtime_flags

    def pre_experiment_setup(self):
        self.fetch()
        self.stage()

    def post_experiment_cleanup(self):
        self.unstage()
        self.remove()

    def pre_try_setup(self):
        pass

    def post_try_cleanup(self):
        pass
