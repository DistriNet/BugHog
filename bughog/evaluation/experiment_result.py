from dataclasses import dataclass

from bughog.version_control.version import Version


@dataclass(frozen=True)
class ExperimentResult:
    executable_version: Version | None
    executable_origin: str | None
    state: dict
    raw_results: dict
    result_variables: set[tuple[str, str]]
    is_dirty: bool

    @property
    def is_reproduced(self) -> bool:
        return self.poc_is_reproduced(self.result_variables)

    @staticmethod
    def poc_is_reproduced(result_variables: set[tuple[str, str]] | None) -> bool:
        if result_variables is None:
            return False
        for key, value in result_variables:
            if key.lower() == 'reproduced' and value.lower() == 'ok':
                return True
        return False

    @staticmethod
    def poc_passed_sanity_check(result_variables: set[tuple[str, str]] | None) -> bool:
        if result_variables is None:
            return False
        for key, value in result_variables:
            if key.lower() == 'sanity_check' and value.lower() == 'ok':
                return True
        return False

    @staticmethod
    def poc_is_dirty(result_variables: set[tuple[str, str]] | None) -> bool:
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
        """
        if self.executable_version is None:
            raise ValueError('executable_version is None')
        return self.executable_version.padded()

    def to_dict(self) -> dict:
        return {
            'executable_version': str(self.executable_version) if self.executable_version else None,
            'executable_origin': self.executable_origin,
            'state': self.state,
            'raw_results': self.raw_results,
            'result_variables': list(self.result_variables),
            'is_dirty': self.is_dirty,
        }
