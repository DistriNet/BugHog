from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class JSEngineEvaluationFramework(EvaluationFramework):
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        return any(file.name in ('poc.js', 'script.cmd') for file in experiment_folder.files)

    def get_poc_file_name(self) -> str:
        return 'poc.js'

    def get_comment_delimiter(self) -> str:
        return '//'

    def get_default_experiment_script(self, experiment_folder: Folder) -> list[str]:
        return ['run poc.js']

    def fill_empty_experiment_with_default(self, path: str):
        pass
