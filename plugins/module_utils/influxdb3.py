# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
High level client for the InfluxDB 3 (Core/Enterprise) REST API (``/api/v3``).

Covers operator/admin token creation and database management on top of
:class:`InfluxHTTP` using the ``Bearer`` authorization scheme.
"""

from __future__ import annotations

from typing import Any

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.bodsch.influx.plugins.module_utils.influx_http import (
    InfluxHTTP,
    InfluxHTTPError,
)

__all__ = ["InfluxDB3Client", "InfluxHTTPError"]

# Keys an InfluxDB 3 "list databases" entry may use for the database name.
_DB_NAME_KEYS = ("iox::database", "db", "database", "name")


class InfluxDB3Client(InfluxHTTP):
    """Resource oriented client for InfluxDB 3."""

    def __init__(
        self,
        module: AnsibleModule,
        base_url: str,
        token: str | None = None,
        validate_certs: bool = True,
        timeout: int = 10,
    ) -> None:
        """Initialize the client using the ``Bearer`` authorization scheme."""
        super().__init__(
            module=module,
            base_url=base_url,
            token=token,
            auth_scheme="Bearer",
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
        """Return ``(status, body)`` of the ``/ping`` endpoint."""
        return self.get("/ping", authorize=False)

    # ------------------------------------------------------------------ #
    # admin token
    # ------------------------------------------------------------------ #
    def create_admin_token(self) -> tuple[int, dict[str, Any]]:
        """
        Create the operator (admin) token.

        Before authorization is configured this endpoint requires no token.
        A second creation attempt returns a conflict status because only one
        operator token can exist.

        Returns:
            ``(status, body)``; ``body`` carries ``token`` on success (201).
        """
        status, body = self.post(
            "/api/v3/configure/token/admin",
            authorize=False,
            expected=(201, 200, 400, 409),
        )
        return status, body if isinstance(body, dict) else {}

    def regenerate_admin_token(self) -> tuple[int, dict[str, Any]]:
        """Regenerate the operator (admin) token (requires a valid token)."""
        status, body = self.post(
            "/api/v3/configure/token/admin/regenerate",
            expected=(201, 200),
        )
        return status, body if isinstance(body, dict) else {}

    def create_named_admin_token(self, name: str, expiry_secs: int | None = None) -> dict[str, Any]:
        """Create a named admin token (requires a valid operator token)."""
        payload: dict[str, Any] = {"token_name": name}
        if expiry_secs:
            payload["expiry_secs"] = int(expiry_secs)
        _, body = self.post("/api/v3/configure/token/named_admin", body=payload, expected=(201, 200))
        return body if isinstance(body, dict) else {}

    # ------------------------------------------------------------------ #
    # databases
    # ------------------------------------------------------------------ #
    def list_databases(self) -> set[str]:
        """Return the set of existing (non-deleted) database names."""
        _, body = self.get("/api/v3/configure/database", query={"format": "json"}, expected=(200,))
        names: set[str] = set()
        rows = body if isinstance(body, list) else (body.get("databases") if isinstance(body, dict) else [])
        for row in rows or []:
            name = _database_name(row)
            if name:
                names.add(name)
        return names

    def create_database(self, name: str) -> None:
        """Create a database by name."""
        self.post("/api/v3/configure/database", body={"db": name}, expected=(200, 201))

    def delete_database(self, name: str) -> None:
        """Delete a database by name."""
        self.delete("/api/v3/configure/database", query={"db": name}, expected=(200, 204))


def _database_name(row: Any) -> str | None:
    """Extract the database name from a list-databases row."""
    if isinstance(row, str):
        return row
    if isinstance(row, dict):
        for key in _DB_NAME_KEYS:
            if row.get(key):
                return str(row[key])
    return None
