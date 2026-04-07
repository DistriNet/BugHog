import re
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
    def poc_is_reproduced(result_variables: Optional[set[tuple[str, str]]]) -> bool:
        if result_variables is None:
            return False
        for key, value in result_variables:
            if key.lower() == 'reproduced' and value.lower() == 'ok':
                return True
        return False

    @staticmethod
    def poc_passed_sanity_check(result_variables: Optional[set[tuple[str, str]]]) -> bool:
        if result_variables is None:
            return False
        for key, value in result_variables:
            if key.lower() == 'sanity_check' and value.lower() == 'ok':
                return True
        return False

    @staticmethod
    def poc_is_dirty(result_variables: Optional[set[tuple[str, str]]]) -> bool:
        """
        Returns whether the poc is dirty: it is not reproduced and the sanity check did not succeed.
        """
        reproduced = ExperimentResult.poc_is_reproduced(result_variables)
        sanity_check_succeeded = ExperimentResult.poc_passed_sanity_check(result_variables)
        return not reproduced and not sanity_check_succeeded

    @property
    def padded_subject_version(self) -> str:
        """
        Returns a zero-padded version string derived from the executable's version,
        suitable for lexicographic comparison.

        Each dot-separated numeric segment is left-padded with zeros to 4 digits.
        A trailing build-metadata suffix (e.g. the '-<hash>' in '0.0.1-abc123f')
        is stripped from the last segment before padding and then re-attached, so
        both 'M.m.p' and 'M.m.p-hash' version formats are handled uniformly.
        The result for '0.0.1-abc123f' would be '0000.0000.0001-abc123f'.

        Raises ValueError if executable_version is None or does not match the
        expected format (1-4 digit dot-separated segments with an optional
        trailing '-<suffix>').
        """
        if self.executable_version is None or not re.fullmatch(r'\d{1,4}(\.\d{1,4})*(-\w+)?', self.executable_version):
            raise ValueError(f"Unsupported version format: '{self.executable_version}'")
        padding_target = 4
        padded_version = []
        for sub in self.executable_version.split('.'):
            numeric, _, suffix = sub.partition('-')
            padded = '0' * (padding_target - len(numeric)) + numeric
            if suffix:
                padded += '-' + suffix
            padded_version.append(padded)
        return '.'.join(padded_version)

    def to_dict(self) -> dict:
        return {
            'executable_version': self.executable_version,
            'executable_origin': self.executable_origin,
            'state': self.state,
            'raw_results': self.raw_results,
            'result_variables': list(self.result_variables),
            'is_dirty': self.is_dirty,
        }
