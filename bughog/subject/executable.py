import logging
import os
import shutil
import signal
import subprocess
import time
from abc import ABC, abstractmethod
from enum import Enum, auto, unique
from typing import Optional

from bughog import util
from bughog.evaluation.collectors.logs import LogCollector
from bughog.evaluation.file_structure import Folder
from bughog.parameters import SubjectConfiguration
from bughog.version_control.state.base import State

logger = logging.getLogger(__name__)


class Executable(ABC):
    """
    Abstract base class representing a subject executable, which is executed during evaluation.
    """

    def __init__(self, config: SubjectConfiguration, state: State) -> None:
        self.config = config
        self.state = state
        self.origin = None
        self.status = ExecutableStatus.NEW
        self.error_message = None
        self._runtime_flags = []
        self._runtime_env_vars = {}
        self.__version = None
        self.__process: Optional[subprocess.Popen] = None

    # #
    # TO BE IMPLEMENT BY EVERY EVALUATION SUBJECT EXECUTABLE
    # #

    @property
    @abstractmethod
    def executable_name(self) -> str:
        """
        Returns the executable name, required to call it in the CLI.
        """
        pass

    @property
    @abstractmethod
    def post_experiment_sleep_duration(self) -> int:
        """
        Returns the number of seconds should be waited between experiments.
        """
        pass

    @abstractmethod
    def _optimize_for_storage(self) -> None:
        """
        Optimizes executable files right before storage.
        """
        pass

    @abstractmethod
    def _configure_executable(self) -> None:
        """
        Configures the executable folder after staging.
        """
        pass

    @property
    @abstractmethod
    def supported_options(self) -> list[str]:
        pass

    @abstractmethod
    def _get_version(self) -> str:
        """
        Runs the executable to retrieve its version string.
        """
        pass

    @abstractmethod
    def pre_experiment_setup(self):
        """
        Executes the setup required for an experiment.
        """
        pass

    @abstractmethod
    def pre_try_setup(self):
        """
        Executes the setup required for a try.
        """
        pass

    @abstractmethod
    def post_try_cleanup(self):
        """
        Executes the cleanup required after a try.
        """
        pass

    @abstractmethod
    def post_experiment_cleanup(self):
        """
        Executes the cleanup required after an experiment.
        """
        pass

    @abstractmethod
    def _get_cli_command(self) -> list[str]:
        pass

    # #
    # HELPER FUNCTIONS
    # #

    @property
    def log_path(self) -> str:
        return LogCollector.log_path

    @property
    @util.ensure_folder_exists
    def storage_folder(self) -> str:
        if self.state.has_local_executable():
            return self.state.get_local_executable_folder_path()
        else:
            return self.temporary_storage_folder

    @property
    @util.ensure_folder_exists
    def temporary_storage_folder(self) -> str:
        return os.path.join('/tmp/executables/', f'{self.config.subject_name}-{str(self.state.index)}')

    @property
    @util.ensure_folder_exists
    def staging_folder(self) -> str:
        return os.path.join('/tmp/staging/', f'{self.config.subject_name}-{str(self.state.index)}')

    @property
    def executable_path(self) -> str:
        return os.path.join(self.staging_folder, self.executable_name)

    @property
    def is_ready_for_use(self) -> bool:
        return os.path.isfile(self.executable_path) and self.version is not None

    @property
    def version(self) -> str:
        if self.__version is None:
            self.__version = self._get_version()
        return self.__version

    def add_runtime_flags(self, flags: list[str]) -> None:
        self._runtime_flags.extend(flags)

    def add_runtime_env_vars(self, vars: list[str]) -> None:
        for var in vars:
            if '=' in var:
                key, value = var.split('=', 1)
                # Concatenate duplicated ASAN_OPTIONS values with a colon
                if key == 'ASAN_OPTIONS' and key in self._runtime_env_vars:
                    self._runtime_env_vars[key] += ':' + value
                else:
                    self._runtime_env_vars[key] = value

    def fetch(self):
        from bughog.database.mongo.executable_cache import ExecutableCache

        if self.state.has_local_executable():
            logger.info(f'Executable for {self.state.name} was found locally.')
        elif ExecutableCache.fetch_executable_files(self.config, self.state.name, self.temporary_storage_folder):
            logger.info(f'Executable for {self.state.name} was fetched from cache.')
        elif not self.state.has_publicly_available_executable():
            raise Exception(f'Executable for {self.state.name} is not available online.')
        else:
            start = time.time()
            executable_urls = self.state.get_executable_source_urls()
            util.download_and_extract(executable_urls, self.temporary_storage_folder)
            elapsed_time = time.time() - start
            logger.info(f'Executable for {self.state.name} was downloaded in {elapsed_time:.2f}s')
            self._optimize_for_storage()
            ExecutableCache.store_executable_files(self.config, self.state.name, self.temporary_storage_folder)

    def remove(self):
        if not self.state.has_local_executable():
            shutil.rmtree(self.temporary_storage_folder)

    def stage(self):
        self.unstage()
        util.copy_folder(self.temporary_storage_folder, self.staging_folder)
        self._configure_executable()

    def unstage(self):
        if os.path.isfile(self.staging_folder):
            os.remove(self.staging_folder)
        elif os.path.isdir(self.staging_folder):
            shutil.rmtree(self.staging_folder)

    def run(self, experiment_specific_params: list[str], cwd: Optional[Folder] = None, timeout: int = 5):
        """
        Runs the executable with the given arguments, and kills it after the given timeout.
        """
        cli_command = self._get_cli_command() + experiment_specific_params
        logger.debug(f'Executing: {" ".join(cli_command)}')
        with open(self.log_path, 'a+') as file:
            popen_args = {'args': cli_command, 'stdout': file, 'stderr': file}
            if cwd:
                popen_args['cwd'] = cwd.path
            if self._runtime_env_vars:
                popen_args['env'] = self._runtime_env_vars
            self.__process = subprocess.Popen(**popen_args)
            time.sleep(timeout)

    def terminate(self):
        if self.__process is None:
            return
        logger.debug('Terminating subject process using SIGINT...')
        # Use SIGINT and SIGTERM to end process such that cookies remain saved.
        self.__process.send_signal(signal.SIGINT)
        self.__process.send_signal(signal.SIGTERM)

        try:
            stdout, stderr = self.__process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            logger.info('Subject process did not terminate after 5s. Killing process through pkill...')
            cli_command = self._get_cli_command()
            subprocess.run(['pkill', '-2', cli_command[0].split('/')[-1]])

        self.__process.wait()
        logger.debug('Subject process terminated.')


@unique
class ExecutableStatus(Enum):
    """
    The condition of an executable.
    """

    COMPLETED = auto()
    READY_FOR_USE = auto()
    EXPERIMENT_FAILED = auto()
    UNAVAILABLE = auto()
    NEW = auto()
