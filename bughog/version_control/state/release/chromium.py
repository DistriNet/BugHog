# import requests

# from bughog.database.mongo.mongodb import MongoDB
# from bughog.version_control.repository.online.chromium import get_release_revision_id, get_release_revision_number
# from bughog.version_control.states.revisions.chromium import ChromiumRevision
# from bughog.version_control.states.versions.base import ReleaseState


# class ChromiumVersion(ReleaseState):
#     def __init__(self, major_version: int):
#         super().__init__(major_version)

#     def _get_rev_nb(self) -> int:
#         return get_release_revision_number(self.major_version)

#     def _get_rev_id(self) -> str:
#         return get_release_revision_id(self.major_version)

#     @property
#     def browser_name(self):
#         return 'chromium'

#     def has_online_binary(self):
#         cached_binary_available_online = MongoDB().has_executable_available_online('chromium', self)
#         if cached_binary_available_online is not None:
#             return cached_binary_available_online
#         url = f'https://www.googleapis.com/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{self._revision_nb}%2Fchrome-linux.zip'
#         req = requests.get(url)
#         has_binary_online = req.status_code == 200
#         MongoDB().store_binary_availability_online_cache('chromium', self, has_binary_online)
#         return has_binary_online

#     def get_online_binary_urls(self) -> list[str]:
#         return [
#             (
#                 'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/%s%%2F%s%%2Fchrome-%s.zip?alt=media'
#                 % ('Linux_x64', self._revision_nb, 'linux')
#             )
#         ]

#     def convert_to_revision(self) -> ChromiumRevision:
#         return ChromiumRevision(revision_nb=self._revision_nb)
