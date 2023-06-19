import time

from bci.evaluations.evaluation_framework import EvaluationFramework
from bci.evaluations.xsleaks.mongodb import XSLeaksMonogDB
from bci.evaluations.xsleaks.testcase.first import First, TestCase
from bci.evaluations.xsleaks.testcase import cases
from bci.version_control.states.state import State


all_mech_groups = [cls.__name__ for cls in TestCase.__subclasses__()]


class XSLeaksEvaluation(EvaluationFramework):

    db_class = XSLeaksMonogDB

    @staticmethod
    def get_case_object(browser: str, browser_version: str, mech_id: str, mech_group: str,
                        browser_binary: str, state: State) -> TestCase:
        case_class = getattr(cases, mech_group)
        return case_class(browser, browser_version, mech_id, mech_group, browser_binary, state)

    def perform_specific_evaluation(self, automation: str, browser: str, browser_version: str, driver_version: str,
                                    browser_config: str, extension_file: str, additional_cli_options: list,
                                    mech_id: str, mech_group: str, browser_binary: str, driver_exec: str,
                                    state: State, cookie_name: str):
        if mech_group == "first":
            test = First(browser, browser_version, mech_id, browser_binary, state)
        else:
            test = self.get_case_object(browser, browser_version, mech_id, mech_group, browser_binary, state)
        if test is None:
            raise AttributeError("Unknown test '%s'" % mech_group)

        report = test.run()
        time.sleep(5)
        mongodb = XSLeaksMonogDB.get_instance()

        is_dirty = self.is_dirty_evaluation(report)
        mongodb.store_data(automation, browser, browser_version, driver_version, browser_config,
                           None, additional_cli_options, state, mech_group, report, is_dirty)

    def get_data_in_json(self, data_path, mech_group):
        pass

    @staticmethod
    def is_dirty_evaluation(report):
        return report is None

    def get_mech_groups(self):
        return all_mech_groups
