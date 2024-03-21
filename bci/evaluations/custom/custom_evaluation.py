import logging
import os
from unittest import TestResult

from bci.browser.configuration.browser import Browser
from bci.configuration import Global
from bci.evaluations.collector import Collector
from bci.evaluations.collector import Type
from bci.evaluations.custom.custom_mongodb import CustomMongoDB
from bci.evaluations.evaluation_framework import EvaluationFramework
from bci.evaluations.logic import TestParameters

logger = logging.getLogger(__name__)


class CustomEvaluationFramework(EvaluationFramework):

    db_class = CustomMongoDB

    def __init__(self):
        super().__init__()
        self.tests_per_project = {}
        self.tests = {}
        self.initialize_tests_and_url_queues()

    def initialize_tests_and_url_queues(self):
        page_folder_path = Global.custom_page_folder
        project_names = [name for name in os.listdir(page_folder_path) if os.path.isdir(os.path.join(page_folder_path, name))]
        for project_name in project_names:
            # Find tests in folder
            project_path = os.path.join(page_folder_path, project_name)
            self.tests_per_project[project_name] = {}
            for test_name in os.listdir(project_path):
                url_queue_file_path = os.path.join(project_path, test_name, 'url_queue.txt')
                if os.path.isfile(url_queue_file_path):
                    # If an URL queue is specified, it is parsed and used
                    with open(url_queue_file_path) as file:
                        self.tests_per_project[project_name][test_name] = file.readlines()
                        self.tests[test_name] = self.tests_per_project[project_name][test_name]
                else:
                    # Otherwise, a default URL queue is used, based on the domain that hosts the main page
                    test_folder_path = os.path.join(project_path, test_name)
                    for domain in os.listdir(test_folder_path):
                        main_folder_path = os.path.join(test_folder_path, domain, 'main')
                        if os.path.exists(main_folder_path):
                            self.tests_per_project[project_name][test_name] = [
                                f'https://{domain}/{project_name}/{test_name}/main',
                                'https://a.test/report/?bughog_sanity_check=OK'
                            ]
                            self.tests[test_name] = self.tests_per_project[project_name][test_name]

    def perform_specific_evaluation(self, browser: Browser, params: TestParameters) -> TestResult:
        logger.info(f'Starting test for {params}')
        browser_version = browser.version
        binary_origin = browser.get_binary_origin()

        collector = Collector([Type.REQUESTS, Type.LOGS])
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

    def get_mech_groups(self, project=None):
        if project:
            return sorted(self.tests_per_project[project].keys())
        return sorted(self.tests_per_project.keys())

    def get_projects(self) -> list[str]:
        return sorted(list(self.tests_per_project.keys()))
