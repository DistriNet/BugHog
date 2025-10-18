from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class File:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    def __repr__(self):
        return f'File(name={self.name}, path={self.path})'


class Folder:
    __files_and_folders_to_ignore = ['.DS_Store']

    def __init__(self, name: str, path: str):
        """
        Initializes the Folder instance.

        :param name: Name of the folder.
        :param path: Absolute path of the folder, including the name.
        """
        self.name = name
        self.path = path
        self.subfolders: list[Folder] = []
        self.files: list[File] = []
        self.tags: list[str] = []

    @classmethod
    def parse(cls, path: str) -> Folder:
        folder_name = os.path.basename(path)
        folder = Folder(folder_name, path)

        try:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.name in cls.__files_and_folders_to_ignore:
                        continue
                    elif entry.is_dir():
                        folder.subfolders.append(Folder.parse(entry.path))
                    elif entry.is_file():
                        folder.files.append(File(entry.name, entry.path))
        except PermissionError:
            logger.warning(f"Could not access folder '{path}', skipping.")
            pass

        return folder

    def get_all_folders_with_tag(self, tag: str) -> list[Folder]:
        all_folders_with_tag = []
        if tag in self.tags:
            all_folders_with_tag.append(self)
        for folder in self.subfolders:
            all_folders_with_tag.extend(folder.get_all_folders_with_tag(tag))
        return all_folders_with_tag

    def serialize(self) -> dict:
        return {
            'name': self.name,
            'path': self.path,
            'tags': self.tags,
            'subfolders': [subfolder.serialize() for subfolder in self.subfolders],
            'files': [{'name': file.name, 'path': file.path} for file in self.files],
        }

    def __repr__(self):
        return f'Folder(name={self.name}, path={self.path}, subfolders={self.subfolders}, files={self.files})'
