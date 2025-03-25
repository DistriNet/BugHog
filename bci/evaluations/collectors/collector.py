import logging
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

    def collect_results(self) -> dict:
        all_data = {}
        for collector in self.collectors:
            collector.parse_data()
            all_data.update(collector.data)
        logger.debug(f'Collected data: {all_data}')
        return all_data
