import re

from .base import BaseCollector


class LogCollector(BaseCollector):

    def __init__(self) -> None:
        super().__init__()
        self.data['log_vars'] = set()

    def start(self):
        with open('/tmp/browser.log', 'w') as file:
            file.write('')

    def stop(self):
        pass

    def parse_data(self):
        data = set()
        regex = r'\+\+\+bughog_(.+)=(.+)\+\+\+'
        with open('/tmp/browser.log', 'r+') as log_file:
            log_lines = [line for line in log_file.readlines()]
            log_file.write('')
        regex_match_lists = [re.findall(regex, line) for line in log_lines if re.search(regex, line)]
        # Flatten list
        regex_matches = [regex_match for regex_match_list in regex_match_lists for regex_match in regex_match_list]
        for match in regex_matches:
            var = match[0]
            val = match[1]
            data.add({'var': var, 'val': val})
        self.data['log_vars'] = data

    @property
    def raw_data(self) -> dict[str,list]:
        return {'logs': []}

    @property
    def result_variables(self) -> set[tuple[str, str]]:
        return self.data['log_vars']
