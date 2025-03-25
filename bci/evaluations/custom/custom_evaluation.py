import logging
import os
from typing import Optional

from bci.browser.configuration.browser import Browser
from bci.browser.interaction.interaction import Interaction
from bci.configuration import Global
from bci.evaluations.collectors.collector import Collector, Type
from bci.evaluations.evaluation_framework import EvaluationFramework, FailedSanityCheck
from bci.evaluations.logic import TestParameters, TestResult
from bci.version_control.state_result_factory import StateResultFactory
from bci.web.clients import Clients

logger = logging.getLogger(__name__)


class CustomEvaluationFramework(EvaluationFramework):
    __files_and_folders_to_ignore = ['.DS_Store']

    def __init__(self):
        super().__init__()
        self.dir_tree = self.initialize_dir_tree()
        self.tests_per_project = self.initialize_tests_and_interactions(self.dir_tree)

    @staticmethod
    def initialize_dir_tree() -> dict:
        """
        Initializes directory tree of experiments.
        """
        path = Global.custom_page_folder
        dir_tree = {}

        def set_nested_value(d: dict, keys: list[str], value: dict):
            nested_dict = d
            for key in keys[:-1]:
                nested_dict = nested_dict[key]
            nested_dict[keys[-1]] = value

        for root, dirs, files in os.walk(path):
            # Remove base path from root
            root = root[len(path) :]
            keys = root.split('/')[1:]
            subdir_tree = {
                dir: {} for dir in dirs if dir not in CustomEvaluationFramework.__files_and_folders_to_ignore
            } | {file: None for file in files if file not in CustomEvaluationFramework.__files_and_folders_to_ignore}
            if root:
                set_nested_value(dir_tree, keys, subdir_tree)
            else:
                dir_tree = subdir_tree

        return dir_tree

    @staticmethod
    def initialize_tests_and_interactions(dir_tree: dict) -> dict:
        experiments_per_project = {}
        page_folder_path = Global.custom_page_folder
        for project, experiments in dir_tree.items():
            # Find tests in folder
            project_path = os.path.join(page_folder_path, project)
            experiments_per_project[project] = {}
            for experiment in experiments:
                data = {}

                if interaction_script := CustomEvaluationFramework.__get_interaction_script(project_path, experiment):
                    data['script'] = interaction_script
                elif url_queue := CustomEvaluationFramework.__get_url_queue(project, project_path, experiment):
                    data['url_queue'] = url_queue

                data['runnable'] = CustomEvaluationFramework.is_runnable_experiment(project, experiment, dir_tree, data)

                experiments_per_project[project][experiment] = data
        return experiments_per_project

    @staticmethod
    def __get_interaction_script(project_path: str, experiment: str) -> list[str] | None:
        interaction_file_path = os.path.join(project_path, experiment, 'script.cmd')
        if os.path.isfile(interaction_file_path):
            # If an interaction script is specified, it is parsed and used
            with open(interaction_file_path) as file:
                return file.readlines()
        return None

    @staticmethod
    def __get_url_queue(project: str, project_path: str, experiment: str) -> Optional[list[str]]:
        url_queue_file_path = os.path.join(project_path, experiment, 'url_queue.txt')
        if os.path.isfile(url_queue_file_path):
            # If an URL queue is specified, it is parsed and used
            with open(url_queue_file_path) as file:
                return file.readlines()
        else:
            # Otherwise, a default URL queue is used, based on the domain that hosts the main page
            experiment_path = os.path.join(project_path, experiment)
            assert os.path.isdir(experiment_path)
            for domain in os.listdir(experiment_path):
                main_folder_path = os.path.join(experiment_path, domain, 'main')
                if os.path.exists(main_folder_path):
                    return [
                        f'https://{domain}/{project}/{experiment}/main',
                        'https://a.test/report/?bughog_sanity_check=OK',
                    ]
        return None

    @staticmethod
    def is_runnable_experiment(project: str, poc: str, dir_tree: dict[str, dict], data: dict[str, str]) -> bool:
        # Always runnable if there is either an interaction script or url_queue present
        if 'script' in data or 'url_queue' in data:
            return True

        # Should have exactly one main folder otherwise
        domains = dir_tree[project][poc]
        main_paths = [paths for paths in domains.values() if paths is not None and 'main' in paths.keys()]
        if len(main_paths) != 1:
            return False
        # Main should have index.html
        if 'index.html' not in main_paths[0]['main'].keys():
            return False
        return True

    def perform_specific_evaluation(self, browser: Browser, params: TestParameters) -> TestResult:
        logger.info(f'Starting test for {params}')
        browser_version = browser.version
        binary_origin = browser.get_binary_origin()

        state_result_factory = StateResultFactory(experiment=params.mech_group)
        collector = Collector([Type.REQUESTS, Type.LOGS])
        collector.start()

        is_dirty = False
        tries_left = 3
        experiment = self.tests_per_project[params.evaluation_configuration.project][params.mech_group]
        try:
            sanity_check_was_successful = False
            poc_was_reproduced = False
            while not poc_was_reproduced and tries_left > 0:
                tries_left -= 1
                browser.pre_try_setup()
                if 'script' in experiment:
                    interaction = Interaction(browser, experiment['script'], params)
                    interaction.execute()
                else:
                    url_queue = experiment['url_queue']
                    for url in url_queue:
                        browser.visit(url)
                browser.post_try_cleanup()
                intermediary_state_result = state_result_factory.get_result(collector.collect_results())
                sanity_check_was_successful |= not intermediary_state_result.is_dirty
                poc_was_reproduced = intermediary_state_result.reproduced
            if not poc_was_reproduced and not sanity_check_was_successful:
                raise FailedSanityCheck()
        except FailedSanityCheck:
            logger.error('Evaluation sanity check has failed', exc_info=True)
            is_dirty = True
        except Exception as e:
            logger.error(f'An error during evaluation: {e}', exc_info=True)
            is_dirty = True
        finally:
            logger.debug(f'Evaluation finished with {tries_left} tries left')
            collector.stop()
            results = collector.collect_results()
        return params.create_test_result_with(browser_version, binary_origin, results, is_dirty)

    def get_mech_groups(self, project: str) -> list[tuple[str, bool]]:
        if project not in self.tests_per_project:
            return []
        pocs = [(poc_name, poc_data['runnable']) for poc_name, poc_data in self.tests_per_project[project].items()]
        return sorted(pocs, key=lambda x: x[0])

    def get_projects(self) -> list[str]:
        return sorted(list(self.tests_per_project.keys()))

    def create_empty_project(self, project_name: str):
        self.is_valid_name(project_name)
        if project_name in self.dir_tree:
            raise AttributeError(f"The given project name '{project_name}' already exists.")

        new_project_path = os.path.join(Global.custom_page_folder, project_name)
        os.mkdir(new_project_path)
        self.sync_with_folders()

    def get_poc_structure(self, project: str, poc: str) -> dict:
        return self.dir_tree[project][poc]

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

    def create_empty_poc(self, project: str, poc_name: str):
        self.is_valid_name(poc_name)
        poc_path = os.path.join(Global.custom_page_folder, project, poc_name)
        if os.path.exists(poc_path):
            raise AttributeError(f"The given PoC name '{poc_name}' already exists.")

        os.makedirs(poc_path)
        self.sync_with_folders()
        Clients.push_experiments_to_all()

    def add_page(self, project: str, poc: str, domain: str, path: str, file_type: str):
        domain_path = os.path.join(Global.custom_page_folder, project, poc, domain)
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)

        self.is_valid_name(path)
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

        self.sync_with_folders()
        # Notify clients of change (an experiment might now be runnable)
        Clients.push_experiments_to_all()

    def add_config(self, project: str, poc: str, type: str) -> bool:
        content = self.get_default_file_content(type)

        if content == '':
            return False

        file_path = os.path.join(Global.custom_page_folder, project, poc, type)
        with open(file_path, 'w') as file:
            file.write(content)

        self.sync_with_folders()
        # Notify clients of change (an experiment might now be runnable)
        Clients.push_experiments_to_all()

        return True

    @staticmethod
    def get_default_file_content(file_type: str) -> str:
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), f'default_files/{file_type}')

        if not os.path.exists(path):
            return ''

        with open(path, 'r') as file:
            return file.read()

    def sync_with_folders(self):
        self.dir_tree = self.initialize_dir_tree()
        self.tests_per_project = self.initialize_tests_and_interactions(self.dir_tree)
        logger.info('Framework is synced with folders')
