"""
Base class for ZeusDL site login handlers.

Each handler is responsible for authenticating with one site and returning
a populated CookieJar that can then be saved by the CookieManager.

Implementors must override:
    login(username, password) -> http.cookiejar.CookieJar

They may override:
    verify(jar) -> bool        -- test if an existing jar is still valid
"""

import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Optional


class LoginError(RuntimeError):
    """Raised when a login attempt fails (wrong credentials, site down, etc.)."""


class BaseSiteLogin(ABC):
    """Abstract base for site-specific login handlers."""

    # Subclasses set this to the primary domain (for cookie scoping)
    SITE_DOMAIN: str = ""

    # Browser-like headers to avoid trivial bot-detection
    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # ── Abstract ─────────────────────────────────

    @abstractmethod
    def login(self, username: str, password: str) -> http.cookiejar.CookieJar:
        """
        Authenticate with the site and return a populated CookieJar.
        Raise LoginError on failure.
        """

    # ── Optional override ────────────────────────

    def verify(self, jar: http.cookiejar.CookieJar) -> bool:
        """
        Return True if the cookies in jar appear to be valid (e.g. a quick
        HEAD request returns 200 instead of 401).  Default: always True.
        Subclasses can override to do a lightweight check.
        """
        return True

    # ── Helpers for subclasses ───────────────────

    def _make_opener(
        self,
        jar: Optional[http.cookiejar.CookieJar] = None,
    ) -> urllib.request.OpenerDirector:
        """Return a urllib opener with cookie support and browser-like headers."""
        if jar is None:
            jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar),
            urllib.request.HTTPRedirectHandler(),
        )
        opener.addheaders = list(self.DEFAULT_HEADERS.items())
        return opener

    def _get(
        self,
        opener: urllib.request.OpenerDirector,
        url: str,
        extra_headers: Optional[dict] = None,
        timeout: int = 30,
    ) -> tuple[int, str]:
        """GET url and return (status_code, body_text)."""
        req = urllib.request.Request(url, headers=extra_headers or {})
        try:
            with opener.open(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")

    def _post(
        self,
        opener: urllib.request.OpenerDirector,
        url: str,
        data: dict,
        extra_headers: Optional[dict] = None,
        timeout: int = 30,
    ) -> tuple[int, str]:
        """POST url-encoded data and return (status_code, body_text)."""
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(url, data=encoded, headers=headers, method="POST")
        try:
            with opener.open(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")

    def _post_json(
        self,
        opener: urllib.request.OpenerDirector,
        url: str,
        payload: dict,
        extra_headers: Optional[dict] = None,
        timeout: int = 30,
    ) -> tuple[int, dict | str]:
        """POST JSON payload and return (status_code, parsed_json_or_text)."""
        import json as _json
        body = _json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with opener.open(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                try:
                    return resp.status, _json.loads(raw)
                except Exception:
                    return resp.status, raw
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            try:
                return e.code, _json.loads(raw)
            except Exception:
                return e.code, raw

    @staticmethod
    def _hidden_inputs(html: str) -> dict[str, str]:
        """Extract hidden form inputs from an HTML page."""
        import re
        return {
            m.group(1): m.group(2)
            for m in re.finditer(
                r'<input[^>]+type=["\']hidden["\'][^>]+name=["\']([^"\']+)["\'][^>]+value=["\']([^"\']*)["\']',
                html,
                re.IGNORECASE,
            )
        }
