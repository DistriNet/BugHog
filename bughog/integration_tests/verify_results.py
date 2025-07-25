from collections import defaultdict

from bughog.database.mongo.mongodb import MongoDB
from bughog.evaluation.experiment_result import ExperimentResult
from bughog.parameters import EvaluationParameters
from bughog.version_control.state.base import State


def verify(evaluation_parameters_list: list[EvaluationParameters]) -> list[list]:
    grouped_results = defaultdict(list)
    for evaluation_parameters in evaluation_parameters_list:
        experiment_name = evaluation_parameters.evaluation_range.experiment_name
        verification_func = verification_functions()[experiment_name]
        states = MongoDB().get_evaluated_states(evaluation_parameters, None)
        nb_of_success_results = len(list(filter(lambda x: verification_func(x), states)))
        nb_of_fail_results = len(list(filter(lambda x: not verification_func(x) and not ExperimentResult.poc_is_dirty(x.result_variables), states)))
        nb_of_error_results = len(list(filter(lambda x: ExperimentResult.poc_is_dirty(x.result_variables), states)))
        nb_of_results = nb_of_success_results + nb_of_fail_results + nb_of_error_results
        success_ratio = 0 if nb_of_results == 0 else round((nb_of_success_results / nb_of_results) * 100)

        result = {
            'experiment_name': experiment_name,
            'subject_type': evaluation_parameters.subject_configuration.subject_type,
            'subject_name': evaluation_parameters.subject_configuration.subject_name,
            'nb_of_success_results': nb_of_success_results,
            'nb_of_fail_results': nb_of_fail_results,
            'nb_of_error_results': nb_of_error_results,
            'success_ratio': success_ratio,
        }

        grouped_results[evaluation_parameters.subject_configuration.subject_type].append(result)

    # Return list of lists, each sublist for one subject_type
    return list(grouped_results.values())


def verification_functions() -> dict:
    def all_reproduced(state: State) -> bool:
        return ExperimentResult.poc_is_reproduced(state.result_variables)

    def none_reproduced(state: State) -> bool:
        return not ExperimentResult.poc_is_reproduced(state.result_variables)

    return {
        'all_reproduced': all_reproduced,
        'none_reproduced': none_reproduced,
        'click': all_reproduced,
    }
