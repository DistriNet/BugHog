from bci.version_control.repository.online.firefox import get_release_revision_number, get_release_revision_id
from bci.version_control.states.versions.base import BaseVersion


class FirefoxVersion(BaseVersion):

    def __init__(self, major_version: int):
        super().__init__(major_version)

    def _get_rev_nb(self):
        return get_release_revision_number(self.major_version)

    def _get_rev_id(self):
        return get_release_revision_id(self.major_version)

    @property
    def browser_name(self):
        return 'firefox'

    def has_online_binary(self):
        return f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{self._rev_nb}%2Fchrome-linux.zip'

    def get_online_binary_url(self):
        return f'https://ftp.mozilla.org/pub/firefox/releases/{self.major_version}.0/linux-x86_64/en-US/firefox-{self.major_version}.0.tar.bz2'
