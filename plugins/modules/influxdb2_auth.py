#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module to manage InfluxDB 2 authorizations (API tokens)."""

from __future__ import annotations

from typing import Any
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb2 import (
    InfluxDB2Client,
    InfluxHTTPError,
)

DOCUMENTATION = r"""
---
module: influxdb2_auth
short_description: Manage InfluxDB 2 authorizations (API tokens).
version_added: "1.3.0"
description:
  - Creates, removes or toggles InfluxDB 2 authorizations through the HTTP API.
  - Authorizations are matched by their C(description); when no permissions are
    supplied, read and write access to all buckets of the given organization is
    granted by default.
  - The complete set of authorizations is passed at once and iterated inside the
    module.
options:
  host:
    description: Base URL of the InfluxDB instance.
    type: str
    default: "http://127.0.0.1:8086"
  token:
    description: Operator token used for authentication.
    type: str
    required: true
  authorizations:
    description:
      - Mapping of authorization description to its definition.
      - "Recognised keys: C(state) (C(create)/C(present), C(delete)/C(absent),
        C(active) or C(inactive)), C(organization) (name) and C(permissions)."
    type: dict
    required: true
  validate_certs:
    description: Whether to validate TLS certificates.
    type: bool
    default: true
  timeout:
    description: HTTP request timeout in seconds.
    type: int
    default: 10
author:
  - Bodo Schulz (@bodsch)
"""

EXAMPLES = r"""
- name: ensure read/write token for main-org exists
  bodsch.influx.influxdb2_auth:
    host: "http://127.0.0.1:8086"
    token: "{{ vault_influxdb_token }}"
    authorizations:
      telegraf-rw:
        state: create
        organization:
          name: main-org
"""

RETURN = r"""
authorizations:
  description: Per-authorization result entries (C(changed)/C(failed)/C(state)).
  type: list
  returned: always
"""


_ABSENT = ("absent", "delete", "removed")
_STATUS = ("active", "inactive")


def _default_permissions(org_id: str) -> list[dict[str, Any]]:
    """Grant read and write access to all buckets of an organization."""
    return [
        {"action": "read", "resource": {"type": "buckets", "orgID": org_id}},
        {"action": "write", "resource": {"type": "buckets", "orgID": org_id}},
    ]


def _find(existing: list[dict[str, Any]], description: str) -> dict[str, Any] | None:
    """Return the first authorization matching ``description``."""
    for auth in existing:
        if auth.get("description") == description:
            return auth
    return None


def _ensure_authorization(
    client: InfluxDB2Client,
    existing: list[dict[str, Any]],
    orgs: dict[str, dict[str, Any]],
    description: str,
    definition: dict[str, Any],
    check_mode: bool,
) -> dict[str, Any]:
    """Reconcile a single authorization and return its result entry."""
    state = str(definition.get("state", "create")).lower()
    current = _find(existing, description)

    if state in _ABSENT:
        if not current:
            return {"changed": False, "failed": False, "state": "already absent"}
        if check_mode:
            return {"changed": True, "failed": False, "state": "would be deleted"}
        client.delete_authorization(current["id"])
        return {"changed": True, "failed": False, "state": "deleted"}

    changed = False
    actions: list[str] = []

    if not current:
        organization = definition.get("organization") or {}
        org = orgs.get(organization.get("name")) if organization.get("name") else None
        if not org:
            return {"changed": False, "failed": True, "state": "organization not found"}
        permissions = definition.get("permissions") or _default_permissions(org["id"])
        if check_mode:
            actions.append("would be created")
            changed = True
        else:
            current = client.create_authorization(org["id"], permissions, description=description)
            actions.append("created")
            changed = True

    desired_status = state if state in _STATUS else None
    if desired_status and current and current.get("status") not in (None, desired_status):
        if check_mode:
            actions.append(f"would be set {desired_status}")
        else:
            client.set_authorization_status(current["id"], desired_status)
            actions.append(f"set {desired_status}")
        changed = True

    if not actions:
        return {"changed": False, "failed": False, "state": "present"}
    return {"changed": changed, "failed": False, "state": ", ".join(actions)}


def main() -> None:
    """Module entrypoint."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", default="http://127.0.0.1:8086"),
            token=dict(type="str", required=True, no_log=True),
            authorizations=dict(type="dict", required=True),
            validate_certs=dict(type="bool", default=True),
            timeout=dict(type="int", default=10),
        ),
        supports_check_mode=True,
    )

    params = module.params
    client = InfluxDB2Client(
        module=module,
        base_url=params["host"],
        token=params["token"],
        validate_certs=params["validate_certs"],
        timeout=params["timeout"],
    )

    try:
        existing = client.list_authorizations()
        orgs = client.list_organizations()
    except InfluxHTTPError as exc:
        module.fail_json(msg=f"unable to query authorizations/organizations: {exc}")
        return

    result_state: list[dict[str, dict[str, Any]]] = []
    for description, definition in (params["authorizations"] or {}).items():
        definition = definition or {}
        try:
            entry = _ensure_authorization(client, existing, orgs, description, definition, module.check_mode)
        except InfluxHTTPError as exc:
            entry = {"changed": False, "failed": True, "state": str(exc)}
        result_state.append({description: entry})

    _, has_changed, has_failed, _, _, _ = results(module, result_state)

    module.exit_json(
        changed=has_changed,
        failed=has_failed,
        authorizations=result_state,
    )


if __name__ == "__main__":
    main()
