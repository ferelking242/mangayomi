"""
PornHub / PornHub Premium login handler.

Authentication flow
───────────────────
1. GET /login  →  grab token / hidden inputs
2. POST credentials
3. Verify session cookie exists
"""

import http.cookiejar
import re

from .base import BaseSiteLogin, LoginError


class PornHubLogin(BaseSiteLogin):
    SITE_DOMAIN = "pornhub.com"

    _LOGIN_PAGE = "https://www.pornhub.com/login"
    _LOGIN_POST = "https://www.pornhub.com/front/authenticate"

    def login(self, username: str, password: str) -> http.cookiejar.CookieJar:
        jar = http.cookiejar.CookieJar()
        opener = self._make_opener(jar)

        # Step 1: fetch login page (sets age cookies + CSRF token)
        status, html = self._get(opener, self._LOGIN_PAGE)
        if status not in (200, 301, 302):
            raise LoginError(f"PornHub: login page returned HTTP {status}")

        # Extract token from page
        token_match = re.search(r'name=["\']token["\'][^>]+value=["\']([^"\']+)["\']', html)
        token = token_match.group(1) if token_match else ""

        hidden = self._hidden_inputs(html)
        hidden.setdefault("token", token)

        # Step 2: POST credentials
        payload = {
            **hidden,
            "username": username,
            "password": password,
            "remember": "1",
        }

        status, body = self._post(
            opener,
            self._LOGIN_POST,
            payload,
            extra_headers={
                "Referer": self._LOGIN_PAGE,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            },
        )

        # Step 3: verify
        if not self._has_session_cookie(jar):
            raise LoginError(
                "PornHub: login failed — no session cookie received. "
                "Check your username/password."
            )

        return jar

    @staticmethod
    def _has_session_cookie(jar: http.cookiejar.CookieJar) -> bool:
        for cookie in jar:
            if "pornhub" in (cookie.domain or ""):
                name_l = cookie.name.lower()
                if any(k in name_l for k in ("session", "user", "auth", "remember", "login")):
                    return True
        return False
