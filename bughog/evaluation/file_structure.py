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
            case 'html' | 'xml':
                return r'<!--', r'-->'
            case 'css':
                return r'/\*', r'\*/'
            case 'js':
                return r'//', None
            case 'wat':
                return r';;', None
            case _:
                return None

    def get_bughog_poc_parameter(self, name: str) -> str | None:
        if delimiters := self.comment_delimiters:
            prefix = delimiters[0]
            suffix = delimiters[1]
            with open(self.path, 'r') as poc:
                for line in poc:
                    # Stop looking upon the first non-comment line that also is not the document declaration.
                    if not re.match(rf'^\s*{prefix}', line) and '<!DOCTYPE' not in line:
                        break
                    match = re.search(rf'^\s*{prefix}\s*bughog_{name}:\s*(.*)\s*{suffix if suffix else ''}\s*$', line)
                    if match:
                        return match.group(1).strip()
        else:
            logger.error(f'BugHog parameters are not supported for file "{self.name}".')
        return None

    def __repr__(self):
        return f'File(name={self.name}, path={self.path})'


class Folder:
    __files_and_folders_to_ignore = [
        '.DS_Store',
        '.git',
        'README.md'
    ]

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
        matched = [file for file in self.files if file.name == name]
        if len(matched) == 0:
            raise Exception(f'Could not find {name} in {self.path}.')
        return matched[0]

    def create_file(self, name: str, content: bytes):
        self.__can_create(name)
        new_file_path = os.path.join(self.path, name)
        with open(new_file_path, 'bw') as file:
            file.write(content)

    def get_folder(self, name: str) -> Folder:
        matched = [file for file in self.subfolders if file.name == name]
        if len(matched) == 0:
            raise Exception(f'Could not find folder {name}.')
        return matched[0]

    def create_folder(self, name: str) -> Folder:
        self.__can_create(name)
        new_project_path = os.path.join(self.path, name)
        os.mkdir(new_project_path)
        new_folder = Folder(name, os.path.join(self.path, name))
        self.subfolders.append(new_folder)
        return new_folder

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

    def folder_exists(self, name: str) -> bool:
        return os.path.isdir(os.path.join(self.path, name))

    def file_exists(self, name: str) -> bool:
        return os.path.isfile(os.path.join(self.path, name))

    def __can_create(self, name: str) -> None:
        if self.folder_exists(name) or self.file_exists(name):
            raise AttributeError(f"The given file or folder name '{name}' already exists.")
        if name is None or name == '':
            raise AttributeError('The file name cannot be empty.')
        regex = r'^[A-Za-z0-9_\-.]+$'
        if re.match(regex, name) is None:
            raise AttributeError(f"The given name '{name}' is invalid. Only letters, numbers, '.', '-' and '_' can be used, and the name should not be empty.")

    def __repr__(self):
        return f'Folder(name={self.name}, path={self.path}, subfolders={self.subfolders}, files={self.files})'
