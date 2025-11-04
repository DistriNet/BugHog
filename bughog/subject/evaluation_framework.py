import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Optional

from bughog.evaluation.file_structure import Folder

logger = logging.getLogger(__name__)


class EvaluationFramework(ABC):
    def __init__(self, subject_type: str) -> None:
        self.experiment_root_folder = os.path.join('./subject/', subject_type, 'experiments')
        if not os.path.isdir(self.experiment_root_folder):
            raise AttributeError(f"Could not open '{self.experiment_root_folder}'.")

    @abstractmethod
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        pass

    @abstractmethod
    def get_default_experiment_script(self, experiment_folder: Folder) -> list[str]:
        """
        Returns the default script, which is used when no 'script.cmd' is present in the experiment's folder.
        """
        pass

    @abstractmethod
    def fill_empty_experiment_with_default(self, path: str):
        """
        Populates an empty experiment with default folders and files.
        """
        pass

    @abstractmethod
    def get_poc_file_name(self) -> str:
        pass

    @abstractmethod
    def get_comment_prefix_delimiter(self) -> str:
        pass

    def get_comment_suffix_delimiter(self) -> str:
        return ''

    def get_runtime_flags(self, experiment_folder: Folder) -> list[str]:
        """
        Returns the experiment-defined runtime flags.
        """

        if args := self.get_bughog_poc_parameter(experiment_folder, 'runtime_flags'):
            return args.split()
        return []

    def get_runtime_env_vars(self, experiment_folder: Folder) -> list[str]:
        """
        Returns the experiment-defined environment variables.
        """
        if args := self.get_bughog_poc_parameter(experiment_folder, 'env_vars'):
            return args.split()
        return []

    def get_runtime_args(self, experiment_folder: Folder) -> list[str]:
        """
        Returns the experiment-defined executable arguments.
        """
        if args := self.get_bughog_poc_parameter(experiment_folder, 'runtime_args'):
            return args.split()
        return []

    def get_expected_output_regex(self, experiment_folder: Folder) -> Optional[str]:
        """
        Returns the experiment-defined expected output regex.
        """
        return self.get_bughog_poc_parameter(experiment_folder, 'expected_output')

    def get_unexpected_output_regex(self, experiment_folder: Folder) -> Optional[str]:
        """
        Returns the experiment-defined unexpected output regex.
        """
        return self.get_bughog_poc_parameter(experiment_folder, 'unexpected_output')

    def get_bughog_poc_parameter(self, experiment_folder: Folder, parameter: str) -> Optional[str]:
        """
        Returns the given parameter's value, as defined in the poc file.
        """
        poc_path = os.path.join(experiment_folder.path, self.get_poc_file_name())
        with open(poc_path, 'r') as poc:
            for line in poc:
                if parameter_value := self._parse_bughog_poc_param_line(line, parameter):
                    return parameter_value
        return None

    def _parse_bughog_poc_param_line(self, line: str, parameter: str) -> str | None:
        prefix = self.get_comment_prefix_delimiter()
        suffix = self.get_comment_suffix_delimiter()
        match = re.search(rf'^\s*{prefix}\s*bughog_{parameter}:\s*(.*)\s*{suffix}\s*$', line)
        return match.group(1).strip() if match else None

    def get_default_file_content(self, file_type: str) -> bytes:
        """
        Returns the default file content upon creation of a new file within an experiment context.
        """
        default_file_content_file = os.path.join(self.experiment_root_folder, '_default_files', file_type)
        if not os.path.isdir(default_file_content_file):
            logger.warning(f"Could not find default file content for file type '{file_type}'.")
            return b''
        with open(default_file_content_file, 'rb') as file:
            return file.read()

    def requires_sanity_check(self) -> bool:
        return True
