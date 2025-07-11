from bughog.subject.evaluation_framework import EvaluationFramework


class JSEngineEvaluationFramework(EvaluationFramework):
    def experiment_sanity_check_succeeded(self, result_variables) -> bool:
        pass

    def experiment_is_valid(self, project: str, experiment: str) -> bool:
        pass

    def create_empty_experiment(self, project: str, experiment: str):
        pass
