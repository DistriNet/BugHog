from bughog.configuration import Global
from bughog.parameters import (
    EvaluationParameters,
    EvaluationRange,
    SequenceConfiguration,
    SubjectConfiguration,
)
from bughog.subject import factory


def get_default_browser_configuration(subject_type: str, subject_name: str) -> SubjectConfiguration:
    return SubjectConfiguration(
        subject_type,
        subject_name,
        'default',
        [],
        [],
    )


def get_default_evaluation_range(mech_group: str, only_releases: bool) -> EvaluationRange:
    return EvaluationRange(
        'IntegrationTests',
        mech_group,
        (20, 136),
        None,
        only_releases,
    )


def get_default_sequence_config(sequence_limit: int) -> SequenceConfiguration:
    return SequenceConfiguration(
        8,
        sequence_limit,
        'comp_search',
    )


def get_default_evaluation_parameters(
    subject_type: str, subject_name: str, mech_group: str, sequence_limit: int = 50, only_releases: bool = True
) -> EvaluationParameters:
    database_params = Global.get_database_params()
    return EvaluationParameters(
        get_default_browser_configuration(subject_type, subject_name),
        get_default_evaluation_range(mech_group, only_releases),
        get_default_sequence_config(sequence_limit),
        database_params,
    )


def get_eval_parameters_list(experiments: list[str]) -> list[EvaluationParameters]:
    evaluation_parameters_list = []
    for subject_type in factory.get_all_subject_types():
        for subject_name in factory.get_all_subject_names_for(subject_type):
            for experiment in experiments:
                if experiment == 'all_reproduced':
                    sequence_limit = 999
                else:
                    sequence_limit = 50
                params = get_default_evaluation_parameters(subject_type, subject_name, experiment, sequence_limit=sequence_limit)
                evaluation_parameters_list.append(params)
    return evaluation_parameters_list
