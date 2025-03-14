import logging
from abc import abstractmethod
from enum import Enum

from bci.evaluations.collectors.base import BaseCollector

from .logs import LogCollector
from .requests import RequestCollector

logger = logging.getLogger(__name__)


class Type(Enum):
    REQUESTS = 1
    LOGS = 2


class Collector:
    def __init__(self, types: list[Type]) -> None:
        self.collectors: list[BaseCollector] = []
        if Type.REQUESTS in types:
            collector = RequestCollector()
            self.collectors.append(collector)
        if Type.LOGS in types:
            collector = LogCollector()
            self.collectors.append(collector)
        logger.debug(f'Using {len(self.collectors)} result collectors')

    def start(self):
        for collector in self.collectors:
            collector.start()

    def stop(self):
        for collector in self.collectors:
            collector.stop()

    def sanity_check_was_successful(self) -> bool:
        all_data = self.collect_results()
        if {'var': 'sanity_check', 'val': 'OK'} in all_data['req_vars']:
            return True
        # We still perform the legacy sanity check
        elif [request for request in all_data['requests'] if 'report/?leak=baseline' in request['url']]:
            return True
        else:
            return False

    def poc_is_likely_reproduced(self) -> bool:
        """
        Returns whether the PoC is likely reproduced by simply checking the `bughog_reproduced` variable.
        If this variable is detected, the evaluation should not need any more retries.

        **Warning**: this method should only be used for performance purposes.
        """
        all_data = self.collect_results()
        return {'var': 'reproduced', 'val': 'OK'} in all_data['req_vars']

    def collect_results(self) -> dict:
        all_data = {}
        for collector in self.collectors:
            collector.parse_data()
            all_data.update(collector.data)
        logger.debug(f'Collected data: {all_data}')
        return all_data
