from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from bughog.database.mongo.mongodb import MongoDB
from bughog.exceptions import UserError
from bughog.parameters import EvaluationParameters
from bughog.subject import factory
from bughog.subject.state_oracle import StateOracle
from bughog.version_control.state.base import ShallowState, State
from bughog.version_control.state.commit_state import CommitState
from bughog.version_control.state.release_state import ReleaseState
from bughog.version_control.version import Version


class StateFactory(ABC):
    def __init__(self, oracle: StateOracle, eval_params: EvaluationParameters) -> None:
        self._oracle = oracle
        self._eval_params = eval_params
        self.boundary_states: tuple[State, State] = self._create_boundary_states()

    @abstractmethod
    def _create_boundary_states(self) -> tuple[State, State]:
        pass

    @abstractmethod
    def create_state(self, index: int) -> State:
        pass

    @abstractmethod
    def create_state_from_dict(self, state_dict: dict) -> State:
        pass

    def create_evaluated_state(self, state_dict: dict) -> State:
        state = self.create_state_from_dict(state_dict)
        state.result_variables = set(tuple(item) for item in state_dict['result']['variables'])
        state.result_attempt = state_dict['result'].get('attempt', 1)
        return state

    def create_evaluated_states(self, dirty: bool | None = None) -> Iterator[State]:
        for state_dict in MongoDB().get_evaluated_states(self._eval_params, self.boundary_states, dirty=dirty):
            yield self.create_evaluated_state(state_dict)


class ReleaseStateFactory(StateFactory):
    def _create_boundary_states(self) -> tuple[ReleaseState, ReleaseState]:
        versions = self._eval_params.evaluation_range.versions
        if not versions:
            raise UserError(f'No release versions found in the given range for {self._oracle.subject_name}.')
        if self._oracle.only_artisanal and self._oracle.count_artisanal_executables('release') < 2:
            raise UserError(f'Not enough artisanal release executables provided for {self._oracle.subject_name}.')
        return (
            self.create_state(0),
            self.create_state(len(versions) - 1),
        )

    def create_state(self, index: int) -> ReleaseState:
        versions = self._eval_params.evaluation_range.versions
        if not versions:
            raise UserError('ReleaseStateFactory requires a list of versions.')
        return ReleaseState(self._oracle, versions[index], index=index)

    def create_state_from_dict(self, state_dict: dict) -> ReleaseState:
        all_versions = self._eval_params.evaluation_range.versions
        assert all_versions is not None, 'ReleaseStateFactory requires a list of versions.'

        state = state_dict.get('state', {})
        commit_nb = state.get('commit_nb')
        commit_id = state.get('commit_id')
        # Prefer 'version' (present for 0.x.y releases like Servo). Fall back to 'major_version'
        # for backwards compatibility with older documents that only stored the integer major version.
        raw_version = state.get('version') if state.get('version') is not None else state.get('major_version')
        if raw_version is not None:
            release_version = Version(str(raw_version))
        else:
            raise ValueError('Release states must have a version.')

        index = all_versions.index(release_version)
        return ReleaseState(self._oracle, release_version, index, commit_nb, commit_id)


class CommitStateFactory(StateFactory):
    def _create_boundary_states(self) -> tuple[CommitState, CommitState]:
        eval_range = self._eval_params.evaluation_range
        if self._oracle.only_artisanal and self._oracle.count_artisanal_executables('commit') < 2:
            raise UserError(f'Not enough artisanal commit executables provided for {self._oracle.subject_name}.')
        if eval_range.versions:
            nb_of_versions = len(eval_range.versions)
            first_state = ReleaseState(self._oracle, eval_range.versions[0], index=0).convert_to_commit_state()
            last_release = ReleaseState(self._oracle, eval_range.versions[-1], index=nb_of_versions - 1)
            if self._oracle.get_latest_supported_release_version().major == last_release.index:
                last_state = CommitState(self._oracle, commit_nb=self._oracle.get_most_recent_commit_nb())
            else:
                last_state = last_release.convert_to_commit_state()
            return first_state, last_state
        elif eval_range.version_range:
            first_state = ReleaseState(self._oracle, eval_range.version_range[0]).convert_to_commit_state()
            last_release = ReleaseState(self._oracle, eval_range.version_range[1])
            if self._oracle.get_latest_supported_release_version().major == last_release.index:
                last_state = CommitState(self._oracle, commit_nb=self._oracle.get_most_recent_commit_nb())
            else:
                last_state = last_release.convert_to_commit_state()
            return first_state, last_state
        elif eval_range.commit_nb_range:
            return (
                CommitState(self._oracle, commit_nb=eval_range.commit_nb_range[0]),
                CommitState(self._oracle, commit_nb=eval_range.commit_nb_range[1]),
            )
        raise ValueError('CommitStateFactory requires a version_range or commit_nb_range.')

    def create_state(self, index: int) -> CommitState:
        return CommitState(self._oracle, commit_nb=index)

    def create_state_from_dict(self, state_dict: dict) -> CommitState:
        commit_nb = state_dict.get('state', {}).get('commit_nb')
        commit_id = state_dict.get('state', {}).get('commit_id')
        return CommitState(self._oracle, commit_nb=commit_nb, commit_id=commit_id)


def create_state_factory(eval_params: EvaluationParameters) -> StateFactory:
    subject = factory.get_subject_from_params(eval_params.subject_configuration)
    if eval_params.evaluation_range.only_release_commits:
        return ReleaseStateFactory(subject.state_oracle, eval_params)
    return CommitStateFactory(subject.state_oracle, eval_params)


def create_state_from_shallow_state(shallow_state: ShallowState, subject_type: str, subject_name: str) -> State:
    subject_class = factory.get_subject(subject_type, subject_name)
    oracle = subject_class.state_oracle
    commit_nb = shallow_state.commit_nb
    commit_id = shallow_state.commit_id
    match shallow_state.type:
        case 'commit':
            return CommitState(oracle, commit_nb=commit_nb, commit_id=commit_id)
        case 'release':
            version = shallow_state.version
            if version is None:
                raise ValueError('Release states must have a version.')
            return ReleaseState(oracle, version, commit_nb=commit_nb, commit_id=commit_id)
        case _:
            raise Exception(f'Unknown state type: {shallow_state.type}')
