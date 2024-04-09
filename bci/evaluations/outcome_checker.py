import re
from abc import abstractmethod

from bci.evaluations.logic import SequenceConfiguration, TestResult


class OutcomeChecker:

    def __init__(self, sequence_config: SequenceConfiguration):
        self.sequence_config = sequence_config

    @abstractmethod
    def get_outcome(self, result: TestResult) -> bool:
        '''
        Returns the outcome of the test result.

        - None in case of an error.
        - True if the test was reproduced.
        - False if the test was not reproduced.
        '''
        if result.is_dirty:
            return None
        if result.reproduced:
            return True
        # Backwards compatibility
        if self.sequence_config.target_mech_id:
            return self.get_outcome_for_proxy(result)

    def get_outcome_for_proxy(self, result: TestResult) -> bool | None:
        target_mech_id = self.sequence_config.target_mech_id
        target_cookie = self.sequence_config.target_cookie_name
        requests = result.data.get('requests')
        if requests is None:
            return None
        regex = rf'^https:\/\/[a-zA-Z0-9-]+\.[a-zA-Z]+\/report\/\?leak={target_mech_id}$'
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
