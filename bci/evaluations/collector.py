from abc import abstractmethod
from enum import Enum
import logging

from bci.evaluations.collectors.base import BaseCollector

from .collectors.requests import RequestCollector
from .collectors.logs import LogCollector

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

    @abstractmethod
    def collect_results(self) -> dict:
        all_data = {}
        for collector in self.collectors:
            all_data.update(collector.data)
        logger.debug(f'Collected data: {all_data}')
        return all_data
