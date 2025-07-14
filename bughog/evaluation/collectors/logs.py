import re

from .base import BaseCollector


class LogCollector(BaseCollector):
    log_path = '/tmp/bughog_eval.log'

    def __init__(self) -> None:
        super().__init__()
        self.data['logs'] = []
        self.data['log_vars'] = set()

    def start(self):
        with open(self.log_path, 'w') as file:
            file.write('')

    def stop(self):
        pass

    def parse_data(self):
        data = set()
        regex = r'bughog_(.+)=(.+)'
        with open(self.log_path, 'r+') as log_file:
            self.data['logs'] = [line.strip() for line in log_file.readlines()]
        regex_match_lists = [re.findall(regex, line) for line in self.data['logs'] if re.search(regex, line)]
        # Flatten list
        regex_matches = [regex_match for regex_match_list in regex_match_lists for regex_match in regex_match_list]
        for match in regex_matches:
            var = match[0]
            val = match[1]
            data.add((var, val))
        self.data['log_vars'] = data

    @property
    def raw_data(self) -> dict[str,list]:
        return {'logs': self.data['logs']}

    @property
    def result_variables(self) -> set[tuple[str, str]]:
        return self.data['log_vars']
