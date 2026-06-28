#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module to manage InfluxDB 2 buckets via the HTTP API."""

from __future__ import annotations


DOCUMENTATION = r"""
---
module: influxdb2_buckets
short_description: Manage InfluxDB 2 buckets.
version_added: "1.3.0"
description:
  - Creates, updates or removes InfluxDB 2 buckets through the HTTP API.
  - The complete set of buckets is passed at once and iterated inside the module.
options:
  host:
    description: Base URL of the InfluxDB instance.
    type: str
    default: "http://127.0.0.1:8086"
  token:
    description: Operator token used for authentication.
    type: str
    required: true
  buckets:
    description:
      - Mapping of bucket name to its definition.
      - "Recognised keys: C(state) (C(create)/C(present) or C(delete)/C(absent)),
        C(description), C(organization) with C(name), and C(retention) (e.g.
        C(0), C(30m), C(1d))."
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
- name: ensure buckets exist
  bodsch.influx.influxdb2_buckets:
    host: "http://127.0.0.1:8086"
    token: "{{ vault_influxdb_token }}"
    buckets:
      bucket01:
        state: create
        description: First bucket
        organization:
          name: main-org
        retention: 1d
"""

RETURN = r"""
buckets:
  description: Per-bucket result entries (C(changed)/C(failed)/C(state)).
  type: list
  returned: always
"""

from typing import Any
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb2 import (
    InfluxDB2Client,
    InfluxHTTPError,
    bucket_retention_seconds,
    parse_duration,
)

_ABSENT = ("absent", "delete", "removed")


def _ensure_bucket(
    client: InfluxDB2Client,
    existing: dict[str, dict[str, Any]],
    orgs: dict[str, dict[str, Any]],
    name: str,
    definition: dict[str, Any],
    check_mode: bool,
) -> dict[str, Any]:
    """Reconcile a single bucket and return its result entry."""
    state = str(definition.get("state", "create")).lower()
    current = existing.get(name)

    if state in _ABSENT:
        if not current:
            return {"changed": False, "failed": False, "state": "already absent"}
        if check_mode:
            return {"changed": True, "failed": False, "state": "would be deleted"}
        client.delete_bucket(current["id"])
        return {"changed": True, "failed": False, "state": "deleted"}

    description = definition.get("description")
    retention_seconds = parse_duration(definition.get("retention"))

    if not current:
        organization = definition.get("organization") or {}
        org_name = organization.get("name")
        org = orgs.get(org_name) if org_name else None
        if not org:
            return {"changed": False, "failed": True, "state": f"organization '{org_name}' not found"}
        if check_mode:
            return {"changed": True, "failed": False, "state": "would be created"}
        client.create_bucket(
            org_id=org["id"],
            name=name,
            description=description,
            retention_seconds=retention_seconds,
        )
        return {"changed": True, "failed": False, "state": "created"}

    needs_update = bucket_retention_seconds(current) != retention_seconds or (
        description is not None and current.get("description", "") != description
    )
    if not needs_update:
        return {"changed": False, "failed": False, "state": "present"}
    if check_mode:
        return {"changed": True, "failed": False, "state": "would be updated"}
    client.update_bucket(
        current["id"],
        retention_seconds=retention_seconds,
        description=description,
    )
    return {"changed": True, "failed": False, "state": "updated"}


def main() -> None:
    """Module entrypoint."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", default="http://127.0.0.1:8086"),
            token=dict(type="str", required=True, no_log=True),
            buckets=dict(type="dict", required=True),
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
        existing = client.list_buckets()
        orgs = client.list_organizations()
    except InfluxHTTPError as exc:
        module.fail_json(msg=f"unable to query buckets/organizations: {exc}")
        return

    result_state: list[dict[str, dict[str, Any]]] = []
    for name, definition in (params["buckets"] or {}).items():
        definition = definition or {}
        try:
            entry = _ensure_bucket(client, existing, orgs, name, definition, module.check_mode)
        except (InfluxHTTPError, ValueError) as exc:
            entry = {"changed": False, "failed": True, "state": str(exc)}
        result_state.append({name: entry})

    _, has_changed, has_failed, _, _, _ = results(module, result_state)

    module.exit_json(
        changed=has_changed,
        failed=has_failed,
        buckets=result_state,
    )


if __name__ == "__main__":
    main()
