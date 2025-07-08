# from bughog.version_control.repository.online.firefox import get_release_revision_id, get_release_revision_number
# from bughog.version_control.states.revisions.firefox import FirefoxRevision
# from bughog.version_control.states.versions.base import ReleaseState


# class FirefoxVersion(ReleaseState):
#     def __init__(self, major_version: int):
#         super().__init__(major_version)

#     def _get_rev_nb(self) -> int:
#         return get_release_revision_number(self.major_version)

#     def _get_rev_id(self) -> str:
#         return get_release_revision_id(self.major_version)

#     @property
#     def browser_name(self) -> str:
#         return 'firefox'

#     def has_online_binary(self) -> bool:
#         return True

#     def get_online_binary_urls(self) -> list[str]:
#         return [
#             f'https://ftp.mozilla.org/pub/firefox/releases/{self.major_version}.0/linux-x86_64/en-US/firefox-{self.major_version}.0.tar.bz2',
#             f'https://ftp.mozilla.org/pub/firefox/releases/{self.major_version}.0/linux-x86_64/en-US/firefox-{self.major_version}.0.tar.xz',
#         ]

#     def convert_to_revision(self) -> FirefoxRevision:
#         return FirefoxRevision(revision_nb=self._revision_nb)
