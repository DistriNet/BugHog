import pytest

from bughog.exceptions import MissingParametersError
from bughog.parameters import (
    DatabaseParameters,
    EvaluationRange,
    ExperimentParameters,
    SequenceConfiguration,
    SubjectConfiguration,
    create_evaluation_params,
    create_experiment_params,
)
from bughog.version_control.state.base import ShallowState


def _db():
    return DatabaseParameters('localhost', 'admin', 'secret', 'bughog', 0)


def _subject():
    return SubjectConfiguration('browser', 'chromium', 'default', [], [])


def _state():
    return ShallowState('commit', None, 100, None)


# --- SubjectConfiguration ---

class TestSubjectConfiguration:
    def test_from_dict_defaults(self):
        config = SubjectConfiguration.from_dict({'subject_type': 'browser', 'subject_name': 'chromium'})
        assert config.subject_setting == 'default'
        assert config.cli_options == []
        assert config.extensions == []

    def test_from_dict_explicit_fields(self):
        config = SubjectConfiguration.from_dict({
            'subject_type': 'js_engine',
            'subject_name': 'v8',
            'subject_setting': 'headless',
            'cli_options': ['--flag'],
            'extensions': ['ext'],
        })
        assert config.subject_setting == 'headless'
        assert config.cli_options == ['--flag']
        assert config.extensions == ['ext']

    def test_to_dict_roundtrip(self):
        data = {
            'subject_type': 'browser',
            'subject_name': 'chromium',
            'subject_setting': 'default',
            'cli_options': [],
            'extensions': [],
        }
        assert SubjectConfiguration.from_dict(data).to_dict() == data


# --- EvaluationRange ---

class TestEvaluationRange:
    def test_version_range(self):
        r = EvaluationRange(major_version_range=(100, 120))
        assert r.major_version_range == (100, 120)
        assert r.commit_nb_range is None

    def test_commit_range(self):
        r = EvaluationRange(commit_nb_range=(1000, 2000))
        assert r.commit_nb_range == (1000, 2000)
        assert r.major_version_range is None

    def test_equal_bounds_allowed(self):
        EvaluationRange(commit_nb_range=(500, 500))

    def test_neither_range_raises(self):
        with pytest.raises(AttributeError):
            EvaluationRange()

    def test_inverted_version_range_raises(self):
        with pytest.raises(AssertionError):
            EvaluationRange(major_version_range=(120, 100))

    def test_inverted_commit_range_raises(self):
        with pytest.raises(AssertionError):
            EvaluationRange(commit_nb_range=(2000, 1000))

    def test_from_dict_version_range(self):
        r = EvaluationRange.from_dict({'version_range': ['100', '120']})
        assert r.major_version_range == (100, 120)

    def test_from_dict_version_range_full_version(self):
        r = EvaluationRange.from_dict({'version_range': ['100.0.1', '120.5.2']})
        assert r.major_version_range == (100, 120)

    def test_from_dict_commit_range(self):
        r = EvaluationRange.from_dict({'lower_commit_nb': '1000', 'upper_commit_nb': '2000'})
        assert r.commit_nb_range == (1000, 2000)

    def test_from_dict_only_release_commits_defaults_false(self):
        r = EvaluationRange.from_dict({'version_range': ['1', '5']})
        assert r.only_release_commits is False

    def test_from_dict_only_release_commits_true(self):
        r = EvaluationRange.from_dict({'version_range': ['1', '5'], 'only_release_commits': True})
        assert r.only_release_commits is True

    def test_from_dict_partial_commit_range_returns_none(self):
        # Only lower bound provided — commit range should be None
        with pytest.raises(AttributeError):
            EvaluationRange.from_dict({'lower_commit_nb': '1000'})


# --- SequenceConfiguration ---

class TestSequenceConfiguration:
    def test_defaults(self):
        config = SequenceConfiguration.from_dict({})
        assert config.nb_of_containers == 1
        assert config.sequence_limit == 50
        assert config.search_strategy is None

    def test_explicit_values(self):
        config = SequenceConfiguration.from_dict({
            'nb_of_containers': '4',
            'sequence_limit': '100',
            'search_strategy': 'bgb',
        })
        assert config.nb_of_containers == 4
        assert config.sequence_limit == 100
        assert config.search_strategy == 'bgb'


# --- DatabaseParameters ---

class TestDatabaseParameters:
    def test_str(self):
        assert str(DatabaseParameters('host', 'user', 'pass', 'db', 0)) == 'user@host:27017/db'

    def test_repr(self):
        assert repr(DatabaseParameters('host', 'user', 'pass', 'db', 0)) == 'user@host:27017/db'

    def test_from_dict_roundtrip(self):
        params = DatabaseParameters('localhost', 'admin', 'secret', 'mydb', 10)
        assert DatabaseParameters.from_dict(params.to_dict()) == params


# --- ExperimentParameters serialization ---

class TestExperimentParametersSerialization:
    def test_serialize_returns_string(self):
        params = ExperimentParameters('proj', 'poc', _subject(), _state(), _db())
        assert isinstance(params.serialize(), str)

    def test_serialize_deserialize_roundtrip(self):
        params = ExperimentParameters('proj', 'poc', _subject(), _state(), _db())
        assert ExperimentParameters.deserialize(params.serialize()) == params


# --- create_experiment_params ---

class TestCreateExperimentParams:
    def _base(self):
        return {
            'subject_type': 'browser',
            'subject_name': 'chromium',
            'project_name': 'test_project',
            'poc_name': 'test_poc',
        }

    def test_with_commit_nb(self):
        data = {**self._base(), 'commit_nb': 12345}
        params = create_experiment_params(data, _db())
        assert params.state.type == 'commit'
        assert params.state.commit_nb == 12345

    def test_with_commit_id(self):
        data = {**self._base(), 'commit_id': 'abc123def'}
        params = create_experiment_params(data, _db())
        assert params.state.type == 'commit'
        assert params.state.commit_id == 'abc123def'

    def test_with_major_version(self):
        data = {**self._base(), 'major_version': 100}
        params = create_experiment_params(data, _db())
        assert params.state.type == 'version'
        assert params.state.major_version == 100

    def test_with_full_version(self):
        data = {**self._base(), 'major_version': '100.0.1234'}
        params = create_experiment_params(data, _db())
        assert params.state.type == 'version'
        assert params.state.major_version == 100

    def test_missing_state_raises(self):
        with pytest.raises(MissingParametersError):
            create_experiment_params(self._base(), _db())

    def test_project_and_poc_stored(self):
        data = {**self._base(), 'commit_nb': 1}
        params = create_experiment_params(data, _db())
        assert params.project_name == 'test_project'
        assert params.experiment_name == 'test_poc'


# --- create_evaluation_params ---

class TestCreateEvaluationParams:
    def _base(self):
        return {
            'subject_type': 'browser',
            'subject_name': 'chromium',
            'project_name': 'test_project',
            'version_range': ['100', '110'],
            'experiments': ['poc1', 'poc2'],
        }

    def test_one_result_per_experiment(self):
        params_list = create_evaluation_params(self._base(), _db())
        assert len(params_list) == 2

    def test_experiments_are_sorted(self):
        data = {**self._base(), 'experiments': ['poc_b', 'poc_a']}
        params_list = create_evaluation_params(data, _db())
        assert [p.experiment_name for p in params_list] == ['poc_a', 'poc_b']

    def test_no_experiments_raises(self):
        data = {
            'subject_type': 'browser',
            'subject_name': 'chromium',
            'project_name': 'test_project',
            'version_range': ['100', '110'],
        }
        with pytest.raises(MissingParametersError):
            create_evaluation_params(data, _db())

    def test_experiment_to_plot_merged(self):
        data = {**self._base(), 'experiments': ['poc1'], 'experiment_to_plot': 'poc2'}
        params_list = create_evaluation_params(data, _db())
        names = {p.experiment_name for p in params_list}
        assert 'poc1' in names and 'poc2' in names

    def test_only_to_plot_filters_others(self):
        data = {**self._base(), 'experiment_to_plot': 'poc1'}
        params_list = create_evaluation_params(data, _db(), only_to_plot=True)
        assert len(params_list) == 1
        assert params_list[0].experiment_name == 'poc1'
