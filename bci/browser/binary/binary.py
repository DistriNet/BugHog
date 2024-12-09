from __future__ import annotations

import logging
import os
import time
from abc import abstractmethod
from typing import Optional

from bci import util
from bci.browser.binary.artisanal_manager import ArtisanalBuildManager
from bci.database.mongo.binary_cache import BinaryCache
from bci.version_control.states.state import State

logger = logging.getLogger(__name__)


class Binary:
    def __init__(self, state: State):
        self.state = state
        self.__version = None

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
        bin_path = self.get_bin_path()
        if bin_path is None:
            raise AttributeError('Binary path is not available')

        if 'artisanal' in bin_path:
            return 'artisanal'
        elif 'downloaded' in bin_path:
            return 'downloaded'
        else:
            raise AttributeError(f"Unknown binary origin for path '{self.get_bin_path()}'")

    @staticmethod
    def _list_downloaded_binaries(bin_folder_path: str) -> list[dict[str, str]]:
        binaries = []
        for subfolder_path in os.listdir(os.path.join(bin_folder_path, 'downloaded')):
            bin_entry = {}
            bin_entry['id'] = subfolder_path
            binaries.append(bin_entry)
        return binaries

    @staticmethod
    def list_artisanal_binaries(bin_folder_path: str, executable_name: str):
        return Binary._get_artisanal_manager(bin_folder_path, executable_name).get_artisanal_binaries_list()

    @staticmethod
    def _get_artisanal_manager(bin_folder_path: str, executable_name: str) -> ArtisanalBuildManager:
        return ArtisanalBuildManager(bin_folder_path, executable_name)

    def fetch_binary(self):
        # Check cache
        if self.is_built():
            logger.info(f'Binary for {self.state.index} is already in place')
            return
        # Consult binary cache
        elif BinaryCache.fetch_binary_files(self.get_potential_bin_path(), self.state):
            logger.info(f'Binary for {self.state.index} fetched from cache')
            return
        # Try to download binary
        elif self.is_available_online():
            start = time.time()
            self.download_binary()
            elapsed_time = time.time() - start
            logger.info(f'Binary for {self.state.index} downloaded in {elapsed_time:.2f}s')
            BinaryCache.store_binary_files(self.get_potential_bin_path(), self.state)
        else:
            raise BuildNotAvailableError(self.browser_name, self.state)

    def is_available(self):
        """
        Returns True if the binary is available either locally or online.
        """
        return self.is_available_locally() or self.is_available_online()

    def is_available_locally(self):
        bin_path = self.get_bin_path()
        return bin_path is not None

    def is_available_online(self):
        return self.state.has_online_binary()

    @abstractmethod
    def download_binary(self):
        pass

    def is_built(self):
        bin_path = self.get_bin_path()
        return bin_path is not None

    def get_bin_path(self) -> Optional[str]:
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
            return os.path.join(self.bin_folder_path, 'artisanal', self.state.name, self.executable_name)
        return os.path.join(self.bin_folder_path, 'downloaded', self.state.name, self.executable_name)

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
            return os.path.join(self.bin_folder_path, 'artisanal', self.state.name)
        return os.path.join(self.bin_folder_path, 'downloaded', self.state.name)

    def remove_bin_folder(self):
        path = self.get_bin_folder_path()
        if path and 'artisanal' not in path:
            if not util.rmtree(path):
                logger.error("Could not remove folder '%s'" % path)

    @abstractmethod
    def _get_version(self) -> str:
        pass


class BuildNotAvailableError(Exception):
    def __init__(self, browser_name, build_state):
        super().__init__('Browser build not available: %s (%s)' % (browser_name, build_state))
