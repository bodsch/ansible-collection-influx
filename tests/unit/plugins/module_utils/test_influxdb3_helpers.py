# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the InfluxDB 3 module_utils helpers."""

from __future__ import annotations

from ansible_collections.bodsch.influx.plugins.module_utils.influxdb3 import _database_name


def test_database_name_from_iox_key():
    assert _database_name({"iox::database": "sensors"}) == "sensors"


def test_database_name_from_plain_keys():
    assert _database_name({"db": "logs"}) == "logs"
    assert _database_name({"name": "metrics"}) == "metrics"


def test_database_name_from_string():
    assert _database_name("events") == "events"


def test_database_name_unknown_returns_none():
    assert _database_name({"unrelated": "x"}) is None
    assert _database_name(42) is None
