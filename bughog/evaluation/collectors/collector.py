import logging
from enum import Enum

from bughog.evaluation.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class Type(Enum):
    REQUESTS = 1
    LOGS = 2


class Collector:
    def __init__(self, subcollectors: list[BaseCollector]) -> None:
        self.subcollectors = subcollectors
        logger.debug(f'Using {len(self.subcollectors)} result collectors')

    def start(self):
        for collector in self.subcollectors:
            collector.start()

    def stop(self):
        for collector in self.subcollectors:
            collector.stop()

    def collect_results(self) -> tuple[dict,dict[str,str]]:
        raw_results = {}
        result_variables = {}
        for collector in self.subcollectors:
            collector.parse_data()
            raw_results.update(collector.data)
            result_variables.update(collector.result_variables)
        return raw_results, result_variables
