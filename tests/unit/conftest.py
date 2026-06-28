# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE)

"""
Bootstrap an importable ``ansible_collections`` tree for the unit tests.

This lets ``module_utils`` and module code (which use fully qualified
``ansible_collections.bodsch.influx...`` imports) be imported under plain
``pytest`` without an installed collection. Under ``ansible-test units`` the
tree already exists, so the bootstrap simply becomes a no-op addition.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _find_dependency(name: str) -> Path | None:
    """Locate an installed sibling collection (e.g. ``core``)."""
    candidates: list[Path] = []
    for entry in os.environ.get("ANSIBLE_COLLECTIONS_PATH", "").split(os.pathsep):
        if entry:
            candidates.append(Path(entry) / "ansible_collections" / "bodsch" / name)
    candidates.append(Path.home() / ".ansible" / "collections" / "ansible_collections" / "bodsch" / name)
    candidates.append(Path("/usr/share/ansible/collections/ansible_collections/bodsch") / name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _bootstrap_collections_path() -> None:
    """Create a temporary collections tree symlinked to this repository."""
    root = Path(tempfile.gettempdir()) / "bodsch_influx_unit_collections"
    namespace = root / "ansible_collections" / "bodsch"
    namespace.mkdir(parents=True, exist_ok=True)

    influx = namespace / "influx"
    if not influx.exists():
        influx.symlink_to(_REPO_ROOT, target_is_directory=True)

    for dependency in ("core", "systemd", "scm"):
        link = namespace / dependency
        source = _find_dependency(dependency)
        if source and not link.exists():
            link.symlink_to(source, target_is_directory=True)

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


_bootstrap_collections_path()
