import logging
import os
from unittest import TestResult
from bci.browser.configuration.browser import Browser

from bci.configuration import Global
from bci.evaluations.custom.custom_mongodb import CustomMongoDB
from bci.evaluations.evaluation_framework import EvaluationFramework
from bci.evaluations.logic import TestParameters
from bci.http.collector import Collector


logger = logging.getLogger(__name__)


class CustomEvaluationFramework(EvaluationFramework):

    db_class = CustomMongoDB

    def __init__(self):
        super().__init__()
        self.tests_per_project = {}
        self.tests = {}
        self.initialize_tests_and_url_queues()

    def initialize_tests_and_url_queues(self):
        used_test_names = {}
        page_folder_path = Global.custom_page_folder
        test_folder_path = Global.custom_test_folder
        if not os.path.isdir(test_folder_path):
            return
        project_names = [name for name in os.listdir(test_folder_path) if os.path.isdir(os.path.join(test_folder_path, name))]
        for project_name in project_names:
            # Find tests in folder
            project_path = os.path.join(test_folder_path, project_name)
            self.tests_per_project[project_name] = {}
            for test_name in os.listdir(project_path):
                if test_name in used_test_names:
                    raise AttributeError(f'Test name \'{test_name}\' should be unique over all projects (found in {project_name} and {used_test_names[test_name]})')
                used_test_names[test_name] = project_name
                test_path = os.path.join(project_path, test_name)
                if os.path.isdir(test_path):
                    with open(os.path.join(test_path, 'url_queue.txt')) as file:
                        self.tests_per_project[project_name][test_name] = file.readlines()
                        self.tests[test_name] = self.tests_per_project[project_name][test_name]
            # Find remaining tests by checking the pages hosting tests
            project_path = os.path.join(page_folder_path, project_name)
            for test_name in os.listdir(project_path):
                test_path = os.path.join(project_path, test_name)
                for domain in os.listdir(test_path):
                    main_folder_path = os.path.join(project_path, test_path, domain, 'main')
                    if os.path.exists(main_folder_path) and test_name not in used_test_names:
                        used_test_names[test_name] = project_name
                        self.tests_per_project[project_name][test_name] = [
                            f'https://{domain}/{project_name}/{test_name}/main',
                            'https://a.test/report/?leak=baseline'
                        ]
                        self.tests[test_name] = self.tests_per_project[project_name][test_name]

    def perform_specific_evaluation(self, browser: Browser, params: TestParameters) -> TestResult:
        logger.info(f'Starting test for {params}')
        browser_version = browser.version
        binary_origin = browser.get_binary_origin()

        collector = Collector()
        collector.start()

        is_dirty = False
        try:
            url_queue = self.tests[params.mech_group]
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
            if not is_dirty:
                if len([request for request in collector.requests if 'report/?leak=baseline' in request['url']]) == 0:
                    is_dirty = True
            result = {
                'requests': collector.requests
            }
        return params.create_test_result_with(browser_version, binary_origin, result, is_dirty)

    def get_mech_groups(self, project=None):
        if project:
            return sorted(self.tests_per_project[project].keys())
        return sorted(self.tests_per_project.keys())

    def get_projects(self) -> list[str]:
        return sorted(list(self.tests_per_project.keys()))
