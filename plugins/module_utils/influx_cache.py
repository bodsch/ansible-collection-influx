# -*- coding: utf-8 -*-

# (c) 2020-2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
File-system cache for InfluxDB download metadata lookups.

The InfluxDB download resolver performs several remote lookups that are stable
for minutes-to-hours and either expensive or rate-limited:

- the InfluxDB 3 install script (latest-version detection)
- the GitHub Releases list / release-by-tag JSON (InfluxDB 2)
- the per-artifact ``.sha256`` files
- HEAD existence checks for tarballs

This helper caches the *raw HTTP payload* (text) per ``(method, url)`` on disk
under a configurable cache directory, with a TTL in minutes. The TTL check is
delegated to ``bodsch.core``'s ``cache_valid``; directory creation to
``bodsch.core``'s ``create_directory``.

Only successful responses are written by the caller, so a cache hit always
represents a known-good payload. Set ``cache_minutes=0`` (or an empty
``cache_dir``) to disable caching entirely.

:license: Apache-2.0
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from ansible_collections.bodsch.core.plugins.module_utils.cache.cache_valid import cache_valid
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory

# Characters not safe for a cache filename are collapsed to a single underscore.
_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


class InfluxDownloadCache:
    """
    Per-``(method, url)`` on-disk cache for InfluxDB download lookups.

    Each cache entry is a single file holding the raw HTTP payload as UTF-8
    text. The filename is derived from the HTTP method, the URL's last path
    segment (for human readability) and a short hash of ``method:url`` (to
    avoid collisions), e.g.::

        get-install_influxdb3.sh-1a2b3c4d5e6f.cache
        head-influxdb3-core-3.10.0_linux_amd64.tar.gz-0f1e2d3c4b5a.cache

    Attributes
    ----------
    module : AnsibleModule
        Ansible module instance (used for logging).
    cache_dir : pathlib.Path or None
        Absolute cache directory, or ``None`` when caching is disabled.
    cache_minutes : int
        TTL in minutes. ``0`` disables caching.
    enabled : bool
        ``True`` only when a cache directory is set and ``cache_minutes > 0``.
    """

    def __init__(self, module: Any, cache_dir: str | None, cache_minutes: int) -> None:
        """
        Initialise the cache and ensure the cache directory exists.

        :param module:        Ansible module instance (used for logging).
        :param cache_dir:     Cache directory (``~`` is expanded). Falsy values
                              disable caching.
        :param cache_minutes: TTL in minutes. ``0`` disables caching.
        """
        self.module = module
        self.cache_minutes = int(cache_minutes or 0)
        self.cache_dir = Path(cache_dir).expanduser() if cache_dir else None
        self.enabled = bool(self.cache_dir) and self.cache_minutes > 0

        if self.enabled:
            create_directory(str(self.cache_dir))

    def _path_for(self, method: str, url: str) -> Path:
        """Build the cache file path for a ``(method, url)`` pair."""
        method = method.lower()
        digest = hashlib.sha1(f"{method}:{url}".encode("utf-8")).hexdigest()[:12]
        segment = url.rstrip("/").rsplit("/", 1)[-1] or "index"
        segment = _UNSAFE_RE.sub("_", segment)[:64]
        return self.cache_dir / f"{method}-{segment}-{digest}.cache"

    def get(self, method: str, url: str) -> str | None:
        """
        Return the cached payload for ``(method, url)`` if it is still fresh.

        :returns: The cached UTF-8 payload on a fresh hit, or ``None`` on a
                  miss, expiry, or read error. Expired files are removed by
                  ``cache_valid``.
        """
        if not self.enabled:
            return None

        path = self._path_for(method, url)

        # cache_valid() returns True when the file is stale or missing
        # (and removes it). Invert to "is the cache still fresh?".
        if cache_valid(self.module, str(path), self.cache_minutes, True):
            return None

        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None

    def set(self, method: str, url: str, payload: str) -> None:
        """
        Store ``payload`` for ``(method, url)``. No-op when caching is disabled.
        """
        if not self.enabled:
            return

        path = self._path_for(method, url)
        try:
            path.write_text(payload, encoding="utf-8")
        except OSError as exc:
            self.module.log(msg=f"InfluxDownloadCache: failed to write {path}: {exc}")
