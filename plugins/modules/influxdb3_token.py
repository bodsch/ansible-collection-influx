#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module to create the InfluxDB 3 operator (admin) token."""

from __future__ import annotations


DOCUMENTATION = r"""
---
module: influxdb3_token
short_description: Create the InfluxDB 3 operator (admin) token.
version_added: "1.3.0"
description:
  - Creates the operator (admin) token of an InfluxDB 3 instance via the
    C(/api/v3/configure/token/admin) endpoint.
  - InfluxDB 3 only allows a single operator token; a second creation attempt is
    reported as C(changed=false). When I(token_file) is given the created token
    is cached so subsequent runs stay idempotent and can reuse the value.
options:
  host:
    description: Base URL of the InfluxDB instance.
    type: str
    required: true
  version:
    description: The InfluxDB version; the module is a no-op for non-3 versions.
    type: str
    required: true
  auth_enabled:
    description: Whether authentication is enabled; the module is a no-op when false.
    type: bool
    required: true
  token_file:
    description:
      - Optional path used to cache the created operator token (mode C(0600)).
      - When the file already exists the cached token is returned unchanged.
    type: path
    required: false
  force:
    description: Regenerate the operator token even if one already exists.
    type: bool
    default: false
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
- name: create operator token
  bodsch.influx.influxdb3_token:
    host: "http://127.0.0.1:8181"
    version: "3.0.0"
    auth_enabled: true
    token_file: /etc/influxdb/operator.token
  register: operator
  no_log: true
"""

RETURN = r"""
token:
  description: The operator token (only present when created or cached).
  type: str
  returned: when available
msg:
  description: A human readable status message.
  type: str
  returned: always
"""

import os
from pathlib import Path
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.influx.plugins.module_utils.influxdb3 import (
    InfluxDB3Client,
    InfluxHTTPError,
)


def _major_version(value: str) -> int | None:
    """Return the leading major version number, or ``None`` when unparsable."""
    try:
        return int(str(value).strip().split(".")[0])
    except (TypeError, ValueError):
        return None


def _read_cached_token(path: Path) -> str | None:
    """Return a cached token from ``path`` if it exists and is non-empty."""
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def _write_cached_token(path: Path, token: str) -> None:
    """Persist ``token`` to ``path`` with restrictive permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token, encoding="utf-8")
    os.chmod(path, 0o600)


def main() -> None:
    """Module entrypoint."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type="str", required=True),
            version=dict(type="str", required=True),
            auth_enabled=dict(type="bool", required=True),
            token_file=dict(type="path", required=False),
            force=dict(type="bool", default=False),
            validate_certs=dict(type="bool", default=True),
            timeout=dict(type="int", default=10),
        ),
        supports_check_mode=True,
    )

    params = module.params

    major = _major_version(params["version"])
    if major is None:
        module.fail_json(msg=f"invalid version: {params['version']!r}")
        return

    if major != 3:
        module.exit_json(changed=False, failed=False, msg=f"not an InfluxDB 3 version ({params['version']}).")

    if not params["auth_enabled"]:
        module.exit_json(changed=False, failed=False, msg="authentication is disabled.")

    token_file = Path(params["token_file"]) if params.get("token_file") else None

    # An existing cache wins unless a regeneration was explicitly requested.
    if token_file and not params["force"]:
        cached = _read_cached_token(token_file)
        if cached:
            module.exit_json(changed=False, failed=False, token=cached, msg="operator token already present (cached).")

    client = InfluxDB3Client(
        module=module,
        base_url=params["host"],
        token=_read_cached_token(token_file) if token_file else None,
        validate_certs=params["validate_certs"],
        timeout=params["timeout"],
    )

    if module.check_mode:
        module.exit_json(changed=True, failed=False, msg="operator token would be created.")

    try:
        if params["force"]:
            status, body = client.regenerate_admin_token()
        else:
            status, body = client.create_admin_token()
    except InfluxHTTPError as exc:
        module.fail_json(msg=f"operator token request failed: {exc}")
        return

    token = body.get("token") if isinstance(body, dict) else None

    if token:
        if token_file:
            _write_cached_token(token_file, token)
        module.exit_json(changed=True, failed=False, token=token, msg="operator token created.")

    # No token returned: an operator token already exists server-side.
    module.exit_json(
        changed=False,
        failed=False,
        msg=f"operator token already exists (HTTP {status}); value not retrievable.",
    )


if __name__ == "__main__":
    main()
