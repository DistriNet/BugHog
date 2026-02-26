from __future__ import annotations

import base64
import logging
import pickle
from dataclasses import asdict, dataclass
from typing import Optional

from bughog.exceptions import MissingParametersError
from bughog.version_control.state.base import ShallowState

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExperimentParameters:
    """
    All parameters required to define an experiment.
    """

    project_name: str
    experiment_name: str
    subject_configuration: SubjectConfiguration
    state: ShallowState
    database_params: DatabaseParameters

    def serialize(self) -> str:
        pickled_bytes = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
        return base64.b64encode(pickled_bytes).decode('ascii')

    @staticmethod
    def deserialize(pickled_str: str) -> ExperimentParameters:
        pickled_bytes = base64.b64decode(pickled_str)
        return pickle.loads(pickled_bytes)


@dataclass(frozen=True)
class EvaluationParameters:
    """
    All parameters required to define an evaluation.
    """

    project_name: str
    experiment_name: str
    subject_configuration: SubjectConfiguration
    evaluation_range: EvaluationRange
    sequence_configuration: SequenceConfiguration
    database_params: DatabaseParameters

    def to_experiment_parameters(self, state: ShallowState) -> ExperimentParameters:
        return ExperimentParameters(
            self.project_name, self.experiment_name, self.subject_configuration, state, self.database_params
        )

    def to_plot_parameters(self, experiment_name: str, dirty_results_allowed: bool = True) -> PlotParameters:
        return PlotParameters(
            self.project_name,
            experiment_name,
            self.subject_configuration,
            self.evaluation_range,
            self.sequence_configuration,
            self.database_params,
            experiment_name,
            dirty_results_allowed,
        )


@dataclass(frozen=True)
class SubjectConfiguration:
    subject_type: str
    subject_name: str
    subject_setting: str
    cli_options: list[str]
    extensions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> SubjectConfiguration:
        return SubjectConfiguration(
            data['subject_type'],
            data['subject_name'],
            data.get('subject_setting', 'default'),
            data.get('cli_options', []),
            data.get('extensions', []),
        )


@dataclass(frozen=True)
class EvaluationRange:
    major_version_range: tuple[int, int] | None = None
    commit_nb_range: tuple[int, int] | None = None
    only_release_commits: bool = False

    def __post_init__(self):
        if self.major_version_range:
            assert self.major_version_range[0] <= self.major_version_range[1]
        elif self.commit_nb_range:
            assert self.commit_nb_range[0] <= self.commit_nb_range[1]
        else:
            raise AttributeError('Evaluation ranges require either major versions or commit numbers')

    @staticmethod
    def from_dict(data: dict) -> EvaluationRange:
        return EvaluationRange(
            EvaluationRange.__get_version_range(data),
            EvaluationRange.__get_commit_nb_range(data),
            data.get('only_release_commits', False),
        )

    @staticmethod
    def __get_version_range(form_data: dict[str, str]) -> tuple[int, int] | None:
        if range := form_data.get('version_range', None):
            if len(range) == 2:
                return (int(range[0]), int(range[1]))
        return None

    @staticmethod
    def __get_commit_nb_range(form_data: dict[str, str]) -> tuple[int, int] | None:
        lower_rev_number = form_data.get('lower_commit_nb', None)
        upper_rev_number = form_data.get('upper_commit_nb', None)
        lower_rev_number = int(lower_rev_number) if lower_rev_number else None
        upper_rev_number = int(upper_rev_number) if upper_rev_number else None
        if lower_rev_number is None or upper_rev_number is None:
            return None
        return (lower_rev_number, upper_rev_number) if lower_rev_number is not None else None


@dataclass(frozen=True)
class SequenceConfiguration:
    nb_of_containers: int
    sequence_limit: int = 10000
    search_strategy: str | None = None

    @staticmethod
    def from_dict(data: dict) -> SequenceConfiguration:
        return SequenceConfiguration(
            int(data.get('nb_of_containers', 1)),
            int(data.get('sequence_limit', 50)),
            data.get('search_strategy', None),
        )


@dataclass(frozen=True)
class DatabaseParameters:
    host: str
    username: str
    password: str
    database_name: str
    executable_cache_limit: int

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> DatabaseParameters:
        return DatabaseParameters(
            data['host'],
            data['username'],
            data['password'],
            data['database_name'],
            data['executable_cache_limit'],
        )

    def __str__(self) -> str:
        return f'{self.username}@{self.host}:27017/{self.database_name}'

    def __repr__(self) -> str:
        return f'{self.username}@{self.host}:27017/{self.database_name}'


@dataclass(frozen=True)
class PlotParameters(EvaluationParameters):
    experiment: Optional[str]
    dirty_results_allowed: bool


def create_evaluation_params(
    kwargs: dict, database_params: DatabaseParameters, only_to_plot=False
) -> list[EvaluationParameters]:
    experiments = set(x for x in kwargs.get('experiments', []) + [kwargs.get('experiment_to_plot')] if x is not None)
    if len(experiments) == 0:
        raise MissingParametersError()

    subject_configuration = SubjectConfiguration.from_dict(kwargs)
    sequence_configuration = SequenceConfiguration.from_dict(kwargs)
    evaluation_params_list = []
    for experiment in sorted(experiments):
        if only_to_plot and experiment != kwargs.get('experiment_to_plot'):
            continue
        evaluation_range = EvaluationRange.from_dict(kwargs)
        evaluation_params = EvaluationParameters(
            kwargs['project_name'],
            experiment,
            subject_configuration,
            evaluation_range,
            sequence_configuration,
            database_params,
        )
        evaluation_params_list.append(evaluation_params)
    return evaluation_params_list


def create_experiment_params(kwargs: dict, database_params: DatabaseParameters) -> ExperimentParameters:
    subject_configuration = SubjectConfiguration.from_dict(kwargs)
    if 'major_version' in kwargs:
        state_type = 'version'
    elif 'commit_nb' in kwargs or 'commit_id' in kwargs:
        state_type = 'commit'
    else:
        raise MissingParametersError(
            'Experiment parameters require either a major version, commit number, or commit id.'
        )
    state = ShallowState(
        state_type,
        kwargs.get('major_version'),
        kwargs.get('commit_nb'),
        kwargs.get('commit_id'),
    )
    return ExperimentParameters(
        kwargs['project_name'], kwargs['poc_name'], subject_configuration, state, database_params
    )


def __get_cookie_name(form_data: dict[str, str]) -> str | None:
    if form_data['check_for'] == 'request':
        return None
    if 'cookie_name' in form_data:
        return form_data['cookie_name']
    return 'generic'
