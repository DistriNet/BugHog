from typing import Optional
from urllib.parse import urlparse

from bci.version_control.states.state import StateResult


class StateResultFactory:
    def __init__(self, experiment: Optional[str] = None) -> None:
        self.__experiment = experiment

    def get_result(self, state_result_data: dict) -> StateResult:
        """
        Returns a StateResult object based on the given state result data.
        """
        requests = state_result_data.get('requests', [])
        request_vars = state_result_data.get('req_vars', [])
        log_vars = state_result_data.get('log_vars', [])
        reproduced = self.__is_reproduced(request_vars, log_vars) or self.__is_reproduced_deprecated(requests)
        is_dirty = not reproduced and not (
            self.__sanity_check_was_successful(state_result_data)
            or self.__sanity_check_was_successful_deprecated(state_result_data)
        )
        return StateResult(requests, request_vars, log_vars, is_dirty, reproduced)

    def __sanity_check_was_successful(self, state_result_data: dict) -> bool:
        """
        Returns whether the sanity check was successful.
        """
        return {'var': 'sanity_check', 'val': 'OK'} in state_result_data['req_vars']

    def __sanity_check_was_successful_deprecated(self, state_result_data: dict) -> bool:
        """
        Returns whether the sanity check was successful based on the leak GET parameter (deprecated).
        """
        if self.__experiment is None:
            return False
        requests_to_report_endpoint = [
            request for request in state_result_data['requests'] if 'report/?leak=baseline' in request['url']
        ]
        return len(requests_to_report_endpoint) > 0

    def __is_reproduced(self, request_vars: list, log_vars: list) -> bool:
        """
        Returns whether the PoC is reproduced according to the reproduced variable.
        """
        return {'var': 'reproduced', 'val': 'OK'} in request_vars + log_vars

    def __is_reproduced_deprecated(self, requests: dict) -> bool:
        """
        Returns whether the PoC is reproduced according to the leak GET parameter (deprecated).
        """
        # Because Nginx takes care of all HTTPS traffic, flask (which doubles as proxy) only sees HTTP traffic.
        # Browser <--HTTPS--> Nginx <--HTTP--> Flask
        if self.__experiment is None:
            return False
        valid_report_requests = [
            request
            for request in requests
            if (
                urlparse(request['url']).path in ['/report', '/report/']
                and f'leak={self.__experiment}' in urlparse(request['url']).query
            )
        ]
        return valid_report_requests != []
