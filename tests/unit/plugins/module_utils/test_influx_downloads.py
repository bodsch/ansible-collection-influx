# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the InfluxDownloads resolver helpers."""

from __future__ import annotations

import pytest

from ansible_collections.bodsch.influx.plugins.module_utils.influx_downloads import InfluxDownloads


def _resolver() -> InfluxDownloads:
    """Build an InfluxDownloads instance without running __init__."""
    return InfluxDownloads.__new__(InfluxDownloads)


def test_normalize_arch():
    r = _resolver()
    assert r._normalize_arch("x86_64") == "amd64"
    assert r._normalize_arch("amd64") == "amd64"
    assert r._normalize_arch("aarch64") == "arm64"
    assert r._normalize_arch("ARM64") == "arm64"
    with pytest.raises(ValueError):
        r._normalize_arch("sparc")


def test_semver_key():
    assert InfluxDownloads._semver_key("2.7.12") == (2, 7, 12)
    assert InfluxDownloads._semver_key("not-a-version") == (0, 0, 0)
    assert max(["2.7.1", "2.7.12", "2.10.0"], key=InfluxDownloads._semver_key) == "2.10.0"


def test_extract_first_sha256():
    text = "abc\n3b1f " + "a" * 64 + " trailing"
    assert InfluxDownloads._extract_first_sha256(text) == "a" * 64
    assert InfluxDownloads._extract_first_sha256("no hash here") is None


def test_parse_v2_release_body_markdown_link():
    sha = "b" * 64
    body = (
        f"[influxdb2-2.7.5-linux-amd64.tar.gz]"
        f"(https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.5-linux-amd64.tar.gz) {sha}"
    )
    artifact, url, parsed_sha = InfluxDownloads._parse_v2_release_body(body, "2.7.5", "amd64")
    assert artifact == "influxdb2-2.7.5-linux-amd64.tar.gz"
    assert url.endswith("influxdb2-2.7.5-linux-amd64.tar.gz")
    assert parsed_sha == sha


def test_parse_v2_release_body_underscore_naming():
    sha = "c" * 64
    body = f"influxdb2-2.7.12_linux_amd64.tar.gz   {sha}"
    artifact, url, parsed_sha = InfluxDownloads._parse_v2_release_body(body, "2.7.12", "amd64")
    assert artifact == "influxdb2-2.7.12_linux_amd64.tar.gz"
    assert url is None
    assert parsed_sha == sha


def test_parse_v2_release_body_missing_raises():
    with pytest.raises(RuntimeError):
        InfluxDownloads._parse_v2_release_body("nothing useful", "2.7.5", "amd64")
