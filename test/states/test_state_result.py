import unittest

from bci.evaluations.collectors.collector import Collector, Type
from bci.version_control.state_result_factory import StateResultFactory


class TestCollector(unittest.TestCase):

    @staticmethod
    def get_collector(request_urls: list[str]) -> Collector:
        collector = Collector([Type.REQUESTS])
        requests = [{'url': url} for url in request_urls]
        collector.collectors[0].data['requests'] = requests
        return collector

    def test_request_parsing_1(self):
        collector = TestCollector.get_collector([
            'https://a.test/report/?bughog_reproduced=OK',
            'https://a.test/report/?bughog_sanity_check=OK'
        ])
        state_result_factory = StateResultFactory()

        state_result = state_result_factory.get_result(collector.collect_results())
        assert state_result.reproduced
        assert not state_result.is_dirty

    def test_request_parsing_2(self):
        collector = TestCollector.get_collector([
            'https://a.test/report/?bughog_reproduced=OK'
        ])
        state_result_factory = StateResultFactory()

        state_result = state_result_factory.get_result(collector.collect_results())
        assert state_result.reproduced
        assert not state_result.is_dirty

    def test_request_parsing_3(self):
        collector = TestCollector.get_collector([
            'https://a.test/report/?bughog_sanity_check=OK'
        ])
        state_result_factory = StateResultFactory()

        state_result = state_result_factory.get_result(collector.collect_results())
        assert not state_result.reproduced
        assert not state_result.is_dirty

    def test_request_parsing_4(self):
        collector = TestCollector.get_collector([
            'https://a.test/report/?bughog_bogus=OK'
        ])
        state_result_factory = StateResultFactory()

        state_result = state_result_factory.get_result(collector.collect_results())
        assert not state_result.reproduced
        assert state_result.is_dirty

    def test_request_parsing_5(self):
        collector = TestCollector.get_collector([
            'https://a.test/report/?random_var=bogus&bughog_reproduced=OK',
            'https://a.test/report/?bughog_sanity_check=OK'
        ])
        state_result_factory = StateResultFactory()

        state_result = state_result_factory.get_result(collector.collect_results())
        assert state_result.reproduced
        assert not state_result.is_dirty

    def test_request_parsing_deprecated_1(self):
        experiment = 'exp_name'
        collector = TestCollector.get_collector([
            f'https://a.test/report/?leak={experiment}',
            'https://a.test/report/?leak=baseline'
        ])
        state_result_factory = StateResultFactory(experiment=experiment)

        state_result = state_result_factory.get_result(collector.collect_results())
        assert state_result.reproduced
        assert not state_result.is_dirty

    def test_request_parsing_deprecated_2(self):
        experiment = 'exp_name'
        collector = TestCollector.get_collector([
            f'https://a.test/report/?leak={experiment}'
        ])
        state_result_factory = StateResultFactory(experiment=experiment)

        state_result = state_result_factory.get_result(collector.collect_results())
        assert state_result.reproduced
        assert not state_result.is_dirty

    def test_request_parsing_deprecated_3(self):
        experiment = 'exp_name'
        collector = TestCollector.get_collector([
            'https://a.test/report/?leak=baseline'
        ])
        state_result_factory = StateResultFactory(experiment=experiment)

        state_result = state_result_factory.get_result(collector.collect_results())
        assert not state_result.reproduced
        assert not state_result.is_dirty

    def test_request_parsing_deprecated_4(self):
        experiment = 'exp_name'
        collector = TestCollector.get_collector([
            'https://a.test/report/?leak=not_the_experiment_name',
            'https://a.test/report/?leak=baseline'
        ])
        state_result_factory = StateResultFactory(experiment=experiment)

        state_result = state_result_factory.get_result(collector.collect_results())
        assert not state_result.reproduced
        assert not state_result.is_dirty

    def test_request_parsing_deprecated_5(self):
        experiment = 'exp_name'
        collector = TestCollector.get_collector([
            f'https://a.test/report/?random_var=bogus&leak={experiment}',
            'https://a.test/report/?leak=baseline'
        ])
        state_result_factory = StateResultFactory(experiment=experiment)

        state_result = state_result_factory.get_result(collector.collect_results())
        assert state_result.reproduced
        assert not state_result.is_dirty
