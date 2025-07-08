# from typing import Optional

# import requests

# from bughog.database.mongo.mongodb import MongoDB
# from bughog.version_control.revision_parser.chromium_parser import ChromiumRevisionParser
# from bughog.version_control.states.revisions.base import CommitState

# PARSER = ChromiumRevisionParser()


# class ChromiumRevision(CommitState):
#     def __init__(self, revision_id: Optional[str] = None, revision_nb: Optional[int] = None):
#         super().__init__(revision_id, revision_nb)

#     @property
#     def browser_name(self):
#         return 'chromium'
