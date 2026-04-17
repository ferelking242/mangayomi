import re
import urllib.parse

from ..common import InfoExtractor
from ...utils import (
    NO_DEFAULT,
    clean_html,
    determine_ext,
    int_or_none,
    str_to_int,
    urljoin,
)


class XNXXBaseIE(InfoExtractor):
    """Shared helpers for all XNXX extractors."""

    _BASE = 'https://www.xnxx.com'

    @staticmethod
    def _uniform_entry(video_id, title=None, thumbnail=None, duration=None,
                       view_count=None, uploader=None, tags=None):
        """Return a uniform ZeusDL video entry for XNXX list pages."""
        return {
            '_type': 'url',
            'id': str(video_id),
            'url': f'https://www.xnxx.com/video-{video_id}/',
            'ie_key': 'XNXX',
            'title': clean_html(title) if title else str(video_id),
            'thumbnail': thumbnail,
            'duration': int_or_none(duration),
            'view_count': int_or_none(str(view_count or '').replace(',', '').replace(' ', '')),
            'uploader': uploader,
            'tags': tags or [],
            'age_limit': 18,
        }

    def _scrape_video_list(self, start_url, list_id, label='page'):
        """Scrape a paginated XNXX listing page (HTML-based), yielding uniform entries."""
        next_url = start_url
        page_num = 0
        while next_url:
            page_num += 1
            page = self._download_webpage(
                next_url, list_id, f'Downloading {label} {page_num}', fatal=False)
            if not page:
                break

            found = False
            # XNXX video thumbs are in <div class="thumb-block"> anchors
            for mobj in re.finditer(
                    r'<a[^>]+href=["\'](?P<path>/video-?(?P<vid_id>[0-9a-z]+)/[^"\']+)["\'][^>]*>'
                    r'(?:.*?<img[^>]+(?:src|data-src)=["\'](?P<thumb>[^"\']+)["\'])?',
                    page, re.DOTALL):
                vid_id = mobj.group('vid_id')
                if not vid_id:
                    continue
                found = True
                yield self._uniform_entry(
                    video_id=vid_id,
                    thumbnail=mobj.group('thumb'),
                )

            if not found:
                break

            # Find next page
            next_mobj = re.search(
                r'<a[^>]+class=["\'][^"\']*next[^"\']*["\'][^>]+href=["\']([^"\']+)["\']', page)
            if next_mobj:
                next_url = urljoin(self._BASE, next_mobj.group(1))
            else:
                # offset-based pagination: /0, /1, /2 …
                offset_mobj = re.search(r'/(\d+)$', next_url)
                if offset_mobj:
                    next_offset = int(offset_mobj.group(1)) + 1
                    next_url = re.sub(r'/\d+$', f'/{next_offset}', next_url)
                else:
                    break


class XNXXIE(XNXXBaseIE):
    IE_NAME = 'xnxx'
    IE_DESC = 'XNXX — single video'
    _VALID_URL = r'https?://(?:video|www)\.xnxx3?\.com/video-?(?P<id>[0-9a-z]+)/'
    _TESTS = [{
        'url': 'http://www.xnxx.com/video-55awb78/skyrim_test_video',
        'info_dict': {
            'id': '55awb78',
            'ext': 'mp4',
            'title': 'Skyrim Test Video',
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        def get(meta, default=NO_DEFAULT, fatal=True):
            return self._search_regex(
                rf'set{meta}\s*\(\s*(["\'])(?P<value>(?:(?!\1).)+)\1',
                webpage, meta, default=default, fatal=fatal, group='value')

        title = self._og_search_title(webpage, default=None) or get('VideoTitle')
        thumbnail = (self._og_search_thumbnail(webpage, default=None)
                     or get('ThumbUrl', fatal=False)
                     or get('ThumbUrl169', fatal=False))
        duration = int_or_none(self._og_search_property('duration', webpage))
        view_count = str_to_int(self._search_regex(
            r'id=["\']nb-views-number[^>]+>([\d,.]+)', webpage, 'view count', default=None))
        tags = re.findall(
            r'<a[^>]+href=["\'][^"\']+/tags/[^"\']+["\'][^>]*>([^<]+)</a>', webpage)
        uploader = self._html_search_regex(
            r'<a[^>]+href=["\'][^"\']+/profiles/[^"\']+["\'][^>]*>([^<]+)</a>',
            webpage, 'uploader', default=None)

        formats = []
        for mobj in re.finditer(
                r'setVideo(?:Url(?P<id>Low|High)|HLS)\s*\(\s*(?P<q>["\'])(?P<url>(?:https?:)?//.+?)(?P=q)', webpage):
            format_url = mobj.group('url')
            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    quality=1, m3u8_id='hls', fatal=False))
            else:
                format_id = mobj.group('id')
                if format_id:
                    format_id = format_id.lower()
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'quality': -1 if format_id == 'low' else 0,
                })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'uploader': uploader,
            'tags': tags,
            'formats': formats,
            'age_limit': 18,
        }


class XNXXProfileIE(XNXXBaseIE):
    IE_NAME = 'xnxx:profile'
    IE_DESC = 'XNXX — user profile videos (all pages)'
    _VALID_URL = r'https?://(?:www\.)?xnxx3?\.com/profiles/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        profile_id = self._match_id(url)
        profile_url = f'{self._BASE}/profiles/{profile_id}/videos/best/0'
        webpage = self._download_webpage(profile_url, profile_id, fatal=False) or ''
        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=profile_id)
        entries = self._scrape_video_list(profile_url, profile_id, label='profile page')
        return self.playlist_result(entries, profile_id, f'XNXX — {title}')


class XNXXCategoryIE(XNXXBaseIE):
    IE_NAME = 'xnxx:category'
    IE_DESC = 'XNXX — category/tag page (all pages)'
    _VALID_URL = r'https?://(?:www\.)?xnxx3?\.com/(?:tags?|category)/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        cat_id = self._match_id(url)
        mobj = re.match(r'https?://[^/]+/(?:tag|category)', url)
        path_type = 'tag' if mobj else 'category'
        cat_url = f'{self._BASE}/{path_type}/{urllib.parse.quote(cat_id)}/0'
        entries = self._scrape_video_list(cat_url, cat_id, label='category page')
        return self.playlist_result(entries, cat_id, f'XNXX — {cat_id}')


class XNXXSearchIE(XNXXBaseIE):
    IE_NAME = 'xnxx:search'
    IE_DESC = 'XNXX — search results (all pages)'
    _VALID_URL = r'https?://(?:www\.)?xnxx3?\.com/search/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        query_id = self._match_id(url)
        query = urllib.parse.unquote_plus(query_id).replace('+', ' ')
        search_url = f'{self._BASE}/search/{urllib.parse.quote(query_id)}/0'
        entries = self._scrape_video_list(search_url, query_id, label='search page')
        return self.playlist_result(entries, query_id, f'XNXX — Search: {query}')


class XNXXChannelIE(XNXXBaseIE):
    IE_NAME = 'xnxx:channel'
    IE_DESC = 'XNXX — channel/pornstar page (all pages)'
    _VALID_URL = r'https?://(?:www\.)?xnxx3?\.com/(?:pornstar|channel|amateur)/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        mobj = re.match(r'https?://[^/]+/([^/]+)/', url)
        path_type = mobj.group(1) if mobj else 'pornstar'
        channel_url = f'{self._BASE}/{path_type}/{urllib.parse.quote(channel_id)}/0'
        webpage = self._download_webpage(channel_url, channel_id, fatal=False) or ''
        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=channel_id)
        entries = self._scrape_video_list(channel_url, channel_id, label='channel page')
        return self.playlist_result(entries, channel_id, f'XNXX — {title}')
