from bughog.parameters import (
    EvaluationConfiguration,
    EvaluationParameters,
    EvaluationRange,
    SequenceConfiguration,
    SubjectConfiguration,
)


def get_default_browser_configuration(browser_name: str) -> SubjectConfiguration:
    return SubjectConfiguration(
        browser_name,
        'default',
        [],
        [],
    )


def get_default_evaluation_configuration() -> EvaluationConfiguration:
    return EvaluationConfiguration(
        'IntegrationTests',
        'terminal',
    )


def get_default_evaluation_range(mech_group: str, only_releases: bool) -> EvaluationRange:
    return EvaluationRange(
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
    browser_name: str, mech_group: str, sequence_limit: int = 50, only_releases: bool = True
) -> EvaluationParameters:
    return EvaluationParameters(
        get_default_browser_configuration(browser_name),
        get_default_evaluation_configuration(),
        get_default_evaluation_range(mech_group, only_releases),
        get_default_sequence_config(sequence_limit),
        'integrationtests_' + browser_name,
    )


def get_eval_parameters_list(mech_groups: list[str]) -> list[EvaluationParameters]:
    evaluation_parameters_list = []
    for browser_name in ['chromium', 'firefox']:
        for mech_group in mech_groups:
            if mech_group == 'all_reproduced':
                sequence_limit = 999
            else:
                sequence_limit = 50
            params = get_default_evaluation_parameters(browser_name, mech_group, sequence_limit=sequence_limit)
            evaluation_parameters_list.append(params)
    return evaluation_parameters_list
