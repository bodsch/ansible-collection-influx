# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Ansible jinja2 filter to populate InfluxDB download URLs, files and binaries."""

from __future__ import annotations

__metaclass__ = type

import copy
from typing import Any

from ansible.utils.display import Display

display = Display()

_RELEASE_URL_CORE = "https://dl.influxdata.com/influxdb/releases"
_RELEASE_URL_CLIENT = "https://dl.influxdata.com/influxctl/releases"


class FilterModule(object):
    """Fill in the version dependent download metadata of a release definition."""

    def filters(self) -> dict[str, Any]:
        """Return the filters exposed by this plugin."""
        return {
            'influxdb_update_release': self.influxdb_update_release,
        }

    def influxdb_update_release(self, data: dict[str, Any], core_version: str, client_version: str) -> dict[str, Any]:
        """
        Populate download URLs, artifact file names and binary names.

        The values differ between InfluxDB 2 (``influxd``/``influx``) and
        InfluxDB 3 (``influxdb3``/``influxctl``); the client of v2 is shipped
        from the same release server as the core.

        Args:
            data: The release definition to enrich (not mutated).
            core_version: The InfluxDB core version (e.g. ``"2.7.5"``).
            client_version: The CLI/client version.

        Returns:
            A new release definition with ``download_urls``, ``files`` and
            ``binaries`` populated for ``core`` and ``client``.
        """
        display.v(
            f"influxdb_update_release(self, data: {data}, "
            f"core_version: {core_version}, client_version: {client_version})"
        )

        major = int(str(core_version)[0:1])

        url_core = _RELEASE_URL_CORE
        url_client = _RELEASE_URL_CLIENT if major >= 3 else _RELEASE_URL_CORE

        if major == 2:
            file_core = f"influxdb2-{core_version}_linux_amd64.tar.gz"
            file_client = f"influxdb2-client-{client_version}-linux-amd64.tar.gz"
            binary_core = "influxd"
            binary_client = "influx"
        elif major == 3:
            file_core = f"influxdb3-core-{core_version}_linux_amd64.tar.gz"
            file_client = f"influxctl-v{client_version}-linux-x86_64.tar.gz"
            binary_core = "influxdb3"
            binary_client = "influxctl"
        else:
            # Unsupported major version: return the data unchanged.
            return data

        result = copy.deepcopy(data)

        result.setdefault('download_urls', {})
        result.setdefault('files', {})
        result.setdefault('binaries', {})

        result['download_urls']['core'] = url_core
        result['download_urls']['client'] = url_client
        result['files']['core'] = file_core
        result['files']['client'] = file_client
        result['binaries']['core'] = binary_core
        result['binaries']['client'] = binary_client

        display.v(f"= result: {result}")

        return result
