import ast
import logging
from collections import defaultdict
from typing import Callable, Generator

from bughog.database.mongo.mongodb import MongoDB
from bughog.evaluation.experiment_result import ExperimentResult
from bughog.evaluation.experiments import Experiments
from bughog.evaluation.file_structure import Folder
from bughog.integration_tests import evaluation_configurations
from bughog.parameters import EvaluationParameters
from bughog.subject import factory
from bughog.subject.evaluation_framework import EvaluationFramework
from bughog.version_control.state.base import State

TEST_PROJECT_NAME = '_tests'
logger = logging.getLogger(__name__)


def get_all_testable_subject_types() -> Generator[str]:
    for subject_type in factory.get_all_subject_types():
        all_experiments = factory.create_experiments(subject_type)
        if TEST_PROJECT_NAME in all_experiments.get_projects():
            yield subject_type
        else:
            logger.warning(f'Skipping {subject_type} testing, because no "{TEST_PROJECT_NAME} was found.')


def verify_all() -> dict:
    grouped_results = defaultdict(list)
    for subject_type in get_all_testable_subject_types():
        all_experiments = factory.create_experiments(subject_type)
        experiments = all_experiments.get_experiments(TEST_PROJECT_NAME)
        elegible_experiments = [experiment[0] for experiment in experiments if experiment[1]]
        eval_parameters_list = evaluation_configurations.get_eval_parameters_list(subject_type, elegible_experiments)

        for eval_parameters in eval_parameters_list:
            experiment_verification = __verify_experiment(eval_parameters, all_experiments)
            if experiment_verification:
                grouped_results[subject_type].append(experiment_verification)

    # Return list of lists, each sublist for one subject_type
    return grouped_results


def __verify_experiment(eval_parameters: EvaluationParameters, all_experiments: Experiments) -> dict | None:
    experiment_name = eval_parameters.evaluation_range.experiment_name
    experiment_folder = all_experiments.get_experiment_folder(eval_parameters)

    verification_func = __get_verification_function(all_experiments.framework, experiment_folder)
    if verification_func is None:
        return None

    states = MongoDB().get_evaluated_states(eval_parameters, None)
    nb_of_success_results = len(list(filter(lambda x: verification_func(x), states)))
    nb_of_fail_results = len(list(filter(lambda x: not verification_func(x) and not ExperimentResult.poc_is_dirty(x.result_variables), states)))
    nb_of_error_results = len(list(filter(lambda x: ExperimentResult.poc_is_dirty(x.result_variables), states)))
    nb_of_results = nb_of_success_results + nb_of_fail_results + nb_of_error_results
    success_ratio = 0 if nb_of_results == 0 else round((nb_of_success_results / nb_of_results) * 100)

    return {
        'experiment_name': experiment_name,
        'subject_type': eval_parameters.subject_configuration.subject_type,
        'subject_name': eval_parameters.subject_configuration.subject_name,
        'nb_of_success_results': nb_of_success_results,
        'nb_of_fail_results': nb_of_fail_results,
        'nb_of_error_results': nb_of_error_results,
        'success_ratio': success_ratio,
    }


def __get_verification_function(eval_framework: EvaluationFramework, experiment_folder: Folder) -> Callable | None:
    param_name = 'expected_reproducing_versions'
    param_value = eval_framework.get_bughog_poc_parameter(experiment_folder, param_name)

    if param_value is None:
        logger.error(f'Skipping {experiment_folder.name}, because "{param_name}" was not defined.')
        return None

    match param_value:
        case 'all':
            return lambda state: ExperimentResult.poc_is_reproduced(state.result_variables)
        case 'none':
            return lambda state: not ExperimentResult.poc_is_reproduced(state.result_variables)
        case _:
            if type(param_value) is str:
                reproducing_ranges = ast.literal_eval(param_value)
                if type(reproducing_ranges) is list[tuple[int,int]]:
                    return __create_complex_verification_function(reproducing_ranges)

    logger.error(f'Skipping {experiment_folder.name}, because could not parse given "{param_name}".')
    return None


def __create_complex_verification_function(reproducing_ranges: list[tuple[int,int]]) -> Callable:
    def verification_function(state: State):
        for start, end in reproducing_ranges:
            if start <= state.index <= end:
                return ExperimentResult.poc_is_reproduced(state.result_variables)
        return not ExperimentResult.poc_is_reproduced(state.result_variables)

    return verification_function
