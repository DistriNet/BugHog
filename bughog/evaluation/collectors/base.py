import logging
import re
from abc import abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseCollector:
    def __init__(self) -> None:
        self.data = {}
        self.expected_output_regex = None
        self.unexpected_output_regex = None

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def parse_data(self):
        pass

    @property
    @abstractmethod
    def raw_data(self) -> dict[str,list]:
        pass

    @property
    @abstractmethod
    def result_variables(self) -> set[tuple[str,str]]:
        pass

    def set_expected_output_regex(self, regex: Optional[str]) -> None:
        if self.unexpected_output_regex:
            logger.error('Ignoring expected output regex because unexpected output regex is already set.')
        else:
            self.expected_output_regex = regex

    def set_unexpected_output_regex(self, regex: Optional[str]) -> None:
        if self.expected_output_regex:
            logger.error('Ignoring unexpected output regex because expected output regex is already set.')
        else:
            self.unexpected_output_regex = regex

    def _parse_for_expected_output(self, data) -> None:
        assert not (self.expected_output_regex and self.unexpected_output_regex)
        if self.expected_output_regex:
            if [line for line in self.data['logs'] if re.search(self.expected_output_regex, line)]:
                data.add(('reproduced', 'ok'))
        elif self.unexpected_output_regex:
            if not [line for line in self.data['logs'] if re.search(self.unexpected_output_regex, line)]:
                data.add(('reproduced', 'ok'))
