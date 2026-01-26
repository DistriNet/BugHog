import unittest

from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.collectors.requests import RequestCollector
from bughog.evaluation.experiment_result import ExperimentResult


class TestCollector(unittest.TestCase):
    @staticmethod
    def get_collector(request_urls: list[str]) -> Collector:
        collector = Collector([RequestCollector()])
        requests = [{'url': url} for url in request_urls]
        collector.subcollectors[0].data['requests'] = requests
        return collector

    def test_request_parsing_1(self):
        collector = TestCollector.get_collector(
            ['https://a.test/report/?bughog_reproduced=OK', 'https://a.test/report/?bughog_sanity_check=OK']
        )

        _, variables = collector.collect_results()
        assert ExperimentResult.poc_is_reproduced(variables)
        assert not ExperimentResult.poc_is_dirty(variables)

    def test_request_parsing_2(self):
        collector = TestCollector.get_collector(['https://a.test/report/?bughog_reproduced=OK'])

        _, variables = collector.collect_results()
        assert ExperimentResult.poc_is_reproduced(variables)
        assert not ExperimentResult.poc_is_dirty(variables)

    def test_request_parsing_3(self):
        collector = TestCollector.get_collector(['https://a.test/report/?bughog_sanity_check=OK'])

        _, variables = collector.collect_results()
        assert not ExperimentResult.poc_is_reproduced(variables)
        assert not ExperimentResult.poc_is_dirty(variables)

    def test_request_parsing_4(self):
        collector = TestCollector.get_collector(['https://a.test/report/?bughog_bogus=OK'])

        _, variables = collector.collect_results()
        assert not ExperimentResult.poc_is_reproduced(variables)
        assert ExperimentResult.poc_is_dirty(variables)

    def test_request_parsing_5(self):
        collector = TestCollector.get_collector(
            [
                'https://a.test/report/?random_var=bogus&bughog_reproduced=OK',
                'https://a.test/report/?bughog_sanity_check=OK',
            ]
        )

        _, variables = collector.collect_results()
        assert ExperimentResult.poc_is_reproduced(variables)
        assert not ExperimentResult.poc_is_dirty(variables)
