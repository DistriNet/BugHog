from functools import total_ordering
from typing import Any

from packaging.version import parse


@total_ordering
class Version:
    """
    A wrapper around packaging.version.Version to provide BugHog-specific
    logic like 'selectable_version' and consistent padding.
    """

    def __init__(self, version_str: str):
        self._original_str = version_str
        # Handle formats like "0.0.1-<hash>" (Servo).
        # PEP 440 local versions use '+' (e.g. 0.0.1+hash).
        parsed_str = version_str
        if '-' in version_str:
            base, suffix = version_str.split('-', 1)
            parsed_str = f'{base}+{suffix}'

        self._v = parse(parsed_str)

    @property
    def major(self) -> int:
        return self._v.major

    @property
    def minor(self) -> int:
        return self._v.minor

    @property
    def patch(self) -> int:
        return self._v.micro

    @property
    def is_pre_release(self) -> bool:
        return self.major == 0

    @property
    def selectable_version(self) -> str:
        """
        Returns the version string that should be used for selection in the UI/API.
        - For major versions >= 1, returns the major version (e.g. "100").
        - For major versions == 0 and minor >= 1, returns major.minor (e.g. "0.1").
        - For major versions == 0 and minor == 0, returns major.minor.patch (e.g. "0.0.1").
        """
        if self.major >= 1:
            return str(self.major)
        if self.minor >= 1:
            return f'{self.major}.{self.minor}'
        return f'{self.major}.{self.minor}.{self.patch}'

    def padded(self, segment_length: int = 4) -> str:
        """
        Returns a zero-padded version string suitable for lexicographic comparison.
        Matches the logic in ExperimentResult.padded_subject_version.
        """
        padded_segments = []
        for s in self._v.release:
            s_str = str(s)
            if len(s_str) > segment_length:
                raise ValueError(f"Version segment '{s_str}' exceeds maximum length of {segment_length}")
            padded_segments.append(s_str.zfill(segment_length))

        padded_base = '.'.join(padded_segments)

        if self._v.local:
            return f'{padded_base}-{self._v.local}'
        return padded_base

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._v == other._v

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._v < other._v

    def __repr__(self) -> str:
        return f"Version('{self._original_str}')"

    def __str__(self) -> str:
        return self._original_str
