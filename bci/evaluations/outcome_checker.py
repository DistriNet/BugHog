from abc import abstractmethod

from bci.evaluations.logic import SequenceConfiguration, TestResult


class OutcomeChecker:

    def __init__(self, sequence_config: SequenceConfiguration):
        self.sequence_config = sequence_config

    @abstractmethod
    def get_outcome(self, result: TestResult) -> bool:
        if self.sequence_config.target_mech_id:
            return self.get_outcome_for_proxy(result)

    def get_outcome_for_proxy(self, result: TestResult) -> bool | None:
        target_mech_id = self.sequence_config.target_mech_id
        target_cookie = self.sequence_config.target_cookie_name
        if result.requests is None:
            return None
        requests_to_result_endpoint = list(filter(lambda x: f'https://adition.com/report/?leak={target_mech_id}' in x['url'], result.requests))
        for request in requests_to_result_endpoint:
            headers = request['headers']
            if not target_cookie:
                return True
            else:
                if 'Cookie' in headers:
                    if target_cookie in headers['Cookie']:
                        return True
        return False
