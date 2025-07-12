from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class BrowserEvaluationFramework(EvaluationFramework):
    def experiment_sanity_check_succeeded(self, result_variables: tuple[str, str]) -> bool:
        for variable, value in result_variables:
            if variable.lower() == 'sanity_check' and value.lower() == 'ok':
                return True
        return False

    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        return 'script.cmd' in [file.name for file in experiment_folder.files]

    def create_empty_experiment(self, project: str, experiment: str):
        pass

    def get_default_file_content(self, file_type: str):
        pass
