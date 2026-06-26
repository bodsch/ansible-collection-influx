# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the ``influxdb_fix_binary`` filter."""

from __future__ import annotations

import pytest

from conftest import load_filter_module


def test_registration():
    """The filter must be registered under its public name."""
    filters = load_filter_module("influxdb_fix_binary").filters()
    assert "influxdb_fix_binary" in filters
    assert callable(filters["influxdb_fix_binary"])


@pytest.mark.parametrize(
    "prefix,version,kind,expected",
    [
        ("influxdb", "2", "", "influxdb2"),
        ("influxdb", "3", "", "influxdb3-core"),
        ("influxdb", "2", "client", "influxdb2-client"),
        ("influxdb", "3", "client", "influxctl"),
    ],
)
def test_fix_binary(prefix, version, kind, expected):
    """Server and client artifact names are derived per major version."""
    f = load_filter_module("influxdb_fix_binary")
    assert f.influxdb_fix_binary(prefix, version, kind) == expected
