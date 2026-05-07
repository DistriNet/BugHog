import logging
from functools import lru_cache
from os import getenv
from typing import Any
from urllib.parse import urljoin, urlparse

from bughog.util.http import fetch_dict, fetch_list
from bughog.version_control.version import Version

logger = logging.getLogger(__name__)

SERVICE_API = getenv('BUGHOG_SERVICE_API', 'https://api.bughog.distrinet-research.be/')
if not urlparse(SERVICE_API).scheme:
    SERVICE_API = f'https://{SERVICE_API}'

BASE_URL = urljoin(SERVICE_API, '/v1/repos/')
LRU_CACHE_SIZE = 1024


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_commit_info(subject_name: str, commit_nb: str) -> dict[str, Any]:
    url = urljoin(BASE_URL, f'{subject_name}/commits/{commit_nb}')
    return fetch_dict(url)


def find_latest_commit_info(subject_name: str) -> dict[str, Any]:
    return find_commit_info(subject_name, 'latest')


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_commit_nb(subject_name: str, commit_id: str) -> int:
    url = urljoin(BASE_URL, f'{subject_name}/commits/{commit_id}')
    commit_info = fetch_dict(url)
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
    return fetch_dict(url)


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_version_info(subject_name: str, version: Version, has_public_executable: bool | None = None) -> dict[str, Any]:
    """
    Returns the earliest version entry associated with the given version.

    If the full version does not result in a valid entry, it falls back to
    shorter version segments (e.g., M.m.p -> M.m -> M).
    """
    attempts = [str(version)]

    s = 1
    while True:
        v_truncated = version.truncate(s)
        if v_truncated is None:
            break
        v_str = str(v_truncated)
        if v_str not in attempts:
            attempts.append(v_str)
        s += 1

    for attempt_version_str in attempts:
        url = urljoin(BASE_URL, f'{subject_name}/versions/{attempt_version_str}')
        if has_public_executable is not None:
            url += f'?has_executable={str(has_public_executable).lower()}'

        version_list = fetch_list(url)
        if len(version_list) > 0:
            return version_list[0]

    raise Exception(f'BugHog service responded with an empty or invalid list for all version attempts: {attempts}.')


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_all_versions(subject_name: str) -> list[dict]:
    url = urljoin(BASE_URL, f'{subject_name}/versions')
    return fetch_list(url)


@lru_cache(maxsize=LRU_CACHE_SIZE)
def find_latest_major_version(subject_name: str) -> Version:
    url = urljoin(BASE_URL, f'{subject_name}/versions/latest')
    version_str = fetch_dict(url).get('version')
    if version_str is None:
        raise Exception('BugHog service response did not include a valid major version.')
    return Version(version_str)
