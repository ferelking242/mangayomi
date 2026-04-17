"""
ZeusDL Auth CLI

Usage
─────
    python3 -m zeusdl.auth <command> [args]

Commands
────────
    list                         List all known sites and credential status
    save   <site> <user> <pass>  Save credentials for a site
    delete <site>                Remove saved credentials for a site
    refresh <site>               Force a fresh login and update the cookie file
    status  <site>               Show cookie freshness info for a site
    sites                        Print all supported site keys

Examples
────────
    python3 -m zeusdl.auth list
    python3 -m zeusdl.auth save brazzers email@example.com "MyP@ssword"
    python3 -m zeusdl.auth refresh brazzers
    python3 -m zeusdl.auth status brazzers
    python3 -m zeusdl.auth delete brazzers
"""

import sys
import json
import time


def _fmt_age(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"


def cmd_list(args: list[str]) -> int:
    from .credential_store import get_store
    sites = get_store().list_sites()
    saved = [s for s in sites if s["has_credentials"]]
    print(f"\n  ZeusDL Credentials ({len(saved)} saved)\n")
    by_cat: dict[str, list] = {}
    for s in sites:
        by_cat.setdefault(s["category"], []).append(s)

    cat_order = ["adult", "general", "streaming", "learning", "anime"]
    for cat in cat_order:
        group = by_cat.get(cat, [])
        if not group:
            continue
        print(f"  ── {cat.upper()} ──────────────────────────")
        for s in group:
            icon = "✓" if s["has_credentials"] else "·"
            user = f"  ({s['username']})" if s["username"] else ""
            print(f"  {icon}  {s['site']:<25} {s['label']}{user}")
        print()
    return 0


def cmd_save(args: list[str]) -> int:
    if len(args) < 3:
        print("Usage: save <site> <username> <password>", file=sys.stderr)
        return 1
    site, username, password = args[0], args[1], args[2]
    from .credential_store import get_store, SITE_REGISTRY
    if site not in SITE_REGISTRY:
        print(f"Unknown site: {site!r}", file=sys.stderr)
        print("Run 'python3 -m zeusdl.auth sites' to see valid site keys.", file=sys.stderr)
        return 1
    get_store().save(site, username, password)
    print(f"✓ Credentials saved for {site!r} ({username})")
    return 0


def cmd_delete(args: list[str]) -> int:
    if not args:
        print("Usage: delete <site>", file=sys.stderr)
        return 1
    site = args[0]
    from .credential_store import get_store
    if not get_store().delete(site):
        print(f"No credentials found for {site!r}", file=sys.stderr)
        return 1
    from .cookie_manager import get_manager
    get_manager().delete(site)
    print(f"✓ Credentials and cookies removed for {site!r}")
    return 0


def cmd_refresh(args: list[str]) -> int:
    if not args:
        print("Usage: refresh <site>", file=sys.stderr)
        return 1
    site = args[0]
    from .session_guard import SessionGuard
    guard = SessionGuard(verbose=True)
    ctx = guard.ensure(site, force_refresh=True)
    if not ctx.is_authenticated:
        print(f"No credentials saved for {site!r}. Run 'save' first.", file=sys.stderr)
        return 1
    print(f"✓ {ctx}")
    return 0


def cmd_status(args: list[str]) -> int:
    if not args:
        print("Usage: status <site>", file=sys.stderr)
        return 1
    site = args[0]
    from .cookie_manager import get_manager
    from .credential_store import get_store
    cred = get_store().load(site)
    status = get_manager().status(site)
    print(f"\n  Site       : {site}")
    print(f"  Credentials: {'✓ saved (' + cred['username'] + ')' if cred else '✗ none'}")
    print(f"  Cookies    : {'exists' if status['has_cookies'] else 'none'}")
    if status["has_cookies"]:
        print(f"  Fresh      : {'✓ yes' if status['is_fresh'] else '✗ stale'}")
        print(f"  Age        : {_fmt_age(status['age_seconds'])}")
        print(f"  TTL        : {_fmt_age(status['ttl_seconds'])}")
        expires = status.get("expires_in")
        if expires is not None:
            print(f"  Expires in : {_fmt_age(float(expires))}")
    print()
    return 0


def cmd_sites(args: list[str]) -> int:
    from .credential_store import SITE_REGISTRY
    print("\n  Supported site keys:\n")
    for key, info in SITE_REGISTRY.items():
        domains = ", ".join(info["domains"])
        has_handler = "auto-login" if info.get("login_handler") else "cookie/pass"
        print(f"  {key:<25} {info['label']:<35} [{has_handler}]")
    print()
    return 0


COMMANDS = {
    "list": cmd_list,
    "save": cmd_save,
    "delete": cmd_delete,
    "refresh": cmd_refresh,
    "status": cmd_status,
    "sites": cmd_sites,
}


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = args[0]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd!r}", file=sys.stderr)
        print(f"Available: {', '.join(COMMANDS)}", file=sys.stderr)
        return 1
    return COMMANDS[cmd](args[1:])


if __name__ == "__main__":
    sys.exit(main())
