# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the ``influxdb_fix_release`` filter."""

from __future__ import annotations

from conftest import load_filter_module


def test_registration():
    """The filter must be registered under its public name."""
    filters = load_filter_module("influxdb_fix_release").filters()
    assert "influxdb_fix_release" in filters
    assert callable(filters["influxdb_fix_release"])


def test_rewrites_artifact_for_newer_version():
    """Versions newer than the threshold switch to the ``_linux_amd64`` naming."""
    f = load_filter_module("influxdb_fix_release")
    data = {"files": {"influxdb": "influxdb2-2.7.5-linux-amd64.tar.gz"}}
    result = f.influxdb_release(data, influxdb_version="2.7.5", version="2.7.1")
    assert result["files"]["influxdb"] == "influxdb2-2.7.5_linux_amd64.tar.gz"


def test_keeps_artifact_for_older_or_equal_version():
    """Versions not greater than the threshold are left untouched."""
    f = load_filter_module("influxdb_fix_release")
    data = {"files": {"influxdb": "influxdb2-2.7.0-linux-amd64.tar.gz"}}
    result = f.influxdb_release(data, influxdb_version="2.7.0", version="2.7.1")
    assert result["files"]["influxdb"] == "influxdb2-2.7.0-linux-amd64.tar.gz"


def test_no_threshold_means_no_change():
    """Without a threshold version the data passes through unchanged."""
    f = load_filter_module("influxdb_fix_release")
    data = {"files": {"influxdb": "influxdb2-2.7.5-linux-amd64.tar.gz"}}
    result = f.influxdb_release(data, influxdb_version="2.7.5")
    assert result["files"]["influxdb"] == "influxdb2-2.7.5-linux-amd64.tar.gz"


def test_version_compare_is_available():
    """Regression: ``version_compare`` must exist (was dropped during the split)."""
    f = load_filter_module("influxdb_fix_release")
    assert f.version_compare("2.7.5", ">", "2.7.1") is True
    assert f.version_compare("2.7.0", ">", "2.7.1") is False
    assert f.version_compare("2.7.5", "??", "2.7.1") is False
