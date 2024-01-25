import logging
from bci.util import request_json
from bci.version_control.repository.repository import Repository

LOGGER = logging.getLogger("bci")

META_DATA_URL = "https://distrinet.pages.gitlab.kuleuven.be/users/gertjan-franken/bughog-revision-metadata/firefox_release_base_revs.json"
REPO_REVISION_URL = "https://hg.mozilla.org/releases/mozilla-release/rev/"


class OnlineFirefoxRepo(Repository):

    def __init__(self) -> None:
        super().__init__()
        LOGGER.debug("Fetching Firefox meta data...")
        self.meta_data: list[dict] = request_json(META_DATA_URL)["data"]

    def is_tag(self, tag) -> bool:
        return tag in [info["release_tag"] for info in self.meta_data]

    def get_release_tag(self, major_release_version) -> str:
        for entry in self.meta_data:
            if entry["major_version"] == major_release_version:
                return entry["release_tag"]
        raise AttributeError(f"Could not find release tag associated with version '{major_release_version}'")

    def get_release_revision_number(self, major_release_version: int) -> int:
        for entry in self.meta_data:
            if entry["major_version"] == major_release_version:
                return entry["revision_number"]
        raise AttributeError(f"Could not find major release version '{major_release_version}'")
