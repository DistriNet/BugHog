from __future__ import annotations

import base64
import json
import logging
from dataclasses import asdict, dataclass
import pickle
from typing import Literal, Optional

from werkzeug.datastructures import ImmutableMultiDict


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvaluationParameters:
    """
    All parameters required to define an evaluation.
    """

    subject_configuration: SubjectConfiguration
    evaluation_configuration: EvaluationConfiguration
    evaluation_range: EvaluationRange
    sequence_configuration: SequenceConfiguration
    database_params: DatabaseParameters

    # def create_experiment_params(self, state_params: StateParameters) -> ExperimentParameters:
    #     return ExperimentParameters(
    #         self.subject_configuration,
    #         self.evaluation_configuration,
    #         state_params,
    #         self.evaluation_range.experiment_name,
    #         self.database_params,
    #     )

    def serialize(self) -> str:
        pickled_bytes = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
        return base64.b64encode(pickled_bytes).decode('ascii')

    @staticmethod
    def deserialize(pickled_str: str) -> EvaluationParameters:
        pickled_bytes = base64.b64decode(pickled_str)
        return pickle.loads(pickled_bytes)

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
        return SubjectConfiguration(data['subject_type'], data['subject_name'], data['subject_setting'], data['cli_options'], data['extensions'])


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
    experiment_name: str
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
        return DatabaseParameters(
            data['host'],
            data['username'],
            data['password'],
            data['database_name'],
            data['binary_cache_limit'],
        )

    def __str__(self) -> str:
        return f'{self.username}@{self.host}:27017/{self.database_name}'


# @dataclass(frozen=True)
# class ExperimentParameters:
#     """
#     Parameters that define a single experiment.
#     """
#     subject_configuration: SubjectConfiguration
#     evaluation_configuration: EvaluationConfiguration
#     state_params: StateParameters
#     experiment: str
#     database_params: DatabaseParameters

#     def _to_dict(self):
#         return {
#             'subject_configuration': self.subject_configuration.to_dict(),
#             'evaluation_configuration': self.evaluation_configuration.to_dict(),
#             'state': self.state_params,
#             'experiment': self.experiment,
#             'database_params': self.database_params,
#         }

#     def create_test_result_with(
#         self, subject_version: str, binary_origin: str, data: dict, dirty: bool
#     ) -> ExperimentResult:
#         return ExperimentResult(self, subject_version, binary_origin, data, dirty)

#     @staticmethod
#     def from_dict(data) -> Optional[ExperimentParameters]:
#         if data is None:
#             return None
#         subject_configuration = SubjectConfiguration.from_dict(data)
#         evaluation_configuration = EvaluationConfiguration.from_dict(data)
#         state = StateParameters.from_dict(data)
#         experiment = data['experiment']
#         database_collection = data['db_collection']
#         return ExperimentParameters(
#             subject_configuration, evaluation_configuration, state, experiment, database_collection
#         )

#     def serialize(self) -> str:
#         return json.dumps(self._to_dict())

#     def __repr__(self) -> str:
#         param_dict = self._to_dict()
#         # Mask password
#         param_dict['database_connection_params']['password'] = '*'
#         return json.dumps(param_dict)

#     @staticmethod
#     def get_database_params(string: str) -> DatabaseParameters:
#         data = json.loads(string)
#         return DatabaseParameters.from_dict(data['database_connection_params'])

#     @staticmethod
#     def deserialize(string: str) -> ExperimentParameters:
#         data = json.loads(string)
#         subject_config = SubjectConfiguration.from_dict(data['subject_configuration'])
#         eval_config = EvaluationConfiguration.from_dict(data['evaluation_configuration'])
#         state = StateParameters.from_dict(data['state'])
#         experiment = data['experiment']
#         database_params = DatabaseParameters.from_dict(data['database_params'])
#         return ExperimentParameters(subject_config, eval_config, state, experiment, database_params)

#     def __str__(self) -> str:
#         return f'Eval({self.state_params}: [{", ".join(self.experiment)}])'


# @dataclass(frozen=True)
# class ExperimentResult:
#     params: ExperimentParameters
#     subject_version: str
#     binary_origin: str
#     data: dict
#     is_dirty: bool = False
#     driver_version: str | None = None

#     @property
#     def padded_subject_version(self):
#         padding_target = 4
#         padded_version = []
#         for sub in self.subject_version.split('.'):
#             if len(sub) > padding_target:
#                 raise AttributeError(f"Version '{self.subject_version}' is too big to be padded")
#             padded_version.append('0' * (padding_target - len(sub)) + sub)
#         return '.'.join(padded_version)


# @dataclass(frozen=True)
# class PlotParameters:
#     experiment: Optional[str]
#     subject_name: Optional[str]
#     database_collection: Optional[str]
#     major_version_range: Optional[tuple[int, int]] = None
#     revision_number_range: Optional[tuple[int, int]] = None
#     subject_config: str = 'default'
#     cli_options: Optional[list[str]] = None
#     dirty_allowed: bool = True

#     @staticmethod
#     def from_dict(data: dict) -> PlotParameters:
#         if data.get('lower_version', None) and data.get('upper_version', None):
#             major_version_range = (data['lower_version'], data['upper_version'])
#         else:
#             major_version_range = None
#         if data.get('lower_revision_nb', None) and data.get('upper_revision_nb', None):
#             revision_number_range = (
#                 data['lower_revision_nb'],
#                 data['upper_revision_nb'],
#             )
#         else:
#             revision_number_range = None
#         return PlotParameters(
#             data.get('plot_experiment', None),
#             data.get('target_mech_id', None),
#             data.get('subject_name', None),
#             data.get('db_collection', None),
#             major_version_range=major_version_range,
#             revision_number_range=revision_number_range,
#             subject_config=data.get('subject_setting', 'default'),
#             cli_options=data.get('cli_options', []),
#             dirty_allowed=data.get('dirty_allowed', True),
#        )


# @dataclass(frozen=True)
# class StateParameters:
#     type: Literal['release', 'commit']
#     version_or_commit: int

#     def __post_init__(self):
#         if self.type not in ('release', 'commit'):
#             raise AttributeError("Type should be either 'release' or 'commit'")

#     def to_dict(self) -> dict:
#         return asdict(self)

#     @staticmethod
#     def from_dict(data) -> StateParameters:
#         return StateParameters(data['type'], data['version_or_commit'])


@staticmethod
def evaluation_factory(kwargs: ImmutableMultiDict) -> list[EvaluationParameters]:
    experiments = kwargs.get('tests')
    if experiments is None:
        raise MissingParametersException()

    subject_configuration = SubjectConfiguration.from_dict(kwargs)
    evaluation_configuration = EvaluationConfiguration(
        kwargs['project'], kwargs['automation'], int(kwargs.get('seconds_per_visit', 5))
    )
    sequence_configuration = SequenceConfiguration(
        int(kwargs.get('nb_of_containers')),
        int(kwargs.get('sequence_limit')),
        kwargs.get('search_strategy'),
    )
    evaluation_params_list = []
    for experiment in experiments:
        evaluation_range = EvaluationRange(
            experiment,
            __get_version_range(kwargs),
            __get_revision_number_range(kwargs),
            kwargs.get('only_release_revisions', False),
        )
        database_collection = kwargs.get('db_collection')
        evaluation_params = EvaluationParameters(
            subject_configuration,
            evaluation_configuration,
            evaluation_range,
            sequence_configuration,
            database_collection,
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


class MissingParametersException(Exception):
    pass
