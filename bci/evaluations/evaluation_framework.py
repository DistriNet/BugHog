import logging
import os
import re
import traceback
from abc import ABC, abstractmethod

from bci.browser.configuration.browser import Browser
from bci.configuration import Global
from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import TestParameters, TestResult, WorkerParameters
from bci.version_control.states.state import StateCondition

logger = logging.getLogger(__name__)


class EvaluationFramework(ABC):
    def __init__(self):
        self.should_stop = False

    def evaluate(self, worker_params: WorkerParameters):
        test_params = worker_params.create_test_params()

        if MongoDB().has_result(test_params):
            logger.warning(
                f"Experiment '{test_params.mech_group}' for '{test_params.state}' was already performed, skipping."
            )
            return

        browser_config = worker_params.browser_configuration
        eval_config = worker_params.evaluation_configuration
        state = worker_params.state
        browser = Browser.get_browser(browser_config, eval_config, state)
        browser.pre_evaluation_setup()

        if self.should_stop:
            self.should_stop = False
            return
        try:
            browser.pre_test_setup()
            result = self.perform_specific_evaluation(browser, test_params)
            MongoDB().store_result(result)
            logger.info(f'Test finalized: {test_params}')
        except Exception as e:
            state.condition = StateCondition.FAILED
            logger.error('An error occurred during evaluation', exc_info=True)
            traceback.print_exc()
        finally:
            browser.post_test_cleanup()

        browser.post_evaluation_cleanup()
        logger.debug('Evaluation finished')

    @abstractmethod
    def perform_specific_evaluation(self, browser: Browser, params: TestParameters) -> TestResult:
        pass

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
    def get_mech_groups(self, project: str) -> list[tuple[str, bool]]:
        """
        Returns the available mechanism groups for this evaluation framework.
        """
        pass

    @staticmethod
    def is_valid_name(name: str) -> None:
        """
        Checks whether the given string is a valid experiment, page or project name, and raises an exception if not.
        This is to prevent issues with URL encoding and decoding.

        :param name: Name to be checked on validity.
        """
        if name is None or name == '':
            raise AttributeError("The given name cannot be empty.")
        if re.match(r'^[A-Za-z0-9_\-.]+$', name) is None:
            raise AttributeError(
                f"The given name '{name}' is invalid. Only letters, numbers, "
                "'.', '-' and '_' can be used, and the name should not be empty."
            )

