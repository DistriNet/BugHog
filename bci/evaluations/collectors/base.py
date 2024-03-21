import re
from abc import abstractmethod


class BaseCollector:

    def __init__(self) -> None:
        self.data = {}

    @abstractmethod
    def start():
        pass

    @abstractmethod
    def stop():
        pass

    @staticmethod
    def _parse_bughog_variables(raw_log_lines: list[str], regex) -> list[tuple[str, str]]:
        '''
        Parses the given `raw_log_lines` for matches against the given `regex`.
        '''
        data = []
        regex_match_lists = [re.findall(regex, line) for line in raw_log_lines if re.search(regex, line)]
        # Flatten list
        regex_matches = [regex_match for regex_match_list in regex_match_lists for regex_match in regex_match_list]
        for match in regex_matches:
            var = match[0]
            val = match[1]
            BaseCollector._add_val_var_pair(var, val, data)
        return data


    @staticmethod
    def _add_val_var_pair(var: str, val: str, data: list) -> list:
        for entry in data:
            if entry['var'] == var and entry['val'] == val:
                return data
        data.append({
            'var': var,
            'val': val
        })
