import os
import re
from typing import Optional

from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class WasmRuntimeEvaluationFramework(EvaluationFramework):
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        return any(file.name in ('poc.wasm', 'script.cmd') for file in experiment_folder.files)

    def get_runtime_flags(self, experiment_folder: Folder) -> list[str]:
        poc_path = os.path.join(experiment_folder.path, 'poc.wasm')
        with open(poc_path, 'r') as poc:
            for line in poc:
                match = re.search(r'^//\s*bughog_runtime_flags:\s*(.*)$', line)
                if match:
                    flags_line = match.group(1)
                    return flags_line.split()
        return []

    def get_runtime_env_vars(self, experiment_folder: Folder) -> list[str]:
        poc_path = os.path.join(experiment_folder.path, 'poc.wasm')
        with open(poc_path, 'r') as poc:
            for line in poc:
                match = re.search(r'^//\s*bughog_env_vars:\s*(.*)$', line)
                if match:
                    flags_line = match.group(1)
                    return flags_line.split()
        return []

    def get_expected_output_regex(self, experiment_folder: Folder) -> Optional[str]:
        poc_path = os.path.join(experiment_folder.path, 'poc.wasm')
        with open(poc_path, 'r') as poc:
            for line in poc:
                match = re.search(r'^//\s*bughog_expected_output:\s*(.*)$', line)
                if match:
                    return match.group(1).strip()
        return None

    def get_unexpected_output_regex(self, experiment_folder: Folder) -> Optional[str]:
        poc_path = os.path.join(experiment_folder.path, 'poc.wasm')
        with open(poc_path, 'r') as poc:
            for line in poc:
                match = re.search(r'^//\s*bughog_unexpected_output:\s*(.*)$', line)
                if match:
                    return match.group(1).strip()
        return None

    def get_default_experiment_script(self, experiment_folder: Folder) -> list[str]:
        return ['run poc.wasm']

    def fill_empty_experiment_with_default(self, path: str):
        pass
