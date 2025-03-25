import re

from .base import BaseCollector


class LogCollector(BaseCollector):

    def __init__(self) -> None:
        super().__init__()
        self.data['log_vars'] = []

    def start(self):
        with open('/tmp/browser.log', 'w') as file:
            file.write('')

    def stop(self):
        pass

    def parse_data(self):
        data = []
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
            data.append({'var': var, 'val': val})
        self.data['log_vars'] = data
