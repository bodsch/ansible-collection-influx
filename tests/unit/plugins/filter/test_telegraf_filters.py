# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the Telegraf filters."""

from __future__ import annotations

import pytest

from conftest import load_filter_module


# --------------------------------------------------------------------------- #
# telegraf_checksum
# --------------------------------------------------------------------------- #
def test_checksum_registration():
    filters = load_filter_module("telegraf_checksum").filters()
    assert "telegraf_checksum" in filters


def test_checksum_picks_matching_line():
    f = load_filter_module("telegraf_checksum")
    data = [
        "abc123  telegraf-1.28.5.windows-amd64.tar.gz",
        "def456  telegraf-1.28.5.linux-amd64.tar.gz",
    ]
    assert f.checksum(data, "linux", "amd64") == "def456"


def test_checksum_no_match_returns_none():
    """Regression: no matching line must return ``None`` instead of raising IndexError."""
    f = load_filter_module("telegraf_checksum")
    assert f.checksum(["abc  telegraf-1.0.0.darwin-arm64.tar.gz"], "linux", "amd64") is None


def test_checksum_non_list_returns_none():
    f = load_filter_module("telegraf_checksum")
    assert f.checksum(None, "linux", "amd64") is None


# --------------------------------------------------------------------------- #
# telegraf_clean_list
# --------------------------------------------------------------------------- #
def test_clean_list_registration():
    filters = load_filter_module("telegraf_clean_list").filters()
    assert "telegraf_clean_list" in filters


def test_clean_list_keeps_only_configured_entries():
    f = load_filter_module("telegraf_clean_list")
    data = [
        {"type": "cpu", "config": {"percpu": True}},
        {"type": "mem"},
        {"type": "disk", "config": None},
        {"type": "net", "config": {"interfaces": ["eth0"]}},
    ]
    result = f.telegraf_clean_list(data)
    assert [e["type"] for e in result] == ["cpu", "net"]


def test_clean_list_non_list_returns_empty():
    f = load_filter_module("telegraf_clean_list")
    assert f.telegraf_clean_list(None) == []


# --------------------------------------------------------------------------- #
# telegraf_input_value
# --------------------------------------------------------------------------- #
def test_input_value_registration():
    filters = load_filter_module("telegraf_input_value").filters()
    assert "telegraf_input_value" in filters


@pytest.mark.parametrize(
    "value,expected",
    [
        (5, (True, 5)),
        (0, (False, 0)),
        (True, (True, "true")),
        (False, (True, "false")),
        ("true", (True, "true")),
        ("FALSE", (True, "false")),
        ("hostname", (True, '"hostname"')),
        ("", (False, '""')),
        (["a", "b"], (True, '["a","b"]')),
        ([], (False, [])),
    ],
)
def test_input_value(value, expected):
    f = load_filter_module("telegraf_input_value")
    assert f.input_value(value) == expected
