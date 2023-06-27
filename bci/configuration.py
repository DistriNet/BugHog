import logging
import logging.handlers
import os
import sys

import bci.database.mongo.container as container
from bci.evaluations.logic import DatabaseConnectionParameters

logger = logging.getLogger(__name__)


class Global:

    custom_page_folder = '/app/experiments/pages'
    custom_test_folder = '/app/experiments/url_queues'

    @staticmethod
    def get_extension_folder(browser: str) -> str:
        return Global.get_browser_config_class(browser).extension_folder

    @staticmethod
    def get_browser_config_class(browser: str):
        match browser:
            case 'chromium':
                return Chromium
            case 'firefox':
                return Firefox
            case _:
                raise ValueError(f'Invalid browser \'{browser}\'')

    @staticmethod
    def initialize_folders():
        for browser in ['chromium', 'firefox']:
            if not os.path.isfile(f'/app/browser/binaries/{browser}/artisanal/meta.json'):
                with open(f'/app/browser/binaries/{browser}/artisanal/meta.json', 'w') as file:
                    file.write('{}')

    @staticmethod
    def get_database_connection_params() -> DatabaseConnectionParameters:
        if 'BCI_MONGO_HOST' not in os.environ or \
                'BCI_MONGO_USERNAME' not in os.environ or \
                'BCI_MONGO_DATABASE' not in os.environ or \
                'BCI_MONGO_PASSWORD' not in os.environ:
            logger.info('Could not find database environment variables, using database container...')
            return container.run()
        else:
            logger.info(f'Found database environment variables for connection to \'{os.getenv("BCI_MONGO_HOST")}\'')
            return DatabaseConnectionParameters(
                os.getenv('BCI_MONGO_HOST'),
                os.getenv('BCI_MONGO_USERNAME'),
                os.getenv('BCI_MONGO_PASSWORD'),
                os.getenv('BCI_MONGO_DATABASE')
            )


class Chromium:

    extension_folder = '/app/browser/extensions/chromium'
    repo_to_use = 'online'


class Firefox:

    extension_folder = '/app/browser/extensions/firefox'
    repo_to_use = 'online'


class CustomHTTPHandler(logging.handlers.HTTPHandler):

    def __init__(self, host: str, url: str, method: str = 'GET', secure: bool = False, credentials=None, context=None) -> None:
        super().__init__(host, url, method=method, secure=secure, credentials=credentials, context=context)
        self.hostname = os.getenv('HOSTNAME')

    def mapLogRecord(self, record):
        record_dict = super().mapLogRecord(record)
        record_dict['hostname'] = self.hostname
        return record_dict


class Loggers:

    formatter = logging.Formatter(fmt='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
    memory_handler = logging.handlers.MemoryHandler(capacity=100, flushLevel=logging.ERROR)

    @staticmethod
    def configure_loggers():
        hostname = os.getenv('HOSTNAME')

        # Configure bci_logger
        bci_logger = logging.getLogger('bci')
        bci_logger.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        file_handler = logging.handlers.RotatingFileHandler(f'/app/logs/{hostname}.log', mode='a', backupCount=2)
        http_handler = CustomHTTPHandler('core:5000', '/api/log/', method='POST', secure=False)

        stream_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        http_handler.setLevel(logging.INFO)

        stream_handler.setFormatter(Loggers.formatter)
        file_handler.setFormatter(Loggers.formatter)
        http_handler.setFormatter(Loggers.formatter)

        # Configure web_logger
        web_logger = logging.getLogger('web_gui')
        web_logger.setLevel(logging.DEBUG)

        web_file_handler = logging.handlers.RotatingFileHandler('/app/logs/web_gui.log', mode='a', backupCount=2)
        web_http_handler = CustomHTTPHandler('host.docker.internal:5000', '/api/log/', method='POST', secure=False)

        web_file_handler.setLevel(logging.DEBUG)
        web_http_handler.setLevel(logging.INFO)

        web_file_handler.setFormatter(Loggers.formatter)
        web_http_handler.setFormatter(Loggers.formatter)

        web_logger.addHandler(web_file_handler)
        web_logger.addHandler(web_http_handler)

        # Configure memory handler
        Loggers.memory_handler.setLevel(logging.INFO)
        buffer_formatter = logging.handlers.BufferingHandler(Loggers.formatter)
        Loggers.memory_handler.setFormatter(buffer_formatter)

        bci_logger.addHandler(stream_handler)
        bci_logger.addHandler(file_handler)
        bci_logger.addHandler(http_handler)
        bci_logger.addHandler(Loggers.memory_handler)

        # Log uncaught exceptions
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            bci_logger.critical('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))

        sys.excepthook = handle_exception

        bci_logger.debug('Loggers initialized')

    @staticmethod
    def get_formatted_buffer_logs() -> list[str]:
        return [Loggers.formatter.format(record) for record in Loggers.memory_handler.buffer]
