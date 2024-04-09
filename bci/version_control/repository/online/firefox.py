import logging
import bci.version_control.repository.online.parser as parser
from bci.util import request_json

__META_DATA_URL = "https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/firefox_release_base_revs.json"
__REPO_REVISION_URL = "https://hg.mozilla.org/releases/mozilla-release/rev/"

LOGGER = logging.getLogger(__name__)
LOGGER.debug("Fetching Firefox meta data...")
__META_DATA: list[dict] = request_json(__META_DATA_URL)["data"]


def is_tag(tag: str) -> bool:
    return parser.is_tag(tag, __META_DATA)


def get_release_tag(major_release_version: int) -> str:
    return parser.get_release_tag(major_release_version, __META_DATA)


def get_release_revision_number(major_release_version: int) -> int:
    return parser.get_release_revision_number(major_release_version, __META_DATA)


def get_release_revision_id(major_release_version: int) -> int:
    return parser.get_release_revision_id(major_release_version, __META_DATA)


def get_most_recent_major_version() -> int:
    return parser.get_most_recent_major_version(__META_DATA)
