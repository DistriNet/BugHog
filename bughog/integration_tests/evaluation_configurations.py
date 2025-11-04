import os

from bughog.configuration import Global
from bughog.integration_tests import verify_results
from bughog.parameters import (
    EvaluationParameters,
    EvaluationRange,
    SequenceConfiguration,
    SubjectConfiguration,
)
from bughog.subject import factory


def get_default_configuration(subject_type: str, subject_name: str) -> SubjectConfiguration:
    return SubjectConfiguration(
        subject_type,
        subject_name,
        'default',
        [],
        [],
    )


def get_default_evaluation_range(subject_type: str, subject_name: str, experiment: str, only_releases: bool) -> EvaluationRange:
    min_version, max_version = factory.get_subject_availability(subject_type, subject_name)
    return EvaluationRange(
        verify_results.TEST_PROJECT_NAME,
        experiment,
        (min_version, max_version),
        None,
        only_releases,
    )


def get_default_sequence_config(sequence_limit: int) -> SequenceConfiguration:
    cpu_count = os.cpu_count()
    return SequenceConfiguration(
        cpu_count if cpu_count is not None else 7,
        sequence_limit,
        'comp_search',
    )


def get_default_evaluation_parameters(subject_type: str, subject_name: str, experiment: str, sequence_limit: int = 100, only_releases: bool = True) -> EvaluationParameters:
    database_params = Global.get_database_params()
    return EvaluationParameters(
        get_default_configuration(subject_type, subject_name),
        get_default_evaluation_range(subject_type, subject_name, experiment, only_releases),
        get_default_sequence_config(sequence_limit),
        database_params,
    )


def get_eval_parameters_list(subject_type: str, experiments: list[str]) -> list[EvaluationParameters]:
    evaluation_parameters_list = []
    for subject_name in factory.get_all_subject_names_for(subject_type):
        for experiment in experiments:
            params = get_default_evaluation_parameters(subject_type, subject_name, experiment, sequence_limit=100)
            evaluation_parameters_list.append(params)
    return evaluation_parameters_list
