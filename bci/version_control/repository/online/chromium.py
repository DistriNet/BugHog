import logging
from bci.util import request_json
from bci.version_control.repository.repository import Repository

LOGGER = logging.getLogger("bci")

META_DATA_URL = "https://gjfr.dev/res/data/chromium.json"
REPO_TAGS_URL = "https://chromium.googlesource.com/chromium/src/+refs/"


class OnlineChromiumRepo(Repository):

    def __init__(self) -> None:
        super().__init__()
        LOGGER.debug("Fetching Chromium meta data...")
        self.meta_data = request_json(META_DATA_URL)["data"]

    def is_tag(self, tag) -> bool:
        return tag in [info["release_tag"] for info in self.meta_data.values()]

    def get_release_tag(self, major_release_version: int) -> str:
        for entry in self.meta_data:
            if entry["major_version"] == major_release_version:
                return entry["release_tag"]
        raise AttributeError(f"Could not find release tag associated with version '{major_release_version}'")

    def get_revision_id(self, revision_number: int) -> str:
        raise NotImplementedError()

    def get_revision_number(self, revision_id) -> int:
        raise NotImplementedError()

    def get_major_release_version(self, revision_number: int) -> int:
        raise NotImplementedError()

    def get_release_revision_number(self, major_release_version):
        for entry in self.meta_data:
            if entry["major_version"] == major_release_version:
                return entry["revision_number"]
        raise AttributeError(f"Could not find major release version '{major_release_version}'")
