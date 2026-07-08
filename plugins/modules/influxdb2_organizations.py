#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module to manage InfluxDB 2 organizations via the HTTP API."""

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
module: influxdb2_organizations
short_description: Manage InfluxDB 2 organizations.
version_added: "1.3.0"
description:
  - Creates or removes InfluxDB 2 organizations through the HTTP API.
  - The complete set of organizations is passed at once and iterated inside the
    module; no Ansible C(loop) is required.
options:
  host:
    description: Base URL of the InfluxDB instance.
    type: str
    default: "http://127.0.0.1:8086"
  token:
    description: Operator token used for authentication.
    type: str
    required: true
  organizations:
    description:
      - Mapping of organization name to its definition.
      - Each value may define C(state) (C(create)/C(present) or C(delete)/C(absent))
        and an optional C(description).
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
- name: ensure organizations exist
  bodsch.influx.influxdb2_organizations:
    host: "http://127.0.0.1:8086"
    token: "{{ vault_influxdb_token }}"
    organizations:
      main-org:
        state: create
        description: Main organization
      guest-org:
        state: create
"""

RETURN = r"""
organizations:
  description: Per-organization result entries (C(changed)/C(failed)/C(state)).
  type: list
  returned: always
"""


_ABSENT = ("absent", "delete", "removed")


def _ensure_organization(
    client: InfluxDB2Client,
    existing: dict[str, dict[str, Any]],
    name: str,
    definition: dict[str, Any],
    check_mode: bool,
) -> dict[str, Any]:
    """Reconcile a single organization and return its result entry."""
    state = str(definition.get("state", "create")).lower()
    description = definition.get("description")
    current = existing.get(name)

    if state in _ABSENT:
        if not current:
            return {"changed": False, "failed": False, "state": "already absent"}
        if check_mode:
            return {"changed": True, "failed": False, "state": "would be deleted"}
        client.delete_organization(current["id"])
        return {"changed": True, "failed": False, "state": "deleted"}

    if not current:
        if check_mode:
            return {"changed": True, "failed": False, "state": "would be created"}
        client.create_organization(name=name, description=description)
        return {"changed": True, "failed": False, "state": "created"}

    if description is not None and current.get("description", "") != description:
        if check_mode:
            return {"changed": True, "failed": False, "state": "would be updated"}
        client.update_organization(current["id"], description=description)
        return {"changed": True, "failed": False, "state": "updated"}

    return {"changed": False, "failed": False, "state": "present"}


def main() -> None:
    """Module entrypoint."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", default="http://127.0.0.1:8086"),
            token=dict(type="str", required=True, no_log=True),
            organizations=dict(type="dict", required=True),
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
        existing = client.list_organizations()
    except InfluxHTTPError as exc:
        module.fail_json(msg=f"unable to list organizations: {exc}")
        return

    result_state: list[dict[str, dict[str, Any]]] = []
    for name, definition in (params["organizations"] or {}).items():
        definition = definition or {}
        try:
            entry = _ensure_organization(client, existing, name, definition, module.check_mode)
        except InfluxHTTPError as exc:
            entry = {"changed": False, "failed": True, "state": str(exc)}
        result_state.append({name: entry})

    _, has_changed, has_failed, _, _, _ = results(module, result_state)

    module.exit_json(
        changed=has_changed,
        failed=has_failed,
        organizations=result_state,
    )


if __name__ == "__main__":
    main()
