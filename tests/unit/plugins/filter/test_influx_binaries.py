# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the ``influx_binaries`` filter."""

from __future__ import annotations

from conftest import load_filter_module


def test_registration():
    """The filter must be registered under its public name and be callable."""
    filters = load_filter_module("influx_binaries").filters()
    assert "influx_binaries" in filters
    assert callable(filters["influx_binaries"])


def test_maps_basename_to_path():
    """A list of find results maps each base name to its absolute path."""
    f = load_filter_module("influx_binaries")
    data = [
        {"path": "/opt/influxd/2.7.5/influxd"},
        {"path": "/opt/influx/2.7.5/influx"},
    ]
    assert f.influx_binaries(data) == {
        "influxd": "/opt/influxd/2.7.5/influxd",
        "influx": "/opt/influx/2.7.5/influx",
    }


def test_entries_without_path_are_ignored():
    """Entries lacking a usable path are skipped."""
    f = load_filter_module("influx_binaries")
    data = [{"path": ""}, {"mode": "0755"}, {"path": "/usr/bin/influxd"}]
    assert f.influx_binaries(data) == {"influxd": "/usr/bin/influxd"}


def test_non_list_returns_empty_dict():
    """Any non-list input yields an empty dictionary."""
    f = load_filter_module("influx_binaries")
    assert f.influx_binaries(None) == {}
    assert f.influx_binaries("nope") == {}
