# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Ansible jinja2 filter to derive the InfluxDB binary/package base name."""

from __future__ import annotations

__metaclass__ = type

from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """Append the version (and edition) suffix to an InfluxDB artifact name."""

    def filters(self) -> dict[str, Any]:
        """Return the filters exposed by this plugin."""
        return {
            'influxdb_fix_binary': self.influxdb_fix_binary,
        }

    def influxdb_fix_binary(self, data: str, influxdb_version: str, influxdb_type: str = "") -> str:
        """
        Build the InfluxDB artifact base name for server or client binaries.

        Examples:
            * server, v2 -> ``influxdb2``
            * server, v3 -> ``influxdb3-core``
            * client, v2 -> ``influxdb2-client``
            * client, v3 -> ``influxctl``

        Args:
            data: The artifact prefix (e.g. ``influxdb``).
            influxdb_version: The major version as a string (``"2"`` / ``"3"``).
            influxdb_type: ``"client"`` for the CLI artifact, otherwise the server.

        Returns:
            The assembled artifact base name.
        """
        display.v(
            f"influxdb_fix_binary(self, data: {data}, "
            f"influxdb_version: {influxdb_version}, influxdb_type: {influxdb_type})"
        )

        major = int(influxdb_version)
        suffix: list[str] = []

        if influxdb_type == 'client':
            if major == 2:
                suffix = [influxdb_version, "client"]
                data += '-'.join(suffix)
            if major == 3:
                data = "influxctl"
        else:
            if major in (2, 3):
                suffix.append(influxdb_version)
            if major == 3:
                suffix.append("core")
            data += '-'.join(suffix)

        display.v(f"= result: {data}")

        return data
