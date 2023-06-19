from bci import cli
from bci.version_control.repository.repository import Repository


class LocalChromiumRepo(Repository):

    def __init__(self, path):
        if not self.is_repo(path):
            raise AttributeError("Invalid Chromium repository: '%s'" % path)
        self.path = path

    @staticmethod
    def is_repo(path):
        command = "git -C %s rev-parse --is-inside-work-tree" % path
        status = cli.execute_and_return_status(command)
        return status == 0

    def is_tag(self, tag) -> bool:
        raise NotImplementedError()

    def get_release_tag(self, version) -> str:
        raise NotImplementedError()

    def get_revision_id(self, revision_number: int = None, tag: str = None) -> str:
        raise NotImplementedError()

    def get_revision_number(self, revision_id: int = None, tag: str = None) -> int:
        raise NotImplementedError()

    def get_release_revision_number(self, major_release_version: int) -> int:
        raise NotImplementedError()
