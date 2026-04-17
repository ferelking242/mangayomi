"""
Brazzers extractor (Project1 / MindGeek API).

Authentication
──────────────
Brazzers uses the auth-service.project1service.com API.  Direct username/password
login requires a Google reCAPTCHA v3 token which cannot be solved headlessly.

Recommended auth flow:
1. Login in your browser at https://site-ma.brazzers.com/login
2. Export cookies (e.g. with a browser extension like "Get cookies.txt LOCALLY")
3. Pass the cookie file:  zeusdl --cookies ~/brazzers.txt URL

Alternatively, store the access_token_ma + refresh_token via the credential store.
The session guard will auto-renew access tokens using the refresh token.
"""

import json
import re

from ..common import InfoExtractor
from ...utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    unified_timestamp,
)


DATA_API = 'https://site-api.project1service.com'
AUTH_API = 'https://auth-service.project1service.com'
INSTANCE_URL = 'https://site-ma.brazzers.com/'


class BrazzersIE(InfoExtractor):
    _NETRC_MACHINE = 'brazzers'

    _VALID_URL = (
        r'https?://(?P<host>(?:[\w-]+\.)?brazzers\.com)'
        r'/(?:video/(?:view/)?|scene/)(?P<id>\d+)(?:/[\w-]+)?/?'
    )

    _TESTS = [{
        'url': 'https://www.brazzers.com/video/view/260663/valentina-nappi-in-i-see-youre-busy/',
        'info_dict': {
            'id': '260663',
            'ext': 'mp4',
            'title': str,
            'description': str,
            'thumbnail': str,
            'age_limit': 18,
        },
        'skip': 'Requires premium account',
    }, {
        'url': 'https://site-ma.brazzers.com/scene/8369971/fuck-me-and-fuck-off',
        'info_dict': {
            'id': '8369971',
            'ext': 'mp4',
            'title': str,
            'age_limit': 18,
        },
        'skip': 'Requires premium account',
    }]

    def _get_instance_token(self, video_id):
        """Fetch the per-request instance JWT from the Brazzers site."""
        import http.cookiejar
        jar = http.cookiejar.CookieJar()
        opener_headers = {'User-Agent': self._FAKE_UA}
        # Use yt-dlp's _request_webpage to share the cookiejar
        webpage = self._download_webpage(
            INSTANCE_URL, video_id,
            note='Fetching instance token',
            errnote='Could not reach Brazzers',
        )
        # Parse __JUAN.config for extra API config
        config = {}
        m = re.search(r'window\.__JUAN\.config\s*=\s*(\{[^\n]{50,}\})\s*;', webpage)
        if m:
            try:
                config = json.loads(m.group(1))
            except Exception:
                pass

        # The instance_token is set in the cookies; retrieve it via the cookiejar
        for cookie in self._downloader.cookiejar:
            if cookie.name == 'instance_token':
                return cookie.value, cookie
        return None, None

    def _get_session_id(self):
        """Return app_session_id from the shared cookiejar."""
        for cookie in self._downloader.cookiejar:
            if cookie.name == 'app_session_id':
                return cookie.value
        return ''

    def _get_access_token(self):
        """Return access_token_ma from cookies if present (set by --cookies or prior login)."""
        for cookie in self._downloader.cookiejar:
            if cookie.name == 'access_token_ma':
                return cookie.value
        return None

    def _perform_login(self, username, password):
        """
        Login to Brazzers via auth-service.project1service.com.

        Brazzers requires a Google reCAPTCHA v3 token for first-time login.
        If reCAPTCHA is blocking, instruct the user to use --cookies instead.
        """
        self.report_login()

        # First get instance token (needed as the Instance header for the auth API)
        instance_token, _ = self._get_instance_token(None)
        session_id = self._get_session_id()

        if not instance_token:
            self.report_warning('Could not obtain instance token — login may fail.')

        # Check if we already have an access_token_ma cookie (from --cookies)
        if self._get_access_token():
            self.to_screen('[brazzers] Found access_token_ma in cookies — skipping login')
            return

        # Check if we have a stored refresh_token to renew the session
        refresh_token = self._get_stored_refresh_token()
        if refresh_token:
            self.to_screen('[brazzers] Attempting session renewal with stored refresh token')
            if self._renew_token(refresh_token, instance_token, session_id):
                return

        # Attempt full login (requires valid reCAPTCHA token)
        self.to_screen('[brazzers] Attempting direct login (requires reCAPTCHA)')
        self._direct_login(username, password, instance_token, session_id)

    def _get_stored_refresh_token(self):
        """Retrieve a stored refresh token from yt-dlp params or netrc extras."""
        # Check if a refresh_token was passed via --video-password or via cookies
        for cookie in self._downloader.cookiejar:
            if cookie.name == 'refresh_token_ma':
                return cookie.value
        return None

    def _renew_token(self, refresh_token, instance_token, session_id):
        """Use refresh_token to get a new access_token without reCAPTCHA."""
        try:
            data = self._download_json(
                f'{AUTH_API}/v1/authenticate/renew',
                None,
                note='Renewing Brazzers session token',
                errnote='Token renewal failed',
                data=json.dumps({'refreshToken': refresh_token}).encode(),
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Instance': instance_token or '',
                    'x-app-session-id': session_id,
                    'Origin': 'https://site-ma.brazzers.com',
                    'Referer': 'https://site-ma.brazzers.com/',
                },
                fatal=False,
            )
            if data and data.get('access_token'):
                self.to_screen('[brazzers] Session token renewed successfully')
                self._store_tokens(data)
                return True
        except Exception as e:
            self.report_warning(f'Token renewal failed: {e}')
        return False

    def _direct_login(self, username, password, instance_token, session_id):
        """
        Attempt login via POST /v1/authenticate.
        Note: Requires a valid Google reCAPTCHA v3 token.
        We try with a placeholder; if reCAPTCHA is required, advise the user.
        """
        try:
            data = self._download_json(
                f'{AUTH_API}/v1/authenticate',
                None,
                note='Logging in to Brazzers',
                errnote='Brazzers login failed',
                data=json.dumps({
                    'googleReCaptchaResponse': 'x' * 800,
                    'googleReCaptchaVersion': 'v3',
                    'hostname': 'site-ma.brazzers.com',
                    'password': password,
                    'username': username,
                }).encode(),
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Instance': instance_token or '',
                    'x-app-session-id': session_id,
                    'Origin': 'https://site-ma.brazzers.com',
                    'Referer': 'https://site-ma.brazzers.com/login',
                },
                fatal=False,
            )
            if data and data.get('access_token'):
                self.to_screen('[brazzers] Login successful')
                self._store_tokens(data)
                return
            err = data.get('message', '') if isinstance(data, dict) else ''
        except Exception as e:
            err = str(e)

        if 'captcha' in err.lower() or 'recaptcha' in err.lower() or '3004' in err:
            raise ExtractorError(
                'Brazzers login requires a browser reCAPTCHA token. '
                'Please login in your browser, export cookies, and pass them with --cookies. '
                'See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp',
                expected=True,
            )
        raise ExtractorError(f'Brazzers login failed: {err}', expected=True)

    def _store_tokens(self, data):
        """Store access/refresh tokens in the cookiejar for this session."""
        import http.cookiejar
        import time
        access_token = data.get('access_token', '')
        refresh_token = data.get('refresh_token', '')
        expires_in = int_or_none(data.get('expires_in')) or 3600

        def _make_cookie(name, value, expires, domain='.brazzers.com'):
            return http.cookiejar.Cookie(
                version=0, name=name, value=value,
                port=None, port_specified=False,
                domain=domain, domain_specified=True, domain_initial_dot=True,
                path='/', path_specified=True,
                secure=True, expires=int(time.time()) + expires,
                discard=False, comment=None, comment_url=None,
                rest={},
            )

        jar = self._downloader.cookiejar
        if access_token:
            jar.set_cookie(_make_cookie('access_token_ma', access_token, expires_in))
        if refresh_token:
            jar.set_cookie(_make_cookie('refresh_token_ma', refresh_token, 86400 * 30))

    def _build_api_headers(self, instance_token, session_id, access_token=None):
        """Build the headers required by site-api.project1service.com."""
        headers = {
            'Accept': 'application/json',
            'Origin': 'https://site-ma.brazzers.com',
            'Referer': 'https://site-ma.brazzers.com/',
            'Instance': instance_token or '',
            'x-app-session-id': session_id or '',
        }
        if access_token:
            headers['Authorization'] = access_token
        return headers

    def _extract_formats_from_videos(self, videos, video_id):
        """
        Parse the videos dict from the Project1 release API response.

        Structure:
          {
            "mediabook": {"files": {"720p": {"urls": {"view": "..."}, "type": "http", ...}}},
            "full":      {"files": {"1080p": {"urls": {"view": "...", "download": "..."}, ...}}},
            ...
          }
        """
        formats = []
        PREFER_ORDER = ['full', 'clip', 'mediabook']

        for video_type in sorted(videos, key=lambda t: PREFER_ORDER.index(t) if t in PREFER_ORDER else 99):
            video_entry = videos[video_type]
            files = video_entry.get('files') or {}
            is_full = video_type == 'full'

            for quality_label, file_info in files.items():
                view_url = (file_info.get('urls') or {}).get('view')
                dl_url = (file_info.get('urls') or {}).get('download')
                url = dl_url or view_url
                if not url:
                    continue

                height = int_or_none(re.search(r'(\d+)p', quality_label or ''), group=1)

                fmt = {
                    'url': url,
                    'ext': 'mp4',
                    'format_id': f'{video_type}-{quality_label}',
                    'height': height,
                    'fps': int_or_none(file_info.get('fps')),
                    'filesize': int_or_none(file_info.get('sizeBytes')),
                    'vcodec': file_info.get('codec'),
                    'quality': 1 if is_full else -1,  # prefer full over trailer
                }
                formats.append(fmt)

        return formats

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')

        # ── Step 1: Get instance token (sets cookies for this domain) ─────
        instance_token, _ = self._get_instance_token(video_id)
        session_id = self._get_session_id()
        access_token = self._get_access_token()

        if not instance_token:
            raise ExtractorError(
                'Could not obtain Brazzers instance token. The site may be down.',
                expected=True,
            )

        # ── Step 2: Call the Project1 releases API ────────────────────────
        api_headers = self._build_api_headers(instance_token, session_id, access_token)

        release = self._download_json(
            f'{DATA_API}/v2/releases/{video_id}',
            video_id,
            note='Fetching release metadata from Project1 API',
            errnote='Failed to fetch release metadata',
            headers=api_headers,
        )

        result = release.get('result') or {}

        # ── Step 3: Check member access ───────────────────────────────────
        can_play = result.get('canPlay', False)
        is_member_unlocked = result.get('isMemberUnlocked', False)
        videos = result.get('videos') or {}

        if not can_play:
            self.raise_login_required(
                'This Brazzers video requires a premium membership. '
                'Login with --cookies (browser export) or --username/--password.',
                method='cookies',
            )

        # ── Step 4: Extract video formats ─────────────────────────────────
        formats = self._extract_formats_from_videos(videos, video_id)

        if not formats:
            if not access_token:
                self.raise_login_required(
                    'No video streams found. This video requires a Brazzers premium account. '
                    'Export your browser cookies and pass them with --cookies.',
                    method='cookies',
                )
            raise ExtractorError(
                f'No video streams found for Brazzers scene {video_id}.',
                expected=True,
            )

        # ── Step 5: Metadata ──────────────────────────────────────────────
        title = str_or_none(result.get('title')) or video_id
        description = str_or_none(result.get('description'))

        timestamp = unified_timestamp(str_or_none(result.get('dateReleased')))

        actors = result.get('actors') or []
        cast = [a['name'] for a in actors if a.get('name')]

        tags = result.get('tags') or []
        categories = [t['name'] for t in tags if t.get('name') and t.get('isVisible')]

        # Thumbnail — pick the best image from imageMasters or images
        thumbnail = None
        for img_list_key in ('imageMasters', 'images'):
            imgs = result.get(img_list_key) or []
            if imgs:
                thumbnail = (imgs[0].get('src') or imgs[0].get('url') or
                             imgs[0].get('path'))
                if thumbnail:
                    break

        # Also check children galleries for images
        if not thumbnail:
            for child in result.get('children') or []:
                if child.get('type') == 'gallery':
                    for img_list_key in ('imageMasters', 'images'):
                        imgs = child.get(img_list_key) or []
                        if imgs:
                            thumbnail = (imgs[0].get('src') or imgs[0].get('url') or
                                         imgs[0].get('path'))
                            if thumbnail:
                                break
                if thumbnail:
                    break

        duration = None
        for vtype in videos.values():
            duration = int_or_none(vtype.get('length'))
            if duration:
                break

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
            'timestamp': timestamp,
            'duration': duration,
            'cast': cast or None,
            'categories': categories or None,
            'age_limit': 18,
            'availability': 'subscriber' if is_member_unlocked else 'public',
        }

    # yt-dlp uses this fake UA internally
    _FAKE_UA = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )


class BrazzersPlaylistIE(InfoExtractor):
    """
    Playlist extractor for Brazzers category / pornstar / tag pages.
    e.g. https://www.brazzers.com/pornstar/view/xxx/
    """

    _NETRC_MACHINE = 'brazzers'
    _VALID_URL = r'https?://(?:[\w-]+\.)?brazzers\.com/(?:pornstar|category|tag)/(?:view/)?(?P<id>[\w-]+)/?'

    _TESTS = [{
        'url': 'https://www.brazzers.com/pornstar/view/valentina-nappi/',
        'info_dict': {
            'id': 'valentina-nappi',
            'title': str,
        },
        'playlist_mincount': 1,
        'skip': 'Requires premium account',
    }]

    def _real_extract(self, url):
        list_id = self._match_id(url)
        webpage = self._download_webpage(url, list_id)

        title = self._html_search_meta(['og:title', 'twitter:title'], webpage, default=list_id)

        entries = [
            self.url_result(link, ie=BrazzersIE.ie_key())
            for link in _ordered_set(re.findall(
                r'<a[^>]+href=["\']([^"\']*brazzers\.com/(?:video/(?:view/)?\d+|scene/\d+)[^"\']*)["\']',
                webpage,
            ))
        ]

        return self.playlist_result(entries, playlist_id=list_id, playlist_title=title)


def _ordered_set(iterable):
    seen = set()
    result = []
    for item in iterable:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
