import logging
import os
from abc import abstractmethod

from bughog.evaluation.collectors.collector import Collector

logger = logging.getLogger(__name__)


class EvaluationFramework:
    def __init__(self, subject_type: str) -> None:
        self.experiment_root_folder = os.path.join('/app/subject/', subject_type, 'experiments')
        if not os.path.isdir(self.experiment_root_folder):
            raise AttributeError(f"Could not open '{self.experiment_root_folder}'.")
        self.collector = self.get_collector()

    @abstractmethod
    def get_collector(self) -> Collector:
        pass

    @abstractmethod
    def experiment_is_valid(self, project: str, experiment: str) -> bool:
        pass

    @abstractmethod
    def create_empty_experiment(self, project: str, experiment: str):
        pass

    @abstractmethod
    def execute_script_command(self, command: str):
        pass

    def get_default_file_content(self, file_type: str) -> bytes:
        default_file_content_file = os.path.join(self.experiment_root_folder, '_default_files', file_type)
        if not os.path.isdir(default_file_content_file):
            logger.warning(f"Could not find default file content for file type '{file_type}'.")
            return b''
        with open(default_file_content_file, 'rb') as file:
            return file.read()
