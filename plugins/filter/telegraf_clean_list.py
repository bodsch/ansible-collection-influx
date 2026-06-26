# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Ansible jinja2 filter to drop Telegraf plugin entries without a config."""

from __future__ import annotations

__metaclass__ = type

from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """Filter a list of Telegraf plugin definitions to those carrying a config."""

    def filters(self) -> dict[str, Any]:
        """Return the filters exposed by this plugin."""
        return {
            'telegraf_clean_list': self.telegraf_clean_list,
        }

    def telegraf_clean_list(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Return only the entries that define a non-empty ``config``.

        Args:
            data: A list of Telegraf plugin definitions.

        Returns:
            The subset of ``data`` whose entries provide a truthy ``config``.
        """
        result: list[dict[str, Any]] = []

        if isinstance(data, list):
            result = [entry for entry in data if isinstance(entry, dict) and entry.get('config')]

        display.v(f"= result: {result}")

        return result
