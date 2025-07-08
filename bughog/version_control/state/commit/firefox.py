# from typing import Optional

# from bughog.database.mongo.revision_cache import RevisionCache
# from bughog.version_control.states.base import State
# from bughog.version_control.states.revisions.base import CommitState


# class FirefoxRevision(CommitState):
#     def __init__(
#         self, revision_id: Optional[str] = None, revision_nb: Optional[int] = None, major_version: Optional[int] = None
#     ):
#         super().__init__(revision_id=revision_id, revision_nb=revision_nb)
#         self.major_version = major_version

#     @property
#     def browser_name(self) -> str:
#         return 'firefox'

#     def has_online_binary(self) -> bool:
#         return RevisionCache.firefox_has_binary_for(revision_nb=self.revision_nb, revision_id=self._revision_id)

#     def get_online_binary_urls(self) -> list[str]:
#         result = RevisionCache.firefox_get_binary_info(self._revision_id)
#         if result is None:
#             raise AttributeError(f"Could not find binary url for '{self._revision_id}'")
#         binary_base_url = result['files_url']
#         app_version = result['app_version']
#         return [
#             f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.bz2',
#             f'{binary_base_url}firefox-{app_version}.en-US.linux-x86_64.tar.xz',
#         ]

#     def get_previous_and_next_state_with_binary(self) -> tuple[State, State]:
#         previous_revision_nb, next_revision_nb = RevisionCache.firefox_get_previous_and_next_revision_nb_with_binary(
#             self.revision_nb
#         )

#         return (
#             FirefoxRevision(revision_nb=previous_revision_nb) if previous_revision_nb else None,
#             FirefoxRevision(revision_nb=next_revision_nb) if next_revision_nb else None,
#         )

#     def _fetch_missing_data(self):
#         if self._revision_id is None:
#             self._revision_id = RevisionCache.firefox_get_revision_id(self._revision_nb)
#         if self._revision_nb is None and self._revision_id is not None:
#             self._revision_nb = RevisionCache.firefox_get_revision_number(self._revision_id)
