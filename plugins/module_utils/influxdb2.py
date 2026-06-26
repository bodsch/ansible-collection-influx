# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
High level client for the InfluxDB v2 REST API (``/api/v2``).

The client exposes resource operations (setup, organizations, users, buckets
and authorizations) on top of :class:`InfluxHTTP`. All methods raise
:class:`InfluxHTTPError` on failure and return decoded API objects, so the
modules can focus on idempotency and result aggregation.
"""

from __future__ import annotations

import re
from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.bodsch.influx.plugins.module_utils.influx_http import (
    InfluxHTTP,
    InfluxHTTPError,
)

__all__ = ["InfluxDB2Client", "InfluxHTTPError"]


class InfluxDB2Client(InfluxHTTP):
    """Resource oriented client for InfluxDB 2."""

    def __init__(
        self,
        module: AnsibleModule,
        base_url: str,
        token: str | None = None,
        validate_certs: bool = True,
        timeout: int = 10,
    ) -> None:
        """Initialize the client using the ``Token`` authorization scheme."""
        super().__init__(
            module=module,
            base_url=base_url,
            token=token,
            auth_scheme="Token",
            validate_certs=validate_certs,
            timeout=timeout,
        )

    # ------------------------------------------------------------------ #
    # health
    # ------------------------------------------------------------------ #
    def health(self) -> tuple[int, Any]:
        """Return ``(status, body)`` of the ``/health`` endpoint."""
        return self.get("/health", authorize=False)

    def ping(self) -> tuple[int, Any]:
        """Return ``(status, body)`` of the ``/ping`` endpoint (204 on success)."""
        return self.get("/ping", authorize=False)

    # ------------------------------------------------------------------ #
    # setup / onboarding
    # ------------------------------------------------------------------ #
    def onboarding_allowed(self) -> bool:
        """Return ``True`` when initial onboarding has not been performed yet."""
        _, body = self.get("/api/v2/setup", authorize=False, expected=(200,))
        return bool(isinstance(body, dict) and body.get("allowed"))

    def setup(
        self,
        username: str,
        password: str,
        org: str,
        bucket: str,
        token: str | None = None,
        retention_seconds: int | None = None,
    ) -> dict[str, Any]:
        """
        Perform the initial onboarding (first user, organization, bucket, token).

        Returns:
            The decoded onboarding response (contains ``auth.token``).
        """
        payload: dict[str, Any] = {
            "username": username,
            "password": password,
            "org": org,
            "bucket": bucket,
        }
        if token:
            payload["token"] = token
        if retention_seconds:
            payload["retentionPeriodSeconds"] = int(retention_seconds)

        _, body = self.post("/api/v2/setup", body=payload, authorize=False, expected=(200, 201))
        return body if isinstance(body, dict) else {}

    # ------------------------------------------------------------------ #
    # organizations
    # ------------------------------------------------------------------ #
    def list_organizations(self) -> dict[str, dict[str, Any]]:
        """Return existing organizations keyed by name."""
        _, body = self.get("/api/v2/orgs", query={"limit": 100}, expected=(200,))
        orgs = body.get("orgs", []) if isinstance(body, dict) else []
        return {o["name"]: o for o in orgs if isinstance(o, dict) and o.get("name")}

    def create_organization(self, name: str, description: str | None = None) -> dict[str, Any]:
        """Create an organization and return the created object."""
        payload: dict[str, Any] = {"name": name}
        if description is not None:
            payload["description"] = description
        _, body = self.post("/api/v2/orgs", body=payload, expected=(201,))
        return body if isinstance(body, dict) else {}

    def update_organization(self, org_id: str, name: str | None = None, description: str | None = None) -> dict[str, Any]:
        """Update an organization's name and/or description."""
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        _, body = self.patch(f"/api/v2/orgs/{org_id}", body=payload, expected=(200,))
        return body if isinstance(body, dict) else {}

    def delete_organization(self, org_id: str) -> None:
        """Delete an organization by id."""
        self.delete(f"/api/v2/orgs/{org_id}", expected=(204,))

    # ------------------------------------------------------------------ #
    # users
    # ------------------------------------------------------------------ #
    def list_users(self) -> dict[str, dict[str, Any]]:
        """Return existing users keyed by name."""
        _, body = self.get("/api/v2/users", query={"limit": 100}, expected=(200,))
        users = body.get("users", []) if isinstance(body, dict) else []
        return {u["name"]: u for u in users if isinstance(u, dict) and u.get("name")}

    def create_user(self, name: str) -> dict[str, Any]:
        """Create a user and return the created object."""
        _, body = self.post("/api/v2/users", body={"name": name}, expected=(201,))
        return body if isinstance(body, dict) else {}

    def set_user_password(self, user_id: str, password: str) -> None:
        """Set or update a user's password."""
        self.post(f"/api/v2/users/{user_id}/password", body={"password": password}, expected=(204,))

    def delete_user(self, user_id: str) -> None:
        """Delete a user by id."""
        self.delete(f"/api/v2/users/{user_id}", expected=(204,))

    # ------------------------------------------------------------------ #
    # buckets
    # ------------------------------------------------------------------ #
    def list_buckets(self, org: str | None = None) -> dict[str, dict[str, Any]]:
        """Return existing buckets keyed by name (optionally scoped to an org)."""
        _, body = self.get("/api/v2/buckets", query={"org": org, "limit": 100}, expected=(200,))
        buckets = body.get("buckets", []) if isinstance(body, dict) else []
        return {b["name"]: b for b in buckets if isinstance(b, dict) and b.get("name")}

    def create_bucket(
        self,
        org_id: str,
        name: str,
        description: str | None = None,
        retention_seconds: int = 0,
    ) -> dict[str, Any]:
        """Create a bucket and return the created object."""
        payload: dict[str, Any] = {
            "orgID": org_id,
            "name": name,
            "retentionRules": _retention_rules(retention_seconds),
        }
        if description is not None:
            payload["description"] = description
        _, body = self.post("/api/v2/buckets", body=payload, expected=(201,))
        return body if isinstance(body, dict) else {}

    def update_bucket(
        self,
        bucket_id: str,
        retention_seconds: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update a bucket's retention and/or description."""
        payload: dict[str, Any] = {}
        if retention_seconds is not None:
            payload["retentionRules"] = _retention_rules(retention_seconds)
        if description is not None:
            payload["description"] = description
        _, body = self.patch(f"/api/v2/buckets/{bucket_id}", body=payload, expected=(200,))
        return body if isinstance(body, dict) else {}

    def delete_bucket(self, bucket_id: str) -> None:
        """Delete a bucket by id."""
        self.delete(f"/api/v2/buckets/{bucket_id}", expected=(204,))

    # ------------------------------------------------------------------ #
    # authorizations (API tokens)
    # ------------------------------------------------------------------ #
    def list_authorizations(self, org: str | None = None) -> list[dict[str, Any]]:
        """Return authorizations, optionally scoped to an organization name."""
        _, body = self.get("/api/v2/authorizations", query={"org": org}, expected=(200,))
        auths = body.get("authorizations", []) if isinstance(body, dict) else []
        return [a for a in auths if isinstance(a, dict)]

    def create_authorization(
        self,
        org_id: str,
        permissions: list[dict[str, Any]],
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create an authorization (token) and return the created object."""
        payload: dict[str, Any] = {"orgID": org_id, "permissions": permissions}
        if description is not None:
            payload["description"] = description
        _, body = self.post("/api/v2/authorizations", body=payload, expected=(201,))
        return body if isinstance(body, dict) else {}

    def set_authorization_status(self, auth_id: str, status: str) -> dict[str, Any]:
        """Set an authorization's status to ``active`` or ``inactive``."""
        _, body = self.patch(f"/api/v2/authorizations/{auth_id}", body={"status": status}, expected=(200,))
        return body if isinstance(body, dict) else {}

    def delete_authorization(self, auth_id: str) -> None:
        """Delete an authorization by id."""
        self.delete(f"/api/v2/authorizations/{auth_id}", expected=(204,))

    # ------------------------------------------------------------------ #
    # organization membership
    # ------------------------------------------------------------------ #
    def list_org_members(self, org_id: str) -> dict[str, dict[str, Any]]:
        """Return the members of an organization keyed by user name."""
        _, body = self.get(f"/api/v2/orgs/{org_id}/members", expected=(200,))
        users = body.get("users", []) if isinstance(body, dict) else []
        return {u["name"]: u for u in users if isinstance(u, dict) and u.get("name")}

    def list_org_owners(self, org_id: str) -> dict[str, dict[str, Any]]:
        """Return the owners of an organization keyed by user name."""
        _, body = self.get(f"/api/v2/orgs/{org_id}/owners", expected=(200,))
        users = body.get("users", []) if isinstance(body, dict) else []
        return {u["name"]: u for u in users if isinstance(u, dict) and u.get("name")}

    def add_org_member(self, org_id: str, user_id: str) -> None:
        """Add a user as a member of an organization."""
        self.post(f"/api/v2/orgs/{org_id}/members", body={"id": user_id}, expected=(201,))

    def add_org_owner(self, org_id: str, user_id: str) -> None:
        """Add a user as an owner of an organization."""
        self.post(f"/api/v2/orgs/{org_id}/owners", body={"id": user_id}, expected=(201,))

    # ------------------------------------------------------------------ #
    # convenience
    # ------------------------------------------------------------------ #
    def organization_id(self, name: str) -> str | None:
        """Return the id of an organization by name, or ``None`` if missing."""
        return (self.list_organizations().get(name) or {}).get("id")


def _retention_rules(retention_seconds: int) -> list[dict[str, Any]]:
    """
    Build the InfluxDB ``retentionRules`` payload.

    A value of ``0`` means "keep forever" and is represented by an empty list.
    """
    seconds = int(retention_seconds or 0)
    if seconds <= 0:
        return []
    return [{"type": "expire", "everySeconds": seconds}]


def bucket_retention_seconds(bucket: dict[str, Any]) -> int:
    """Return the configured retention (in seconds) of a bucket object."""
    for rule in bucket.get("retentionRules", []) or []:
        if isinstance(rule, dict) and rule.get("type", "expire") == "expire":
            return int(rule.get("everySeconds") or 0)
    return 0


_DURATION_UNITS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
}


def parse_duration(value: Any) -> int:
    """
    Convert a retention duration into seconds.

    Accepts integers (already seconds) and strings such as ``"0"``, ``"30m"``,
    ``"1h"``, ``"1d"`` or ``"2w"``. ``0`` / empty means "infinite" (kept forever).

    Args:
        value: The duration to parse.

    Returns:
        The duration in seconds (``0`` for infinite retention).

    Raises:
        ValueError: If the string cannot be parsed.
    """
    if value is None:
        return 0
    if isinstance(value, bool):
        raise ValueError(f"invalid retention duration: {value!r}")
    if isinstance(value, int):
        return max(0, value)

    text = str(value).strip().lower()
    if not text or text in ("0", "0s"):
        return 0
    if text.isdigit():
        return int(text)

    total = 0
    matched = False
    for amount, unit in re.findall(r"(\d+)([smhdw])", text):
        total += int(amount) * _DURATION_UNITS[unit]
        matched = True
    if not matched:
        raise ValueError(f"invalid retention duration: {value!r}")
    return total
