#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2020-2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""Ansible module to resolve InfluxDB download metadata for Linux tarballs."""

from __future__ import annotations


DOCUMENTATION = r"""
---
module: influx_download_data
short_description: Resolve InfluxDB tarball download metadata for Linux.
version_added: "1.3.0"
description:
  - Resolves the concrete version, artifact name, download URL and SHA256
    checksum for an InfluxDB OSS v2 or InfluxDB 3 (core/enterprise) Linux tarball.
  - Linux only; no OS packages and no container installation.
options:
  major_version:
    description: The InfluxDB major version line.
    type: int
    required: true
    choices: [2, 3]
  version:
    description: A pinned version (C(x.y.z)) or C(latest).
    type: str
    required: true
  influxdb3_edition:
    description: The InfluxDB 3 edition (only relevant for C(major_version=3)).
    type: str
    default: core
    choices: [core, enterprise]
  download_base:
    description: Base URL for download artifacts.
    type: str
    default: "https://dl.influxdata.com/influxdb/releases"
  architecture:
    description: Target architecture (e.g. C(x86_64), C(amd64), C(aarch64), C(arm64)).
    type: str
    default: x86_64
  github_token:
    description: Optional GitHub token to raise the API rate limit (v2 resolution).
    type: str
    default: ""
  timeout:
    description: HTTP request timeout in seconds.
    type: int
    default: 15
  validate_certs:
    description: Whether to validate TLS certificates.
    type: bool
    default: true
  user_agent:
    description: The HTTP C(User-Agent) header value.
    type: str
    default: "ansible-influx-downloads"
author:
  - Bodo Schulz (@bodsch)
"""

EXAMPLES = r"""
- name: resolve latest InfluxDB 3 core download
  bodsch.influx.influx_download_data:
    major_version: 3
    version: latest
    architecture: "{{ ansible_architecture }}"
  register: influx_download
"""

RETURN = r"""
version:
  description: The resolved version.
  type: str
  returned: success
download_artifact:
  description: The resolved artifact file name.
  type: str
  returned: success
download_url:
  description: The resolved download URL.
  type: str
  returned: success
download_checksum:
  description: The SHA256 checksum of the artifact.
  type: str
  returned: success
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.influx.plugins.module_utils.influx_downloads import InfluxDownloads


def main() -> None:
    """Module entrypoint."""
    module = AnsibleModule(
        argument_spec=dict(
            major_version=dict(type="int", required=True, choices=[2, 3]),
            version=dict(type="str", required=True),
            influxdb3_edition=dict(type="str", default="core", choices=["core", "enterprise"]),
            download_base=dict(type="str", default=InfluxDownloads._DEFAULT_DOWNLOAD_BASE),
            architecture=dict(type="str", default="x86_64"),
            github_token=dict(type="str", default="", no_log=True),
            timeout=dict(type="int", default=15),
            validate_certs=dict(type="bool", default=True),
            user_agent=dict(type="str", default="ansible-influx-downloads"),
        ),
        supports_check_mode=True,
    )

    helper = InfluxDownloads(module)
    result = helper.run()

    if result.get("failed"):
        module.fail_json(**result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
