import time
import unittest

import requests

from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.collectors.requests import RequestCollector


class TestCollector(unittest.TestCase):
    @staticmethod
    def test_start_stop():
        collector = Collector([RequestCollector()])
        raw_results, variables = collector.collect_results()
        assert raw_results['requests'] == []
        assert variables == set()

        collector.start()
        time.sleep(2)
        collector.stop()

        raw_results, variables = collector.collect_results()
        assert raw_results['requests'] == []
        assert variables == set()
        time.sleep(1)
        # Port should be freed

        collector.start()
        time.sleep(2)
        collector.stop()

    @staticmethod
    def test_requests():
        collector = Collector([RequestCollector()])
        collector.start()
        response_data = {'url': 'https://leak.test/report/?bughog_testvar=123', 'method': 'GET', 'headers': [], 'content': 'test'}
        requests.post('http://localhost:5001', json=response_data)
        time.sleep(1)
        collector.stop()
        raw_results, variables = collector.collect_results()
        assert raw_results['requests'] == [response_data]
        assert len(variables) == 1 and ('testvar', '123') in variables
