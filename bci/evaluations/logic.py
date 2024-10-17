from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass

from werkzeug.datastructures import ImmutableMultiDict

import bci.browser.cli_options.chromium as cli_options_chromium
import bci.browser.cli_options.firefox as cli_options_firefox
from bci.version_control.states.state import State, StateResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvaluationParameters:
    browser_configuration: BrowserConfiguration
    evaluation_configuration: EvaluationConfiguration
    evaluation_range: EvaluationRange
    sequence_configuration: SequenceConfiguration
    database_collection: str

    def create_worker_params_for(
        self, state: State, database_connection_params: DatabaseParameters) -> WorkerParameters:
        return WorkerParameters(
            self.browser_configuration,
            self.evaluation_configuration,
            state,
            self.evaluation_range.mech_groups,
            self.database_collection,
            database_connection_params
        )

    def create_test_for(self, state: State, mech_group: str) -> TestParameters:
        assert mech_group in self.evaluation_range.mech_groups
        return TestParameters(
            self.browser_configuration, self.evaluation_configuration, state, mech_group, self.database_collection
        )

    def create_plot_params(self, mech_group: str, target_mech_id: str, dirty_allowed: bool = True) -> PlotParameters:
        assert mech_group in self.evaluation_range.mech_groups
        return PlotParameters(
            mech_group,
            target_mech_id,
            self.browser_configuration.browser_name,
            self.database_collection,
            self.evaluation_range.major_version_range,
            self.evaluation_range.revision_number_range,
            self.browser_configuration.browser_setting,
            self.browser_configuration.extensions,
            self.browser_configuration.cli_options,
            dirty_allowed,
            self.sequence_configuration.target_cookie_name,
        )


@dataclass(frozen=True)
class BrowserConfiguration:
    browser_name: str
    browser_setting: str
    cli_options: list[str]
    extensions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> BrowserConfiguration:
        return BrowserConfiguration(
            data['browser_name'], data['browser_setting'], data['cli_options'], data['extensions']
        )


@dataclass(frozen=True)
class EvaluationConfiguration:
    project: str
    automation: str
    seconds_per_visit: int = 5

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> EvaluationConfiguration:
        return EvaluationConfiguration(data['project'], data['automation'], data['seconds_per_visit'])


@dataclass(frozen=True)
class EvaluationRange:
    mech_groups: list[str]
    major_version_range: tuple[int, int] | None = None
    revision_number_range: tuple[int, int] | None = None
    only_release_revisions: bool = False

    def __post_init__(self):
        if self.major_version_range:
            assert self.major_version_range[0] <= self.major_version_range[1]
        elif self.revision_number_range:
            assert self.revision_number_range[0] <= self.revision_number_range[1]
        else:
            raise AttributeError('Evaluation ranges require either major versions or revision numbers')


@dataclass(frozen=True)
class SequenceConfiguration:
    nb_of_containers: int = 8
    sequence_limit: int = 10000
    target_mech_id: str | None = None
    target_cookie_name: str | None = None
    search_strategy: str | None = None


@dataclass(frozen=True)
class DatabaseParameters:
    host: str
    username: str
    password: str
    database_name: str
    binary_cache_limit: int

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> DatabaseParameters:
        return DatabaseParameters(data['host'], data['username'], data['password'], data['database_name'], data['binary_cache_limit'])

    def __str__(self) -> str:
        return f'{self.username}@{self.host}:27017/{self.database_name}'


@dataclass(frozen=True)
class WorkerParameters:
    browser_configuration: BrowserConfiguration
    evaluation_configuration: EvaluationConfiguration
    state: State
    mech_groups: list[str]
    database_collection: str
    database_connection_params: DatabaseParameters

    def create_test_params_for(self, mech_group: str) -> TestParameters:
        assert mech_group in self.mech_groups
        return TestParameters(
            self.browser_configuration, self.evaluation_configuration, self.state, mech_group, self.database_collection
        )

    def create_all_test_params(self) -> list[TestParameters]:
        return [
            TestParameters(
                self.browser_configuration,
                self.evaluation_configuration,
                self.state,
                mech_group,
                self.database_collection,
            )
            for mech_group in self.mech_groups
        ]

    def _to_dict(self):
        return {
            'browser_configuration': self.browser_configuration.to_dict(),
            'evaluation_configuration': self.evaluation_configuration.to_dict(),
            'state': self.state.to_dict(),
            'mech_groups': self.mech_groups,
            'database_collection': self.database_collection,
            'database_connection_params': self.database_connection_params.to_dict()
        }

    def serialize(self) -> str:
        return json.dumps(self._to_dict())

    def __repr__(self) -> str:
        param_dict = self._to_dict()
        # Mask password
        param_dict['database_connection_params']['password'] = '*'
        return json.dumps(param_dict)

    @staticmethod
    def deserialize(string: str) -> WorkerParameters:
        data = json.loads(string)
        browser_config = BrowserConfiguration.from_dict(data['browser_configuration'])
        eval_config = EvaluationConfiguration.from_dict(data['evaluation_configuration'])
        state = State.from_dict(data['state'])
        mech_groups = data['mech_groups']
        database_collection = data['database_collection']
        database_connection_params = DatabaseParameters.from_dict(data['database_connection_params'])
        return WorkerParameters(
            browser_config, eval_config, state, mech_groups, database_collection, database_connection_params
        )

    def __str__(self) -> str:
        return f'Eval({self.state}: [{", ".join(self.mech_groups)}])'


@dataclass(frozen=True)
class TestParameters:
    browser_configuration: BrowserConfiguration
    evaluation_configuration: EvaluationConfiguration
    state: State
    mech_group: str
    database_collection: str

    def create_test_result_with(self, browser_version: str, binary_origin: str, data: dict, dirty: bool) -> TestResult:
        return TestResult(self, browser_version, binary_origin, data, dirty)


@dataclass(frozen=True)
class TestResult:
    params: TestParameters
    browser_version: str
    binary_origin: str
    data: dict
    is_dirty: bool = False
    driver_version: str | None = None

    @property
    def padded_browser_version(self):
        padding_target = 4
        padded_version = []
        for sub in self.browser_version.split('.'):
            if len(sub) > padding_target:
                raise AttributeError(f"Version '{self.browser_version}' is too big to be padded")
            padded_version.append('0' * (padding_target - len(sub)) + sub)
        return '.'.join(padded_version)

    def get_state_result(self) -> StateResult:
        return StateResult.from_dict(self.data, self.is_dirty)


@dataclass(frozen=True)
class PlotParameters:
    mech_group: str
    target_mech_id: str
    browser_name: str
    database_collection: str
    major_version_range: tuple[int] = None
    revision_number_range: tuple[int] = None
    browser_config: str = 'default'
    extensions: list[str] = None
    cli_options: list[str] = None
    dirty_allowed: bool = True
    target_cookie_name: str = None


@staticmethod
def evaluation_factory(kwargs: ImmutableMultiDict) -> EvaluationParameters:
    browser_configuration = BrowserConfiguration(
        kwargs.get('browser_name'), kwargs.get('browser_setting'), __get_cli_arguments(kwargs), __get_extensions(kwargs)
    )
    evaluation_configuration = EvaluationConfiguration(
        kwargs.get('project'), kwargs.get('automation'), int(kwargs.get('seconds_per_visit', 5))
    )
    evaluation_range = EvaluationRange(
        kwargs.get('tests', []),
        __get_version_range(kwargs),
        __get_revision_number_range(kwargs),
        kwargs.get('only_release_revisions', False),
    )
    sequence_configuration = SequenceConfiguration(
        int(kwargs.get('nb_of_containers')),
        int(kwargs.get('sequence_limit')),
        kwargs.get('target_mech_id', None),
        __get_cookie_name(kwargs),
        kwargs.get('search_strategy'),
    )
    database_collection = kwargs.get('db_collection')
    evaluation_params = EvaluationParameters(
        browser_configuration, evaluation_configuration, evaluation_range, sequence_configuration, database_collection
    )
    return evaluation_params


@staticmethod
def __get_cookie_name(form_data: dict[str, str]) -> str | None:
    if form_data['check_for'] == 'request':
        return None
    if 'cookie_name' in form_data:
        return form_data['cookie_name']
    return 'generic'


@staticmethod
def __get_version_range(form_data: dict[str, str]) -> tuple[int, int] | None:
    lower_version = form_data.get('lower_version', None)
    upper_version = form_data.get('upper_version', None)
    lower_version = int(lower_version) if lower_version else None
    upper_version = int(upper_version) if upper_version else None
    assert (lower_version is None) == (upper_version is None)
    return (lower_version, upper_version) if lower_version is not None else None


@staticmethod
def __get_revision_number_range(form_data: dict[str, str]) -> tuple[int, int] | None:
    lower_rev_number = form_data.get('lower_revision_nb', None)
    upper_rev_number = form_data.get('upper_revision_nb', None)
    lower_rev_number = int(lower_rev_number) if lower_rev_number else None
    upper_rev_number = int(upper_rev_number) if upper_rev_number else None
    assert (lower_rev_number is None) == (upper_rev_number is None)
    return (lower_rev_number, upper_rev_number) if lower_rev_number is not None else None


@staticmethod
def __get_extensions(form_data: dict[str, str]) -> list[str]:
    return list(
        map(
            lambda x: x.replace('ext_', ''),
            filter(
                lambda x: x.startswith('ext_') and form_data[x] == 'true',
                form_data.keys(),
            ),
        )
    )


@staticmethod
def __get_cli_arguments(form_data: dict[str, str]) -> list[str]:
    browser = form_data.get('browser_name', None)
    match browser:
        case 'chromium':
            available_cli_options = cli_options_chromium.get_all_cli_options()
        case 'firefox':
            available_cli_options = cli_options_firefox.get_all_cli_options()
        case _:
            raise AttributeError(f"Unknown browser '{browser}'")
    return list(filter(lambda x: x in form_data, available_cli_options))
