# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the InfluxDB 2 module_utils helpers."""

from __future__ import annotations

import pytest

from ansible_collections.bodsch.influx.plugins.module_utils.influxdb2 import (
    bucket_retention_seconds,
    parse_duration,
    _retention_rules,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, 0),
        ("", 0),
        ("0", 0),
        ("0s", 0),
        ("30m", 1800),
        ("1h", 3600),
        ("1d", 86400),
        ("2w", 1209600),
        ("1h30m", 5400),
        (3600, 3600),
        (-5, 0),
        ("604800", 604800),
    ],
)
def test_parse_duration(value, expected):
    assert parse_duration(value) == expected


def test_parse_duration_rejects_garbage():
    with pytest.raises(ValueError):
        parse_duration("nonsense")


def test_parse_duration_rejects_bool():
    with pytest.raises(ValueError):
        parse_duration(True)


def test_retention_rules():
    assert _retention_rules(0) == []
    assert _retention_rules(86400) == [{"type": "expire", "everySeconds": 86400}]


def test_bucket_retention_seconds():
    assert bucket_retention_seconds({"retentionRules": [{"type": "expire", "everySeconds": 3600}]}) == 3600
    assert bucket_retention_seconds({"retentionRules": []}) == 0
    assert bucket_retention_seconds({}) == 0
