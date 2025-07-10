from bughog.subject.webbrowser.state_cache import PublicBrowserStateCache


def is_tag(tag: str) -> bool:
    return PublicBrowserStateCache.is_tag("firefox", tag)


def get_release_tag(major_release_version: int) -> str:
    return PublicBrowserStateCache.get_release_tag("firefox", major_release_version)


def get_release_revision_number(major_release_version: int) -> int:
    return PublicBrowserStateCache.get_release_commit_nb("firefox", major_release_version)


def get_release_revision_id(major_release_version: int) -> str:
    return PublicBrowserStateCache.get_release_commit_id("firefox", major_release_version)


def get_most_recent_major_version() -> int:
    return PublicBrowserStateCache.get_most_recent_major_version("firefox")
