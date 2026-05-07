from __future__ import annotations

from functools import total_ordering
from typing import Any

from packaging.version import parse


@total_ordering
class Version:
    """
    A wrapper around packaging.version.Version to provide BugHog-specific
    logic like 'selectable_version' and consistent padding.
    """

    def __init__(self, version_str_or_int: str | int):
        version_str = str(version_str_or_int)
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
    def base_version(self) -> str:
        return self._v.base_version

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

    def next_padded(self, segment_length: int = 4) -> str:
        """
        Returns the padded version string of the next version (last segment incremented by 1),
        suitable as an exclusive upper bound in lexicographic range queries.
        Example: Version('0.0.6').next_padded() == '0000.0000.0007'
                 Version('145').next_padded()   == '0146'
        """
        release = list(self._v.release)
        release[-1] += 1
        return '.'.join(str(s).zfill(segment_length) for s in release)

    def matches(self, other: Any) -> bool:
        """
        Returns True if this version 'could' be the other version.
        This is primarily a prefix match on version segments.
        Example:
        - Version('12').matches(Version('12.0.1')) -> True
        - Version('13.1').matches(Version('13.1.2')) -> True
        - Version('13.1').matches(Version('13.2')) -> False
        """
        if not isinstance(other, Version):
            return NotImplemented

        if len(self._v.release) <= len(other._v.release):
            if other._v.release[: len(self._v.release)] != self._v.release:
                return False
        else:
            if self != other:
                return False

        if self._v.local is not None:
            return self._v.local == other._v.local

        return True

    def truncate(self, segments: int = 1) -> Version | None:
        """
        Returns a new Version truncated by the specified number of segments.
        Example:
        - Version('12.0.1').truncate(1) -> Version('12.0')
        - Version('12.0.1').truncate(2) -> Version('12')
        - Version('12.0.1').truncate(3) -> None
        """
        if segments < 1:
            raise ValueError('Segments must be at least 1')

        keep = len(self._v.release) - segments
        if keep <= 0:
            return None

        truncated_release = self._v.release[:keep]
        truncated_version_str = '.'.join(str(s) for s in truncated_release)
        return Version(truncated_version_str)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._v == other._v

    def __hash__(self) -> int:
        return hash(self._v)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._v < other._v

    def __repr__(self) -> str:
        return f"Version('{self._original_str}')"

    def __str__(self) -> str:
        return self._original_str
