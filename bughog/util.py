"""
Functions from the os and shutil libraries show erroneous behavior when attempting to move a file from one file system
to another. These methods should be safe.
"""

import functools
import json
import logging
import os
import shutil
import tarfile
import time
import zipfile
from typing import Optional
from urllib.parse import urlparse

from requests import RequestException, Session
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__name__)


def safe_move_file(src_path, dst_path):
    if not os.path.isfile(src_path):
        raise AttributeError("src path is not a file: '%s'" % src_path)
    if not os.path.exists(os.path.dirname(dst_path)):
        os.makedirs(dst_path)
    shutil.copyfile(src_path, dst_path)
    os.remove(src_path)


def safe_move_dir(src_path, dst_path):
    if not os.path.isdir(src_path):
        raise AttributeError("src path is not a directory: '%s'" % src_path)
    if not os.path.exists(dst_path):
        os.makedirs(dst_path)
    for file_or_dir in os.listdir(src_path):
        new_src_path = os.path.join(src_path, file_or_dir)
        new_dst_path = os.path.join(dst_path, file_or_dir)
        if os.path.isfile(new_src_path):
            safe_move_file(new_src_path, new_dst_path)
        elif os.path.isdir(new_src_path):
            safe_move_dir(new_src_path, new_dst_path)
        else:
            raise AttributeError('Something went wrong')
    shutil.rmtree(src_path)


def copy_folder(src_path, dst_path):
    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)


def remove_all_in_folder(folder_path: str, except_files: Optional[list[str]] = None) -> None:
    except_files = [] if except_files is None else except_files
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name not in except_files:
                os.remove(file_path)
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            shutil.rmtree(dir_path)


def rmtree(src_path):
    """
    Removes folder at given src_path.

    :param src_path: path to the folder that is to be removed
    :return: True if the folder was successfully removed, otherwise False.
    """
    max_tries = 10
    for _ in range(0, max_tries):
        try:
            shutil.rmtree(src_path)
            return True
        except OSError:
            time.sleep(2)
            continue
    return False


def read_web_report(file_name):
    report_folder = "/reports"
    path = os.path.join(report_folder, file_name)
    if not os.path.isfile(path):
        raise ResourceNotFound(path)
    with open(path, 'r') as file:
        return json.load(file)


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


@functools.lru_cache(maxsize=128)
def request_json(url: str, token: Optional[str] = None) -> list | dict:
    session = __get_session(token=token)
    logger.debug(f'Requesting {url}')
    try:
        with session.get(url, timeout=60, stream=True) as resp:
            if resp.status_code >= 400:
                raise ResourceNotFound(url)
            return resp.json()
    except RequestException as e:
        raise ResourceNotFound from e


def request_final_url(url: str) -> str:
    session = __get_session()
    logger.debug(f'Requesting {url}')
    try:
        resp = session.get(url, timeout=60, stream=True)
        if resp.status_code >= 400:
            raise ResourceNotFound(url)
        return resp.url
    except RequestException as e:
        raise ResourceNotFound from e


def __get_session(token: Optional[str] = None, max_retries: int = 3, backoff_factor: float = 2.0) -> Session:
    session = Session()
    if token:
        session.headers.update({
            'Authorization': f'Bearer {token}'
        })

    retries = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=tuple(range(500,600)),
        allowed_methods={'GET'},
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def download_and_extract(urls: list[str], dst_folder_path: str) -> bool:
    """
    Downloads the archive residing at the given URL and extracts it to the given dest_path.
    This method currently supports zip, tar.bz2 and tar.xz archives.

    :return bool: Returns True if the archive was successfully downloaded and extracted, otherwise False.
    """
    for url in urls:
        logger.debug(f"Attempting to download archive from '{url}'.")
        tmp_file_name = urlparse(url).path.split('/')[-1]
        tmp_file_path = os.path.join('/tmp', tmp_file_name)
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
            logger.debug("Download failed.")
            continue

        logger.debug(f"Extracting downloaded archive '{tmp_file_path}'.")
        _, file_extension = os.path.splitext(tmp_file_path)
        match file_extension:
            case '.zip':
                unzip(tmp_file_path, dst_folder_path)
            case '.bz2':
                untar(tmp_file_path, dst_folder_path)
            case '.xz':
                untar(tmp_file_path, dst_folder_path)
            case _:
                AttributeError(f'File extension {file_extension} is not supported.')
        os.remove(tmp_file_path)
        return True
    return False


def unzip(src_archive_path: str, dst_folder_path: str) -> None:
    with zipfile.ZipFile(src_archive_path, 'r') as zip:
        members = zip.namelist()
        top_dirs_and_files = {name.split('/')[0] for name in members}
        # If there is a single top-level directory, we move all contents up.
        if len(top_dirs_and_files) == 1:
            parent_folder_path = os.path.dirname(dst_folder_path)
            zip.extractall(parent_folder_path)
            safe_move_dir(os.path.join(parent_folder_path, top_dirs_and_files.pop()), dst_folder_path)
        else:
            os.makedirs(dst_folder_path, exist_ok=True)
            zip.extractall(dst_folder_path)


def untar(src_archive_path: str, dst_folder_path: str) -> None:
    os.makedirs(dst_folder_path, exist_ok=True)
    # We do not inspects contents first like in unzip, because this is a very costly operation for tar archives.
    with tarfile.open(src_archive_path, 'r:*') as tar:
        tar.extractall(dst_folder_path)
        members = os.listdir(dst_folder_path)
        top_dirs_and_files = {name.split('/')[0] for name in members}
        # If there is a single top-level directory, we move all contents up.
        if len(top_dirs_and_files) == 1:
            safe_move_dir(os.path.join(dst_folder_path, members.pop()), dst_folder_path + '_2')
            shutil.rmtree(dst_folder_path)
            safe_move_dir(os.path.join(dst_folder_path + '_2'), dst_folder_path)


def ensure_folder_exists(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        path = func(*args, **kwargs)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path
    return wrapper


class ResourceNotFound(Exception):
    pass
