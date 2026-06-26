#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module to manage InfluxDB 2 users via the HTTP API."""

from __future__ import annotations


DOCUMENTATION = r"""
---
module: influxdb2_users
short_description: Manage InfluxDB 2 users.
version_added: "1.3.0"
description:
  - Creates or removes InfluxDB 2 users through the HTTP API and optionally
    assigns them as member or owner of an organization.
  - Passwords are only set when a user is created; existing users are left
    untouched to keep the operation idempotent.
  - The complete set of users is passed at once and iterated inside the module.
options:
  host:
    description: Base URL of the InfluxDB instance.
    type: str
    default: "http://127.0.0.1:8086"
  token:
    description: Operator token used for authentication.
    type: str
    required: true
  users:
    description:
      - Mapping of user name to its definition.
      - "Recognised keys: C(state) (C(create)/C(present) or C(delete)/C(absent)),
        C(password), and C(organization) with C(name) and C(admin)."
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
- name: ensure users exist
  bodsch.influx.influxdb2_users:
    host: "http://127.0.0.1:8086"
    token: "{{ vault_influxdb_token }}"
    users:
      admin:
        state: create
        password: "{{ vault_admin_password }}"
        organization:
          name: main-org
          admin: true
      guest01:
        state: create
        password: "{{ vault_guest_password }}"
        organization:
          name: guest-org
"""

RETURN = r"""
users:
  description: Per-user result entries (C(changed)/C(failed)/C(state)).
  type: list
  returned: always
"""

from typing import Any
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb2 import (
    InfluxDB2Client,
    InfluxHTTPError,
)

_ABSENT = ("absent", "delete", "removed")


def _ensure_membership(
    client: InfluxDB2Client,
    org_cache: dict[str, dict[str, dict[str, Any]]],
    org_id: str,
    user_name: str,
    user_id: str,
    admin: bool,
    check_mode: bool,
) -> bool:
    """Ensure org membership/ownership; return ``True`` when a change happened."""
    key = ("owners" if admin else "members", org_id)
    if key not in org_cache:
        org_cache[key] = (
            client.list_org_owners(org_id) if admin else client.list_org_members(org_id)
        )
    if user_name in org_cache[key]:
        return False
    if check_mode:
        return True
    if admin:
        client.add_org_owner(org_id, user_id)
    else:
        client.add_org_member(org_id, user_id)
    return True


def _ensure_user(
    client: InfluxDB2Client,
    existing: dict[str, dict[str, Any]],
    orgs: dict[str, dict[str, Any]],
    org_cache: dict[str, dict[str, dict[str, Any]]],
    name: str,
    definition: dict[str, Any],
    check_mode: bool,
) -> dict[str, Any]:
    """Reconcile a single user and return its result entry."""
    state = str(definition.get("state", "create")).lower()
    current = existing.get(name)

    if state in _ABSENT:
        if not current:
            return {"changed": False, "failed": False, "state": "already absent"}
        if check_mode:
            return {"changed": True, "failed": False, "state": "would be deleted"}
        client.delete_user(current["id"])
        return {"changed": True, "failed": False, "state": "deleted"}

    actions: list[str] = []
    changed = False

    if not current:
        if check_mode:
            actions.append("would be created")
            changed = True
            user_id = None
        else:
            created = client.create_user(name=name)
            user_id = created.get("id")
            actions.append("created")
            changed = True
            password = definition.get("password")
            if password and user_id:
                client.set_user_password(user_id, password)
                actions.append("password set")
    else:
        user_id = current.get("id")

    organization = definition.get("organization") or {}
    org_name = organization.get("name")
    if org_name and user_id:
        org = orgs.get(org_name)
        if not org:
            return {"changed": changed, "failed": True, "state": f"organization '{org_name}' not found"}
        admin = bool(organization.get("admin", False))
        if _ensure_membership(client, org_cache, org["id"], name, user_id, admin, check_mode):
            actions.append("owner added" if admin else "member added")
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
            users=dict(type="dict", required=True),
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
        existing = client.list_users()
        orgs = client.list_organizations()
    except InfluxHTTPError as exc:
        module.fail_json(msg=f"unable to query users/organizations: {exc}")
        return

    org_cache: dict[str, dict[str, dict[str, Any]]] = {}
    result_state: list[dict[str, dict[str, Any]]] = []
    for name, definition in (params["users"] or {}).items():
        definition = definition or {}
        try:
            entry = _ensure_user(client, existing, orgs, org_cache, name, definition, module.check_mode)
        except InfluxHTTPError as exc:
            entry = {"changed": False, "failed": True, "state": str(exc)}
        result_state.append({name: entry})

    _, has_changed, has_failed, _, _, _ = results(module, result_state)

    module.exit_json(
        changed=has_changed,
        failed=has_failed,
        users=result_state,
    )


if __name__ == "__main__":
    main()
