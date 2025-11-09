from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class WasmRuntimeEvaluationFramework(EvaluationFramework):
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        return any(file.name in ('poc.wat', 'script.cmd') for file in experiment_folder.files)

    def get_poc_file_name(self) -> str:
        return 'poc.wat'

    def get_default_experiment_script(self, experiment_folder: Folder) -> list[str]:
        return ['run poc.wat']

    def fill_empty_experiment_with_default(self, path: str):
        pass

    def requires_sanity_check(self) -> bool:
        return False
