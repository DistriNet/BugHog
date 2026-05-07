import json
import logging
import os
import shutil
from urllib.parse import urlparse

from requests import RequestException, Session
from requests.adapters import HTTPAdapter, Retry

from bughog.util import fs

logger = logging.getLogger(__name__)


class ResourceNotFound(Exception):
    pass


def read_web_report(file_name):
    report_folder = '/reports'
    path = os.path.join(report_folder, file_name)
    if not os.path.isfile(path):
        raise ResourceNotFound(path)
    with open(path, 'r') as file:
        return json.load(file)


def post_request(url: str, json: dict) -> None:
    session = __get_session()
    logger.debug(f'Sending POST to {url}.')
    try:
        session.post(url, json=json)
    except RequestException:
        logger.warning(f'Could not propagate request to collector at {url}.')


def __get_session(token: str | None = None, max_retries: int = 3, backoff_factor: int = 2) -> Session:
    session = Session()
    if token:
        session.headers.update({'Authorization': f'Bearer {token}'})

    retries = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=tuple(range(500, 600)),
        allowed_methods={'GET'},
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def request_html(url: str):
    session = __get_session()
    logger.debug(f'Requesting {url}')
    try:
        with session.get(url, timeout=60, stream=True) as resp:
            if resp.status_code >= 400:
                raise ResourceNotFound(url)
            return resp.content
    except RequestException as e:
        raise ResourceNotFound from e


def request_json(url: str, params: dict | None = None, token: str | None = None) -> list | dict:
    session = __get_session(token=token)
    logger.debug(f'Requesting {url}')
    try:
        with session.get(url, params=params, timeout=60, stream=True) as resp:
            if resp.status_code >= 400:
                raise ResourceNotFound(url)
            return resp.json()
    except Exception as e:
        raise ResourceNotFound from e


def request_final_url(url: str, params: dict | None = None) -> str:
    session = __get_session()
    logger.debug(f'Requesting {url}')
    try:
        resp = session.get(url, params=params, timeout=60, stream=True)
        if resp.status_code >= 400:
            raise ResourceNotFound(url)
        return resp.url
    except RequestException as e:
        raise ResourceNotFound from e


def __fetch(url: str) -> dict | list | None:
    try:
        return request_json(url)
    except ResourceNotFound:
        logger.warning(f'Could not fetch {url}')
        return None


def fetch_list(url: str) -> list:
    data = __fetch(url)
    if data is None:
        return []
    if not isinstance(data, list):
        logger.warning(f'Expected a list from {url} but got {type(data)}')
        return []
    return data


def fetch_dict(url: str) -> dict:
    data = __fetch(url)
    if data is None:
        return {}
    if not isinstance(data, dict):
        logger.warning(f'Expected a dict from {url} but got {type(data)}')
        return {}
    return data


def download_and_extract(urls: list[str], dst_folder_path: str) -> bool:
    """
    Downloads the archive residing at the given URL and extracts it to the given dest_path.
    This method currently supports zip, tar.gz, tar.bz2 and tar.xz archives.

    :return bool: Returns True if the archive was successfully downloaded and extracted, otherwise False.
    """
    for url in urls:
        logger.debug(f"Attempting to download archive from '{url}'.")
        tmp_file_name = urlparse(url).path.split('/')[-1]
        tmp_file_path = os.path.join('/memory', tmp_file_name)
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
        session = __get_session()
        try:
            with session.get(url, stream=True) as resp:
                if resp.status_code >= 400:
                    continue
                with open(tmp_file_path, 'wb') as file:
                    shutil.copyfileobj(resp.raw, file)
        except RequestException:
            logger.debug('Download failed.')
            continue

        logger.debug(f"Extracting downloaded archive '{tmp_file_path}'.")
        _, file_extension = os.path.splitext(tmp_file_path)
        match file_extension:
            case '.zip':
                fs.unzip(tmp_file_path, dst_folder_path)
            case '.gz' | '.bz2' | '.xz':
                fs.untar(tmp_file_path, dst_folder_path)
            case _:
                raise AttributeError(f'File extension {file_extension} is not supported.')
        os.remove(tmp_file_path)
        return True
    return False
