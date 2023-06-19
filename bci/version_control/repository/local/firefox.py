from bci import cli
from bci.version_control.repository.repository import Repository
from bci.version_control.states.firefox import FirefoxState

RELEASE_TAG_REGEX = "FIREFOX_RELEASE_%s_BASE"
BACKUP_RELEASE_TAG_REGEX = "FIREFOX_RELEASE_%s"
BACKUP_RELEASE_TAG_REGEX2 = "FIREFOX_RELEASE_%s.0"
BACKUP_RELEASE_TAG_REGEX3 = "FIREFOX_RELEASE_%s.0.1"
BACKUP_RELEASE_TAG_REGEX4 = "FIREFOX_RELEASE_%s.0.2"


class LocalFirefoxRepo(Repository):

    def __init__(self, path):
        if not self.is_repo(path):
            raise AttributeError("Invalid Firefox repository: '%s'" % path)
        self.path = path

    def checkout(self, changeset_id):
        command = "hg update --rev %s" % changeset_id
        return self.execute(command)

    def is_tag(self, tag):
        command = 'hg log --rev tag(%s)' % tag
        status = self.execute_and_return_status(command)
        return status == 0

    def get_tag_list(self):
        command = 'hg log --rev tag() --template "{tags}\n"'
        raw = self.execute_and_return_output(command)
        return list(filter(None, str(raw).replace("\n", " ").split(" ")))

    def get_changeset_id(self, tag):
        command = 'hg id --rev tag(%s) --template "{node}\n"' % tag
        raw = self.execute_and_return_output(command)
        return str(raw).replace("\n", "")

    def get_changeset_id_from_revision_id(self, revision_id):
        command = 'hg id --rev %s --template "{node}\n"' % revision_id
        raw = self.execute_and_return_output(command)
        return str(raw).replace("\n", "")

    def get_revision_id(self, changeset_id) -> int:
        command = 'hg id --rev %s --template "{rev}\n"' % changeset_id
        raw = self.execute_and_return_output(command)
        return int(str(raw).replace("\n", ""))

    def get_state(self, tag, version: int = None):
        changeset_id = self.get_changeset_id(tag)
        return FirefoxState(changeset_id, version=version)

    def get_changeset_parent_ids(self, changeset_id):
        command = 'hg log --rev parents(%s) --template "{node}\n"' % changeset_id
        raw = self.execute_and_return_output(command)
        return list(filter(None, str(raw).replace("\n", " ").split(" ")))

    def get_changeset_child_ids(self, changeset_id):
        command = 'hg log --rev children(%s) --template "{node}\n"' % changeset_id
        raw = self.execute_and_return_output(command)
        return list(filter(None, str(raw).replace("\n", " ").split(" ")))

    def get_changeset_lineage(self, ancestor_changeset_id, descendant_changeset_id):
        # IMPORTANT!    This command will only get a sequence of consecutive revision ids, starting with the one
        #               associated with the ancestor_changeset_id and ending with the one associated with the
        #               descendant_changeset_id. If this has to be changed to a real path from start to ending,
        #               use 'hg log --rev %s::%s --template "{node}\n"' (double colon instead of single).
        command = 'hg log --rev %s:%s --template "{node}\n"' % (ancestor_changeset_id, descendant_changeset_id)
        raw = self.execute_and_return_output(command)
        return list(filter(None, str(raw).replace("\n", " ").split(" ")))

    # def is_descendant_of(self, ancestor_changeset_id, descendant_changeset_id):
    #    lineage = self.get_changeset_lineage(ancestor_changeset_id, descendant_changeset_id)
    #    return len(lineage) != 0

    def execute(self, command):
        cli.execute(command + " --cwd " + self.path)

    def execute_and_return_status(self, command):
        return cli.execute_and_return_status(command, cwd=self.path)

    def execute_and_return_output(self, command):
        return cli.execute_and_return_output(command, cwd=self.path, output_possibly_empty=True)

    @staticmethod
    def is_repo(path):
        command = "hg --cwd %s root" % path
        status = cli.execute_and_return_status(command)
        return status == 0

    def get_changeset_lineage_spread(self, ancestor_changeset_id, descendant_changeset_id, nb_of_changeset_ids=None):
        complete_changeset_list = self.get_changeset_lineage(ancestor_changeset_id, descendant_changeset_id)
        if nb_of_changeset_ids:
            interval = round(len(complete_changeset_list) / (1 + nb_of_changeset_ids))
            changeset_list = []
            for i in range(1, nb_of_changeset_ids):
                changeset_list.append(complete_changeset_list[i * interval])
            changeset_list.append(complete_changeset_list[len(complete_changeset_list) - 1])
        else:
            changeset_list = complete_changeset_list
        return changeset_list

    def get_release_tag(self, version):
        tag = RELEASE_TAG_REGEX % str(version)
        if self.is_tag(tag):
            return tag
        tag = BACKUP_RELEASE_TAG_REGEX % str(version)
        if self.is_tag(tag):
            return tag
        tag = BACKUP_RELEASE_TAG_REGEX2 % str(version)
        if self.is_tag(tag):
            return tag
        tag = BACKUP_RELEASE_TAG_REGEX3 % str(version)
        if self.is_tag(tag):
            return tag
        tag = BACKUP_RELEASE_TAG_REGEX4 % str(version)
        if self.is_tag(tag):
            return tag
        raise AttributeError(
            "Could not find changeset id associated with version '%s' (using release tag and backup release tag)" %
            version)

    def get_state_id_from_version(self, version):
        version_tag = self.get_release_tag(version)
        return self.get_state(version_tag).id
