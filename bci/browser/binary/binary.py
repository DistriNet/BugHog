from __future__ import annotations

import logging
import os
from abc import abstractmethod

from bci import util
from bci.browser.binary.artisanal_manager import ArtisanalBuildManager
from bci.version_control.states.state import State

logger = logging.getLogger('bci')


class Binary:

    def __init__(self, state: State):
        self.state = state
        self.__version = None
        self.only_releases = None

    def set_only_releases(self, only_releases):
        self.only_releases = only_releases

    @property
    def version(self) -> str:
        if self.__version is None:
            self.__version = self._get_version()
        return self.__version

    @property
    @abstractmethod
    def executable_name(self) -> str:
        pass

    @property
    @abstractmethod
    def browser_name(self) -> str:
        pass

    @property
    @abstractmethod
    def bin_folder_path(self) -> str:
        pass

    @property
    def origin(self) -> str:
        if 'artisanal' in self.get_bin_path():
            return 'artisanal'
        elif 'downloaded' in self.get_bin_path():
            return 'downloaded'
        else:
            raise ValueError(f'Unknown binary origin for path \'{self.get_bin_path()}\'')

    @staticmethod
    def list_downloaded_binaries(bin_folder_path: str) -> list[dict[str, str]]:
        binaries = []
        for subfolder_path in os.listdir(os.path.join(bin_folder_path, "downloaded")):
            bin_entry = {}
            bin_entry["id"] = subfolder_path
            binaries.append(bin_entry)
        return binaries

    @staticmethod
    def list_artisanal_binaries(bin_folder_path: str, executable_name: str):
        return Binary.get_artisanal_manager(bin_folder_path, executable_name).get_artisanal_binaries_list()

    @staticmethod
    def get_artisanal_manager(bin_folder_path: str, executable_name: str) -> ArtisanalBuildManager:
        return ArtisanalBuildManager(bin_folder_path, executable_name)

    def fetch_binary(self):
        # Check cache
        if self.is_built():
            return
        # Try to download binary
        elif self.__class__.has_available_binary_online(self.state):
            self.download_binary()
        else:
            raise BuildNotAvailableError(self.browser_name, self.state.revision_number)

    @abstractmethod
    def download_binary(self):
        pass

    def is_available_locally_or_online(self):
        return self.has_available_binary_locally() or self.has_available_binary_online()

    def has_available_binary_locally(self):
        bin_path = self.get_bin_path()
        return bin_path is not None

    @abstractmethod
    def has_available_binary_online(self):
        pass

    def is_built(self):
        bin_path = self.get_bin_path()
        return bin_path is not None

    def get_bin_path(self):
        """
        Returns path to binary, only if the binary is available locally. Otherwise it returns None.
        """
        path_downloaded = self.get_potential_bin_path()
        path_artisanal = self.get_potential_bin_path(artisanal=True)
        if os.path.isfile(path_downloaded):
            return path_downloaded
        if os.path.isfile(path_artisanal):
            return path_artisanal
        return None

    def get_potential_bin_path(self, artisanal=False):
        """
        Returns path to potential binary. It does not guarantee whether the binary is available locally.
        """
        if artisanal:
            return os.path.join(self.bin_folder_path, "artisanal", str(self.state.revision_number), self.executable_name)
        return os.path.join(self.bin_folder_path, "downloaded", str(self.state.revision_number), self.executable_name)

    def get_bin_folder_path(self):
        path_downloaded = self.get_potential_bin_folder_path()
        path_artisanal = self.get_potential_bin_folder_path(artisanal=True)
        if os.path.isdir(path_downloaded):
            return path_downloaded
        if os.path.isdir(path_artisanal):
            return path_artisanal
        return None

    def get_potential_bin_folder_path(self, artisanal=False):
        if artisanal:
            return os.path.join(self.bin_folder_path, "artisanal", str(self.state.revision_number))
        return os.path.join(self.bin_folder_path, "downloaded", str(self.state.revision_number))

    def remove_bin_folder(self):
        path = self.get_bin_folder_path()
        if path and "artisanal" not in path:
            if not util.rmtree(path):
                self.logger.error("Could not remove folder '%s'" % path)

    @abstractmethod
    def get_driver_version(self, browser_version):
        pass

    @abstractmethod
    def _get_version(self):
        pass


class BuildNotAvailableError(Exception):

    def __init__(self, browser_name, build_state):
        super().__init__("Browser build not available: %s (%s)" % (browser_name, build_state))
