"""
Cookie lifecycle manager for ZeusDL.

Responsibilities
────────────────
• Store one Netscape-format cookie file per site under
  ~/.config/zeusdl/cookies/<site>.txt  (yt-dlp / ZeusDL can read these directly
  via --cookies <path>)
• Track cookie age in a companion .meta.json file
• Decide when cookies are stale and must be refreshed
• Write a fresh CookieJar (from a login handler) to disk atomically
"""

import http.cookiejar
import json
import os
import time
from pathlib import Path
from typing import Optional

from .credential_store import _config_dir, SITE_REGISTRY


def _cookies_dir() -> Path:
    d = _config_dir() / "cookies"
    d.mkdir(parents=True, exist_ok=True)
    d.chmod(0o700)
    return d


def _cookie_file(site: str) -> Path:
    return _cookies_dir() / f"{site}.txt"


def _meta_file(site: str) -> Path:
    return _cookies_dir() / f"{site}.meta.json"


# ─────────────────────────────────────────────────

class CookieManager:
    """
    Manages per-site Netscape cookie files.

    Usage
    ─────
    cm = CookieManager()

    # Check if we need to (re)login
    if not cm.is_fresh("brazzers"):
        jar = some_login_handler.login(username, password)
        cm.write(\"brazzers\", jar)

    # Pass cookie file to ZeusDL
    cookie_path = cm.cookie_file(\"brazzers\")
    """

    def cookie_file(self, site: str) -> Optional[Path]:
        """Return path to cookie file if it exists, else None."""
        p = _cookie_file(site)
        return p if p.exists() else None

    def is_fresh(self, site: str) -> bool:
        """
        Return True if the cookie file exists and is younger than the site's TTL.
        A site with no registered TTL defaults to 3600 s (1 hour).
        """
        p = _cookie_file(site)
        if not p.exists():
            return False

        meta = self._load_meta(site)
        written_at = meta.get("written_at", 0.0)
        ttl = SITE_REGISTRY.get(site, {}).get("cookie_ttl", 3600)

        return (time.time() - written_at) < ttl

    def write(self, site: str, jar: http.cookiejar.CookieJar) -> Path:
        """
        Write a CookieJar to disk in Netscape/Mozilla format.
        Also updates the metadata (written_at timestamp).
        Returns the path to the written file.
        """
        path = _cookie_file(site)
        mjar = http.cookiejar.MozillaCookieJar(str(path))
        for cookie in jar:
            mjar.set_cookie(cookie)
        mjar.save(ignore_discard=True, ignore_expires=True)
        path.chmod(0o600)
        self._save_meta(site, {"written_at": time.time()})
        return path

    def load(self, site: str) -> Optional[http.cookiejar.MozillaCookieJar]:
        """Load the saved cookie file into a MozillaCookieJar, or return None."""
        path = _cookie_file(site)
        if not path.exists():
            return None
        jar = http.cookiejar.MozillaCookieJar(str(path))
        try:
            jar.load(ignore_discard=True, ignore_expires=True)
            return jar
        except Exception:
            return None

    def write_raw(self, site: str, raw_text: str) -> Path:
        """
        Write a raw Netscape-format cookie file to disk (e.g. pasted from a browser
        extension export).  Also extracts refresh_token if present and stores it
        in credential extras so the Brazzers renew flow can reuse it.

        Returns the path to the saved file.
        """
        path = _cookie_file(site)
        path.write_text(raw_text, encoding="utf-8")
        path.chmod(0o600)
        self._save_meta(site, {"written_at": time.time()})

        # For Brazzers: extract refresh_token_ma from the cookie text and store
        # it in credential extras so we can renew without a browser later.
        self._extract_and_store_extras(site, raw_text)

        return path

    def _extract_and_store_extras(self, site: str, raw_text: str) -> None:
        """
        Parse the Netscape cookie file and persist site-specific tokens as extras.
        Currently handles Brazzers refresh_token_ma.
        """
        import re
        from .credential_store import get_store

        extras: dict = {}

        if site == "brazzers":
            # Each line: domain  flag  path  secure  expiry  name  value
            for line in raw_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7 and parts[5] == "refresh_token_ma":
                    extras["refresh_token"] = parts[6]
                    break

        if extras:
            get_store().save_extras(site, extras)

    def invalidate(self, site: str) -> None:
        """Mark cookies as stale by zeroing the written_at timestamp."""
        self._save_meta(site, {"written_at": 0.0})

    def delete(self, site: str) -> None:
        """Remove cookie file and metadata."""
        _cookie_file(site).unlink(missing_ok=True)
        _meta_file(site).unlink(missing_ok=True)

    def status(self, site: str) -> dict:
        """Return a dict describing the cookie state for a site."""
        meta = self._load_meta(site)
        written_at = meta.get("written_at", 0.0)
        ttl = SITE_REGISTRY.get(site, {}).get("cookie_ttl", 3600)
        age = time.time() - written_at if written_at else None
        return {
            "site": site,
            "has_cookies": _cookie_file(site).exists(),
            "is_fresh": self.is_fresh(site),
            "written_at": written_at or None,
            "age_seconds": round(age) if age is not None else None,
            "ttl_seconds": ttl,
            "expires_in": max(0, round(ttl - age)) if age is not None else None,
        }

    # ── Internal ─────────────────────────────────

    def _load_meta(self, site: str) -> dict:
        p = _meta_file(site)
        if not p.exists():
            return {}
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_meta(self, site: str, data: dict) -> None:
        p = _meta_file(site)
        tmp = p.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        tmp.chmod(0o600)
        tmp.replace(p)


# Module-level singleton
_manager: Optional[CookieManager] = None


def get_manager() -> CookieManager:
    global _manager
    if _manager is None:
        _manager = CookieManager()
    return _manager
