from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExperimentResult:
    executable_version: str
    executable_origin: Optional[str]
    state: dict
    raw_results: dict
    result_variables: dict[str, str]
    is_dirty: bool

    @property
    def poc_is_reproduced(self) -> bool:
        for key, value in self.result_variables.items():
            if key.lower() == 'reproduced' and value.lower() == 'ok':
                return True
        return False

    def padded_subject_version(self) -> Optional[str]:
        """
        Pads the executable's version.
        Returns None if padding fails.
        """
        padding_target = 4
        padded_version = []
        for sub in self.executable_version.split('.'):
            if len(sub) > padding_target:
                return None
            padded_version.append('0' * (padding_target - len(sub)) + sub)
        return '.'.join(padded_version)
