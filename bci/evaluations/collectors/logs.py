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
        data = self._parse_bughog_variables(log_lines, regex)
        self.data['log_vars'] = data
