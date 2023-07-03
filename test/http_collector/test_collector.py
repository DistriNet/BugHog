import time
import unittest

import requests

from bci.http.collector import Collector


class TestCollector(unittest.TestCase):

    @staticmethod
    def test_start_stop():
        collector = Collector()
        assert collector.requests == []

        collector.start()
        time.sleep(2)
        collector.stop()

        assert collector.requests == []
        time.sleep(1)
        # Port should be freed

        collector.start()
        time.sleep(2)
        collector.stop()

    @staticmethod
    def test_requests():
        collector = Collector()
        collector.start()
        requests.post('http://localhost:5001', json={'test': 'test'})
        time.sleep(1)
        collector.stop()
        assert collector.requests == [{'test': 'test'}]
