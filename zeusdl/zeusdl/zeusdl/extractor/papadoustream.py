"""
PapaDuStream platform extractors — moiflix.net and dessinanime.net.

Both sites run on the same custom PHP streaming platform (visible from
identical HTML structure, shared playerjs.js, and cross-links in the footer).
The platform uses PlayerJS + FluidPlayer for video playback.

Video sources are loaded via a server-side AJAX endpoint:
  POST {base_url}/ajax/embed  body: id=<embed_id>&self=<embed_id>
The embed_id is stored in data-embed attributes on .btn-service elements.

Auth: register/login on the site; then import cookies.
"""

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    str_or_none,
    url_or_none,
)


class PapaDuStreamBaseIE(InfoExtractor):
    """Shared logic for the PapaDuStream platform (moiflix / dessinanime)."""

    _BASE = None

    def _fetch_embed_sources(self, embed_id, display_id, referer):
        html = self._download_webpage(
            f'{self._BASE}/ajax/embed',
            display_id,
            note=f'Fetching embed sources for {embed_id}',
            data=f'id={embed_id}&self={embed_id}'.encode(),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': referer,
                'Origin': self._BASE,
            },
            fatal=False,
        )
        return html or ''

    def _parse_embed_html(self, embed_html, display_id):
        formats = []
        subtitles = {}

        iframe_src = self._search_regex(
            r'<iframe[^>]+src=["\'](?P<src>https?://[^"\'<>\s]+)["\']',
            embed_html, 'iframe src', default=None,
        )
        if iframe_src and iframe_src.strip():
            return None, iframe_src, subtitles

        for m in re.finditer(
            r'<source[^>]+src=["\'](?P<src>https?://[^"\'<>\s]+)["\'][^>]*>',
            embed_html,
        ):
            src = url_or_none(m.group('src'))
            if not src:
                continue
            fmt_type = re.search(r'type=["\']([^"\']+)["\']', m.group(0))
            mime = (fmt_type.group(1) if fmt_type else '').lower()
            if 'm3u8' in src or 'hls' in mime:
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, display_id, 'mp4', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif '.mp4' in src or 'mp4' in mime:
                label = re.search(r'label=["\']([^"\']+)["\']', m.group(0))
                height = int_or_none(
                    re.search(r'(\d+)p', label.group(1) if label else ''), group=1)
                formats.append({
                    'url': src,
                    'ext': 'mp4',
                    'format_id': label.group(1) if label else None,
                    'height': height,
                })

        for m in re.finditer(
            r'["\'](?P<src>https?://[^"\'<>\s]+\.m3u8[^"\'<>\s]*)["\']',
            embed_html,
        ):
            src = url_or_none(m.group('src'))
            if src:
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, display_id, 'mp4', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)

        return formats, None, subtitles

    def _extract_metadata(self, webpage, video_id):
        title = (
            self._html_search_meta(['og:title', 'twitter:title'], webpage, default=None)
            or self._search_regex(
                r'<h1[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>(.*?)</h1>',
                webpage, 'title', default=None, flags=re.DOTALL)
            or self._html_search_regex(r'<title>([^<|]+)', webpage, 'title', default=video_id)
        )
        thumbnail = self._html_search_meta(['og:image', 'twitter:image'], webpage, default=None)
        description = self._html_search_meta(['og:description', 'description'], webpage, default=None)

        jsonld = self._search_json(
            r'application/ld\+json[^>]*>', webpage,
            'JSON-LD', video_id, contains_pattern=r'\{[^{}]+\}', default={},
        )
        if not title and jsonld:
            title = jsonld.get('name')
        if not thumbnail and jsonld:
            thumbnail = jsonld.get('image')
        if not description and jsonld:
            description = jsonld.get('description')

        return {
            'title': clean_html(title) or video_id,
            'thumbnail': thumbnail,
            'description': clean_html(description),
        }

    def _real_extract_page(self, url, video_id, is_episode=False):
        webpage = self._download_webpage(url, video_id)
        meta = self._extract_metadata(webpage, video_id)

        embed_ids = re.findall(r'data-embed=["\']([^"\']+)["\']', webpage)

        if not embed_ids and is_episode:
            raise ExtractorError(
                f'No embed sources found for {video_id}. '
                'Try logging in and importing cookies.',
                expected=True,
            )

        if not embed_ids:
            return self.playlist_result([], playlist_id=video_id, **meta)

        all_formats = []
        all_subs = {}
        redirect_url = None

        for embed_id in embed_ids:
            embed_html = self._fetch_embed_sources(embed_id, video_id, referer=url)
            if not embed_html:
                continue
            formats, iframe_src, subs = self._parse_embed_html(embed_html, video_id)
            if iframe_src:
                redirect_url = redirect_url or iframe_src
            if formats:
                all_formats.extend(formats)
            self._merge_subtitles(subs, target=all_subs)

        if not all_formats and redirect_url:
            return self.url_result(redirect_url, video_id=video_id, video_title=meta['title'])

        if not all_formats:
            raise ExtractorError(
                f'No playable streams found for {video_id}. '
                'The embed sources returned empty results — '
                'you may need to be logged in.',
                expected=True,
            )

        self._sort_formats(all_formats)
        return {
            'id': video_id,
            'formats': all_formats,
            'subtitles': all_subs or None,
            **meta,
        }


class MoiFlixIE(PapaDuStreamBaseIE):
    IE_NAME = 'moiflix'
    IE_DESC = 'moiflix.net'

    _VALID_URL = (
        r'https?://(?:www\.)?moiflix\.net'
        r'/(?P<type>movie|episode|show)/(?P<id>[A-Za-z0-9_-]+)'
    )
    _BASE = 'https://moiflix.net'

    _TESTS = [{
        'url': 'https://moiflix.net/movie/lXa3ickIfCobqPG2IhCkqCwdkx704yp8',
        'info_dict': {
            'id': 'lXa3ickIfCobqPG2IhCkqCwdkx704yp8',
            'title': str,
        },
        'skip': 'Sources depend on site availability',
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        content_type = mobj.group('type')
        video_id = mobj.group('id')
        is_episode = content_type == 'episode'
        return self._real_extract_page(url, video_id, is_episode=is_episode)


class MoiFlixShowIE(PapaDuStreamBaseIE):
    IE_NAME = 'moiflix:show'
    IE_DESC = 'moiflix.net — show/series index'

    _VALID_URL = r'https?://(?:www\.)?moiflix\.net/show/(?P<id>[A-Za-z0-9_-]+)/?$'
    _BASE = 'https://moiflix.net'

    _TESTS = [{
        'url': 'https://moiflix.net/show/K1q3iaNGiyHtCkwM4rcSw73FEAxx1t0v',
        'info_dict': {
            'id': 'K1q3iaNGiyHtCkwM4rcSw73FEAxx1t0v',
            'title': str,
        },
        'playlist_mincount': 1,
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)
        meta = self._extract_metadata(webpage, show_id)

        episode_urls = re.findall(
            r'href=["\'](?P<url>https://moiflix\.net/episode/[A-Za-z0-9_-]+)["\']',
            webpage,
        )
        seen = set()
        entries = []
        for ep_url in episode_urls:
            if ep_url not in seen:
                seen.add(ep_url)
                entries.append(self.url_result(ep_url, ie=MoiFlixIE.ie_key()))

        return self.playlist_result(entries, playlist_id=show_id, **meta)


class DessinsAnimeIE(PapaDuStreamBaseIE):
    IE_NAME = 'dessinanime'
    IE_DESC = 'dessinanime.net'

    _VALID_URL = (
        r'https?://(?:www\.)?dessinanime\.net'
        r'/(?P<type>movie|episode|show)/(?P<id>[A-Za-z0-9_-]+)'
    )
    _BASE = 'https://dessinanime.net'

    _TESTS = [{
        'url': 'https://dessinanime.net/movie/10',
        'info_dict': {
            'id': '10',
            'title': str,
        },
        'skip': 'Sources depend on site availability',
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        content_type = mobj.group('type')
        video_id = mobj.group('id')
        is_episode = content_type == 'episode'
        return self._real_extract_page(url, video_id, is_episode=is_episode)


class DessinsAnimeShowIE(PapaDuStreamBaseIE):
    IE_NAME = 'dessinanime:show'
    IE_DESC = 'dessinanime.net — show/series index'

    _VALID_URL = r'https?://(?:www\.)?dessinanime\.net/show/(?P<id>[A-Za-z0-9_-]+)/?$'
    _BASE = 'https://dessinanime.net'

    _TESTS = [{
        'url': 'https://dessinanime.net/show/K1q3iaNGiyHtCkwM4rcSw73FEAxx1t0v',
        'info_dict': {
            'id': 'K1q3iaNGiyHtCkwM4rcSw73FEAxx1t0v',
            'title': str,
        },
        'playlist_mincount': 1,
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)
        meta = self._extract_metadata(webpage, show_id)

        episode_urls = re.findall(
            r'href=["\'](?P<url>https://dessinanime\.net/episode/[A-Za-z0-9_-]+)["\']',
            webpage,
        )
        seen = set()
        entries = []
        for ep_url in episode_urls:
            if ep_url not in seen:
                seen.add(ep_url)
                entries.append(self.url_result(ep_url, ie=DessinsAnimeIE.ie_key()))

        return self.playlist_result(entries, playlist_id=show_id, **meta)
