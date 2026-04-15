"""
Helper module to find commit information for Google repos hosted on GitHub.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from bughog.config import settings
from bughog.util import http
from bughog.version_control.state_not_found import StateNotFound

logger = logging.getLogger(__name__)


def find_commit_nb(owner: str, repo: str, commit_id: str) -> int:
    url = f'https://api.github.com/repos/{owner}/{repo}/commits/{commit_id}'
    resp = http.request_json(url, token=settings.github_token)
    if not resp or not isinstance(resp, dict):
        raise Exception(f'Could not find commit nb for {url}.')
    commit_message = resp.get('commit', {}).get('message', '')
    if commit_nb := __parse_commit_nb(commit_message):
        return commit_nb

    # Get parent, where we should find the commit number
    parent_commit_id = resp['parents'][0]['sha']
    parent_commit_url = f'https://api.github.com/repos/{owner}/{repo}/commits/{parent_commit_id}'
    resp = http.request_json(parent_commit_url, token=settings.github_token)
    if not resp or not isinstance(resp, dict):
        raise Exception(f'Request to {url} returned {resp}.')
    commit_message = resp.get('commit', {}).get('message', '')
    if commit_nb := __parse_commit_nb(commit_message):
        return commit_nb
    raise StateNotFound('commit number', f'commit id {commit_id}', url)


def find_commit_id_with_date(owner: str, repo: str, ts: int) -> str:
    """
    The UNIX timestamp is considered the commit number.
    """
    date = datetime.fromtimestamp(ts + 1, tz=timezone.utc).isoformat().replace('+00:00', 'Z')
    url = f'https://api.github.com/repos/{owner}/{repo}/commits?since={date}&until{date}'
    resp = http.request_json(url, token=settings.github_token)
    if not isinstance(resp, list):
        raise Exception(f'Request to {url} returned {resp}.')
    return resp[0].get('sha')


def find_commit_nb_with_date(owner: str, repo: str, commit_id: str) -> int:
    """
    The UNIX timestamp is considered the commit number.
    """
    url = f'https://api.github.com/repos/{owner}/{repo}/commits/{commit_id}'
    resp = http.request_json(url, token=settings.github_token)
    if not resp or not isinstance(resp, dict):
        raise Exception(f'Could not find commit nb for {url}.')
    date = resp.get('commit', {}).get('author', {}).get('date', None)
    if date is None:
        raise Exception(f'Could not find date for {url}')
    return int(datetime.fromisoformat(date).timestamp())


def find_commit_id_from_tag(owner: str, repo: str, tag: str) -> str:
    url = f'https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag}'
    resp = http.request_json(url, token=settings.github_token)
    if not resp or not isinstance(resp, dict):
        raise Exception(f'Request to {url} returned {resp}.')
    return resp.get('object', {}).get('sha')


def get_all_tags(owner: str, repo: str) -> list[str]:
    url = f'https://api.github.com/repos/{owner}/{repo}/git/refs/tags/'
    resp = http.request_json(url, token=settings.github_token)
    if not resp or not isinstance(resp, list):
        raise Exception(f'Request to {url} returned {resp}.')
    return [re.sub(r'^refs/tags/', '', item['ref']) for item in resp if 'ref' in item]


def __get_reference_commit_nb(owner: str, repo: str) -> int:
    url = f'https://api.github.com/repos/{owner}/{repo}/commits?page=1&per_page=1'
    resp = http.request_json(url, token=settings.github_token)
    if resp and isinstance(resp, list) and len(resp) > 0:
        commit = resp[0]
        commit_message = commit.get('commit', {}).get('message', '')
        match = re.search(r'Cr-Commit-Position: refs/heads/main@\{#(\d+)\}', commit_message)
        if match:
            return int(match.group(1))
    raise Exception(f'Could not fetch reference commit from {url}.')


def __parse_commit_nb(commit_message: str) -> Optional[int]:
    if matches := re.findall(r'Cr-Commit-Position: refs/heads/(?:master|main|candidates)@\{#(\d+)\}', commit_message):
        return int(matches[-1])
    if matches := re.findall(
        r'git-svn-id: https*://v8\.googlecode\.com/svn/(?:trunk|bleeding_edge)@(\d+)', commit_message
    ):
        return int(matches[-1])
    if matches := re.findall(
        r'git-svn-id: https*://v8\.googlecode\.com/svn/branches/bleeding_edge@(\d+)', commit_message
    ):
        return int(matches[-1])
    return None
