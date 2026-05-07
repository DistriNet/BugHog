import pytest

from bughog.subject.state_oracle import StateOracle
from bughog.version_control.version import Version


class TestIsValidCommitId:
    def test_valid_40_lowercase_hex(self):
        assert StateOracle.is_valid_commit_id('a' * 40)
        assert StateOracle.is_valid_commit_id('0123456789abcdef' * 2 + '01234567')

    def test_too_short(self):
        assert not StateOracle.is_valid_commit_id('abc123')

    def test_uppercase_chars_invalid(self):
        assert not StateOracle.is_valid_commit_id('A' * 40)

    def test_special_chars_invalid(self):
        assert not StateOracle.is_valid_commit_id('!' * 40)

    def test_empty_string_invalid(self):
        assert not StateOracle.is_valid_commit_id('')


class TestIsValidCommitNb:
    def test_valid_positive_integer(self):
        assert StateOracle.is_valid_commit_nb(1)
        assert StateOracle.is_valid_commit_nb(12345)

    def test_negative_invalid(self):
        assert not StateOracle.is_valid_commit_nb(-1)

    def test_zero(self):
        assert StateOracle.is_valid_commit_nb(0)


class TestGetFullVersionFromReleaseTag:
    def test_v_prefixed_tag(self):
        assert str(StateOracle.get_full_version_from_release_tag('v100.0.5000')) == '100.0.5000'

    def test_no_prefix(self):
        assert str(StateOracle.get_full_version_from_release_tag('100.0.5000')) == '100.0.5000'

    def test_no_version_returns_none(self):
        assert StateOracle.get_full_version_from_release_tag('latest') is None
        assert StateOracle.get_full_version_from_release_tag('stable') is None

    def test_four_part_version_extracts_all(self):
        # The new regex matches the whole version string
        result = StateOracle.get_full_version_from_release_tag('120.0.6099.109')
        assert str(result) == '120.0.6099.109'


class TestParseCommitNbFromGooglesource:
    def test_refs_heads_main(self):
        html = 'Cr-Commit-Position: refs/heads/main@{#123456}'
        assert StateOracle._parse_commit_nb_from_googlesource(html) == '123456'

    def test_refs_heads_master(self):
        html = 'Cr-Commit-Position: refs/heads/master@{#654321}'
        assert StateOracle._parse_commit_nb_from_googlesource(html) == '654321'

    def test_svn_url(self):
        html = 'svn.chromium.org/chrome/trunk/src@123456 '
        assert StateOracle._parse_commit_nb_from_googlesource(html) == '123456'

    def test_no_match_returns_none(self):
        assert StateOracle._parse_commit_nb_from_googlesource('no relevant content here') is None


class TestGetEarliestTagWithMajor:
    def test_picks_earliest_minor_version(self):
        tags = ['v120.0.5', 'v120.0.1', 'v120.0.10', 'v121.0.0']
        version = Version('120')
        assert StateOracle._get_earliest_tag_version_match(tags, version) == 'v120.0.1'

    def test_ignores_other_major_versions(self):
        tags = ['v119.0.0', 'v121.0.0']
        version = Version('120')
        with pytest.raises(ValueError):
            StateOracle._get_earliest_tag_version_match(tags, version)

    def test_single_candidate(self):
        tags = ['v100.0.0', 'v200.0.0']
        version = Version('100')
        assert StateOracle._get_earliest_tag_version_match(tags, version) == 'v100.0.0'

    def test_empty_list_raises(self):
        version = Version('100')
        with pytest.raises(ValueError):
            StateOracle._get_earliest_tag_version_match([], version)
