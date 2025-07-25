from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExperimentResult:
    executable_version: Optional[str]
    executable_origin: Optional[str]
    state: dict
    raw_results: dict
    result_variables: set[tuple[str, str]]
    is_dirty: bool

    @property
    def is_reproduced(self) -> bool:
        return self.poc_is_reproduced(self.result_variables)

    @staticmethod
    def poc_is_reproduced(result_variables: Optional[set[tuple[str,str]]]) -> bool:
        if result_variables is None:
            return False
        for key, value in result_variables:
            if key.lower() == 'reproduced' and value.lower() == 'ok':
                return True
        return False

    @staticmethod
    def poc_passed_sanity_check(result_variables: Optional[set[tuple[str,str]]]) -> bool:
        if result_variables is None:
            return False
        for key, value in result_variables:
            if key.lower() == 'sanity_check' and value.lower() == 'ok':
                return True
        return False

    @staticmethod
    def poc_is_dirty(result_variables: Optional[set[tuple[str,str]]]) -> bool:
        reproduced = ExperimentResult.poc_is_reproduced(result_variables)
        sanity_check_succeeded = ExperimentResult.poc_passed_sanity_check(result_variables)
        return not reproduced and not sanity_check_succeeded

    @property
    def padded_subject_version(self) -> Optional[str]:
        """
        Pads the executable's version.
        Returns None if padding fails.
        """
        if self.executable_version is None:
            return None
        padding_target = 4
        padded_version = []
        for sub in self.executable_version.split('.'):
            if len(sub) > padding_target:
                return None
            padded_version.append('0' * (padding_target - len(sub)) + sub)
        return '.'.join(padded_version)
