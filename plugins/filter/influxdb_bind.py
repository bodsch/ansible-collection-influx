# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Ansible jinja2 filter to build an InfluxDB HTTP bind URL."""

from __future__ import annotations

__metaclass__ = type

from ipaddress import ip_address
from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """Derive an ``http://host:port`` URL from an InfluxDB bind configuration."""

    def filters(self) -> dict[str, Any]:
        """Return the filters exposed by this plugin."""
        return {
            'influxdb_bind': self.influxdb_bind,
        }

    def influxdb_bind(self, data: dict[str, Any], core_version: int | str) -> str | None:
        """
        Build the HTTP base URL InfluxDB binds to.

        For InfluxDB 2 the ``bind_address`` entry is used (an empty host falls
        back to ``0.0.0.0``); for InfluxDB 3 the ``bind`` entry is used and a
        valid host and port are mandatory.

        Args:
            data: The service configuration carrying ``bind_address`` / ``bind``.
            core_version: The InfluxDB major version (1, 2 or 3).

        Returns:
            The HTTP URL, or ``None`` for v1 or when the address is invalid.
        """
        display.v(f"influxdb_bind(self, data: {data}, core_version: {core_version})")

        version = int(core_version)
        result: str | None = None

        if version == 2:
            host, port = _parse_ip_port(data.get("bind_address"))
            ip_str = host if host else "0.0.0.0"
            if port is not None and _validate_ip(ip_str):
                result = _format_url(ip_str, port)

        elif version == 3:
            host, port = _parse_ip_port(data.get("bind"))
            if host and port is not None and _validate_ip(host):
                result = _format_url(host, port)

        display.v(f"= result: {result}")

        return result


def _parse_ip_port(value: Any) -> tuple[str | None, int | None]:
    """
    Parse ``IP:PORT``, ``[IPv6]:PORT`` or ``:PORT`` (empty host allowed).

    Args:
        value: The raw bind address string.

    Returns:
        A ``(host, port)`` tuple; ``host`` may be an empty string when omitted.
        Returns ``(None, None)`` for invalid input.
    """
    if not isinstance(value, str) or not value:
        return None, None

    # IPv6 in brackets: [::1]:8086
    if value.startswith('['):
        try:
            host, rest = value.split(']', 1)
        except ValueError:
            return None, None
        host = host[1:]  # strip leading '['
        if not rest.startswith(':'):
            return None, None
        return host, _parse_port(rest[1:])

    # IPv4 or empty host: ":8086" or "127.0.0.1:8086"
    if ':' not in value:
        return None, None
    host, port_str = value.rsplit(':', 1)
    return host, _parse_port(port_str)


def _parse_port(port_str: str) -> int | None:
    """Return the port as int when within the valid range, otherwise ``None``."""
    try:
        port = int(port_str)
    except (TypeError, ValueError):
        return None
    return port if 1 <= port <= 65535 else None


def _validate_ip(ip_str: str) -> bool:
    """Return ``True`` when ``ip_str`` is a valid IPv4 or IPv6 address."""
    try:
        ip_address(ip_str)
        return True
    except ValueError:
        return False


def _format_url(ip_str: str, port: int) -> str:
    """Build an ``http://`` URL, bracketing IPv6 hosts."""
    try:
        if ip_address(ip_str).version == 6:
            return f"http://[{ip_str}]:{port}"
    except ValueError:
        pass
    return f"http://{ip_str}:{port}"
