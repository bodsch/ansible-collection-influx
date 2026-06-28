#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module to check the health of an InfluxDB 3 instance via the HTTP API."""

from __future__ import annotations


DOCUMENTATION = r"""
---
module: influxdb3_ping
short_description: Check whether an InfluxDB 3 instance is up and healthy.
version_added: "1.3.0"
description:
  - Queries the InfluxDB 3 C(/health) endpoint via the HTTP API.
  - The module never fails on an unreachable instance, so it can be combined
    with C(retries)/C(until) while waiting for the service to come up.
options:
  host:
    description: Base URL of the InfluxDB instance.
    type: str
    default: "http://127.0.0.1:8181"
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
- name: ensure influxdb 3 is up and running
  bodsch.influx.influxdb3_ping:
    host: "http://127.0.0.1:8181"
  register: ping
  retries: 10
  delay: 5
  until: ping.reachable
"""

RETURN = r"""
reachable:
  description: Whether the C(/health) endpoint returned a healthy status.
  type: bool
  returned: always
rc:
  description: Convenience return code (C(0) when reachable, otherwise C(1)).
  type: int
  returned: always
status:
  description: The HTTP status code of the health request.
  type: int
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb3 import (
    InfluxDB3Client,
    InfluxHTTPError,
)


def main() -> None:
    """Module entrypoint."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", default="http://127.0.0.1:8181"),
            validate_certs=dict(type="bool", default=True),
            timeout=dict(type="int", default=10),
        ),
        supports_check_mode=True,
    )

    client = InfluxDB3Client(
        module=module,
        base_url=module.params["host"],
        validate_certs=module.params["validate_certs"],
        timeout=module.params["timeout"],
    )

    result: dict[str, object] = dict(changed=False, failed=False, reachable=False, rc=1, status=0)

    try:
        status, body = client.health()
        result["status"] = status
        result["reachable"] = 200 <= status < 300
        result["rc"] = 0 if 200 <= status < 300 else 1
        if isinstance(body, dict) and body.get("version"):
            result["version"] = body["version"]
    except InfluxHTTPError as exc:
        result["status"] = exc.status
        result["msg"] = str(exc)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
