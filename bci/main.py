import dataclasses
import logging
import os

import bci.browser.binary.factory as binary_factory
from bci.browser.configuration import chromium, firefox
from bci.configuration import Global, Loggers
from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import EvaluationParameters, PlotParameters
from bci.master import Master

logger = logging.getLogger(__name__)


class Main:

    loggers = None
    master = None

    @staticmethod
    def initialize():
        Main.loggers = Loggers()
        Main.loggers.configure_loggers()
        Main.master = Master()

    @staticmethod
    def is_ready() -> bool:
        return Main.master is not None

    @staticmethod
    def run(params: EvaluationParameters):
        Main.master.run(params)

    @staticmethod
    def stop_gracefully():
        Main.master.activate_stop_gracefully()

    @staticmethod
    def stop_forcefully():
        Main.master.activate_stop_forcefully()

    @staticmethod
    def is_running() -> bool:
        return Main.master.running

    @staticmethod
    def connect_to_database():
        return Main.master.connect_to_database()

    @staticmethod
    def get_logs() -> list[str]:
        return list(map(lambda x: Main.format_to_user_log(x.__dict__), Loggers.memory_handler.buffer))

    @staticmethod
    def format_to_user_log(log: dict) -> str:
        return f'[{log["asctime"]}] - [{log["levelname"]}] - [{log["hostname"]}] - {log["name"]}: {log["msg"]}'

    @staticmethod
    def get_database_info() -> dict:
        return MongoDB.get_info()

    @staticmethod
    def get_browsers() -> list[str]:
        return [
            'chromium',
            'firefox'
        ]

    @staticmethod
    def get_browser_options(browser_name: str) -> list[dict[str, str]]:
        match browser_name:
            case 'chromium':
                return [dataclasses.asdict(option) for option in chromium.SUPPORTED_OPTIONS]
            case 'firefox':
                return [dataclasses.asdict(option) for option in firefox.SUPPORTED_OPTIONS]
            case _:
                raise AttributeError(f'Browser \'{browser_name}\' is not supported')

    @staticmethod
    def get_available_extensions(browser: str) -> list[str]:
        extensions = []
        folder_path = Global.get_extension_folder(browser)
        for _, _, files in os.walk(folder_path):
            extensions.extend(files)
        return list(filter(lambda x: x != '.gitkeep', extensions))

    @staticmethod
    def list_downloaded_binaries(browser):
        return binary_factory.list_downloaded_binaries(browser)

    @staticmethod
    def list_artisanal_binaries(browser):
        return binary_factory.list_artisanal_binaries(browser)

    @staticmethod
    def update_artisanal_binaries(browser):
        return binary_factory.update_artisanal_binaries(browser)

    @staticmethod
    def download_online_binary(browser, rev_number):
        binary_factory.download_online_binary(browser, rev_number)

    @staticmethod
    def get_mech_groups_of_evaluation_framework(evaluation_name: str, project=None):
        return Main.master.get_specific_evaluation_framework(evaluation_name).get_mech_groups(project=project)

    @staticmethod
    def get_projects_of_custom_framework() -> list[str]:
        return Main.master.available_evaluation_frameworks["custom"].get_projects()

    @staticmethod
    def get_html_plot(data: dict) -> tuple[str, int]:
        if data.get('lower_version', None) and data.get('upper_version', None):
            major_version_range = (data['lower_version'], data['upper_version'])
        else:
            major_version_range = None
        if data.get('lower_revision_nb', None) and data.get('upper_revision_nb', None):
            revision_number_range = (data['lower_revision_nb'], data['upper_revision_nb'])
        else:
            revision_number_range = None

        params = PlotParameters(
            data.get('plot_mech_group'),
            data.get('target_mech_id'),
            data.get('browser_name'),
            data.get('db_collection'),
            major_version_range=major_version_range,
            revision_number_range=revision_number_range,
            browser_config=data.get('browser_setting', 'default'),
            extensions=data.get('extensions', []),
            cli_options=data.get('cli_options', []),
            dirty_allowed=data.get('dirty_allowed', True),
            target_cookie_name=None if data.get('check_for') == 'request' else data.get('target_cookie_name', 'generic')
        )
        return Main.master.get_html_plot(params)
