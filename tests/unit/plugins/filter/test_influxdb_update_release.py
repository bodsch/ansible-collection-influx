# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the ``influxdb_update_release`` filter."""

from __future__ import annotations

import copy

from conftest import load_filter_module


def _base():
    return {"download_urls": {}, "files": {}, "binaries": {}}


def test_registration():
    """The filter must be registered under its public name."""
    filters = load_filter_module("influxdb_update_release").filters()
    assert "influxdb_update_release" in filters


def test_v2_release_metadata():
    """v2 produces the influxd/influx artifact and the shared release server."""
    f = load_filter_module("influxdb_update_release")
    result = f.influxdb_update_release(_base(), core_version="2.7.5", client_version="2.7.5")
    assert result["files"]["core"] == "influxdb2-2.7.5_linux_amd64.tar.gz"
    assert result["files"]["client"] == "influxdb2-client-2.7.5-linux-amd64.tar.gz"
    assert result["binaries"]["core"] == "influxd"
    assert result["binaries"]["client"] == "influx"
    assert result["download_urls"]["core"] == result["download_urls"]["client"]


def test_v3_release_metadata():
    """v3 produces influxdb3/influxctl and a dedicated client release server."""
    f = load_filter_module("influxdb_update_release")
    result = f.influxdb_update_release(_base(), core_version="3.1.0", client_version="2.9.0")
    assert result["files"]["core"] == "influxdb3-core-3.1.0_linux_amd64.tar.gz"
    assert result["files"]["client"] == "influxctl-v2.9.0-linux-x86_64.tar.gz"
    assert result["binaries"]["core"] == "influxdb3"
    assert result["binaries"]["client"] == "influxctl"
    assert "influxctl/releases" in result["download_urls"]["client"]


def test_input_is_not_mutated():
    """The filter must not mutate its input (no side effects)."""
    f = load_filter_module("influxdb_update_release")
    data = _base()
    snapshot = copy.deepcopy(data)
    f.influxdb_update_release(data, core_version="2.7.5", client_version="2.7.5")
    assert data == snapshot


def test_missing_nested_keys_are_created():
    """Absent nested dictionaries are created instead of raising."""
    f = load_filter_module("influxdb_update_release")
    result = f.influxdb_update_release({}, core_version="2.7.5", client_version="2.7.5")
    assert result["binaries"]["core"] == "influxd"
