"""
Helper module to find commit information for Google repos hosted on GitHub.
"""

import re
from typing import Optional

from bughog import util


def find_commit_id(owner: str, repo: str, commit_nb: int) -> str:
    ref_commit_nb = __get_reference_commit_nb(owner, repo)
    diff = ref_commit_nb - commit_nb
    if diff < 0:
        raise AttributeError(f"Given commit number {commit_nb} is larger than reference {ref_commit_nb}.")

    commits_per_page = 5
    page = diff // commits_per_page + 1
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?page={page}&per_page={commits_per_page}"
    resp = util.request_json(url)
    if not resp or not isinstance(resp, list):
        raise Exception(f"Could not find commit id for {url}.")

    for commit in resp:
        commit_message = commit.get("commit", {}).get("message", "")
        if commit_nb:= __parse_commit_nb(commit_message):
            return commit.get("sha")
    raise Exception(f"Could not find commit id for {url}.")


def find_commit_nb(owner: str, repo: str, commit_id: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_id}"
    resp = util.request_json(url)
    if not resp or not isinstance(resp, dict):
        raise Exception(f"Could not find commit nb for {url}.")
    commit_message = resp.get("commit", {}).get("message", "")
    if commit_nb:= __parse_commit_nb(commit_message):
        return commit_nb

    # Get parent, where we should find the commit number
    parent_commit_id = resp['parents'][0]['sha']
    parent_commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{parent_commit_id}"
    resp = util.request_json(parent_commit_url)
    if not resp or not isinstance(resp, dict):
        raise Exception(f"Could not find commit nb for {url}.")
    commit_message = resp.get("commit", {}).get("message", "")
    if commit_nb:= __parse_commit_nb(commit_message):
        return commit_nb
    raise Exception(f"Could not find commit nb for {url}.")


def find_commit_id_from_tag(owner: str, repo: str, tag: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag}"
    resp = util.request_json(url)
    if not resp or not isinstance(resp, dict):
        raise Exception(f"Could not find commit nb for {url}.")
    return resp.get("object", {}).get("sha")


def __get_reference_commit_nb(owner: str, repo: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?page=1&per_page=1"
    resp = util.request_json(url)
    if resp and isinstance(resp, list) and len(resp) > 0:
        commit = resp[0]
        commit_message = commit.get("commit", {}).get("message", "")
        match = re.search(r"Cr-Commit-Position: refs/heads/main@\{#(\d+)\}", commit_message)
        if match:
            return int(match.group(1))
    raise Exception(f"Could not fetch reference commit from {url}.")


def __parse_commit_nb(commit_message: str) -> Optional[int]:
    if match := re.search(r"Cr-Commit-Position: refs/heads/(?:master|main|candidates)@\{#(\d+)\}", commit_message):
        return int(match.group(1))
    if match := re.search(r"git-svn-id: http://v8.googlecode.com/svn/trunk@(\d+)", commit_message):
        return int(match.group(1))
    return None
