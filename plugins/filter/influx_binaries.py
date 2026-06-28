# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Ansible jinja2 filter to map discovered binary files to their full paths."""

from __future__ import annotations

__metaclass__ = type

import os
from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """Map a list of ``find`` results to a ``basename -> path`` dictionary."""

    def filters(self) -> dict[str, Any]:
        """Return the filters exposed by this plugin."""
        return {
            'influx_binaries': self.influx_binaries,
        }

    def influx_binaries(self, data: list[dict[str, Any]]) -> dict[str, str]:
        """
        Build a mapping of file base name to absolute path.

        Args:
            data: A list of dictionaries as returned by ``ansible.builtin.find``;
                each entry is expected to carry a ``path`` key.

        Returns:
            A dictionary mapping each file's base name to its absolute path.
            Returns an empty dictionary for any non-list input.
        """
        display.v(f"influx_binaries(self, data: {data})")

        result: dict[str, str] = {}

        if isinstance(data, list):
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                path = entry.get('path')
                if isinstance(path, str) and path:
                    result[os.path.basename(path)] = path

        display.v(f"= result: {result}")

        return result
