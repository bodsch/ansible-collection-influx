# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Ansible jinja2 filter to fix the InfluxDB release artifact naming."""

from __future__ import annotations

__metaclass__ = type

import operator as op
import re
from typing import Any, Callable

from ansible.utils.display import Display

display = Display()

_COMPARATORS: dict[str, Callable[[Any, Any], bool]] = {
    '<': op.lt,
    '<=': op.le,
    '==': op.eq,
    '>=': op.ge,
    '>': op.gt,
}


def _version_tuple(value: str) -> tuple[int, ...]:
    """Convert a dotted version string into a tuple of integers for comparison."""
    parts: list[int] = []
    for chunk in str(value).split("."):
        match = re.match(r"\d+", chunk.strip())
        parts.append(int(match.group()) if match else 0)
    return tuple(parts)


class FilterModule(object):
    """Adjust the InfluxDB download artifact name for newer releases."""

    def filters(self) -> dict[str, Any]:
        """Return the filters exposed by this plugin."""
        return {
            'influxdb_fix_release': self.influxdb_release,
        }

    def influxdb_release(self, data: dict[str, Any], influxdb_version: str, version: str | None = None) -> dict[str, Any]:
        """
        Rewrite the InfluxDB artifact name for versions newer than ``version``.

        From a certain release on, the artifact uses ``_linux_amd64`` instead of
        ``-linux-amd64``. When ``influxdb_version`` is greater than ``version``
        the ``files.influxdb`` entry is rewritten accordingly.

        Args:
            data: The release definition holding ``files.influxdb``.
            influxdb_version: The InfluxDB version that will be installed.
            version: The threshold version; if unset no change is performed.

        Returns:
            The (possibly mutated) release definition.
        """
        display.v(f"influxdb_release(self, data: {data}, influxdb_version: {influxdb_version}, version: {version})")

        if version and self.version_compare(influxdb_version, ">", version):
            value = data.get("files", {}).get("influxdb")
            if isinstance(value, str):
                data["files"]["influxdb"] = re.sub(r'-linux-amd64', '_linux_amd64', value)

        return data

    def version_compare(self, ver1: str, specifier: str, ver2: str) -> bool:
        """
        Compare two version strings using the given specifier.

        Args:
            ver1: Left-hand version.
            specifier: One of ``<``, ``<=``, ``==``, ``>=``, ``>``.
            ver2: Right-hand version.

        Returns:
            ``True`` if the comparison holds, otherwise ``False`` (also for an
            unknown specifier or an unparsable version).
        """
        try:
            return _COMPARATORS[specifier](_version_tuple(ver1), _version_tuple(ver2))
        except (KeyError, ValueError):
            return False
