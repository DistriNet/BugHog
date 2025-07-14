from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class BrowserEvaluationFramework(EvaluationFramework):
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        return 'script.cmd' in [file.name for file in experiment_folder.files]

    def create_empty_experiment(self, project: str, experiment: str):
        pass

    def get_default_experiment_script(self) -> list[str]:
        return ['navigate']

    def get_default_file_content(self, file_type: str):
        pass
