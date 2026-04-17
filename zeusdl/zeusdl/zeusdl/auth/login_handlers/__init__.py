"""
Login handlers for sites that require authentication.

Each handler implements BaseSiteLogin and is registered here by site key.
Add a new handler by subclassing BaseSiteLogin and adding it to HANDLERS.
"""

from .base import BaseSiteLogin, LoginError
from .brazzers import BrazzersLogin
from .pornhub import PornHubLogin

HANDLERS: dict[str, type[BaseSiteLogin]] = {
    "brazzers": BrazzersLogin,
    "pornhub": PornHubLogin,
}


def get_handler(site: str) -> BaseSiteLogin | None:
    """Return an instance of the login handler for a given site key, or None."""
    cls = HANDLERS.get(site)
    return cls() if cls else None


__all__ = ["BaseSiteLogin", "LoginError", "HANDLERS", "get_handler"]
