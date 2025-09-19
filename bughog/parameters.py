from __future__ import annotations

import base64
import logging
import pickle
from dataclasses import asdict, dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvaluationParameters:
    """
    All parameters required to define an evaluation.
    """

    subject_configuration: SubjectConfiguration
    evaluation_range: EvaluationRange
    sequence_configuration: SequenceConfiguration
    database_params: DatabaseParameters

    def serialize(self) -> str:
        pickled_bytes = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
        return base64.b64encode(pickled_bytes).decode("ascii")

    @staticmethod
    def deserialize(pickled_str: str) -> EvaluationParameters:
        pickled_bytes = base64.b64decode(pickled_str)
        return pickle.loads(pickled_bytes)

    def to_plot_parameters(self, experiment_name: str, dirty_results_allowed: bool = True) -> PlotParameters:
        return PlotParameters(
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
        return SubjectConfiguration(data["subject_type"], data["subject_name"], data["subject_setting"], data["cli_options"], data["extensions"])


@dataclass(frozen=True)
class EvaluationRange:
    project_name: str
    experiment_name: str
    major_version_range: tuple[int, int] | None = None
    commit_nb_range: tuple[int, int] | None = None
    only_release_commits: bool = False

    def __post_init__(self):
        if self.major_version_range:
            assert self.major_version_range[0] <= self.major_version_range[1]
        elif self.commit_nb_range:
            assert self.commit_nb_range[0] <= self.commit_nb_range[1]
        else:
            raise AttributeError("Evaluation ranges require either major versions or commit numbers")


@dataclass(frozen=True)
class SequenceConfiguration:
    nb_of_containers: int
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
            data["host"],
            data["username"],
            data["password"],
            data["database_name"],
            data["binary_cache_limit"],
        )

    def __str__(self) -> str:
        return f"{self.username}@{self.host}:27017/{self.database_name}"

    def __repr__(self) -> str:
        return f"{self.username}@{self.host}:27017/{self.database_name}"


@dataclass(frozen=True)
class PlotParameters(EvaluationParameters):
    experiment: Optional[str]
    dirty_results_allowed: bool
    # subject_name: Optional[str]
    # database_collection: Optional[str]
    # major_version_range: Optional[tuple[int, int]] = None
    # revision_number_range: Optional[tuple[int, int]] = None
    # subject_config: str = 'default'
    # cli_options: Optional[list[str]] = None
    # dirty_allowed: bool = True

    # @staticmethod
    # def from_dict(data: dict) -> PlotParameters:
    #     if data.get('lower_version', None) and data.get('upper_version', None):
    #         major_version_range = (data['lower_version'], data['upper_version'])
    #     else:
    #         major_version_range = None
    #     if data.get('lower_revision_nb', None) and data.get('upper_revision_nb', None):
    #         revision_number_range = (
    #             data['lower_revision_nb'],
    #             data['upper_revision_nb'],
    #         )
    #     else:
    #         revision_number_range = None
    #     return PlotParameters(
    #         data.get('plot_experiment', None),
    #         data.get('target_mech_id', None),
    #         data.get('subject_name', None),
    #         data.get('db_collection', None),
    #         major_version_range=major_version_range,
    #         revision_number_range=revision_number_range,
    #         subject_config=data.get('subject_setting', 'default'),
    #         cli_options=data.get('cli_options', []),
    #         dirty_allowed=data.get('dirty_allowed', True),
    #    )



@staticmethod
def evaluation_factory(kwargs: dict, database_params: DatabaseParameters, only_to_plot=False) -> list[EvaluationParameters]:
    experiments = set(x for x in kwargs.get("experiments", []) + [kwargs.get("experiment_to_plot")] if x is not None)
    if len(experiments) == 0:
        raise MissingParametersException()

    subject_configuration = SubjectConfiguration.from_dict(kwargs)
    sequence_configuration = SequenceConfiguration(
        int(kwargs.get("nb_of_containers", 1)),
        int(kwargs.get("sequence_limit", 50)),
        kwargs.get("search_strategy"),
    )
    evaluation_params_list = []
    for experiment in sorted(experiments):
        if only_to_plot and experiment != kwargs.get('experiment_to_plot'):
            continue
        evaluation_range = EvaluationRange(
            kwargs["project_name"],
            experiment,
            __get_version_range(kwargs),
            __get_commit_nb_range(kwargs),
            kwargs.get("only_release_commits", False),
        )
        evaluation_params = EvaluationParameters(
            subject_configuration,
            evaluation_range,
            sequence_configuration,
            database_params,
        )
        evaluation_params_list.append(evaluation_params)
    return evaluation_params_list


@staticmethod
def __get_cookie_name(form_data: dict[str, str]) -> str | None:
    if form_data["check_for"] == "request":
        return None
    if "cookie_name" in form_data:
        return form_data["cookie_name"]
    return "generic"


@staticmethod
def __get_version_range(form_data: dict[str, str]) -> tuple[int, int] | None:
    lower_version = form_data.get("lower_version", None)
    upper_version = form_data.get("upper_version", None)
    lower_version = int(lower_version) if lower_version else None
    upper_version = int(upper_version) if upper_version else None
    if lower_version is None or upper_version is None:
        return None
    return (lower_version, upper_version) if lower_version is not None else None


@staticmethod
def __get_commit_nb_range(form_data: dict[str, str]) -> tuple[int, int] | None:
    lower_rev_number = form_data.get("lower_commit_nb", None)
    upper_rev_number = form_data.get("upper_commit_nb", None)
    lower_rev_number = int(lower_rev_number) if lower_rev_number else None
    upper_rev_number = int(upper_rev_number) if upper_rev_number else None
    if lower_rev_number is None or upper_rev_number is None:
        return None
    return (lower_rev_number, upper_rev_number) if lower_rev_number is not None else None


class MissingParametersException(Exception):
    pass
