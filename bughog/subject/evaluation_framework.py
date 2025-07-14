import logging
import os
from abc import ABC, abstractmethod

from bughog.evaluation.file_structure import Folder

logger = logging.getLogger(__name__)


class EvaluationFramework(ABC):
    def __init__(self, subject_type: str) -> None:
        self.experiment_root_folder = os.path.join('/app/subject/', subject_type, 'experiments')
        if not os.path.isdir(self.experiment_root_folder):
            raise AttributeError(f"Could not open '{self.experiment_root_folder}'.")

    @abstractmethod
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        pass

    @abstractmethod
    def get_default_experiment_script(self) -> list[str]:
        """
        Returns the default script, which is used when no 'script.cmd' is present in the experiment's folder.
        """
        pass

    @abstractmethod
    def create_empty_experiment(self, project: str, experiment: str):
        pass

    def experiment_sanity_check_succeeded(self, result_variables: set[tuple[str, str]]) -> bool:
        for variable, value in result_variables:
            if variable.lower() == 'sanity_check' and value.lower() == 'ok':
                return True
        return False

    def get_default_file_content(self, file_type: str) -> bytes:
        default_file_content_file = os.path.join(self.experiment_root_folder, '_default_files', file_type)
        if not os.path.isdir(default_file_content_file):
            logger.warning(f"Could not find default file content for file type '{file_type}'.")
            return b''
        with open(default_file_content_file, 'rb') as file:
            return file.read()
