from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import EvaluationParameters
from bci.version_control.state_result_factory import StateResultFactory
from bci.version_control.states.state import State


def verify(evaluation_parameters_list: list[EvaluationParameters]) -> list:
    verification_results = []
    for evaluation_parameters in evaluation_parameters_list:
        experiment_name = evaluation_parameters.evaluation_range.mech_group
        verification_func = verification_functions()[experiment_name]
        state_result_factory = StateResultFactory(experiment=experiment_name)
        states = MongoDB().get_evaluated_states(evaluation_parameters, None, state_result_factory)
        nb_of_success_results = len(list(filter(lambda x: verification_func(x) and not x.result.is_dirty, states)))
        nb_of_fail_results = len(list(filter(lambda x: not verification_func(x) and not x.result.is_dirty, states)))
        nb_of_error_results = len(list(filter(lambda x: x.result.is_dirty, states)))
        nb_of_results = nb_of_success_results + nb_of_fail_results + nb_of_error_results
        success_ratio = 0 if nb_of_results == 0 else round((nb_of_success_results / nb_of_results) * 100)
        verification_results.append({
            'experiment_name': experiment_name,
            'browser_name': evaluation_parameters.browser_configuration.browser_name,
            'nb_of_success_results': nb_of_success_results,
            'nb_of_fail_results': nb_of_fail_results,
            'nb_of_error_results': nb_of_error_results,
            'success_ratio': success_ratio,
        })
    return verification_results


def verification_functions() -> dict:
    def all_reproduced(state: State) -> bool:
        if state.result is None:
            return False
        return state.result.reproduced

    def none_reproduced(state: State) -> bool:
        if state.result is None:
            return False
        return not state.result.reproduced

    return {
        'all_reproduced': all_reproduced,
        'none_reproduced': none_reproduced,
        'click': all_reproduced,
    }


