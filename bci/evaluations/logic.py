from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from typing import Optional

from werkzeug.datastructures import ImmutableMultiDict

from bci.version_control.states.state import State

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
            self.evaluation_range.mech_group,
            self.database_collection,
            database_connection_params
        )

    def create_test_for(self, state: State) -> TestParameters:
        return TestParameters(
            self.browser_configuration, self.evaluation_configuration, state, self.evaluation_range.mech_group, self.database_collection
        )

    def create_plot_params(self, target_mech_id: str, dirty_allowed: bool = True) -> PlotParameters:
        return PlotParameters(
            self.evaluation_range.mech_group,
            target_mech_id,
            self.browser_configuration.browser_name,
            self.database_collection,
            self.evaluation_range.major_version_range,
            self.evaluation_range.revision_number_range,
            self.browser_configuration.browser_setting,
            self.browser_configuration.extensions,
            self.browser_configuration.cli_options,
            dirty_allowed,
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
            data['browser_name'],
            data['browser_setting'],
            data['cli_options'],
            data['extensions']
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
    mech_group: str
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
    mech_group: str
    database_collection: str
    database_connection_params: DatabaseParameters

    def create_test_params(self) -> TestParameters:
        return TestParameters(
            self.browser_configuration, self.evaluation_configuration, self.state, self.mech_group, self.database_collection
        )

    def _to_dict(self):
        return {
            'browser_configuration': self.browser_configuration.to_dict(),
            'evaluation_configuration': self.evaluation_configuration.to_dict(),
            'state': self.state.to_dict(),
            'mech_group': self.mech_group,
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
    def get_database_params(string: str) -> DatabaseParameters:
        data = json.loads(string)
        return  DatabaseParameters.from_dict(data['database_connection_params'])

    @staticmethod
    def deserialize(string: str) -> WorkerParameters:
        data = json.loads(string)
        browser_config = BrowserConfiguration.from_dict(data['browser_configuration'])
        eval_config = EvaluationConfiguration.from_dict(data['evaluation_configuration'])
        state = State.from_dict(data['state'])
        mech_group = data['mech_group']
        database_collection = data['database_collection']
        database_connection_params = DatabaseParameters.from_dict(data['database_connection_params'])
        return WorkerParameters(
            browser_config, eval_config, state, mech_group, database_collection, database_connection_params
        )

    def __str__(self) -> str:
        return f'Eval({self.state}: [{", ".join(self.mech_group)}])'


@dataclass(frozen=True)
class TestParameters:
    browser_configuration: BrowserConfiguration
    evaluation_configuration: EvaluationConfiguration
    state: State
    mech_group: str
    database_collection: str

    def create_test_result_with(self, browser_version: str, binary_origin: str, data: dict, dirty: bool) -> TestResult:
        return TestResult(self, browser_version, binary_origin, data, dirty)

    @staticmethod
    def from_dict(data) -> Optional[TestParameters]:
        if data is None:
            return None
        browser_configuration = BrowserConfiguration.from_dict(data)
        evaluation_configuration = EvaluationConfiguration.from_dict(data)
        state = State.from_dict(data)
        mech_group = data['mech_group']
        database_collection = data['db_collection']
        return TestParameters(browser_configuration, evaluation_configuration, state, mech_group, database_collection)

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


@dataclass(frozen=True)
class PlotParameters:
    mech_group: Optional[str]
    target_mech_id: Optional[str]
    browser_name: Optional[str]
    database_collection: Optional[str]
    major_version_range: Optional[tuple[int,int]] = None
    revision_number_range: Optional[tuple[int,int]] = None
    browser_config: str = 'default'
    extensions: Optional[list[str]] = None
    cli_options: Optional[list[str]] = None
    dirty_allowed: bool = True

    @staticmethod
    def from_dict(data: dict) -> PlotParameters:
        if data.get("lower_version", None) and data.get("upper_version", None):
            major_version_range = (data["lower_version"], data["upper_version"])
        else:
            major_version_range = None
        if data.get("lower_revision_nb", None) and data.get("upper_revision_nb", None):
            revision_number_range = (
                data["lower_revision_nb"],
                data["upper_revision_nb"],
            )
        else:
            revision_number_range = None
        return PlotParameters(
            data.get('plot_mech_group', None),
            data.get('target_mech_id', None),
            data.get('browser_name', None),
            data.get('db_collection', None),
            major_version_range=major_version_range,
            revision_number_range=revision_number_range,
            browser_config=data.get("browser_setting", "default"),
            extensions=data.get("extensions", []),
            cli_options=data.get("cli_options", []),
            dirty_allowed=data.get("dirty_allowed", True),
        )


@staticmethod
def evaluation_factory(kwargs: ImmutableMultiDict) -> list[EvaluationParameters]:
    mech_groups = kwargs.get('tests')
    if mech_groups is None:
        raise MissingParametersException()

    browser_configuration = BrowserConfiguration.from_dict(kwargs)
    evaluation_configuration = EvaluationConfiguration(
        kwargs['project'], kwargs['automation'], int(kwargs.get('seconds_per_visit', 5))
    )
    sequence_configuration = SequenceConfiguration(
        int(kwargs.get('nb_of_containers')),
        int(kwargs.get('sequence_limit')),
        kwargs.get('search_strategy'),
    )
    evaluation_params_list = []
    for mech_group in mech_groups:
        evaluation_range = EvaluationRange(
            mech_group,
            __get_version_range(kwargs),
            __get_revision_number_range(kwargs),
            kwargs.get('only_release_revisions', False),
        )
        database_collection = kwargs.get('db_collection')
        evaluation_params = EvaluationParameters(
            browser_configuration, evaluation_configuration, evaluation_range, sequence_configuration, database_collection
        )
        evaluation_params_list.append(evaluation_params)
    return evaluation_params_list


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


class MissingParametersException(Exception):
    pass
