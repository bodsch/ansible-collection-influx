#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module for the initial InfluxDB 2 onboarding via the HTTP API."""

from __future__ import annotations


DOCUMENTATION = r"""
---
module: influxdb2_setup
short_description: Perform the initial InfluxDB 2 onboarding.
version_added: "1.3.0"
description:
  - Creates the first user, organization, bucket and operator token using the
    InfluxDB 2 C(/api/v2/setup) endpoint.
  - The operation is idempotent; onboarding is only performed while the instance
    reports that setup is still allowed.
options:
  host:
    description: Base URL of the InfluxDB instance.
    type: str
    default: "http://127.0.0.1:8086"
  username:
    description: Name of the initial admin user.
    type: str
    required: true
  password:
    description: Password of the initial admin user.
    type: str
    required: true
  org:
    description: Name of the initial organization.
    type: str
    required: true
  bucket:
    description: Name of the initial bucket.
    type: str
    required: true
  token:
    description: Operator token to assign during onboarding (generated when omitted).
    type: str
    required: false
  retention:
    description:
      - Retention period of the initial bucket.
      - Accepts a duration such as C(0), C(30m), C(1h), C(1d) or C(2w);
        C(0) keeps data forever.
    type: str
    default: "0"
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
- name: set influxdb default user, organization, and bucket
  bodsch.influx.influxdb2_setup:
    host: "http://127.0.0.1:8086"
    org: "example-org"
    bucket: "example-bucket"
    username: "example-user"
    password: "{{ vault_influxdb_password }}"
    token: "{{ vault_influxdb_token }}"
"""

RETURN = r"""
changed:
  description: Whether onboarding was performed.
  type: bool
  returned: always
msg:
  description: A human readable status message.
  type: str
  returned: always
org:
  description: The configured organization name.
  type: str
  returned: when changed
bucket:
  description: The configured bucket name.
  type: str
  returned: when changed
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb2 import (
    InfluxDB2Client,
    InfluxHTTPError,
    parse_duration,
)


def main() -> None:
    """Module entrypoint."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", default="http://127.0.0.1:8086"),
            username=dict(type="str", required=True),
            password=dict(type="str", required=True, no_log=True),
            org=dict(type="str", required=True),
            bucket=dict(type="str", required=True),
            token=dict(type="str", required=False, no_log=True),
            retention=dict(type="str", default="0"),
            validate_certs=dict(type="bool", default=True),
            timeout=dict(type="int", default=10),
        ),
        supports_check_mode=True,
    )

    params = module.params
    client = InfluxDB2Client(
        module=module,
        base_url=params["host"],
        token=params.get("token"),
        validate_certs=params["validate_certs"],
        timeout=params["timeout"],
    )

    try:
        retention_seconds = parse_duration(params["retention"])
    except ValueError as exc:
        module.fail_json(msg=str(exc))

    try:
        allowed = client.onboarding_allowed()
    except InfluxHTTPError as exc:
        module.fail_json(msg=f"unable to query setup status: {exc}")
        return

    if not allowed:
        module.exit_json(changed=False, failed=False, msg="InfluxDB has already been set up.")

    if module.check_mode:
        module.exit_json(
            changed=True,
            failed=False,
            msg="InfluxDB onboarding would be performed.",
            org=params["org"],
            bucket=params["bucket"],
        )

    try:
        client.setup(
            username=params["username"],
            password=params["password"],
            org=params["org"],
            bucket=params["bucket"],
            token=params.get("token"),
            retention_seconds=retention_seconds,
        )
    except InfluxHTTPError as exc:
        module.fail_json(msg=f"InfluxDB onboarding failed: {exc}")

    module.exit_json(
        changed=True,
        failed=False,
        msg="InfluxDB onboarding completed.",
        org=params["org"],
        bucket=params["bucket"],
    )


if __name__ == "__main__":
    main()
