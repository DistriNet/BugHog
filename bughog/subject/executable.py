from genericpath import isdir
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
        self.__version = None
        self.origin = None
        self.status = ExecutableStatus.NEW
        self.error_message = None
        self.__process: Optional[subprocess.Popen] = None

    @property
    @abstractmethod
    def executable_name(self) -> str:
        pass

    @property
    @abstractmethod
    def navigation_sleep_duration(self) -> int:
        pass

    @property
    @abstractmethod
    def open_console_hotkey(self) -> list[str]:
        pass

    @property
    def log_path(self) -> str:
        path = os.path.join('/tmp/bh_logs/', f'{self.config.subject_type}-{self.config.subject_name}-{self.state.name}.log')
        if not os.path.isdir(os.path.dirname(path)):
            os.mkdir(os.path.dirname(path))
        return path

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

    @abstractmethod
    def _configure_executable(self):
        """
        Configures the downloaded executable folder after download and extraction, but before it is cached or used.
        This function should be idempotent.
        """
        pass

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
            util.download_and_extract(executable_urls, self.staging_folder)
            elapsed_time = time.time() - start
            logger.info(f'Executable for {self.state.name} was downloaded in {elapsed_time:.2f}s')
            self._configure_executable()
            ExecutableCache.store_executable_files(self.config, self.state.name, self.staging_folder)

    def remove(self):
        if not self.state.has_local_executable():
            shutil.rmtree(self.temporary_storage_folder)

    def stage(self):
        if not self.is_ready_for_use:
            util.copy_folder(self.temporary_storage_folder, self.staging_folder)

    def unstage(self):
        if self.is_ready_for_use:
            shutil.rmtree(self.staging_folder)

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
    def pre_evaluation_setup(self):
        """
        Executes the setup required for an evaluation.
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
    def post_evaluation_cleanup(self):
        """
        Executes the cleanup required after an evaluation.
        """
        pass

    @abstractmethod
    def _get_cli_command(self) -> list[str]:
        pass

    def run(self, experiment_specific_params: list[str], timeout: int = 5):
        """
        Runs the executable with the given arguments, and kills it after the given timeout.
        """
        cli_command = self._get_cli_command() + experiment_specific_params
        logger.debug(f'Executing: {self.executable_path} {" ".join(cli_command)}')
        with open(self.log_path, 'a+') as file:
            proc = subprocess.Popen(cli_command, stdout=file, stderr=file)
            self.__process = proc
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
