import os
import shutil
from bci.evaluations.evaluation_framework import EvaluationFramework
from bci.evaluations.samesite.samesite_mongodb import SamesiteMongoDB
from bci.version_control.states.state import State

all_mech_groups = [
    "appcache",
    "header-csp",
    "header-link",
    "pdf",
    "redirect",
    "script",
    "static",
    "sw",
]


class SameSiteEvaluationFramework(EvaluationFramework):

    db_class = SamesiteMongoDB

    def perform_specific_evaluation(
            self,
            automation: str,
            browser: str,
            browser_version: str,
            driver_version: str,
            browser_config: str,
            extension_name: str,
            additional_cli_options: list,
            mech_id: str,
            mech_group: str,
            browser_binary: str,
            driver_exec: str,
            state: State,
            cookie_name: str):
        if not self.has_result(automation, browser, browser_config, extension_name, additional_cli_options, mech_group, state):
            data_folder = self.get_data_path(browser, state, browser_config)
            extension_path = self.get_extension_path(browser, extension_name) if extension_name else None

            self.logger.info(f"Starting browser evaluation for {browser} v{browser_version} with driver {driver_exec}")
            Jar.do_automation(automation, browser, browser_version, browser_config, extension_path,
                              browser_binary, additional_cli_options, driver_exec, data_folder, mech_group)

            json_data = self.get_data_in_json(data_folder, mech_group)
            is_dirty = self.is_dirty_evaluation(data_folder, mech_group)
            self.db_class.get_instance().store_data(automation, browser, browser_version, driver_version, browser_config,
                                                    extension_name, additional_cli_options, state, mech_group,
                                                    json_data, is_dirty)

            # Remove csv files
            try:
                shutil.rmtree(os.path.dirname(data_folder))
            except OSError:
                self.logger.error("Could not remove temporary data folder", exc_info=True)

        return self.get_result(automation, browser, browser_config, extension_name,
                             additional_cli_options, mech_group, mech_id, state, cookie_name)

    def get_data_in_json(self, data_path, mech_group) -> dict:
        data_file_path = os.path.join(data_path, "%s.csv" % mech_group)
        return self.read_csv_file(data_file_path)

    @staticmethod
    def is_dirty_evaluation(data_path, mech_group):
        """
        Returns True if an exception was thrown during the evaluation, otherwise returns False.
        """
        data_exception_file_path = os.path.join(data_path, "%s_EXCEPTION.csv" % mech_group)
        return os.path.isfile(data_exception_file_path)

    def get_mech_groups(self):
        return all_mech_groups
