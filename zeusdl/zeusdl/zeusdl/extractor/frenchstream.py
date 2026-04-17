"""
FrenchStream extractor (fs13.lol / french-stream.one).

fs13.lol is a mirror of french-stream.one, a French streaming site
built on DataLife Engine (DLE) CMS.  Video pages embed third-party
players loaded from external CDN hosts.

Auth: no account required for free content; some sources need cookies.
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


class FrenchStreamIE(InfoExtractor):
    IE_NAME = 'frenchstream'
    IE_DESC = 'fs13.lol / french-stream.one'

    _VALID_URL = (
        r'https?://(?:www\.)?(?:fs13\.lol|french-stream\.one|french-stream\d*\.(?:one|lol|re|vip))'
        r'/(?P<id>\d+-[\w-]+)\.html'
    )

    _TESTS = [{
        'url': 'https://fs13.lol/15126325-panique-nol.html',
        'info_dict': {
            'id': '15126325',
            'title': str,
        },
        'playlist_mincount': 1,
        'skip': 'Sources vary by availability',
    }]

    _DLE_AJAX = '/engine/ajax/controller.php'

    def _extract_player_sources(self, webpage, news_id, url):
        sources = []

        for m in re.finditer(
            r'<iframe[^>]+src=["\'](?P<src>https?://[^"\'<>\s]+)["\']',
            webpage,
        ):
            src = url_or_none(m.group('src'))
            if src:
                sources.append(src)

        for m in re.finditer(
            r'["\'](?P<src>https?://[^"\'<>\s]+\.(?:m3u8|mp4)[^"\'<>\s]*)["\']',
            webpage,
        ):
            src = url_or_none(m.group('src'))
            if src:
                sources.append(src)

        return list(dict.fromkeys(sources))

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        page_id = mobj.group('id')
        news_id = page_id.split('-')[0]

        webpage = self._download_webpage(url, page_id)

        title = (
            self._html_search_regex(r'<h1[^>]+id=["\']s-title["\'][^>]*>(.*?)</h1>', webpage, 'title', default=None)
            or self._html_search_meta(['og:title', 'twitter:title'], webpage, default=None)
            or self._html_search_regex(r'<title>([^<|]+)', webpage, 'title', default=page_id)
        )
        title = clean_html(title) or page_id

        thumbnail = (
            self._html_search_meta(['og:image', 'twitter:image'], webpage, default=None)
            or self._search_regex(r'url\((https?://[^)]+\.(?:jpg|jpeg|png|webp))', webpage, 'thumbnail', default=None)
        )

        description = self._html_search_meta(['og:description', 'description'], webpage, default=None)

        dle_login_hash = self._search_regex(
            r"var\s+dle_login_hash\s*=\s*['\"]([a-f0-9]+)['\"]",
            webpage, 'dle_login_hash', default='',
        )

        sources = self._extract_player_sources(webpage, news_id, url)

        if not sources:
            try:
                player_html = self._download_webpage(
                    self._BASE_URL(url) + self._DLE_AJAX,
                    news_id,
                    note='Fetching DLE player data',
                    data=f'news_id={news_id}&action=player&user_hash={dle_login_hash}'.encode(),
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Referer': url,
                    },
                    fatal=False,
                )
                if player_html:
                    sources.extend(self._extract_player_sources(player_html, news_id, url))
            except Exception:
                pass

        if not sources:
            raise ExtractorError(
                'No video sources found on this FrenchStream page. '
                'The sources may be loaded dynamically. Try opening the page in a browser.',
                expected=True,
            )

        if len(sources) == 1 and not any(ext in sources[0] for ext in ('.m3u8', '.mp4')):
            return self.url_result(sources[0], video_id=page_id, video_title=title)

        entries = []
        for i, src in enumerate(sources):
            entries.append(self.url_result(src, video_id=f'{page_id}-src{i + 1}'))

        if len(entries) == 1:
            result = entries[0]
            result.update({'id': page_id, 'title': title})
            return result

        return self.playlist_result(entries, playlist_id=page_id, playlist_title=title)

    @staticmethod
    def _BASE_URL(url):
        m = re.match(r'(https?://[^/]+)', url)
        return m.group(1) if m else ''


class FrenchStreamPlaylistIE(InfoExtractor):
    IE_NAME = 'frenchstream:playlist'
    IE_DESC = 'fs13.lol / french-stream.one — category or search pages'

    _VALID_URL = (
        r'https?://(?:www\.)?(?:fs13\.lol|french-stream\.one|french-stream\d*\.(?:one|lol|re|vip))'
        r'/(?![\d][\w-]*\.html)(?P<id>[^?#]+)'
    )

    _TESTS = [{
        'url': 'https://fs13.lol/films/actions/',
        'info_dict': {
            'id': 'films/actions/',
            'title': str,
        },
        'playlist_mincount': 1,
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        title = (
            self._html_search_meta(['og:title', 'twitter:title'], webpage, default=None)
            or self._html_search_regex(r'<title>([^<|]+)', webpage, 'title', default=page_id)
        )

        entries = []
        for m in re.finditer(
            r'href=["\'](?P<url>https?://[^"\']+/\d+-[\w-]+\.html)["\']',
            webpage,
        ):
            entries.append(self.url_result(m.group('url'), ie=FrenchStreamIE.ie_key()))

        seen = set()
        unique_entries = []
        for e in entries:
            u = e['url']
            if u not in seen:
                seen.add(u)
                unique_entries.append(e)

        return self.playlist_result(unique_entries, playlist_id=page_id, playlist_title=clean_html(title))
