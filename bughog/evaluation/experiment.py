import json
import logging
import os
from dataclasses import dataclass
import re
from typing import Optional

from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework
from bughog.web.clients import Clients

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
EXPERIMENT_FOLDER_PATH = '/app/experiments/pages'


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
                if 'script.cmd' in [file.name for file in experiment.files]:
                    experiment.tags.append('runnable')
        return root_folder

    def get_projects(self) -> list[str]:
        project_folders = self.root_folder.get_all_folders_with_tag('project')
        return [folder.name for folder in project_folders]

    def create_empty_project(self, project_name: str):
        self.__is_valid_name(project_name)
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

    def get_poc_structure(self, project, poc) -> dict:
        # TODO
        pass

    def _get_poc_file_path(self, project: str, poc: str, domain: str, path: str, file_name: str) -> str:
        # Top-level config file
        if domain == 'Config' and path == '_':
            return os.path.join(Global.custom_page_folder, project, poc, file_name)

        return os.path.join(Global.custom_page_folder, project, poc, domain, path, file_name)

    def get_poc_file(self, project: str, poc: str, domain: str, path: str, file_name: str) -> str:
        file_path = self._get_poc_file_path(project, poc, domain, path, file_name)
        if os.path.isfile(file_path):
            with open(file_path) as file:
                return file.read()
        raise AttributeError(f"Could not find PoC file at expected path '{file_path}'")

    def update_poc_file(self, project: str, poc: str, domain: str, path: str, file_name: str, content: str) -> bool:
        file_path = self._get_poc_file_path(project, poc, domain, path, file_name)
        if os.path.isfile(file_path):
            if content == '':
                logger.warning('Attempt to save empty file ignored')
                return False
            with open(file_path, 'w') as file:
                file.write(content)
            return True
        return False

    def add_page(self, project: str, poc: str, domain: str, path: str, file_type: str):
        domain_path = os.path.join(self.root_folder_path, project, poc, domain)
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)

        self.__is_valid_name(path)
        if file_type == 'py':
            file_name = path if path.endswith('.py') else path + '.py'
            file_path = os.path.join(domain_path, file_name)
        else:
            page_path = os.path.join(domain_path, path)
            if not os.path.exists(page_path):
                os.makedirs(page_path)
            new_file_name = f'index.{file_type}'
            file_path = os.path.join(page_path, new_file_name)
            headers_file_path = os.path.join(page_path, 'headers.json')
            if not os.path.exists(headers_file_path):
                with open(headers_file_path, 'w') as file:
                    file.write(self.get_default_file_content('headers.json'))

        if os.path.exists(file_path):
            raise AttributeError(f"The given page '{path}' does already exist.")
        with open(file_path, 'w') as file:
            file.write(self.get_default_file_content(file_type))

        self.reload_experiments()
        # Notify clients of change (an experiment might now be runnable)
        Clients.push_experiments_to_all()

    def add_config(self, project: str, poc: str, type: str) -> bool:
        content = self.get_default_file_content(type)

        if content == '':
            return False

        file_path = os.path.join(self.root_folder_path, project, poc, type)
        with open(file_path, 'w') as file:
            file.write(content)

        self.reload_experiments()
        # Notify clients of change (an experiment might now be runnable)
        Clients.push_experiments_to_all()

        return True

    def __get_project_folder(self, project_name: str) -> Folder:
        for project in self.root_folder.subfolders:
            if project.name == project_name:
                return project
        raise Exception(f"Could not find project '{project_name}'")

    def __get_experiment_folder(self, project_name: str, experiment_name: str) -> Folder:
        project = self.__get_project_folder(project_name)
        for experiment in project.subfolders:
            if experiment.name == experiment_name:
                return experiment
        raise Exception(f"Could not find experiment '{experiment_name}'")

    def __get_interaction_script(self, project_name: str, experiment_name: str) -> list[str]:
        experiment = self.__get_experiment_folder(project_name, experiment_name)
        script_path = os.path.join(experiment.path, experiment.name, 'script.cmd')
        if os.path.isfile(script_path):
            # If an interaction script is specified, it is parsed and used
            with open(script_path) as file:
                return file.readlines()
        else:
            raise Exception(f"Could not find experiment script at '{script_path}'")

    def experiment_is_valid(self, project: str, experiment: str) -> bool:
        return self.framework.experiment_is_valid(project, experiment)

    def create_empty_poc(self, project: str, experiment: str):
        return self.framework.create_empty_experiment(project, experiment)

    def execute_script_command(self, command: str):
        return self.framework.execute_script_command(command)

    def get_default_file_content(self, file_type: str) -> str:
        return self.framework.get_default_file_content(file_type)

    def reload_experiments(self):
        self.initialize_experiments()
        logger.info('Experiments are reloaded.')

    @staticmethod
    def __is_valid_name(name: str) -> None:
        """
        Checks whether the given string is a valid experiment, page or project name, and raises an exception if not.
        This is to prevent issues with URL encoding and decoding.

        :param name: Name to be checked on validity.
        """
        if name is None or name == '':
            raise AttributeError('The given name cannot be empty.')
        if re.match(r'^[A-Za-z0-9_\-.]+$', name) is None:
            raise AttributeError(
                f"The given name '{name}' is invalid. Only letters, numbers, "
                "'.', '-' and '_' can be used, and the name should not be empty."
            )


def verify() -> None:
    """
    Verifies the experiment pages, logger warnings for unsupported configurations.
    """
    for project in os.listdir(EXPERIMENT_FOLDER_PATH):
        project_path = os.path.join(EXPERIMENT_FOLDER_PATH, project)
        if not os.path.isdir(project_path):
            logger.warning(f"Unexpected file in '{__user_path(project_path)}' will be ignored.")
            continue
        for experiment in os.listdir(project_path):
            __verify_experiment(project, experiment)


def __verify_experiment(project: str, experiment: str) -> None:
    experiment_path = os.path.join(EXPERIMENT_FOLDER_PATH, project, experiment)
    if not os.path.isdir(experiment_path):
        logger.warning(f"Unexpected file at '{__user_path(experiment_path)}' will be ignored.")
        return
    for domain in os.listdir(experiment_path):
        if domain in ['script.cmd', 'url_queue.txt']:
            continue
        domain_path = os.path.join(experiment_path, domain)
        if not os.path.isdir(domain_path):
            logger.warning(f"Unexpected file '{__user_path(domain_path)}' will be ignored.")
            continue
        if domain not in SUPPORTED_DOMAINS:
            logger.warning(f"Unsupported domain '{domain}' in '{__user_path(experiment_path)}' will be ignored.")
        for page in os.listdir(domain_path):
            __verify_page(project, experiment, domain, page)


def __verify_page(project: str, experiment: str, domain: str, page: str) -> None:
    page_path = os.path.join(EXPERIMENT_FOLDER_PATH, project, experiment, domain, page)
    if page.endswith('.py'):
        return
    if not os.path.isdir(page_path):
        logger.warning(f"Unexpected file at '{__user_path(page_path)}' will be ignored.")
        return
    for file_name in os.listdir(page_path):
        file_path = os.path.join(page_path, file_name)
        if not os.path.isfile(file_path):
            logger.warning(f"Unexpected folder at '{__user_path(page_path)}' will be ignored.")
            continue
        if file_name == 'headers.json':
            __verify_headers(file_path)
            continue
        file_name_split = file_name.split('.')
        if len(file_name_split) < 2:
            logger.warning(f"Could not deduce file extension at '{__user_path(file_path)}'.")
        if file_name_split[-1] not in SUPPORTED_FILE_TYPES:
            logger.warning(f"File type of '{__user_path(file_path)}' is not supported.")


def __verify_headers(path: str) -> None:
    """
    Verifies whether the headers file at the given path is valid.
    """
    with open(path, 'r', encoding='utf-8') as file:
        try:
            json_content = json.load(file)
        except json.decoder.JSONDecodeError:
            logger.warning(f"Could not parse '{__user_path(path)}'")
            return
        if not isinstance(json_content, list):
            raise AttributeError(f"Not a list: '{__user_path(path)}'")
        for item in json_content:
            if 'key' and 'value' not in item:
                logger.warning(f"Not all dictionary entries contain a key-value combination in '{__user_path(path)}'.")


def __user_path(path: str) -> str:
    """
    Translates the given path to the user readeable path outside container.
    """
    if path.startswith('/app/'):
        return path[5:]
    return path
