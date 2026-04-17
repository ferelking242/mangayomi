"""
Brazzers / MindGeek / Project1 login handler.

Authentication strategy
────────────────────────
1. Renew session — if a refresh_token cookie is already in the cookiejar:
      POST /v1/authenticate/renew  (NO captcha needed)
      Valid for 30 days.

2. Cookie import — paste your cookies.txt in the UI:
      Login at https://site-ma.brazzers.com/login in your browser,
      export with "Get cookies.txt LOCALLY" extension,
      then import via Credentials > Import cookies.
"""

import http.cookiejar
import time

from .base import BaseSiteLogin, LoginError


AUTH_API = 'https://auth-service.project1service.com'
INSTANCE_URL = 'https://site-ma.brazzers.com/'


class BrazzersLogin(BaseSiteLogin):
    SITE_DOMAIN = 'brazzers.com'

    def login(self, username: str, password: str) -> http.cookiejar.CookieJar:
        """
        Brazzers requires reCAPTCHA for first-time login.

        If a refresh_token is stored in credential extras, renew the session
        automatically.  Otherwise raise LoginError asking the user to import
        cookies from their browser.
        """
        from ..credential_store import get_store

        extras = get_store().get_extras('brazzers')
        refresh_token = extras.get('refresh_token', '')

        if refresh_token:
            try:
                new_access, new_refresh, expires_in = self.renew(refresh_token)
                jar = http.cookiejar.CookieJar()
                self._set_auth_cookies(jar, new_access, new_refresh, expires_in)
                get_store().save_extras('brazzers', {'refresh_token': new_refresh})
                return jar
            except LoginError:
                get_store().save_extras('brazzers', {'refresh_token': ''})

        raise LoginError(
            'Brazzers requires a browser login to get the initial session.\n\n'
            'Steps:\n'
            '  1. Log in at https://site-ma.brazzers.com/login in your browser\n'
            '  2. Install "Get cookies.txt LOCALLY" (Chrome extension)\n'
            '  3. Export the cookies for brazzers.com\n'
            '  4. In ZeusDL → Credentials → Brazzers → Import cookies\n\n'
            'After the first import, sessions auto-renew for 30 days.'
        )

    def renew(self, refresh_token: str) -> tuple[str, str, int]:
        """
        Renew the access token using a stored refresh token.

        Returns (new_access_token, new_refresh_token, expires_in).
        No reCAPTCHA required.
        """
        jar = http.cookiejar.CookieJar()
        opener = self._make_opener(jar)
        instance_token, session_id = self._get_instance_cookies(opener, jar)

        status, body = self._post_json(
            opener,
            f'{AUTH_API}/v1/authenticate/renew',
            {'refreshToken': refresh_token},
            extra_headers={
                'Instance': instance_token or '',
                'x-app-session-id': session_id or '',
                'Origin': 'https://site-ma.brazzers.com',
                'Referer': 'https://site-ma.brazzers.com/',
            },
        )

        if not isinstance(body, dict) or not body.get('access_token'):
            err = body.get('message', '') if isinstance(body, dict) else str(body)
            raise LoginError(f'Brazzers token renewal failed (HTTP {status}): {err}')

        return (
            body['access_token'],
            body.get('refresh_token', refresh_token),
            int(body.get('expires_in', 900)),
        )

    def _get_instance_cookies(self, opener, jar: http.cookiejar.CookieJar) -> tuple[str | None, str]:
        try:
            self._get(opener, INSTANCE_URL)
        except Exception as exc:
            raise LoginError(f'Brazzers: cannot reach {INSTANCE_URL}: {exc}') from exc

        instance_token = None
        session_id = ''
        for cookie in jar:
            if cookie.name == 'instance_token':
                instance_token = cookie.value
            elif cookie.name == 'app_session_id':
                session_id = cookie.value
        return instance_token, session_id

    @staticmethod
    def _set_auth_cookies(
        jar: http.cookiejar.CookieJar,
        access_token: str,
        refresh_token: str,
        expires_in: int,
    ) -> None:
        now = int(time.time())

        def _make(name, value, lifetime):
            return http.cookiejar.Cookie(
                version=0, name=name, value=value,
                port=None, port_specified=False,
                domain='.brazzers.com', domain_specified=True,
                domain_initial_dot=True,
                path='/', path_specified=True,
                secure=True,
                expires=now + lifetime,
                discard=False,
                comment=None, comment_url=None,
                rest={},
            )

        jar.set_cookie(_make('access_token_ma', access_token, expires_in))
        if refresh_token:
            jar.set_cookie(_make('refresh_token_ma', refresh_token, 86400 * 30))
