import time
import unittest

import requests

from bughog.evaluation.collectors.collector import Collector, Type


class TestCollector(unittest.TestCase):
    @staticmethod
    def test_start_stop():
        collector = Collector([Type.REQUESTS])
        results = collector.collect_result_result_variables()
        assert results['requests'] == []
        assert results['req_vars'] == []

        collector.start()
        time.sleep(2)
        collector.stop()

        results = collector.collect_result_result_variables()
        assert results['requests'] == []
        assert results['req_vars'] == []
        time.sleep(1)
        # Port should be freed

        collector.start()
        time.sleep(2)
        collector.stop()

    @staticmethod
    def test_requests():
        collector = Collector([Type.REQUESTS])
        collector.start()
        response_data = {'url': 'bughog_testvar=123', 'method': 'GET', 'headers': [], 'content': 'test'}
        requests.post('http://localhost:5001', json=response_data)
        time.sleep(1)
        collector.stop()
        results = collector.collect_result_result_variables()
        assert results['requests'] == [response_data]
