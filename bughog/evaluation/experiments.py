import logging
import os
import re
import shutil

from bughog.evaluation.file_structure import Folder
from bughog.parameters import EvaluationParameters
from bughog.subject.evaluation_framework import EvaluationFramework

logger = logging.getLogger(__name__)

SUPPORTED_FILE_TYPES = [
    'css',
    'html',
    'js',
    'py',
    'xml',
]
SUPPORTED_DOMAINS = [
    'leak.test',
    'a.test',
    'sub.a.test',
    'sub.sub.a.test',
    'b.test',
    'sub.b.test',
    'adition.com',
]


class Experiments:
    def __init__(self, subject_type: str, evaluation_framework: EvaluationFramework) -> None:
        self.subject_type = subject_type
        self.framework = evaluation_framework
        self.root_folder = self.initialize_experiments()

    @property
    def root_folder_path(self) -> str:
        return f'/app/subject/{self.subject_type}/experiments/'

    def initialize_experiments(self) -> Folder:
        root_folder = Folder.parse(self.root_folder_path)
        for project in root_folder.subfolders:
            project.tags.append('project')
            for experiment in project.subfolders:
                experiment.tags.append('experiment')
                if self.framework.experiment_is_runnable(experiment):
                    experiment.tags.append('runnable')
        return root_folder

    def get_projects(self) -> list[str]:
        project_folders = self.root_folder.get_all_folders_with_tag('project')
        return sorted([folder.name for folder in project_folders], key=str.lower)

    def create_empty_project(self, project_name: str):
        self.__is_valid_file_or_folder(project_name)
        if project_name in [folder.name for folder in self.root_folder.get_all_folders_with_tag('project')]:
            raise AttributeError(f"The given project name '{project_name}' already exists.")
        new_project_path = os.path.join(self.root_folder_path, project_name)
        os.mkdir(new_project_path)
        self.reload_experiments()

    def get_experiments(self, project_name: str) -> list[tuple[str, bool]]:
        project_root_folder = self.__get_project_folder(project_name)
        experiment_folders = project_root_folder.get_all_folders_with_tag('experiment')
        experiments = [(folder.name, 'runnable' in folder.tags) for folder in experiment_folders]
        return sorted(experiments, key=lambda x: x[0])

    def _get_poc_folder_path(self, project: str, poc: str, folder: str) -> str:
        return os.path.join(self.root_folder_path, project, poc, folder)

    def _get_poc_file_path(self, project: str, poc: str, folder_name: str | None, file_name: str) -> str:
        if folder_name is None:
            return os.path.join(self.root_folder_path, project, poc, file_name)
        return os.path.join(self.root_folder_path, project, poc, folder_name, file_name)

    def get_poc_file(self, project: str, poc: str, folder_name: str | None, file_name: str) -> str:
        file_path = self._get_poc_file_path(project, poc, folder_name, file_name)
        if os.path.isfile(file_path):
            with open(file_path) as file:
                return file.read()
        raise AttributeError(f"Could not find PoC file at expected path '{file_path}'")

    def update_poc_file(self, project: str, poc: str, folder: str | None, file_name: str, content: str) -> bool:
        file_path = self._get_poc_file_path(project, poc, folder, file_name)
        if os.path.isfile(file_path):
            if content == '':
                logger.warning('Attempt to save empty file ignored')
                return False
            with open(file_path, 'w') as file:
                file.write(content)
            return True
        return False

    def add_experiment(self, project: str, poc_name: str) -> None:
        poc_path = os.path.join(self.root_folder_path, project, poc_name)
        if not os.path.exists(poc_path):
            os.makedirs(poc_path)
        else:
            raise AttributeError(f'Experiment {poc_name} for {project} already exists.')

    def add_folder_or_file(self, project: str, poc: str, folder_name: str | None, file_name: str):
        # Validate and create folder
        if folder_name is not None:
            self.__is_valid_file_or_folder(folder_name)
            folder_path = self._get_poc_folder_path(project, poc, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

        # Validate and create file
        if file_name is not None:
            self.__is_valid_file_or_folder(file_name)
            file_path = self._get_poc_file_path(project, poc, folder_name, file_name)
            if os.path.exists(file_path):
                raise AttributeError(f"The given file '{file_path}' already exists.")
            with open(file_path, 'bw') as file:
                file.write(self.get_default_file_content(file_name))

        self.reload_experiments()

    def remove_folder_or_file(self, project: str, poc: str, folder_name: str | None, file_name: str):
        if file_name is not None:
            file_path = self._get_poc_file_path(project, poc, folder_name, file_name)
            os.remove(file_path)
        if folder_name is not None:
            folder_path = self._get_poc_folder_path(project, poc, folder_name)
            shutil.rmtree(folder_path)

    def __get_project_folder(self, project_name: str) -> Folder:
        for project in self.root_folder.subfolders:
            if project.name == project_name:
                return project
        raise Exception(f"Could not find project '{project_name}' for '{self.subject_type}'")

    def __get_experiment_folder(self, project_name: str, experiment_name: str) -> Folder:
        project = self.__get_project_folder(project_name)
        for experiment in project.subfolders:
            if experiment.name == experiment_name:
                return experiment
        raise Exception(f"Could not find experiment '{experiment_name}'")

    def get_experiment_folder(self, params: EvaluationParameters) -> Folder:
        project_name = params.evaluation_range.project_name
        experiment_name = params.evaluation_range.experiment_name
        return self.__get_experiment_folder(project_name, experiment_name)

    def get_experiment_dir_tree(self, project_name: str, experiment_name: str) -> dict:
        experiment_folder = self.__get_experiment_folder(project_name, experiment_name)
        return experiment_folder.serialize()

    def get_interaction_script(self, experiment_folder: Folder) -> list[str]:
        script_path = os.path.join(experiment_folder.path, 'script.cmd')
        if os.path.isfile(script_path):
            # If an interaction script is specified, it is parsed and used
            with open(script_path) as file:
                return file.readlines()
        else:
            return self.framework.get_default_experiment_script(experiment_folder)

    def get_default_file_content(self, file_name: str) -> bytes:
        _, file_type = os.path.splitext(file_name)
        return self.framework.get_default_file_content(file_type)

    def reload_experiments(self):
        self.root_folder = self.initialize_experiments()
        logger.info('Experiments are reloaded.')

    @staticmethod
    def __is_valid_file_or_folder(name: str) -> None:
        """
        Checks whether the given strings are a valid names, and raises an exception if not.
        This is to prevent issues with URL encoding and decoding.

        :param name: File or folder name to be checked.
        """
        if name is None or name == '':
            raise AttributeError('The file name cannot be empty.')
        regex = r'^[A-Za-z0-9_\-.]+$'
        if re.match(regex, name) is None:
            raise AttributeError(f"The given name '{name}' is invalid. Only letters, numbers, '.', '-' and '_' can be used, and the name should not be empty.")
