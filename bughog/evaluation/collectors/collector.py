import logging
from typing import Optional

from bughog.evaluation.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


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

    def set_expected_output_regex(self, regex: Optional[str]):
        for collector in self.subcollectors:
            collector.set_expected_output_regex(regex)

    def collect_results(self) -> tuple[dict,set[tuple[str,str]]]:
        raw_results = {}
        result_variables = set()
        for collector in self.subcollectors:
            collector.parse_data()
            raw_results.update(collector.raw_data)
            result_variables.update(collector.result_variables)
        return raw_results, result_variables
