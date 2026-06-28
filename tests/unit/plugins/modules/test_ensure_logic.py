# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Unit tests for the per-item reconcile helpers of the InfluxDB modules."""

from __future__ import annotations

from typing import Any

from ansible_collections.bodsch.influx.plugins.modules.influxdb2_organizations import _ensure_organization
from ansible_collections.bodsch.influx.plugins.modules.influxdb2_buckets import _ensure_bucket
from ansible_collections.bodsch.influx.plugins.modules.influxdb3_database import _ensure_database


class FakeClient:
    """Record API calls made by the reconcile helpers."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def __getattr__(self, name: str):
        def _record(*args: Any, **kwargs: Any):
            self.calls.append((name, args))
            return {"id": "new-id"}
        return _record

    def names(self) -> list[str]:
        return [name for name, _ in self.calls]


# --------------------------------------------------------------------------- #
# organizations
# --------------------------------------------------------------------------- #
def test_org_created_when_missing():
    client = FakeClient()
    entry = _ensure_organization(client, {}, "main-org", {"state": "create"}, check_mode=False)
    assert entry["changed"] is True and entry["state"] == "created"
    assert "create_organization" in client.names()


def test_org_present_when_unchanged():
    client = FakeClient()
    existing = {"main-org": {"id": "1", "description": "Main"}}
    entry = _ensure_organization(client, existing, "main-org", {"description": "Main"}, check_mode=False)
    assert entry["changed"] is False and entry["state"] == "present"
    assert client.names() == []


def test_org_updated_when_description_differs():
    client = FakeClient()
    existing = {"main-org": {"id": "1", "description": "old"}}
    entry = _ensure_organization(client, existing, "main-org", {"description": "new"}, check_mode=False)
    assert entry["changed"] is True and entry["state"] == "updated"
    assert "update_organization" in client.names()


def test_org_deleted_when_absent():
    client = FakeClient()
    existing = {"guest-org": {"id": "2"}}
    entry = _ensure_organization(client, existing, "guest-org", {"state": "absent"}, check_mode=False)
    assert entry["changed"] is True and entry["state"] == "deleted"
    assert "delete_organization" in client.names()


def test_org_check_mode_makes_no_calls():
    client = FakeClient()
    entry = _ensure_organization(client, {}, "main-org", {"state": "create"}, check_mode=True)
    assert entry["changed"] is True and entry["state"] == "would be created"
    assert client.names() == []


# --------------------------------------------------------------------------- #
# buckets
# --------------------------------------------------------------------------- #
def test_bucket_created_with_org_resolution():
    client = FakeClient()
    orgs = {"main-org": {"id": "org-1"}}
    definition = {"organization": {"name": "main-org"}, "retention": "1d"}
    entry = _ensure_bucket(client, {}, orgs, "bucket01", definition, check_mode=False)
    assert entry["changed"] is True and entry["state"] == "created"
    assert "create_bucket" in client.names()


def test_bucket_fails_when_org_missing():
    client = FakeClient()
    definition = {"organization": {"name": "ghost"}}
    entry = _ensure_bucket(client, {}, {}, "bucket01", definition, check_mode=False)
    assert entry["failed"] is True
    assert client.names() == []


def test_bucket_present_when_retention_matches():
    client = FakeClient()
    existing = {"bucket01": {"id": "b1", "retentionRules": [{"type": "expire", "everySeconds": 86400}]}}
    orgs = {"main-org": {"id": "org-1"}}
    definition = {"organization": {"name": "main-org"}, "retention": "1d"}
    entry = _ensure_bucket(client, existing, orgs, "bucket01", definition, check_mode=False)
    assert entry["changed"] is False and entry["state"] == "present"
    assert client.names() == []


def test_bucket_updated_when_retention_changes():
    client = FakeClient()
    existing = {"bucket01": {"id": "b1", "retentionRules": []}}
    orgs = {"main-org": {"id": "org-1"}}
    definition = {"organization": {"name": "main-org"}, "retention": "1d"}
    entry = _ensure_bucket(client, existing, orgs, "bucket01", definition, check_mode=False)
    assert entry["changed"] is True and entry["state"] == "updated"
    assert "update_bucket" in client.names()


# --------------------------------------------------------------------------- #
# databases (v3)
# --------------------------------------------------------------------------- #
def test_database_created_when_missing():
    client = FakeClient()
    entry = _ensure_database(client, set(), "sensors", {"state": "create"}, check_mode=False)
    assert entry["changed"] is True and entry["state"] == "created"
    assert "create_database" in client.names()


def test_database_present_when_existing():
    client = FakeClient()
    entry = _ensure_database(client, {"sensors"}, "sensors", {"state": "create"}, check_mode=False)
    assert entry["changed"] is False and entry["state"] == "present"
    assert client.names() == []


def test_database_deleted_when_absent():
    client = FakeClient()
    entry = _ensure_database(client, {"logs"}, "logs", {"state": "absent"}, check_mode=False)
    assert entry["changed"] is True and entry["state"] == "deleted"
    assert "delete_database" in client.names()
