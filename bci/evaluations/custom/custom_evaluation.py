import logging
import os
from unittest import TestResult

from bci.browser.configuration.browser import Browser
from bci.configuration import Global
from bci.evaluations.collector import Collector, Type
from bci.evaluations.custom.custom_mongodb import CustomMongoDB
from bci.evaluations.evaluation_framework import EvaluationFramework
from bci.evaluations.logic import TestParameters
from bci.web.clients import Clients

logger = logging.getLogger(__name__)


class CustomEvaluationFramework(EvaluationFramework):

    db_class = CustomMongoDB

    def __init__(self):
        super().__init__()
        self.dir_tree = self.initialize_dir_tree()
        self.tests_per_project = self.initialize_tests_and_url_queues(self.dir_tree)

    @staticmethod
    def initialize_dir_tree() -> dict:
        path = Global.custom_page_folder

        def path_to_dict(path):
            if os.path.isdir(path):
                return {
                    sub_folder: path_to_dict(os.path.join(path, sub_folder))
                    for sub_folder in os.listdir(path) if sub_folder != 'url_queue.txt'
                }
            else:
                return os.path.basename(path)

        return path_to_dict(path)

    @staticmethod
    def initialize_tests_and_url_queues(dir_tree: dict) -> dict:
        experiments_per_project = {}
        page_folder_path = Global.custom_page_folder
        for project, experiments in dir_tree.items():
            # Find tests in folder
            project_path = os.path.join(page_folder_path, project)
            experiments_per_project[project] = {}
            for experiment in experiments:
                url_queue_file_path = os.path.join(project_path, experiment, 'url_queue.txt')
                if os.path.isfile(url_queue_file_path):
                    # If an URL queue is specified, it is parsed and used
                    with open(url_queue_file_path) as file:
                        url_queue = file.readlines()
                else:
                    # Otherwise, a default URL queue is used, based on the domain that hosts the main page
                    experiment_path = os.path.join(project_path, experiment)
                    for domain in os.listdir(experiment_path):
                        main_folder_path = os.path.join(experiment_path, domain, 'main')
                        if os.path.exists(main_folder_path):
                            url_queue = [
                                f'https://{domain}/{project}/{experiment}/main',
                                'https://a.test/report/?bughog_sanity_check=OK'
                            ]
                experiments_per_project[project][experiment] = {
                    'url_queue': url_queue,
                    'runnable': CustomEvaluationFramework.is_runnable_experiment(project, experiment, dir_tree)
                }
        return experiments_per_project

    @staticmethod
    def is_runnable_experiment(project: str, poc: str, dir_tree: dict) -> bool:
        domains = dir_tree[project][poc]
        if not (poc_main_path := [paths for domain, paths in domains.items() if 'main' in paths]):
            return False
        if 'index.html' not in poc_main_path[0]['main'].keys():
            return False
        return True

    def perform_specific_evaluation(self, browser: Browser, params: TestParameters) -> TestResult:
        logger.info(f'Starting test for {params}')
        browser_version = browser.version
        binary_origin = browser.get_binary_origin()

        collector = Collector([Type.REQUESTS, Type.LOGS])
        collector.start()

        is_dirty = False
        try:
            url_queue = self.tests_per_project[params.evaluation_configuration.project][params.mech_group]['url_queue']
            for url in url_queue:
                tries = 0
                while tries < 3:
                    tries += 1
                    browser.visit(url)
        except Exception as e:
            logger.error(f'Error during test: {e}', exc_info=True)
            is_dirty = True
        finally:
            collector.stop()
            data = collector.collect_results()
            if not is_dirty:
                # New way to perform sanity check
                if [var_entry for var_entry in data['req_vars'] if var_entry['var'] == 'sanity_check' and var_entry['val'] == 'OK']:
                    pass
                # Old way for backwards compatibility
                elif [request for request in data['requests'] if 'report/?leak=baseline' in request['url']]:
                    pass
                else:
                    is_dirty = True
        return params.create_test_result_with(browser_version, binary_origin, data, is_dirty)

    def get_mech_groups(self, project: str) -> list[tuple[str, bool]]:
        if project not in self.tests_per_project:
            return []
        pocs = [(poc_name, poc_data['runnable']) for poc_name, poc_data in self.tests_per_project[project].items()]
        return sorted(pocs, key=lambda x: x[0])

    def get_projects(self) -> list[str]:
        return sorted(list(self.tests_per_project.keys()))

    def get_poc_structure(self, project: str, poc: str) -> dict:
        return self.dir_tree[project][poc]

    def get_poc_file(self, project: str, poc: str, domain: str, path: str, file: str) -> str:
        file_path = os.path.join(Global.custom_page_folder, project, poc, domain, path, file)
        if os.path.isfile(file_path):
            with open(file_path) as file:
                return file.read()

    def update_poc_file(self, project: str, poc: str, domain: str, path: str, file: str, content: str) -> bool:
        file_path = os.path.join(Global.custom_page_folder, project, poc, domain, path, file)
        if os.path.isfile(file_path):
            with open(file_path, 'w') as file:
                file.write(content)
            return True
        return False

    def create_empty_poc(self, project: str, poc_name: str) -> bool:
        poc_path = os.path.join(Global.custom_page_folder, project, poc_name)
        if not os.path.exists(poc_path):
            os.makedirs(poc_path)
            self.sync_with_folders()
            Clients.push_experiments_to_all()
            return True
        return False

    def add_page(self, project: str, poc: str, domain: str, path: str, file_type: str) -> bool:
        domain_path = os.path.join(Global.custom_page_folder, project, poc, domain)
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)
        page_path = os.path.join(domain_path, path)
        if not os.path.exists(page_path):
            os.makedirs(page_path)
        new_file_name = f'index.{file_type}'
        file_path = os.path.join(page_path, new_file_name)
        if os.path.exists(file_path):
            return False
        with open(file_path, 'w') as file:
            file.write('')
        headers_file_path = os.path.join(page_path, 'headers.json')
        if not os.path.exists(headers_file_path):
            with open(headers_file_path, 'w') as file:
                file.write('[{"key": "Header-Name", "value": "Header-Value"}]')
        self.sync_with_folders()
        # Notify clients of change (an experiment might now be runnable)
        Clients.push_experiments_to_all()
        return True

    def sync_with_folders(self):
        self.dir_tree = self.initialize_dir_tree()
        self.tests_per_project = self.initialize_tests_and_url_queues(self.dir_tree)
        logger.info('Framework is synced with folders')
