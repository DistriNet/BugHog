from bughog.subject.web_browser.state_cache import PublicBrowserStateCache


def is_tag(tag: str) -> bool:
    return PublicBrowserStateCache.is_tag("chromium", tag)


def get_release_tag(major_release_version: int) -> str:
    return PublicBrowserStateCache.get_release_tag("chromium", major_release_version)


def get_release_commit_nb(major_release_version: int) -> int:
    return PublicBrowserStateCache.get_release_commit_nb("chromium", major_release_version)


def get_release_commit_id(major_release_version: int) -> str:
    return PublicBrowserStateCache.get_release_commit_id("chromium", major_release_version)


def get_most_recent_major_version() -> int:
    return PublicBrowserStateCache.get_most_recent_major_version("chromium")
