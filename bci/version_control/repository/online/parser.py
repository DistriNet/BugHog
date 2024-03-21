def is_tag(tag: str, meta_data: dict) -> bool:
    return tag in [info["release_tag"] for info in meta_data.values()]


def get_release_tag(major_release_version: int, meta_data: dict) -> str:
    for entry in meta_data:
        if entry["major_version"] == major_release_version:
            return entry["release_tag"]
    raise AttributeError(f"Could not find release tag associated with version '{major_release_version}'")


def get_release_revision_number(major_release_version: int, meta_data: dict) -> int:
    for entry in meta_data:
        if entry["major_version"] == major_release_version:
            return entry["revision_number"]
    raise AttributeError(f"Could not find major release version '{major_release_version}'")


def get_most_recent_major_version(meta_data: dict) -> int:
    return max([entry['major_version'] for entry in meta_data])
