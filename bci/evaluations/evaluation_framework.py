import logging
import os
import traceback
from abc import ABC, abstractmethod

from bci.browser.configuration.browser import Browser
from bci.configuration import Global
from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import TestParameters, TestResult, WorkerParameters

logger = logging.getLogger('bci')


class EvaluationFramework(ABC):

    def __init__(self):
        self.should_stop = False

    def evaluate(self, worker_params: WorkerParameters):
        test_params_list = worker_params.create_all_test_params()
        test_params_list_to_evaluate: list[TestParameters] = list(filter(
            lambda x: not self.has_result(x),
            test_params_list
        ))
        logger.info(f'Pending tests for state {worker_params}: {len(test_params_list_to_evaluate)}/{len(test_params_list)}')
        if len(test_params_list_to_evaluate) == 0:
            return

        browser_config = worker_params.browser_configuration
        eval_config = worker_params.evaluation_configuration
        state = worker_params.state
        browser = Browser.get_browser(browser_config, eval_config, state)
        browser.pre_evaluation_setup()

        for test_params in test_params_list_to_evaluate:
            if self.should_stop:
                self.should_stop = False
                return
            try:
                browser.pre_test_setup()
                result = self.perform_specific_evaluation(browser, test_params)

                state.set_evaluation_outcome(result)
                self.db_class.get_instance().store_result(result)
                logger.info(f'Test finalized: {test_params}')
            except Exception as e:
                state.set_evaluation_error(str(e))
                logger.error("An error occurred during evaluation", exc_info=True)
                traceback.print_exc()
            finally:
                browser.post_test_cleanup()

        browser.post_evaluation_cleanup()
        logger.debug('Evaluation finished')

    @abstractmethod
    def perform_specific_evaluation(self, browser: Browser, params: TestParameters) -> TestResult:
        pass

    @property
    @classmethod
    @abstractmethod
    def db_class(cls) -> MongoDB:
        pass

    @classmethod
    def has_result(cls: MongoDB, test_params: TestParameters) -> bool:
        return cls.db_class.get_instance().has_result(test_params)

    @classmethod
    def get_result(cls: MongoDB, test_params: TestParameters) -> TestResult:
        return cls.db_class.get_instance().get_result(test_params)

    @classmethod
    def has_all_results(cls: MongoDB, worker_params: WorkerParameters) -> bool:
        return cls.db_class.get_instance().has_all_results(worker_params)

    @staticmethod
    def get_extension_path(browser: str, extension_file: str):
        folder_path = Global.get_extension_folder(browser)
        path = os.path.join(folder_path, extension_file)
        if not os.path.isfile(path):
            raise AttributeError("Could not find file '%s'" % path)
        return path

    def stop_gracefully(self):
        self.should_stop = True

    @abstractmethod
    def get_mech_groups(self, project=None):
        """
        Returns the available mechanism groups for this evaluation framework.
        """
        pass
