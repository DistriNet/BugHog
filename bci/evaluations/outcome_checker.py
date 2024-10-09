import re

from bci.evaluations.logic import SequenceConfiguration, StateResult
from bci.version_control.states.state import State


class OutcomeChecker:

    def __init__(self, sequence_config: SequenceConfiguration):
        self.sequence_config = sequence_config

    def get_outcome(self, state: State) -> bool | None:
        '''
        Returns the outcome of the test result.

        - None in case of an error.
        - True if the test was reproduced.
        - False if the test was not reproduced.
        '''
        result = state.result
        if result.is_dirty:
            return None
        if result.reproduced:
            return True
        # Backwards compatibility
        if self.sequence_config.target_mech_id:
            return self.__get_outcome_for_proxy(result)

    def __get_outcome_for_proxy(self, result: StateResult) -> bool | None:
        target_mech_id = self.sequence_config.target_mech_id
        target_cookie = self.sequence_config.target_cookie_name
        requests = result.requests
        if requests is None:
            return None
        # DISCLAIMER:
        # Because Nginx takes care of all HTTPS traffic, flask (which doubles as proxy) only sees HTTP traffic.
        # Browser <--HTTPS--> Nginx <--HTTP--> Flask
        regex = rf'^https?:\/\/[a-zA-Z0-9-]+\.[a-zA-Z]+\/report\/\?leak={target_mech_id}$'
        requests_to_result_endpoint = [request for request in requests if re.match(regex, request['url'])]
        for request in requests_to_result_endpoint:
            headers = request['headers']
            if not target_cookie:
                return True
            else:
                if 'Cookie' in headers:
                    if target_cookie in headers['Cookie']:
                        return True
        return False
