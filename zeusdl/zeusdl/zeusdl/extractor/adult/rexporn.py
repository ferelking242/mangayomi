import re

from ..common import InfoExtractor
from ...utils import (
    clean_html,
    int_or_none,
    merge_dicts,
    parse_duration,
    str_or_none,
    unified_strdate,
    urljoin,
)


class RexPornIE(InfoExtractor):
    IE_NAME = 'rexporn'
    IE_DESC = 'RexPorn — single video'
    _VALID_URL = r'https?://(?:www\.)?rexporn\.st/(?:videos?/)?(?P<id>[\w-]+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://www.rexporn.st/videos/some-video-title/',
        'info_dict': {
            'id': 'some-video-title',
            'ext': 'mp4',
            'title': str,
            'age_limit': 18,
        },
        'skip': 'Live site test',
    }]

    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.rexporn.st/',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, headers=self._HEADERS)

        # JSON-LD VideoObject
        json_ld = self._search_json_ld(webpage, video_id, default={})

        title = (
            json_ld.get('title')
            or self._og_search_title(webpage, default=None)
            or self._html_search_regex(r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=video_id)
        )
        title = re.sub(r'\s*[-–|]\s*[Rr]ex[Pp]orn.*$', '', title).strip()

        # Try HTML5 media entries (handles <video>/<source> tags)
        entries = self._parse_html5_media_entries(url, webpage, video_id,
                                                   m3u8_id='hls', mpd_id='dash')
        formats = entries[0]['formats'] if entries else []

        # Fallback: scan for MP4 / m3u8 URLs in inline scripts or data attrs
        if not formats:
            for pattern in (
                r'["\'](?:file|src|videoUrl|video_url|mp4)["\']:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
                r'<source[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']',
                r'jwplayer\([^)]*\)\.setup\(\s*\{[^}]*?file:\s*["\']([^"\']+)["\']',
                r'player\.src\(\s*\{[^}]*?src:\s*["\']([^"\']+)["\']',
            ):
                video_url = self._search_regex(pattern, webpage, 'video url', default=None)
                if video_url:
                    formats.append({'url': video_url, 'ext': 'mp4'})
                    break

        m3u8_url = self._search_regex(
            r'["\']([^"\']+\.m3u8[^"\']*)["\']', webpage, 'm3u8', default=None)
        if m3u8_url and not any('.m3u8' in f.get('url', '') for f in formats):
            m3u8_fmts = self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', fatal=False, headers=self._HEADERS)
            formats.extend(m3u8_fmts)

        thumbnail = (
            json_ld.get('thumbnail')
            or self._og_search_thumbnail(webpage, default=None)
            or self._search_regex(
                r'<video[^>]+poster=["\']([^"\']+)["\']', webpage, 'thumbnail', default=None)
        )

        duration = (
            parse_duration(json_ld.get('duration'))
            or int_or_none(self._search_regex(
                r'data-(?:video-)?duration=["\'](\d+)["\']', webpage, 'duration', default=None))
            or parse_duration(self._search_regex(
                r'<[^>]+class=["\'][^"\']*duration[^"\']*["\'][^>]*>([^<]+)<',
                webpage, 'duration text', default=None))
        )

        view_count = int_or_none(self._search_regex(
            r'(?:views?|watched)[^\d]*(\d[\d,]*)',
            webpage, 'view count', default=None, flags=re.IGNORECASE))

        upload_date = unified_strdate(str_or_none(
            json_ld.get('upload_date')
            or self._search_regex(
                r'(?:Added|Uploaded|Date)[^\d]*(\d{4}[-/]\d{2}[-/]\d{2})',
                webpage, 'upload date', default=None)))

        tags = re.findall(
            r'href=["\'][^"\']*(?:/tag|/category|/model|/pornstar|/actress)/[^"\']+["\']>([^<]+)<',
            webpage)

        cast = [
            m.strip()
            for m in re.findall(
                r'href=["\'][^"\']*(?:/model|/pornstar|/actress)/[^"\']+["\']>([^<]+)<',
                webpage)
            if m.strip()
        ]

        description = clean_html(self._og_search_description(webpage, default=None))

        return merge_dicts({'formats': formats}, {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'upload_date': upload_date,
            'tags': [t.strip() for t in tags if t.strip()],
            'cast': cast,
            'age_limit': 18,
            'http_headers': {'Referer': 'https://www.rexporn.st/'},
        })


class RexPornPlaylistIE(InfoExtractor):
    IE_NAME = 'rexporn:playlist'
    IE_DESC = 'RexPorn — category / tag / search listing'
    _VALID_URL = r'https?://(?:www\.)?rexporn\.st/(?:(?:category|tag|model|search)/(?P<id>[\w-]+)|(?:\?.*[?&](?:q|s)=(?P<query>[^&#]+)))(?:[/?&#]|$)'
    _TESTS = [{
        'url': 'https://www.rexporn.st/category/teen/',
        'info_dict': {
            'id': 'teen',
            'title': str,
        },
        'playlist_mincount': 1,
        'skip': 'Live site test',
    }]

    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.rexporn.st/',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    @classmethod
    def suitable(cls, url):
        return bool(re.match(cls._VALID_URL, url)) and not RexPornIE.suitable(url)

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        playlist_id = mobj.group('id') or mobj.group('query') or 'listing'
        entries = list(self._entries(url, playlist_id))

        webpage = self._download_webpage(url, playlist_id, headers=self._HEADERS, fatal=False) or ''
        title = (
            self._og_search_title(webpage, default=None)
            or playlist_id.replace('-', ' ').title()
        )

        return self.playlist_result(entries, playlist_id, title)

    def _entries(self, start_url, playlist_id):
        seen = set()
        page = 1
        next_url = start_url

        while next_url:
            webpage = self._download_webpage(
                next_url, playlist_id,
                note=f'Downloading page {page}',
                headers=self._HEADERS,
                fatal=False,
            )
            if not webpage:
                break

            found_any = False
            for mobj in re.finditer(
                    r'href=["\'](?:https?://(?:www\.)?rexporn\.st)?(/(?:videos?/)?(?P<vid_id>[\w-]+)/?)["\']',
                    webpage):
                vid_id = mobj.group('vid_id')
                if not vid_id or vid_id in seen or vid_id in (
                        'category', 'tag', 'model', 'search', 'page', 'index'):
                    continue
                seen.add(vid_id)
                found_any = True
                full_url = f'https://www.rexporn.st/videos/{vid_id}/'
                yield {
                    '_type': 'url',
                    'url': full_url,
                    'ie_key': 'RexPorn',
                    'id': vid_id,
                    'title': vid_id.replace('-', ' ').title(),
                    'age_limit': 18,
                }

            if not found_any:
                break

            next_page = self._search_regex(
                r'href=["\']([^"\']+/page/\d+/?)["\'][^>]*>(?:Next|›|»|\d)',
                webpage, 'next page', default=None)
            if not next_page:
                next_page = self._search_regex(
                    r'href=["\']([^"\']*[?&]paged?=\d+[^"\']*)["\'][^>]*>(?:Next|›|»)',
                    webpage, 'next page (query)', default=None)
            if not next_page:
                break

            next_url = urljoin('https://www.rexporn.st', next_page)
            page += 1
