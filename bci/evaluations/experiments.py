import json
import logging
import os

logger = logging.getLogger(__name__)

SUPPORTED_FILE_TYPES = [
    'css',
    'html',
    'js',
    'py',
    'xml',
]
SUPPORTED_DOMAINS = [
    'leak.test',
    'a.test',
    'sub.a.test',
    'sub.sub.a.test',
    'b.test',
    'sub.b.test',
    'adition.com',
]
EXPERIMENT_FOLDER_PATH = '/app/experiments/pages'


def verify() -> None:
    """
    Verifies the experiment pages, logger warnings for unsupported configurations.
    """
    for project in os.listdir(EXPERIMENT_FOLDER_PATH):
        project_path = os.path.join(EXPERIMENT_FOLDER_PATH, project)
        if not os.path.isdir(project_path):
            logger.warning(f"Unexpected file in '{__user_path(project_path)}' will be ignored.")
            continue
        for experiment in os.listdir(project_path):
            __verify_experiment(project, experiment)


def __verify_experiment(project: str, experiment: str) -> None:
    experiment_path = os.path.join(EXPERIMENT_FOLDER_PATH, project, experiment)
    if not os.path.isdir(experiment_path):
        logger.warning(f"Unexpected file at '{__user_path(experiment_path)}' will be ignored.")
        return
    for domain in os.listdir(experiment_path):
        if domain in ['script.cmd', 'url_queue.txt']:
            continue
        domain_path = os.path.join(experiment_path, domain)
        if not os.path.isdir(domain_path):
            logger.warning(f"Unexpected file '{__user_path(domain_path)}' will be ignored.")
            continue
        if domain not in SUPPORTED_DOMAINS:
            logger.warning(f"Unsupported domain '{domain}' in '{__user_path(experiment_path)}' will be ignored.")
        for page in os.listdir(domain_path):
            __verify_page(project, experiment, domain, page)


def __verify_page(project: str, experiment: str, domain: str, page: str) -> None:
    page_path = os.path.join(EXPERIMENT_FOLDER_PATH, project, experiment, domain, page)
    if page.endswith('.py'):
        return
    if not os.path.isdir(page_path):
        logger.warning(f"Unexpected file at '{__user_path(page_path)}' will be ignored.")
        return
    for file_name in os.listdir(page_path):
        file_path = os.path.join(page_path, file_name)
        if not os.path.isfile(file_path):
            logger.warning(f"Unexpected folder at '{__user_path(page_path)}' will be ignored.")
            continue
        if file_name == 'headers.json':
            __verify_headers(file_path)
            continue
        file_name_split = file_name.split('.')
        if len(file_name_split) < 2:
            logger.warning(f"Could not deduce file extension at '{__user_path(file_path)}'.")
        if file_name_split[-1] not in SUPPORTED_FILE_TYPES:
            logger.warning(f"File type of '{__user_path(file_path)}' is not supported.")


def __verify_headers(path: str) -> None:
    """
    Verifies whether the headers file at the given path is valid.
    """
    with open(path, 'r', encoding='utf-8') as file:
        try:
            json_content = json.load(file)
        except json.decoder.JSONDecodeError:
            logger.warning(f"Could not parse '{__user_path(path)}'")
            return
        if not isinstance(json_content, list):
            raise AttributeError(f"Not a list: '{__user_path(path)}'")
        for item in json_content:
            if 'key' and 'value' not in item:
                logger.warning(f"Not all dictionary entries contain a key-value combination in '{__user_path(path)}'.")


def __user_path(path: str) -> str:
    """
    Translates the given path to the user readeable path outside container.
    """
    if path.startswith('/app/'):
        return path[5:]
    return path
