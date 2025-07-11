"""
Helper module to find commit information for Google repos hosted on GitHub.
"""

import re

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
        match = re.search(r"Cr-Commit-Position: refs/heads/main@\{#(\d+)\}", commit_message)
        if match and int(match.group(1)) == commit_nb:
            return commit.get("sha")
    raise Exception(f"Could not find commit id for {url}.")


def find_commit_nb(owner: str, repo: str, commit_id: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_id}"
    resp = util.request_json(url)
    if not resp or not isinstance(resp, dict):
        raise Exception(f"Could not find commit nb for {url}.")
    commit_message = resp.get("commit", {}).get("message", "")
    match = re.search(r"Cr-Commit-Position: refs/heads/main@\{#(\d+)\}", commit_message)
    if match:
        return int(match.group(1))
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
