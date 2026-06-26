# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Ansible jinja2 filter to extract the Telegraf checksum for an OS/arch pair."""

from __future__ import annotations

__metaclass__ = type

import re
from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """Pick the matching Telegraf checksum from a list of checksum lines."""

    def filters(self) -> dict[str, Any]:
        """Return the filters exposed by this plugin."""
        return {
            'telegraf_checksum': self.checksum,
        }

    def checksum(self, data: list[str], os: str, arch: str) -> str | None:
        """
        Return the checksum for the Telegraf archive matching ``os``/``arch``.

        Args:
            data: Checksum lines of the form ``<sum>  telegraf-<ver>_<os>_<arch>.tar.gz``.
            os: The target operating system (e.g. ``linux``).
            arch: The target architecture (e.g. ``amd64``).

        Returns:
            The checksum string, or ``None`` when no line matches.
        """
        display.v(f"telegraf_checksum(self, data, os: {os}, arch: {arch})")

        if not isinstance(data, list):
            return None

        pattern = re.compile(fr".*telegraf-.*.{re.escape(os)}-{re.escape(arch)}.tar.gz")
        matches = [line for line in data if isinstance(line, str) and pattern.search(line)]

        if not matches:
            return None

        return matches[0].split(" ")[0]
