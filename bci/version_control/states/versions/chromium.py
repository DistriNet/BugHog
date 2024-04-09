import requests
from bci.version_control.repository.online.chromium import get_release_revision_number, get_release_revision_id
from bci.version_control.states.versions.base import BaseVersion
from bci.database.mongo.mongodb import MongoDB


class ChromiumVersion(BaseVersion):

    def __init__(self, major_version: int):
        super().__init__(major_version)

    def _get_rev_nb(self):
        return get_release_revision_number(self.major_version)

    def _get_rev_id(self):
        return get_release_revision_id(self.major_version)

    @property
    def browser_name(self):
        return 'chromium'

    def has_online_binary(self):
        cached_binary_available_online = MongoDB.has_binary_available_online('chromium', self)
        if cached_binary_available_online is not None:
            return cached_binary_available_online
        url = f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{self._rev_nb}%2Fchrome-linux.zip'
        req = requests.get(url)
        has_binary_online = req.status_code == 200
        MongoDB.store_binary_availability_online_cache('chromium', self, has_binary_online)
        return has_binary_online

    def get_online_binary_url(self):
        return "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/%s%%2F%s%%2Fchrome-%s.zip?alt=media" % ('Linux_x64', self._rev_nb, 'linux')
