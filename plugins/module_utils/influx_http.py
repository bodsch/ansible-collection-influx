# -*- coding: utf-8 -*-

# (c) 2026, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
Minimal HTTP client for the InfluxDB v2 and v3 REST APIs.

The client wraps :func:`ansible.module_utils.urls.fetch_url` and provides
JSON encoding/decoding, an authorization header (``Token`` for v2,
``Bearer`` for v3) and a uniform error type. It deliberately avoids
``subprocess`` and third-party HTTP libraries.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class InfluxHTTPError(Exception):
    """
    Raised for transport failures and unexpected HTTP status codes.

    Attributes:
        status: The HTTP status code (``0`` for transport-level errors).
        url: The request URL.
        body: The parsed response body (``dict``/``list``) or raw text.
    """

    def __init__(self, message: str, status: int = 0, url: str = "", body: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.url = url
        self.body = body


class InfluxHTTP:
    """Thin JSON-over-HTTP client around ``fetch_url``."""

    def __init__(
        self,
        module: AnsibleModule,
        base_url: str,
        token: str | None = None,
        auth_scheme: str = "Token",
        validate_certs: bool = True,
        timeout: int = 10,
        user_agent: str = "ansible-bodsch-influx",
    ) -> None:
        """
        Initialize the client.

        Args:
            module: The owning :class:`AnsibleModule`.
            base_url: The InfluxDB base URL, e.g. ``http://127.0.0.1:8086``.
            token: An optional API token used for the ``Authorization`` header.
            auth_scheme: ``Token`` (InfluxDB 2) or ``Bearer`` (InfluxDB 3).
            validate_certs: Whether to verify TLS certificates.
            timeout: The per-request timeout in seconds.
            user_agent: The ``User-Agent`` header value.
        """
        self.module = module
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.auth_scheme = auth_scheme
        self.validate_certs = bool(validate_certs)
        self.timeout = int(timeout)
        self.user_agent = user_agent

        # Older ansible-core reads validate_certs from module.params (no kwarg).
        self.module.params.setdefault("validate_certs", self.validate_certs)

    # ------------------------------------------------------------------ #
    # public helpers
    # ------------------------------------------------------------------ #
    def get(self, path: str, query: dict[str, Any] | None = None, **kwargs: Any) -> tuple[int, Any]:
        """Perform a ``GET`` request."""
        return self.request("GET", path, query=query, **kwargs)

    def post(self, path: str, body: Any = None, **kwargs: Any) -> tuple[int, Any]:
        """Perform a ``POST`` request."""
        return self.request("POST", path, body=body, **kwargs)

    def patch(self, path: str, body: Any = None, **kwargs: Any) -> tuple[int, Any]:
        """Perform a ``PATCH`` request."""
        return self.request("PATCH", path, body=body, **kwargs)

    def delete(self, path: str, query: dict[str, Any] | None = None, **kwargs: Any) -> tuple[int, Any]:
        """Perform a ``DELETE`` request."""
        return self.request("DELETE", path, query=query, **kwargs)

    def request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
        expected: tuple[int, ...] | None = None,
        authorize: bool = True,
    ) -> tuple[int, Any]:
        """
        Perform an HTTP request and return ``(status, parsed_body)``.

        Args:
            method: The HTTP verb.
            path: The request path (joined with ``base_url``).
            query: Optional query parameters.
            body: An optional request body; ``dict``/``list`` are JSON encoded.
            headers: Additional request headers.
            expected: When given, a status not contained raises
                :class:`InfluxHTTPError`.
            authorize: Whether to attach the ``Authorization`` header.

        Returns:
            A tuple of the HTTP status code and the parsed response body
            (``dict``/``list`` for JSON, ``str`` otherwise, ``None`` if empty).

        Raises:
            InfluxHTTPError: On transport errors or unexpected status codes.
        """
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urlencode({k: v for k, v in query.items() if v is not None})}"

        request_headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        if authorize and self.token:
            request_headers["Authorization"] = f"{self.auth_scheme} {self.token}"
        if headers:
            request_headers.update(headers)

        data: bytes | None = None
        if body is not None:
            if isinstance(body, (dict, list)):
                data = json.dumps(body).encode("utf-8")
                request_headers.setdefault("Content-Type", "application/json")
            elif isinstance(body, str):
                data = body.encode("utf-8")
            elif isinstance(body, bytes):
                data = body

        self.module.log(f"InfluxHTTP::request({method} {url})")

        resp, info = self._fetch(url, method=method, data=data, headers=request_headers)

        status = int(info.get("status") or 0)
        parsed = self._parse_body(resp, info)

        if status <= 0:
            raise InfluxHTTPError(
                f"{method} {url} failed: {info.get('msg', 'connection error')}",
                status=status,
                url=url,
                body=parsed,
            )

        if expected is not None and status not in expected:
            raise InfluxHTTPError(
                f"{method} {url} returned HTTP {status}: {self._error_message(parsed, info)}",
                status=status,
                url=url,
                body=parsed,
            )

        return status, parsed

    # ------------------------------------------------------------------ #
    # private API
    # ------------------------------------------------------------------ #
    def _fetch(
        self,
        url: str,
        method: str,
        data: bytes | None,
        headers: dict[str, str],
    ) -> tuple[Any, dict[str, Any]]:
        """
        Call ``fetch_url`` while staying compatible across ansible-core versions.

        Newer ansible-core accepts the ``validate_certs`` keyword; older versions
        read it from ``module.params`` and reject the keyword.
        """
        try:
            return fetch_url(
                self.module,
                url,
                method=method,
                data=data,
                headers=headers,
                timeout=self.timeout,
                validate_certs=self.validate_certs,
            )
        except TypeError:
            self.module.params.setdefault("validate_certs", self.validate_certs)
            return fetch_url(
                self.module,
                url,
                method=method,
                data=data,
                headers=headers,
                timeout=self.timeout,
            )

    @staticmethod
    def _parse_body(resp: Any, info: dict[str, Any]) -> Any:
        """Read and decode a response body, parsing JSON when possible."""
        raw = b""
        if resp is not None:
            try:
                raw = resp.read()
            except (AttributeError, ValueError):
                raw = b""
        # On error, fetch_url stores the body in info["body"].
        if not raw and info.get("body"):
            raw = info["body"]

        if not raw:
            return None

        text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
        text = text.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    @staticmethod
    def _error_message(parsed: Any, info: dict[str, Any]) -> str:
        """Build a concise error message from a parsed body or fetch_url info."""
        if isinstance(parsed, dict):
            for key in ("message", "msg", "error", "err"):
                if parsed.get(key):
                    return str(parsed[key])
        if isinstance(parsed, str) and parsed:
            return parsed
        return str(info.get("msg") or "unknown error")
