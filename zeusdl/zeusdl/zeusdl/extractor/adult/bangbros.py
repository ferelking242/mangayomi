"""
BangBros extractor (Project1 / MindGeek API).

BangBros runs on the same Project1 platform as Brazzers.  The API is
identical but the instance URL and cookie domain differ.

Auth
────
BangBros requires a Google reCAPTCHA v3 token for first-time login, so
headless login is not reliable.

Recommended flow:
1. Log in at https://bangbros.com in your browser.
2. Export cookies (e.g. with "Get cookies.txt LOCALLY").
3. Pass them:  zeusdl --cookies ~/bangbros.txt URL
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


_AUTH_API = 'https://auth-service.project1service.com'
_DATA_API = 'https://site-api.project1service.com'
_INSTANCE_URL = 'https://bangbros.com/'


def _extract_project1_formats(videos, video_id):
    formats = []
    PREFER_ORDER = ['full', 'clip', 'mediabook']
    for video_type in sorted(videos, key=lambda t: PREFER_ORDER.index(t) if t in PREFER_ORDER else 99):
        files = (videos[video_type] or {}).get('files') or {}
        is_full = video_type == 'full'
        for quality_label, file_info in files.items():
            urls = file_info.get('urls') or {}
            url = urls.get('download') or urls.get('view')
            if not url:
                continue
            height = int_or_none(re.search(r'(\d+)p', quality_label or ''), group=1)
            formats.append({
                'url': url,
                'ext': 'mp4',
                'format_id': f'{video_type}-{quality_label}',
                'height': height,
                'fps': int_or_none(file_info.get('fps')),
                'filesize': int_or_none(file_info.get('sizeBytes')),
                'vcodec': file_info.get('codec'),
                'quality': 1 if is_full else -1,
            })
    return formats


class BangBrosIE(InfoExtractor):
    _NETRC_MACHINE = 'bangbros'

    _VALID_URL = (
        r'https?://(?:www\.)?bangbros\.com'
        r'/(?:scene|video/(?:view/)?)(?:/(?P<id_num>\d+))?/?(?P<id_slug>[\w-]+)?/?'
    )

    _TESTS = [{
        'url': 'https://www.bangbros.com/scene/lets-get-fucking-weird',
        'info_dict': {
            'id': str,
            'ext': 'mp4',
            'title': str,
            'age_limit': 18,
        },
        'skip': 'Requires premium account',
    }]

    _FAKE_UA = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )

    def _get_instance_token(self, video_id):
        self._download_webpage(
            _INSTANCE_URL, video_id,
            note='Fetching BangBros instance token',
            errnote='Could not reach BangBros',
        )
        for cookie in self._downloader.cookiejar:
            if cookie.name == 'instance_token':
                return cookie.value
        return None

    def _get_session_id(self):
        for cookie in self._downloader.cookiejar:
            if cookie.name == 'app_session_id':
                return cookie.value
        return ''

    def _get_access_token(self):
        for cookie in self._downloader.cookiejar:
            if cookie.name == 'access_token_ma':
                return cookie.value
        return None

    def _api_headers(self, instance_token, session_id, access_token=None):
        h = {
            'Accept': 'application/json',
            'Origin': 'https://bangbros.com',
            'Referer': 'https://bangbros.com/',
            'Instance': instance_token or '',
            'x-app-session-id': session_id or '',
        }
        if access_token:
            h['Authorization'] = access_token
        return h

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        numeric_id = mobj.group('id_num')
        slug = mobj.group('id_slug') or numeric_id

        instance_token = self._get_instance_token(slug)
        session_id = self._get_session_id()
        access_token = self._get_access_token()

        if not instance_token:
            raise ExtractorError(
                'Could not obtain BangBros instance token. The site may be down.',
                expected=True,
            )

        headers = self._api_headers(instance_token, session_id, access_token)

        if numeric_id:
            release = self._download_json(
                f'{_DATA_API}/v2/releases/{numeric_id}',
                slug,
                note='Fetching release metadata',
                headers=headers,
            )
            result = release.get('result') or {}
        else:
            releases = self._download_json(
                f'{_DATA_API}/v2/releases',
                slug,
                note='Searching release by slug',
                query={'slug': slug, 'type': 'scene'},
                headers=headers,
                fatal=False,
            )
            if isinstance(releases, list) and releases:
                entry = releases[0]
                result = entry.get('result') or entry
            elif isinstance(releases, dict):
                result = releases.get('result') or releases
            else:
                raise ExtractorError(f'Scene not found: {slug}', expected=True)

            release_id = str_or_none(result.get('id'))
            if release_id:
                full = self._download_json(
                    f'{_DATA_API}/v2/releases/{release_id}',
                    slug,
                    note='Fetching full release data',
                    headers=headers,
                    fatal=False,
                )
                if full:
                    result = full.get('result') or result

        if not result:
            raise ExtractorError(f'No release data found for {slug}', expected=True)

        can_play = result.get('canPlay', False)
        videos = result.get('videos') or {}

        if not can_play:
            self.raise_login_required(
                'This BangBros video requires a premium membership. '
                'Export your browser cookies and pass them with --cookies.',
                method='cookies',
            )

        formats = _extract_project1_formats(videos, slug)
        if not formats:
            if not access_token:
                self.raise_login_required(
                    'No streams found. This video requires a BangBros premium account.',
                    method='cookies',
                )
            raise ExtractorError(f'No video streams found for {slug}.', expected=True)

        title = str_or_none(result.get('title')) or slug
        description = str_or_none(result.get('description'))
        timestamp = unified_timestamp(str_or_none(result.get('dateReleased')))
        cast = [a['name'] for a in (result.get('actors') or []) if a.get('name')]
        categories = [t['name'] for t in (result.get('tags') or [])
                      if t.get('name') and t.get('isVisible')]

        thumbnail = None
        for key in ('imageMasters', 'images'):
            imgs = result.get(key) or []
            if imgs:
                thumbnail = imgs[0].get('src') or imgs[0].get('url') or imgs[0].get('path')
                if thumbnail:
                    break

        duration = None
        for vtype in videos.values():
            duration = int_or_none(vtype.get('length'))
            if duration:
                break

        video_id = str_or_none(result.get('id')) or slug
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
        }
