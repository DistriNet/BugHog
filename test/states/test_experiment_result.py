import pytest

from bughog.evaluation.experiment_result import ExperimentResult
from bughog.version_control.version import Version


def _make_result(result_variables, executable_version='100.0.1.1'):
    return ExperimentResult(
        executable_version=Version(executable_version) if executable_version else None,
        executable_origin='public',
        state={'type': 'commit', 'commit_nb': 1},
        raw_results={},
        result_variables=result_variables,
        is_dirty=False,
    )


class TestPocIsReproduced:
    def test_reproduced_ok(self):
        assert ExperimentResult.poc_is_reproduced({('reproduced', 'ok')})

    def test_case_insensitive(self):
        assert ExperimentResult.poc_is_reproduced({('REPRODUCED', 'OK')})

    def test_not_reproduced(self):
        assert not ExperimentResult.poc_is_reproduced({('reproduced', 'nok')})

    def test_none_returns_false(self):
        assert not ExperimentResult.poc_is_reproduced(None)

    def test_empty_set_returns_false(self):
        assert not ExperimentResult.poc_is_reproduced(set())

    def test_instance_property_matches_static(self):
        result = _make_result({('reproduced', 'ok')})
        assert result.is_reproduced == ExperimentResult.poc_is_reproduced(result.result_variables)


class TestPocPassedSanityCheck:
    def test_sanity_check_ok(self):
        assert ExperimentResult.poc_passed_sanity_check({('sanity_check', 'ok')})

    def test_case_insensitive(self):
        assert ExperimentResult.poc_passed_sanity_check({('SANITY_CHECK', 'OK')})

    def test_sanity_check_failed(self):
        assert not ExperimentResult.poc_passed_sanity_check({('sanity_check', 'nok')})

    def test_none_returns_false(self):
        assert not ExperimentResult.poc_passed_sanity_check(None)


class TestPocIsDirty:
    def test_dirty_when_neither_reproduced_nor_sanity(self):
        assert ExperimentResult.poc_is_dirty({('bogus', 'value')})

    def test_not_dirty_when_reproduced(self):
        assert not ExperimentResult.poc_is_dirty({('reproduced', 'ok')})

    def test_not_dirty_when_sanity_check_passes(self):
        assert not ExperimentResult.poc_is_dirty({('sanity_check', 'ok')})

    def test_none_is_dirty(self):
        assert ExperimentResult.poc_is_dirty(None)

    def test_empty_set_is_dirty(self):
        assert ExperimentResult.poc_is_dirty(set())


class TestPaddedSubjectVersion:
    def test_standard_four_part_version(self):
        result = _make_result(set(), executable_version='100.0.1.1')
        assert result.padded_subject_version == '0100.0000.0001.0001'

    def test_single_segment(self):
        result = _make_result(set(), executable_version='5')
        assert result.padded_subject_version == '0005'

    def test_segment_too_long_raises(self):
        result = _make_result(set(), executable_version='12345.0.0.0')
        with pytest.raises(ValueError):
            _ = result.padded_subject_version

    def test_none_version_raises(self):
        result = _make_result(set(), executable_version=None)
        with pytest.raises(ValueError):
            _ = result.padded_subject_version

    def test_already_padded(self):
        result = _make_result(set(), executable_version='0001.0002.0003.0004')
        assert result.padded_subject_version == '0001.0002.0003.0004'

    def test_version_with_hash_suffix(self):
        result = _make_result(set(), executable_version='0.0.1-abc123f')
        assert result.padded_subject_version == '0000.0000.0001-abc123f'


class TestToDict:
    def test_contains_expected_keys(self):
        result = _make_result({('reproduced', 'ok')})
        d = result.to_dict()
        assert set(d.keys()) == {
            'executable_version',
            'executable_origin',
            'state',
            'raw_results',
            'result_variables',
            'is_dirty',
        }

    def test_result_variables_serialized_as_list(self):
        result = _make_result({('reproduced', 'ok')})
        assert isinstance(result.to_dict()['result_variables'], list)
