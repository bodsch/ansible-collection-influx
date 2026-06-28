# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the ``influxdb_bind`` filter."""

from __future__ import annotations

from conftest import load_filter_module


def test_registration():
    """The filter must be registered under its public name."""
    filters = load_filter_module("influxdb_bind").filters()
    assert "influxdb_bind" in filters
    assert callable(filters["influxdb_bind"])


def test_version_one_returns_none():
    """InfluxDB 1 has no HTTP bind URL handling."""
    f = load_filter_module("influxdb_bind")
    assert f.influxdb_bind({"bind_address": ":8086"}, 1) is None


def test_v2_with_address():
    """v2 uses ``bind_address`` and builds the URL."""
    f = load_filter_module("influxdb_bind")
    assert f.influxdb_bind({"bind_address": "127.0.0.1:8086"}, 2) == "http://127.0.0.1:8086"


def test_v2_empty_host_falls_back_to_all_interfaces():
    """An empty host in v2 defaults to ``0.0.0.0``."""
    f = load_filter_module("influxdb_bind")
    assert f.influxdb_bind({"bind_address": ":8086"}, 2) == "http://0.0.0.0:8086"


def test_v3_requires_host_and_port():
    """v3 needs a valid host and port, otherwise ``None``."""
    f = load_filter_module("influxdb_bind")
    assert f.influxdb_bind({"bind": "0.0.0.0:8181"}, 3) == "http://0.0.0.0:8181"
    assert f.influxdb_bind({"bind": ":8181"}, 3) is None


def test_invalid_address_returns_none():
    """An unparsable address yields ``None``."""
    f = load_filter_module("influxdb_bind")
    assert f.influxdb_bind({"bind_address": "not-an-address"}, 2) is None


def test_ipv6_is_bracketed():
    """IPv6 hosts are wrapped in brackets for the URL."""
    f = load_filter_module("influxdb_bind")
    assert f.influxdb_bind({"bind": "[::1]:8181"}, 3) == "http://[::1]:8181"
