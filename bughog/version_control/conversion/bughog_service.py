from typing import Any
from functools import lru_cache
from os import getenv
import logging
from urllib.parse import urljoin

from bughog.util import ResourceNotFound, request_json

logger = logging.getLogger(__name__)
# TODO: include default value
# TODO: support HTTPS
SERVICE_API = getenv('BUGHOG_SERVICE_API')
BASE_URL = urljoin(f'http://{SERVICE_API}', '/v1/repos/')
LRU_CACHE_SIZE = 1024


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_commit_info(subject_name: str, commit_nb: str) -> dict[str, Any]:
    url = urljoin(BASE_URL, f'{subject_name}/commits/{commit_nb}')
    return __fetch_dict(url)


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_commit_nb(subject_name: str, commit_id: str) -> int:
    url = urljoin(BASE_URL, f'{subject_name}/commits/{commit_id}')
    commit_info = __fetch_dict(url)
    commit_nb = commit_info.get('nb')
    if commit_nb is None or not isinstance(commit_nb, int):
        raise Exception('BugHog service response did not include a valid commit number.')
    return commit_nb


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_commit_id(subject_name: str, commit_nb: int) -> str | None:
    commit_info = find_commit_info(subject_name, commit_nb)
    commit_id = commit_info.get('id')
    if commit_id is None:
        logger.warning(f'BugHog service could not return a valid commit id for {commit_nb} in {subject_name}.')
        return None
    if not isinstance(commit_id, str):
        logger.warning(f'BugHog service did not return a valid commit id for {commit_nb} in {subject_name}.')
        return None
    return commit_id


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_commit_executable_info(subject_name: str, commit_nb: int) -> dict | None:
    commit_info = find_commit_info(subject_name, commit_nb)
    return commit_info.get('executable_info')


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_nearest_commit_with_executable(
    subject_name: str, target_commit_nb: int, lower_bound: int, upper_bound: int
) -> dict | None:
    max_lower_offset = target_commit_nb - lower_bound
    max_upper_offset = upper_bound - target_commit_nb
    url = urljoin(
        BASE_URL,
        f'{subject_name}/commits/{target_commit_nb}/nearest_with_executable?max_lower_offset={max_lower_offset}&max_upper_offset={max_upper_offset}',
    )
    return __fetch_dict(url)


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_version_commit(subject_name: str, major_version: int, has_public_executable: bool | None = None) -> tuple[int, str]:
    """
    We return the earliest commit associated with the given major version.
    This way, the function will remain consistent as new commits associated with the same version are pushed.
    """
    url = urljoin(BASE_URL, f'{subject_name}/versions/{major_version}')
    if has_public_executable is not None:
        url += f'?has_executable={str(has_public_executable).lower()}'
    version_list = __fetch_list(url)
    if len(version_list) == 0:
        raise Exception('BugHog service responded with an empty list.')
    commit_info = version_list[0].get('commit_info', {})
    commit_nb, commit_id = commit_info.get('nb'), commit_info.get('id')
    if commit_nb is None or commit_id is None or not isinstance(commit_nb, int) or not isinstance(commit_id, str):
        raise Exception('BugHog service response did not include a valid commit number and/or id.')
    return commit_nb, commit_id


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_latest_major_version(subject_name: str) -> int:
    url = urljoin(BASE_URL, f'{subject_name}/versions/latest')
    version_info = __fetch_dict(url)
    major_version = version_info.get('major_version')
    if major_version is None or not isinstance(major_version, int):
        raise Exception('BugHog service response did not include a valid major version.')
    return major_version


def __fetch(url: str) -> dict | list | None:
    try:
        return request_json(url)
    except ResourceNotFound:
        logger.warning(f'Could not fetch {url}')
        return None


def __fetch_list(url: str) -> list:
    data = __fetch(url)
    return data if isinstance(data, list) else []


def __fetch_dict(url: str) -> dict:
    data = __fetch(url)
    return data if isinstance(data, dict) else {}
