#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module to manage InfluxDB 3 databases via the HTTP API."""

from __future__ import annotations

from typing import Any
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb3 import (
    InfluxDB3Client,
    InfluxHTTPError,
)

DOCUMENTATION = r"""
---
module: influxdb3_database
short_description: Manage InfluxDB 3 databases.
version_added: "1.3.0"
description:
  - Creates or removes InfluxDB 3 databases through the C(/api/v3/configure/database)
    endpoint.
  - The complete set of databases is passed at once and iterated inside the module.
options:
  host:
    description: Base URL of the InfluxDB instance.
    type: str
    default: "http://127.0.0.1:8181"
  token:
    description: Operator/admin token used for authentication (omit when auth is disabled).
    type: str
    required: false
  databases:
    description:
      - Mapping of database name to its definition.
      - Each value may define C(state) (C(create)/C(present) or C(delete)/C(absent)).
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
- name: ensure databases exist
  bodsch.influx.influxdb3_database:
    host: "http://127.0.0.1:8181"
    token: "{{ operator.token }}"
    databases:
      sensors:
        state: create
      logs:
        state: create
"""

RETURN = r"""
databases:
  description: Per-database result entries (C(changed)/C(failed)/C(state)).
  type: list
  returned: always
"""


_ABSENT = ("absent", "delete", "removed")


def _ensure_database(
    client: InfluxDB3Client,
    existing: set[str],
    name: str,
    definition: dict[str, Any],
    check_mode: bool,
) -> dict[str, Any]:
    """Reconcile a single database and return its result entry."""
    state = str(definition.get("state", "create")).lower()
    present = name in existing

    if state in _ABSENT:
        if not present:
            return {"changed": False, "failed": False, "state": "already absent"}
        if check_mode:
            return {"changed": True, "failed": False, "state": "would be deleted"}
        client.delete_database(name)
        return {"changed": True, "failed": False, "state": "deleted"}

    if present:
        return {"changed": False, "failed": False, "state": "present"}
    if check_mode:
        return {"changed": True, "failed": False, "state": "would be created"}
    client.create_database(name)
    return {"changed": True, "failed": False, "state": "created"}


def main() -> None:
    """Module entrypoint."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", default="http://127.0.0.1:8181"),
            token=dict(type="str", required=False, no_log=True),
            databases=dict(type="dict", required=True),
            validate_certs=dict(type="bool", default=True),
            timeout=dict(type="int", default=10),
        ),
        supports_check_mode=True,
    )

    params = module.params
    client = InfluxDB3Client(
        module=module,
        base_url=params["host"],
        token=params["token"],
        validate_certs=params["validate_certs"],
        timeout=params["timeout"],
    )

    try:
        existing = client.list_databases()
    except InfluxHTTPError as exc:
        module.fail_json(msg=f"unable to list databases: {exc}")
        return

    result_state: list[dict[str, dict[str, Any]]] = []
    for name, definition in (params["databases"] or {}).items():
        definition = definition or {}
        try:
            entry = _ensure_database(client, existing, name, definition, module.check_mode)
        except InfluxHTTPError as exc:
            entry = {"changed": False, "failed": True, "state": str(exc)}
        result_state.append({name: entry})

    _, has_changed, has_failed, _, _, _ = results(module, result_state)

    module.exit_json(
        changed=has_changed,
        failed=has_failed,
        databases=result_state,
    )


if __name__ == "__main__":
    main()
