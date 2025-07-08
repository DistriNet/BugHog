import logging
import os
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

    @property
    @abstractmethod
    def executable_name(self) -> str:
        pass

    @property
    @abstractmethod
    def log_path(self) -> Optional[str]:
        pass

    @property
    def executable_folder(self) -> str:
        return os.path.join('/tmp', f'{self.config.subject_name}-{str(self.state.index)}')

    @property
    def executable_path(self) -> str:
        return os.path.join(self.executable_folder, self.executable_name)

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

    def download(self):
        from bughog.database.mongo.executable_cache import ExecutableCache
        if self.is_ready_for_use:
            logger.info('Executable with index {self.state.index} is already ready for use.')
        elif ExecutableCache.fetch_executable_files(self.config, self.state, self.executable_path):
            logger.info(f'Executable with index {self.state.index} was fetched from cache.')
        elif not self.state.has_publicly_available_executable():
            raise Exception(f'Executable with index {self.state.index} is not available online.')
        else:
            start = time.time()
            executable_urls = self.state.get_executable_source_urls()
            util.download_and_extract(executable_urls, self.executable_folder)
            elapsed_time = time.time() - start
            logger.info(f'Executable for {self.state.index} downloaded in {elapsed_time:.2f}s')
            self._configure_executable()
            ExecutableCache.store_executable_files(self.config, self.state, self.executable_folder)

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

    def run(self, args: list[str], timeout: int = 5):
        """
        Runs the executable with the given arguments, and kills it after the given timeout.
        """
        logger.debug(f'Executing: {self.executable_path} {" ".join(args)}')
        with open('/tmp/app.log', 'a+') as file:
            proc = subprocess.Popen(args, stdout=file, stderr=file)
            time.sleep(timeout)
            logger.debug('Terminating browser process using SIGINT...')
            # Use SIGINT and SIGTERM to ensure that cookies remain saved in a browser subjects.
            proc.send_signal(signal.SIGINT)
            proc.send_signal(signal.SIGTERM)
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                logger.debug('App process did not terminate after 5s. Killing process through pkill...')
                subprocess.run(['pkill', '-2', args[0].split('/')[-1]])
            proc.wait()
            logger.debug('Browser process terminated.')
            return proc


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
