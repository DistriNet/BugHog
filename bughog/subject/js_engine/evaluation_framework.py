from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class JSEngineEvaluationFramework(EvaluationFramework):
    def experiment_sanity_check_succeeded(self, result_variables) -> bool:
        pass

    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        return True

    def create_empty_experiment(self, project: str, experiment: str):
        pass
