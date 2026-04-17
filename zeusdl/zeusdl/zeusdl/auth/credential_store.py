"""
Secure credential storage for ZeusDL.

Credentials are stored in ~/.config/zeusdl/credentials.json with strict
file permissions (0o600 — owner read/write only), the same model used by
.netrc and SSH private keys.  No external cryptography libraries required.

CLI
───
    python3 -m zeusdl.auth save   <site> <username> <password>
    python3 -m zeusdl.auth list
    python3 -m zeusdl.auth delete <site>
"""

import json
import os
import stat
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────
# Site registry
#
# Maps the site key (same as yt-dlp's _NETRC_MACHINE value) to metadata
# that the session guard and login handlers can use.
# ─────────────────────────────────────────────────

SITE_REGISTRY: dict[str, dict] = {
    # Adult / subscription
    "brazzers": {
        "label": "Brazzers",
        "domains": ["brazzers.com"],
        "category": "adult",
        "login_handler": "brazzers",
        "cookie_ttl": 900,          # seconds — re-login if cookies are older than this
        "retry_on_http": [401, 403],
        "auth_note": "Requires browser cookie import (reCAPTCHA prevents headless login).",
    },
    "pornhub": {
        "label": "PornHub / PornHub Premium",
        "domains": ["pornhub.com", "pornhubpremium.com"],
        "category": "adult",
        "login_handler": "pornhub",
        "cookie_ttl": 3600,
        "retry_on_http": [401, 403],
    },
    "nubiles-porn": {
        "label": "Nubiles Porn",
        "domains": ["nubiles-porn.com", "members.nubiles-porn.com"],
        "category": "adult",
        "login_handler": "nubiles_porn",
        "cookie_ttl": 3600,
        "retry_on_http": [401, 403],
    },
    "eroprofile": {
        "label": "EroProfile",
        "domains": ["eroprofile.com"],
        "category": "adult",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    "iwara": {
        "label": "Iwara",
        "domains": ["iwara.tv"],
        "category": "adult",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    # General
    "youtube": {
        "label": "YouTube",
        "domains": ["youtube.com", "youtu.be"],
        "category": "general",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
    "twitch": {
        "label": "Twitch",
        "domains": ["twitch.tv"],
        "category": "general",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
    "vimeo": {
        "label": "Vimeo",
        "domains": ["vimeo.com"],
        "category": "general",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
    "dailymotion": {
        "label": "Dailymotion",
        "domains": ["dailymotion.com"],
        "category": "general",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
    "reddit": {
        "label": "Reddit",
        "domains": ["reddit.com"],
        "category": "general",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
    "soundcloud": {
        "label": "SoundCloud",
        "domains": ["soundcloud.com"],
        "category": "general",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
    "vk": {
        "label": "VK",
        "domains": ["vk.com"],
        "category": "general",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
    # Streaming
    "curiositystream": {
        "label": "CuriosityStream",
        "domains": ["curiositystream.com"],
        "category": "streaming",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    "dropout": {
        "label": "Dropout",
        "domains": ["dropout.tv"],
        "category": "streaming",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    "watchnebula": {
        "label": "Nebula",
        "domains": ["watchnebula.com", "nebula.tv"],
        "category": "streaming",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    # Learning
    "udemy": {
        "label": "Udemy",
        "domains": ["udemy.com"],
        "category": "learning",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    "linkedin": {
        "label": "LinkedIn Learning",
        "domains": ["linkedin.com", "lynda.com"],
        "category": "learning",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
    # Anime
    "hidive": {
        "label": "HIDIVE",
        "domains": ["hidive.com"],
        "category": "anime",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    # Adult / subscription
    "bangbros": {
        "label": "BangBros",
        "domains": ["bangbros.com"],
        "category": "adult",
        "login_handler": None,
        "cookie_ttl": 900,
        "retry_on_http": [401, 403],
        "auth_note": "Requires browser cookie import (reCAPTCHA prevents headless login).",
    },
    # French streaming
    "frenchstream": {
        "label": "FrenchStream (fs13.lol)",
        "domains": ["fs13.lol", "french-stream.one"],
        "category": "streaming",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    "moiflix": {
        "label": "MoiFlix",
        "domains": ["moiflix.net"],
        "category": "streaming",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    "dessinanime": {
        "label": "DessinsAnimé",
        "domains": ["dessinanime.net"],
        "category": "anime",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [401, 403],
    },
    "freeonlinek": {
        "label": "FreeOnlineK (proxy)",
        "domains": ["freeonlinek.top", "moviestv.my"],
        "category": "streaming",
        "login_handler": None,
        "cookie_ttl": 86400,
        "retry_on_http": [],
    },
}


# ─────────────────────────────────────────────────
# Config directory
# ─────────────────────────────────────────────────

def _config_dir() -> Path:
    """Return (and create) the ZeusDL config directory."""
    base = Path(os.environ.get("ZEUSDL_CONFIG_DIR", "")) or Path.home() / ".config" / "zeusdl"
    base.mkdir(parents=True, exist_ok=True)
    # Restrict to owner-only access
    base.chmod(0o700)
    return base


def _credentials_path() -> Path:
    return _config_dir() / "credentials.json"


# ─────────────────────────────────────────────────
# Credential store
# ─────────────────────────────────────────────────

class CredentialStore:
    """
    Persist site credentials on disk with strict permissions (0o600).

    The credentials file is equivalent in security model to ~/.netrc —
    protected by UNIX file permissions rather than encryption.  Only the
    process owner can read or write it.

    Structure of credentials.json
    ──────────────────────────────
    {
      "brazzers": {
        "username": "email@example.com",
        "password": "s3cr3t",
        "saved_at": 1712345678.0
      }
    }
    """

    def __init__(self, path: Optional[Path] = None):
        self._path = path or _credentials_path()

    # ── I/O ──────────────────────────────────────

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        # Warn if permissions are too open
        mode = self._path.stat().st_mode & 0o777
        if mode & 0o077:
            import sys
            print(
                f"[ZeusDL auth] WARNING: {self._path} has loose permissions "
                f"({oct(mode)}). Run: chmod 600 {self._path}",
                file=sys.stderr,
            )
        with open(self._path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        # Set 600 before rename so the sensitive file is never world-readable
        tmp.chmod(0o600)
        tmp.replace(self._path)

    # ── Public API ───────────────────────────────

    def save(self, site: str, username: str, password: str, extras: Optional[dict] = None) -> None:
        """Save or update credentials for a site. extras can store tokens, etc."""
        import time
        data = self._load()
        existing_extras = (data.get(site) or {}).get("extras", {})
        entry: dict = {
            "username": username,
            "password": password,
            "saved_at": time.time(),
        }
        merged = {**existing_extras, **(extras or {})}
        if merged:
            entry["extras"] = merged
        data[site] = entry
        self._save(data)

    def save_extras(self, site: str, extras: dict) -> None:
        """Merge extra data (e.g. refresh_token) into an existing credential entry."""
        data = self._load()
        if site not in data:
            return
        existing = data[site].get("extras", {})
        data[site]["extras"] = {**existing, **extras}
        self._save(data)

    def get_extras(self, site: str) -> dict:
        """Return the extras dict for a site, or {}."""
        entry = self._load().get(site) or {}
        return entry.get("extras", {})

    def load(self, site: str) -> Optional[dict]:
        """Return {'username': ..., 'password': ..., 'saved_at': ...} or None."""
        return self._load().get(site)

    def delete(self, site: str) -> bool:
        data = self._load()
        if site not in data:
            return False
        del data[site]
        self._save(data)
        return True

    def list_sites(self) -> list[dict]:
        """Return a list of dicts with site metadata (no passwords)."""
        import time
        data = self._load()
        result = []
        for site_key, info in SITE_REGISTRY.items():
            cred = data.get(site_key)
            result.append({
                "site": site_key,
                "label": info["label"],
                "domains": info["domains"],
                "category": info["category"],
                "has_credentials": cred is not None,
                "username": cred["username"] if cred else None,
                "saved_at": cred["saved_at"] if cred else None,
                "auth_note": info.get("auth_note"),
            })
        return result

    def site_for_url(self, url: str) -> Optional[str]:
        """Return the site key that matches a given URL, or None."""
        try:
            from urllib.parse import urlparse
            host = urlparse(url).hostname or ""
            host = host.lower().lstrip("www.")
        except Exception:
            return None
        for site_key, info in SITE_REGISTRY.items():
            for domain in info["domains"]:
                clean = domain.lstrip("www.")
                if host == clean or host.endswith("." + clean):
                    return site_key
        return None

    def credentials_for_url(self, url: str) -> Optional[dict]:
        """Return credentials for the site matching url, or None."""
        site = self.site_for_url(url)
        if site is None:
            return None
        cred = self.load(site)
        if cred is None:
            return None
        return {"site": site, **cred}


# Module-level singleton
_store: Optional[CredentialStore] = None


def get_store() -> CredentialStore:
    global _store
    if _store is None:
        _store = CredentialStore()
    return _store
