# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Ansible jinja2 filter to render a value as a Telegraf/TOML literal."""

from __future__ import annotations

__metaclass__ = type

from typing import Any

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """Render scalars and lists into their Telegraf configuration representation."""

    def filters(self) -> dict[str, Any]:
        """Return the filters exposed by this plugin."""
        return {
            'telegraf_input_value': self.input_value,
        }

    def input_value(self, var: Any) -> tuple[bool, Any]:
        """
        Render ``var`` as a TOML compatible literal and report whether it is set.

        * positive integers and booleans are considered "set"
        * booleans become the strings ``true`` / ``false``
        * the strings ``true``/``false`` pass through lower-cased and unquoted,
          any other non-empty string is quoted
        * non-empty lists become a TOML array of quoted strings

        Args:
            var: The value to render.

        Returns:
            A ``(is_set, rendered_value)`` tuple. ``is_set`` indicates whether
            the value should be emitted; ``rendered_value`` is the TOML literal.
        """
        result = False
        result_value: Any = var

        # NOTE: bool is a subclass of int, so the int branch is evaluated first
        # for booleans by design; the bool branch then overrides the rendering.
        if isinstance(var, int) and not isinstance(var, bool) and var > 0:
            result = True

        if isinstance(var, bool):
            result = True
            result_value = "true" if var else "false"

        # AnsibleUnsafeText is a subclass of str and is matched here as well.
        if isinstance(var, str):
            if var.lower() in ("true", "false"):
                result_value = var.lower()
            else:
                result_value = '"{}"'.format(str(var))
            if len(var) > 0:
                result = True

        if isinstance(var, list) and len(var) > 0:
            _list = '","'.join(var)
            result_value = f'["{_list}"]'
            result = True

        display.v(f"= result: {result}, {result_value}")

        return result, result_value
