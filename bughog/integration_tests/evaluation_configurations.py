import os

from bughog import config
from bughog.integration_tests import verify_results
from bughog.parameters import (
    EvaluationParameters,
    EvaluationRange,
    SequenceConfiguration,
    SubjectConfiguration,
)
from bughog.subject import factory
from bughog.version_control.version import Version


def get_default_configuration(subject_type: str, subject_name: str) -> SubjectConfiguration:
    return SubjectConfiguration(
        subject_type,
        subject_name,
        'default',
        [],
        [],
    )


def get_default_evaluation_range(
    subject_type: str, subject_name: str, experiment: str, only_releases: bool
) -> EvaluationRange:
    subject_availability = factory.get_subject_availability(subject_type, subject_name)
    min_version = subject_availability['min_version']
    max_version = subject_availability['max_version']
    versions = subject_availability['available_versions']

    assert isinstance(min_version, (str, int))
    assert isinstance(max_version, (str, int))
    assert isinstance(versions, list)

    return EvaluationRange(
        (Version(min_version), Version(max_version)),
        [Version(v) for v in versions],
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


def get_default_evaluation_parameters(
    subject_type: str, subject_name: str, experiment: str, sequence_limit: int = 100, only_releases: bool = True
) -> EvaluationParameters:
    database_params = config.get_database_params()
    return EvaluationParameters(
        verify_results.TEST_PROJECT_NAME,
        experiment,
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
