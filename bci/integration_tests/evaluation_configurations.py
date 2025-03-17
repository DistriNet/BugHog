from bci.evaluations.logic import BrowserConfiguration, EvaluationConfiguration, EvaluationParameters, EvaluationRange, SequenceConfiguration


def get_default_browser_configuration(browser_name: str) -> BrowserConfiguration:
    return BrowserConfiguration(
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
        (25, 130),
        None,
        only_releases,
    )

def get_default_sequence_config() -> SequenceConfiguration:
    return SequenceConfiguration(
        8,
        50,
        None,
        None,
        'comp_search',
    )

def get_default_evaluation_parameters(browser_name: str, mech_group: str, only_releases: bool) -> EvaluationParameters:
    return EvaluationParameters(
        get_default_browser_configuration(browser_name),
        get_default_evaluation_configuration(),
        get_default_evaluation_range(mech_group, only_releases),
        get_default_sequence_config(),
        'integrationtests_' + browser_name
    )

def get_eval_parameters_list(mech_groups: list[str]) -> list[EvaluationParameters]:
    evaluation_parameters_list = []
    for browser_name in ['chromium', 'firefox']:
        for mech_group in mech_groups:
            params = get_default_evaluation_parameters(browser_name, mech_group, True)
            evaluation_parameters_list.append(params)
    return evaluation_parameters_list
