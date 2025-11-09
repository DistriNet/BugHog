from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)


class File:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    @property
    def file_type(self) -> str | None:
        if '.' not in self.name:
            return None
        return self.name.split('.')[-1]

    @property
    def comment_delimiters(self) -> tuple[str,str|None] | None:
        match self.file_type:
            case 'html':
                return '<!--', '-->'
            case 'css':
                return '/*', '*/'
            case 'js':
                return '//', None
            case 'wat':
                return ';;', None
            case _:
                return None

    def get_bughog_poc_parameter(self, name: str) -> str | None:
        if delimiters := self.comment_delimiters:
            prefix = delimiters[0]
            suffix = delimiters[1]
            with open(self.path, 'r') as poc:
                for line in poc:
                    match = re.search(rf'^\s*{prefix}\s*bughog_{name}:\s*(.*)\s*{suffix if suffix else ''}\s*$', line)
                    if match:
                        return match.group(1).strip()
        else:
            logger.error(f'BugHog parameters are not supported for file "{self.name}".')
        return None

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

    def get_file(self, name: str) -> File:
        matched_files = [file for file in self.files if file.name == name]
        if len(matched_files) == 0:
            raise Exception(f'Could not find {name} in {self.path}')
        return matched_files[0]

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
