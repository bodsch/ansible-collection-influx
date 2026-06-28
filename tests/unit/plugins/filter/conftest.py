# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""Shared pytest helpers for the filter plugin unit tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

FILTER_DIR = Path(__file__).resolve().parents[4] / "plugins" / "filter"


def load_filter_module(name: str) -> Any:
    """
    Load a filter plugin by file name and return an instantiated ``FilterModule``.

    Loading by path keeps the tests runnable with plain ``pytest`` from the
    repository root, independent of an installed ``ansible_collections`` tree.

    Args:
        name: The filter file name without the ``.py`` suffix.

    Returns:
        An instance of the plugin's ``FilterModule`` class.
    """
    path = FILTER_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"filter_{name}", path)
    assert spec and spec.loader, f"cannot load filter module {name}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FilterModule()


@pytest.fixture
def load_filter():
    """Provide :func:`load_filter_module` as a fixture."""
    return load_filter_module
