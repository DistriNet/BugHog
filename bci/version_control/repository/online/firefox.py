from bci.database.mongo.revision_cache import RevisionCache


def is_tag(tag: str) -> bool:
    return RevisionCache.is_tag('firefox', tag)


def get_release_tag(major_release_version: int) -> str:
    return RevisionCache.get_release_tag('firefox', major_release_version)


def get_release_revision_number(major_release_version: int) -> int:
    return RevisionCache.get_release_revision_number('firefox', major_release_version)


def get_release_revision_id(major_release_version: int) -> int:
    return RevisionCache.get_release_revision_id('firefox', major_release_version)


def get_most_recent_major_version() -> int:
    return RevisionCache.get_most_recent_major_version('firefox')
