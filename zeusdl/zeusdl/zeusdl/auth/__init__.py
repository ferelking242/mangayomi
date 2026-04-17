"""
ZeusDL Auth — credential storage, cookie lifecycle management, and
auto-reconnect for sites that invalidate sessions frequently.

Quick start
───────────
Save credentials (CLI):
    python3 -m zeusdl.auth save brazzers your@email.com yourpassword
    python3 -m zeusdl.auth list
    python3 -m zeusdl.auth refresh brazzers

Use in code (e.g. from download_manager):
    from zeusdl.auth import SessionGuard

    guard = SessionGuard(verbose=True)
    ctx = guard.ensure("https://www.brazzers.com/video/...")
    # ctx.ydl_opts → {"cookiefile": "/path/to/brazzers.txt"}
    #              or {"username": "...", "password": "..."}
    #              or {}   (no credentials)
"""

from .credential_store import CredentialStore, get_store, SITE_REGISTRY
from .cookie_manager import CookieManager, get_manager
from .session_guard import SessionGuard, AuthContext, get_guard
from .login_handlers import get_handler

__all__ = [
    "CredentialStore",
    "get_store",
    "SITE_REGISTRY",
    "CookieManager",
    "get_manager",
    "SessionGuard",
    "AuthContext",
    "get_guard",
    "get_handler",
]
