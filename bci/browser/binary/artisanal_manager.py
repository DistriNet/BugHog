import json
import logging
import os
from bci import cli
from bci.version_control.states.state import State

logger = logging.getLogger('bci')

META_FILE_NAME = "meta.json"


class ArtisanalBuildManager:

    def __init__(self, bin_folder_path: str, executable_name: str) -> None:
        self.builds_folder_path = os.path.join(bin_folder_path, 'artisanal')
        self.executable_name = executable_name
        self.meta_info = self._get_meta_info()

    def update(self):
        subfolders = self._get_subfolders()

        self.add_new_subfolders(subfolders)
        self.remove_deleted_subfolders(subfolders)
        self.recheck_validity_invalid_subfolders()

        self._overwrite_meta_info()

    def get_artisanal_binaries_list(self) -> list:
        return sorted(self.meta_info, key=lambda i: int(i["id"]))

    def has_artisanal_binary_for(self, state: State) -> bool:
        return len(list(filter(lambda x: x['id'] == state.revision_number, self.meta_info))) > 0

    def add_new_subfolders(self, subfolders):
        logger.info("Adding new subfolders to metadata")
        new_subfolders = [subfolder for subfolder in subfolders if subfolder not in [entry["folder"] for entry in self.meta_info if "folder" in entry]]
        for subfolder in new_subfolders:
            self._add_entry(subfolder)

    def remove_deleted_subfolders(self, subfolders):
        logger.info("Removing deleted subfolders from metadata")
        deleted_subfolders = [subfolder for subfolder in [entry["folder"] for entry in self.meta_info if "folder" in entry] if subfolder not in subfolders]
        self.meta_info = [entry for entry in self.meta_info if entry["folder"] not in deleted_subfolders]

    def recheck_validity_invalid_subfolders(self):
        logger.info("Recheck invalid subfolders and update metadata")
        invalid_subfolders = [entry["folder"] for entry in self.meta_info if not entry["valid"]]
        for subfolder in invalid_subfolders:
            self._remove_entry(subfolder)
            self._add_entry(subfolder)

    def _add_entry(self, subfolder):
        subfolder_path = os.path.join(self.builds_folder_path, subfolder)
        # TODO
        rev_id = str(self.browser_build.preferred_binary_representation(subfolder))
        if os.path.isfile(os.path.join(subfolder_path, self.executable_name)):
            if self._is_valid(subfolder_path):
                version = self._get_version(subfolder_path)
                self.meta_info.append({"id": rev_id, "folder": subfolder, "valid": True, "version": version})
            else:
                self.meta_info.append({"id": rev_id, "folder": subfolder, "valid": False})
        else:
            self.meta_info.append({"id": rev_id, "folder": subfolder, "valid": False})

    def _remove_entry(self, subfolder: str):
        self.meta_info = [entry for entry in self.meta_info if entry["folder"] != subfolder]

    def _is_valid(self, build_path: str) -> bool:
        command = "./%s --version" % self.executable_name
        return cli.execute_and_return_status(command, cwd=build_path) == 0

    def _get_version(self, build_path: str) -> str:
        command = "./%s --version" % self.executable_name
        return cli.execute_and_return_output(command, cwd=build_path)

    def _get_meta_info(self) -> dict:
        meta_file_path = os.path.join(self.builds_folder_path, META_FILE_NAME)
        with open(meta_file_path, "r") as file:
            return json.load(file)

    def _overwrite_meta_info(self):
        meta_file_path = os.path.join(self.builds_folder_path, META_FILE_NAME)
        with open(meta_file_path, "w") as file:
            json.dump(self.meta_info, file)

    def _get_subfolders(self) -> list:
        return [subfolder for subfolder in os.listdir(self.builds_folder_path) if os.path.isdir(os.path.join(self.builds_folder_path, subfolder))]
