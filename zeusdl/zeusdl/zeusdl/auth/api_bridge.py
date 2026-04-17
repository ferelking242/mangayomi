"""
Thin JSON bridge for the TypeScript API server to call into the Python auth module.

Usage (called by the TS server as a subprocess):
    python3 -m zeusdl.auth.api_bridge

Reads a single JSON command from stdin, writes a single JSON response to stdout.

Command format
──────────────
    {"cmd": "list"}
    {"cmd": "sites"}
    {"cmd": "save",    "site": "brazzers", "username": "u", "password": "p"}
    {"cmd": "delete",  "site": "brazzers"}
    {"cmd": "status",  "site": "brazzers"}
    {"cmd": "refresh", "site": "brazzers"}
    {"cmd": "import_cookies", "site": "brazzers", "cookie_text": "..."}
    {"cmd": "import_cookies", "url": "https://brazzers.com/...", "cookie_text": "..."}

Response format
───────────────
    {"ok": true,  "data": ...}
    {"ok": false, "error": "..."}
"""

import json
import sys
import os

def main() -> None:
    try:
        raw = sys.stdin.read()
        req = json.loads(raw)
    except Exception as exc:
        _err(f"JSON parse error: {exc}")
        return

    cmd = req.get("cmd", "")

    if cmd == "list":
        from .credential_store import get_store
        _ok(get_store().list_sites())

    elif cmd == "sites":
        from .credential_store import SITE_REGISTRY
        _ok([{"site": k, **v} for k, v in SITE_REGISTRY.items()])

    elif cmd == "save":
        site = req.get("site", "")
        username = (req.get("username") or "").strip()
        password = req.get("password") or ""
        if not site:
            _err("Missing 'site'"); return
        if not username:
            _err("Missing 'username'"); return
        if not password:
            _err("Missing 'password'"); return
        from .credential_store import get_store, SITE_REGISTRY
        if site not in SITE_REGISTRY:
            _err(f"Unknown site '{site}'"); return
        import time
        get_store().save(site, username, password)
        _ok({"site": site, "username": username, "saved_at": time.time()})

    elif cmd == "delete":
        site = req.get("site", "")
        if not site:
            _err("Missing 'site'"); return
        from .credential_store import get_store
        from .cookie_manager import get_manager
        removed = get_store().delete(site)
        if not removed:
            _err(f"No credentials for '{site}'"); return
        get_manager().delete(site)
        _ok({"site": site})

    elif cmd == "status":
        site = req.get("site", "")
        if not site:
            _err("Missing 'site'"); return
        from .cookie_manager import get_manager
        from .credential_store import get_store
        cred = get_store().load(site)
        status = get_manager().status(site)
        status["has_credentials"] = cred is not None
        status["username"] = cred["username"] if cred else None
        _ok(status)

    elif cmd == "import_cookies":
        site = req.get("site", "")
        url  = req.get("url", "")
        raw  = req.get("cookie_text", "")
        if not raw or not raw.strip():
            _err("Missing 'cookie_text'"); return
        # Resolve site key — accept explicit site or auto-detect from URL
        if not site and url:
            from .credential_store import get_store
            site = get_store().site_for_url(url) or ""
        if not site:
            _err("Cannot determine site — provide 'site' or a recognised 'url'"); return
        from .credential_store import SITE_REGISTRY
        if site not in SITE_REGISTRY:
            _err(f"Unknown site '{site}'"); return
        from .cookie_manager import get_manager
        try:
            path = get_manager().write_raw(site, raw.strip())
            _ok({"site": site, "cookie_file": str(path), "written": True})
        except Exception as exc:
            _err(str(exc))

    elif cmd == "refresh":
        site = req.get("site", "")
        if not site:
            _err("Missing 'site'"); return
        from .session_guard import SessionGuard
        guard = SessionGuard(verbose=False)
        ctx = guard.ensure(site, force_refresh=True)
        if not ctx.is_authenticated:
            _err(f"No credentials saved for '{site}'"); return
        _ok({
            "site": ctx.site,
            "method": ctx.method,
            "cookie_file": str(ctx.cookie_file) if ctx.cookie_file else None,
            "username": ctx.username,
        })

    else:
        _err(f"Unknown command: '{cmd}'")


def _ok(data) -> None:
    print(json.dumps({"ok": True, "data": data}), flush=True)

def _err(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}), flush=True)


if __name__ == "__main__":
    main()
