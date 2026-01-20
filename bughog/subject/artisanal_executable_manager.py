import bisect
import logging
import os
from typing import Iterator, Literal

logger = logging.getLogger(__name__)
BASE_EXECUTABLE_FOLDER = '/app/subject'


class ArtisanalExecutableManager:
    """
    Manages storage and retrieval of local executable folders.
    This class is intended to be used as a singleton instance.
    """

    def __init__(self) -> None:
        self._executables = self.load_artisanal_executables()
        logger.info('Loaded artisanal executables.')

    def load_artisanal_executables(self) -> dict[str, dict[str, dict[str, list[str]]]]:
        """
        Loads all available artisanal executables.
        """
        executables = {}
        for subject_type in os.listdir(BASE_EXECUTABLE_FOLDER):
            type_path = os.path.join(BASE_EXECUTABLE_FOLDER, subject_type, 'executables')
            if not os.path.isdir(type_path):
                continue
            executables[subject_type] = {}
            for subject_name in os.listdir(type_path):
                name_path = os.path.join(type_path, subject_name)
                if not os.path.isdir(name_path):
                    continue
                executables[subject_type][subject_name] = {'version': [], 'commit': []}
                for folder in os.listdir(name_path):
                    folder_path = os.path.join(name_path, folder)
                    if os.path.isdir(folder_path):
                        state_type_and_index = self._get_state_type_and_index(folder)
                        if state_type_and_index is not None:
                            if state_type_and_index[0] == 'release':
                                executables[subject_type][subject_name]['version'].append(state_type_and_index[1])
                            elif state_type_and_index[0] == 'commit':
                                executables[subject_type][subject_name]['commit'].append(state_type_and_index[1])
        return executables

    def get_executable_folder(
        self, subject_type: str, subject_name: str, state_type: Literal['release', 'commit'], index: int
    ) -> str | None:
        prefix = 'r' if state_type == 'release' else 'c'
        folder_name = f'{prefix}_{index}'
        path = os.path.join(self._get_subject_base_dir(subject_type, subject_name), folder_name)
        return path if os.path.isdir(path) else None

    def count_executables(self, subject_type: str, subject_name: str, state_type: Literal['release', 'commit']) -> int:
        """
        Returns the number of existing executable folders for a specific subject.
        """
        return len(list(self.get_all_executable_indices(subject_type, subject_name, state_type)))

    def get_all_executable_indices(
        self, subject_type: str, subject_name: str, state_type: Literal['release', 'commit']
    ) -> Iterator[int]:
        """
        Returns a list of all existing executable folders for a specific subject.
        """
        raw_indices = self._executables.get(subject_type, {}).get(subject_name, {}).get(state_type, [])
        for item in raw_indices:
            try:
                yield int(item)
            except (ValueError, TypeError):
                continue

    def get_nearest_state_with_artisanal_executable(
        self,
        subject_type: str,
        subject_name: str,
        state_type: Literal['release', 'commit'],
        target_index: int,
        lower_bound: int,
        upper_bound: int,
    ) -> int | None:
        """
        Returns the closest existing state index with an artisanal executable for the given subject.
        """
        available_indices = [
            i
            for i in self.get_all_executable_indices(subject_type, subject_name, state_type)
            if lower_bound <= int(i) <= upper_bound
        ]
        available_indices.sort()

        if not available_indices:
            return None

        pos = bisect.bisect_left(available_indices, target_index)

        # Target is smaller than the smallest index available.
        if pos == 0:
            return available_indices[0]

        # Target is smaller than the largest index available
        if pos == len(available_indices):
            return available_indices[-1]

        # Target is between two available indices.
        before = available_indices[pos - 1]
        after = available_indices[pos]
        if after - target_index < target_index - before:
            return after
        else:
            return before

    def _get_subject_base_dir(self, subject_type: str, subject_name: str) -> str:
        return os.path.join(BASE_EXECUTABLE_FOLDER, subject_type, 'executables', subject_name)

    def _get_state_type_and_index(self, folder_name: str) -> tuple[Literal['release', 'commit'], int] | None:
        if folder_name.startswith('v_'):
            try:
                index = int(folder_name[2:])
                return 'release', index
            except ValueError:
                return None
        elif folder_name.startswith('c_'):
            try:
                index = int(folder_name[2:])
                return 'commit', index
            except ValueError:
                return None
        return None


# Singleton instance
artisanal_executable_manager = ArtisanalExecutableManager()
