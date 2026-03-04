from bughog.evaluation.collectors.base import BaseCollector


class ConcreteCollector(BaseCollector):
    """Minimal concrete subclass for testing BaseCollector behaviour."""

    def start(self): pass
    def stop(self): pass
    def parse_data(self): pass

    @property
    def raw_data(self): return self.data

    @property
    def result_variables(self): return set()


class TestRegexMutualExclusion:
    def test_set_expected_regex(self):
        c = ConcreteCollector()
        c.set_expected_output_regex(r'SUCCESS')
        assert c.expected_output_regex == r'SUCCESS'
        assert c.unexpected_output_regex is None

    def test_set_unexpected_regex(self):
        c = ConcreteCollector()
        c.set_unexpected_output_regex(r'ERROR')
        assert c.unexpected_output_regex == r'ERROR'
        assert c.expected_output_regex is None

    def test_expected_ignored_if_unexpected_already_set(self):
        c = ConcreteCollector()
        c.set_unexpected_output_regex(r'ERROR')
        c.set_expected_output_regex(r'SUCCESS')
        assert c.expected_output_regex is None

    def test_unexpected_ignored_if_expected_already_set(self):
        c = ConcreteCollector()
        c.set_expected_output_regex(r'SUCCESS')
        c.set_unexpected_output_regex(r'ERROR')
        assert c.unexpected_output_regex is None


class TestParseForExpectedOutput:
    def test_expected_regex_match_adds_reproduced(self):
        c = ConcreteCollector()
        c.set_expected_output_regex(r'SUCCESS')
        c.data['logs'] = ['operation SUCCESS']
        result = set()
        c._parse_for_expected_output(result)
        assert ('reproduced', 'ok') in result

    def test_expected_regex_no_match_does_not_add_reproduced(self):
        c = ConcreteCollector()
        c.set_expected_output_regex(r'SUCCESS')
        c.data['logs'] = ['operation failed']
        result = set()
        c._parse_for_expected_output(result)
        assert ('reproduced', 'ok') not in result

    def test_unexpected_regex_no_match_adds_reproduced(self):
        # When the unexpected pattern is absent, everything is fine → reproduced
        c = ConcreteCollector()
        c.set_unexpected_output_regex(r'ERROR')
        c.data['logs'] = ['everything is fine']
        result = set()
        c._parse_for_expected_output(result)
        assert ('reproduced', 'ok') in result

    def test_unexpected_regex_match_does_not_add_reproduced(self):
        # When the unexpected pattern is present → not reproduced
        c = ConcreteCollector()
        c.set_unexpected_output_regex(r'ERROR')
        c.data['logs'] = ['ERROR: something went wrong']
        result = set()
        c._parse_for_expected_output(result)
        assert ('reproduced', 'ok') not in result

    def test_no_regex_set_does_nothing(self):
        c = ConcreteCollector()
        c.data['logs'] = ['some log line']
        result = set()
        c._parse_for_expected_output(result)
        assert result == set()

    def test_expected_regex_multiple_logs_any_match_sufficient(self):
        c = ConcreteCollector()
        c.set_expected_output_regex(r'SUCCESS')
        c.data['logs'] = ['line one', 'SUCCESS line', 'line three']
        result = set()
        c._parse_for_expected_output(result)
        assert ('reproduced', 'ok') in result
