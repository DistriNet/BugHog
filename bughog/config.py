import logging
import logging.handlers
import os
import sys
from functools import lru_cache

import docker
import docker.errors
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler

from bughog.database.mongo import container
from bughog.parameters import DatabaseParameters

logger = logging.getLogger(__name__)
custom_page_folder = '/app/experiments/pages'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='BUGHOG_')

    version: str | None = None
    github_token: str | None = None
    experiment_tries: int = Field(default=3, gt=0)
    executable_cache_limit: int = Field(default=0, ge=0)
    mongo_host: str | None = None
    mongo_username: str | None = None
    mongo_password: str | None = None
    mongo_database: str | None = None


settings = Settings()


def get_available_domains() -> list[str]:
    return [
        'a.test',
        'sub.a.test',
        'sub.sub.a.test',
        'b.test',
        'sub.b.test',
        'leak.test',
        'adition.com',
    ]


def check_required_env_parameters() -> bool:
    fatal = False
    # HOST_PWD
    if (host_pwd := os.getenv('HOST_PWD')) in ['', None]:
        logger.fatal(
            'The "HOST_PWD" variable is not set. If you\'re using sudo, you might have to pass it explicitly, for example "sudo HOST_PWD=$PWD docker compose up".'
        )
        fatal = True
    else:
        logger.debug(f'HOST_PWD={host_pwd}')

    # Version tag
    try:
        tag = get_tag()
        logger.info(f'Starting BugHog with tag "{tag}"')
    except ValueError as e:
        logger.fatal(str(e))
        fatal = True

    return not fatal


# Singleton pattern with caching
@lru_cache(maxsize=1)
def get_database_params() -> DatabaseParameters:
    host = settings.mongo_host
    username = settings.mongo_username
    password = settings.mongo_password
    database = settings.mongo_database

    if not (host and username and password and database):
        missing = [
            name
            for name, val in [
                ('BUGHOG_MONGO_HOST', host),
                ('BUGHOG_MONGO_USERNAME', username),
                ('BUGHOG_MONGO_PASSWORD', password),
                ('BUGHOG_MONGO_DATABASE', database),
            ]
            if not val
        ]
        logger.info(f'Could not find database parameters {missing}. Using database container...')
        return container.run(settings.executable_cache_limit)

    logger.info(f"Found database environment variables '{username}@{host}/{database}'.")
    return DatabaseParameters(host, username, password, database, settings.executable_cache_limit)


def _read_container_id() -> str | None:
    """Reads the current Docker container ID from /proc/self/cgroup."""
    try:
        with open('/proc/self/cgroup') as f:
            for line in f:
                if '/docker/' in line:
                    return line.strip().split('/docker/')[-1]
    except Exception:
        pass
    return None


def _detect_tag_from_docker() -> str | None:
    """
    Detects the BugHog image tag by inspecting the running container's image via the Docker API.
    Looks for a tag of the form 'bughog/core:<tag>'.
    """
    container_id = _read_container_id()
    if not container_id:
        return None
    try:
        client = docker.from_env()
        running_container = client.containers.get(container_id)
        for tag in running_container.image.tags:
            if tag.startswith('bughog/core:'):
                return tag.split(':', 1)[1]
    except Exception:
        pass
    return None


@lru_cache(maxsize=1)
def get_tag() -> str:
    """
    Returns the Docker image tag of the running BugHog core container.

    Detection order:
    1. 'dev' — if DEVELOPMENT=1 (devcontainer / local dev workflow)
    2. Docker API — tag of the running container's image (e.g. 'bughog/core:1.2.3')
    3. BUGHOG_VERSION environment variable — manual override or fallback
    """
    if os.getenv('DEVELOPMENT') == '1':
        return 'dev'
    tag = _detect_tag_from_docker()
    if tag:
        return tag
    if settings.version:
        logger.debug(f'Docker tag detection failed; using BUGHOG_VERSION override: {settings.version}')
        return settings.version
    raise ValueError(
        'Could not determine the BugHog version tag. '
        'Ensure the core container image is tagged as "bughog/core:<version>", '
        'or set the BUGHOG_VERSION environment variable.'
    )


class CustomHTTPHandler(logging.handlers.HTTPHandler):
    def __init__(
        self, host: str, url: str, method: str = 'GET', secure: bool = False, credentials=None, context=None
    ) -> None:
        super().__init__(host, url, method=method, secure=secure, credentials=credentials, context=context)
        self.hostname = os.getenv('HOSTNAME')

    def mapLogRecord(self, record):
        record_dict = super().mapLogRecord(record)
        record_dict['hostname'] = self.hostname
        return record_dict


class Loggers:
    file_formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S'
    )
    console_fmt = '%(message)s'
    memory_handler = logging.handlers.MemoryHandler(capacity=100, flushLevel=logging.ERROR)

    @staticmethod
    def configure_loggers():
        hostname = os.getenv('HOSTNAME')

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        if root_logger.handlers:
            root_logger.handlers.clear()

        rich_handler = RichHandler(
            rich_tracebacks=True, markup=True, show_path=False, show_time=True, show_level=True, enable_link_path=False
        )

        rich_handler.setLevel(logging.DEBUG)
        rich_handler.setFormatter(logging.Formatter(Loggers.console_fmt))
        root_logger.addHandler(rich_handler)

        # Configure stream handler
        # stream_handler = logging.StreamHandler()
        # stream_handler.setLevel(logging.DEBUG)
        # stream_handler.setFormatter(Loggers.file_formatter)
        # root_logger.addHandler(stream_handler)

        # Configure file handler
        os.makedirs('/app/logs', exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            f'/app/logs/{hostname}.log', mode='a', backupCount=3, maxBytes=8 * 1024 * 1024
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(Loggers.file_formatter)
        root_logger.addHandler(file_handler)

        # Configure http handler for workers
        if hostname != 'bh_core':
            try:
                # Ensure CustomHTTPHandler is defined
                http_handler = CustomHTTPHandler('core:5000', '/api/log/', method='POST', secure=False)
                http_handler.setLevel(logging.INFO)
                http_handler.setFormatter(Loggers.file_formatter)
                root_logger.addHandler(http_handler)
            except NameError:
                pass

        # Configure memory handler
        Loggers.memory_handler.setLevel(logging.INFO)
        Loggers.memory_handler.setFormatter(Loggers.file_formatter)
        root_logger.addHandler(Loggers.memory_handler)

        # Silence noisy libraries
        logging.getLogger('docker').setLevel(logging.WARNING)
        logging.getLogger('pymongo').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').disabled = True

        # Log uncaught exceptions
        sys.excepthook = lambda t, v, tb: root_logger.critical('Uncaught', exc_info=(t, v, tb))

        root_logger.info('Loggers initialized')

    @staticmethod
    def get_logs() -> list[str]:
        logs = []
        for record in Loggers.memory_handler.buffer:
            formatted_msg = Loggers.file_formatter.format(record)
            logs.append(formatted_msg)
        return logs

    @staticmethod
    def format_to_user_log(log: dict) -> str:
        return f'[{log.get("asctime", "?")}] [{log.get("levelname", "?")}] {log.get("name", "?")}: {log.get("msg", "")}'
