"""
SessionGuard — the main entry point for ZeusDL's auth system.

Responsibilities
────────────────
• Given a URL (or site key), ensure that fresh, valid cookies exist for that site
• If cookies are stale or missing → call the appropriate login handler
• If login handler is not available → fall back to --username/--password flags
• On HTTP 401/403 during a download → invalidate cookies and retry once

Typical usage in download_manager
──────────────────────────────────
    from zeusdl.auth import SessionGuard

    guard = SessionGuard()
    ctx = guard.ensure(url)           # returns AuthContext
    ydl_opts = {**ctx.ydl_opts}       # pass these to YoutubeDL()

AuthContext.ydl_opts contains one of:
    {"cookiefile": "/path/to/cookies.txt"}
    {"username": "...", "password": "..."}
    {}   (no auth needed / no credentials saved)
"""

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .cookie_manager import CookieManager, get_manager
from .credential_store import CredentialStore, SITE_REGISTRY, get_store
from .login_handlers import get_handler


# ─────────────────────────────────────────────────
# AuthContext — what the caller uses
# ─────────────────────────────────────────────────

@dataclass
class AuthContext:
    """Result returned by SessionGuard.ensure()."""

    site: Optional[str] = None
    method: str = "none"           # "cookies" | "password" | "none"
    cookie_file: Optional[Path] = None
    username: Optional[str] = None

    @property
    def ydl_opts(self) -> dict:
        """Return the dict to merge into YoutubeDL params."""
        if self.method == "cookies" and self.cookie_file:
            return {"cookiefile": str(self.cookie_file)}
        if self.method == "password" and self.username:
            # SessionGuard deliberately does NOT keep password in memory beyond
            # what's needed — the caller reads it fresh from the store.
            cred = get_store().load(self.site)
            if cred:
                return {"username": cred["username"], "password": cred["password"]}
        return {}

    @property
    def is_authenticated(self) -> bool:
        return self.method != "none"

    def __repr__(self) -> str:
        return (
            f"<AuthContext site={self.site!r} method={self.method!r} "
            f"cookie={'yes' if self.cookie_file else 'no'}>"
        )


# ─────────────────────────────────────────────────
# SessionGuard
# ─────────────────────────────────────────────────

class SessionGuard:
    """
    Ensures valid authentication state before each ZeusDL operation.

    Parameters
    ──────────
    store       : CredentialStore to use (default: module-level singleton)
    cookies     : CookieManager to use (default: module-level singleton)
    verbose     : print status messages to stderr
    """

    def __init__(
        self,
        store: Optional[CredentialStore] = None,
        cookies: Optional[CookieManager] = None,
        verbose: bool = False,
    ):
        self._store = store or get_store()
        self._cookies = cookies or get_manager()
        self._verbose = verbose

    # ── Public API ───────────────────────────────

    def ensure(self, url_or_site: str, *, force_refresh: bool = False) -> AuthContext:
        """
        Return an AuthContext for the given URL (or site key).

        If cookies are fresh → return immediately (no login needed).
        If cookies are stale / missing → attempt to login and write fresh cookies.
        If no login handler → fall back to username+password flags.
        If no credentials saved → return empty AuthContext (no auth).

        Parameters
        ──────────
        url_or_site   : a full URL like "https://www.brazzers.com/..." or a site
                        key like "brazzers"
        force_refresh : if True, skip the freshness check and always re-login
        """
        site = self._resolve_site(url_or_site)
        if site is None:
            return AuthContext()  # unknown site — no auth

        cred = self._store.load(site)
        if cred is None:
            return AuthContext(site=site)  # site known, but no credentials saved

        # ── Fast path: fresh cookies exist ───────
        if not force_refresh and self._cookies.is_fresh(site):
            cookie_file = self._cookies.cookie_file(site)
            if cookie_file:
                self._log(f"[auth] {site}: using cached cookies ({cookie_file.name})")
                return AuthContext(
                    site=site,
                    method="cookies",
                    cookie_file=cookie_file,
                    username=cred["username"],
                )

        # ── Attempt fresh login ───────────────────
        return self._login(site, cred)

    def on_auth_error(self, url_or_site: str) -> AuthContext:
        """
        Call this when ZeusDL encounters a 401/403 or a login-required page.
        Invalidates the current cookies and attempts a fresh login.
        Returns a new AuthContext (or empty if login fails again).
        """
        site = self._resolve_site(url_or_site)
        if site is None:
            return AuthContext()

        self._log(f"[auth] {site}: auth error detected — invalidating cookies and re-logging in")
        self._cookies.invalidate(site)
        return self.ensure(site, force_refresh=True)

    def cookie_status(self, url_or_site: str) -> dict:
        """Return cookie status dict for a site/URL."""
        site = self._resolve_site(url_or_site)
        if site is None:
            return {"site": None, "error": "unknown site"}
        return self._cookies.status(site)

    # ── Internal ─────────────────────────────────

    def _resolve_site(self, url_or_site: str) -> Optional[str]:
        if url_or_site in SITE_REGISTRY:
            return url_or_site
        return self._store.site_for_url(url_or_site)

    def _login(self, site: str, cred: dict) -> AuthContext:
        handler = get_handler(site)

        if handler is None:
            # No login handler — pass credentials directly as ydl opts
            self._log(f"[auth] {site}: no login handler, using --username/--password")
            return AuthContext(
                site=site,
                method="password",
                username=cred["username"],
            )

        username = cred["username"]
        password = cred["password"]

        self._log(f"[auth] {site}: logging in as {username!r} …")
        try:
            jar = handler.login(username, password)
            cookie_file = self._cookies.write(site, jar)
            self._log(f"[auth] {site}: login OK — cookies saved to {cookie_file}")
            return AuthContext(
                site=site,
                method="cookies",
                cookie_file=cookie_file,
                username=username,
            )
        except Exception as exc:
            # Login failed — fall back to --username/--password and let
            # ZeusDL's own extractor handle the auth (it may have its own flow)
            self._log(
                f"[auth] {site}: login handler failed ({exc}) — "
                f"falling back to --username/--password",
                level="warn",
            )
            return AuthContext(
                site=site,
                method="password",
                username=username,
            )

    def _log(self, msg: str, level: str = "info") -> None:
        if self._verbose or level == "warn":
            print(msg, file=sys.stderr, flush=True)


# Module-level singleton (lazy)
_guard: Optional[SessionGuard] = None


def get_guard(verbose: bool = False) -> SessionGuard:
    global _guard
    if _guard is None:
        _guard = SessionGuard(verbose=verbose)
    return _guard
