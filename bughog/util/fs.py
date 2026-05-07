"""
Functions from the os and shutil libraries show erroneous behavior when attempting to move a file from one file system
to another. These methods should be safe.
"""

import functools
import logging
import os
import shutil
import tarfile
import time
import zipfile
from typing import Optional

from bughog.exceptions import OutOfMemoryError

logger = logging.getLogger(__name__)


def safe_move_file(src_path, dst_path):
    if not os.path.isfile(src_path):
        raise AttributeError(f'src path is not a file: {src_path}')

    dst_dir = os.path.dirname(dst_path)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    try:
        os.replace(src_path, dst_path)
    except OSError as e:
        if e.errno == 28 or 'No space left' in str(e):
            logger.error(f'Out of resources while moving file from {src_path} to {dst_path}.')
            raise OutOfMemoryError('No space left on device. Restarting BugHog might help.') from e
        raise e


def safe_move_dir(src_path, dst_path):
    if not os.path.isdir(src_path):
        raise AttributeError(f'src path is not a directory: {src_path}')
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
    try:
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
    except Exception as e:
        if 'No space left on device' in str(e):
            logger.error(f'Out of memory while copying folder from {src_path} to {dst_path}.')
            raise OutOfMemoryError('No space left on device. Restarting BugHog might help.') from e
        raise e


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
