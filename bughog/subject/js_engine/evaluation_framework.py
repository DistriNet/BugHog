from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class JSEngineEvaluationFramework(EvaluationFramework):
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        return any(file.name in ('poc.js', 'script.cmd') for file in experiment_folder.files)

    def get_default_experiment_script(self) -> list[str]:
        return ['run poc.js']

    def create_empty_experiment(self, project: str, experiment: str):
        pass
