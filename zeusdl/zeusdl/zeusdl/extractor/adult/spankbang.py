import re
import urllib.parse

from ..common import InfoExtractor
from ...utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    merge_dicts,
    parse_duration,
    parse_resolution,
    str_to_int,
    url_or_none,
    urlencode_postdata,
    urljoin,
)
from ...utils.traversal import find_element, traverse_obj, trim_str


class SpankBangBaseIE(InfoExtractor):
    """Shared helpers for all SpankBang extractors."""

    _BASE = 'https://spankbang.com'

    def _set_country_cookie(self):
        country = self.get_param('geo_bypass_country') or 'US'
        self._set_cookie('.spankbang.com', 'country', country.upper())

    @staticmethod
    def _uniform_entry(video_id, title=None, thumbnail=None, duration=None,
                       view_count=None, uploader=None, tags=None):
        """Return a uniform ZeusDL video entry dict for SpankBang list pages."""
        return {
            '_type': 'url',
            'id': video_id,
            'url': f'https://spankbang.com/{video_id}/video/',
            'ie_key': 'SpankBang',
            'title': clean_html(title) if title else video_id,
            'thumbnail': thumbnail,
            'duration': parse_duration(duration) if isinstance(duration, str) else int_or_none(duration),
            'view_count': int_or_none(str(view_count or '').replace(',', '').replace(' ', '')),
            'uploader': uploader,
            'tags': tags or [],
            'age_limit': 18,
        }

    def _scrape_list_page(self, start_url, list_id, label='page'):
        """Scrape a paginated SpankBang video listing, yielding uniform entries."""
        next_url = start_url
        page_num = 0
        while next_url:
            page_num += 1
            page = self._download_webpage(
                next_url, list_id, f'Downloading {label} {page_num}',
                impersonate=True, fatal=False)
            if not page:
                break

            found = False
            for mobj in re.finditer(
                    r'<div[^>]+class=["\'][^"\']*video-item[^"\']*["\'][^>]*>.*?'
                    r'<a[^>]+href=["\'](?P<path>/(?P<vid_id>[0-9a-z]+)/(?:video|play)[^"\']*)["\']'
                    r'[^>]*(?:\s+title=["\'](?P<title>[^"\']+)["\'])?[^>]*>.*?'
                    r'(?:<img[^>]+(?:data-src|src)=["\'](?P<thumb>[^"\']+)["\'])?',
                    page, re.DOTALL):
                vid_id = mobj.group('vid_id')
                path = mobj.group('path')
                if not vid_id or not path:
                    continue
                found = True
                title = mobj.group('title')
                thumb = mobj.group('thumb')

                # Extract duration if present near the card
                duration = None
                # view count
                view_count = None

                yield self._uniform_entry(
                    video_id=vid_id,
                    title=title,
                    thumbnail=thumb,
                    duration=duration,
                    view_count=view_count,
                )

            if not found:
                # Fallback: simpler link pattern
                for mobj in re.finditer(
                        r'href=["\'](?P<path>/(?P<vid_id>[0-9a-z]+)/video/[^"\']+)["\']',
                        page):
                    vid_id = mobj.group('vid_id')
                    if vid_id:
                        found = True
                        yield self._uniform_entry(vid_id)

            if not found:
                break

            # Find next page
            next_mobj = re.search(
                r'<a[^>]+class=["\'][^"\']*next[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
                page)
            if next_mobj:
                next_url = urljoin(self._BASE, next_mobj.group(1))
            else:
                break


class SpankBangIE(SpankBangBaseIE):
    IE_NAME = 'spankbang'
    IE_DESC = 'SpankBang — single video'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:[^/]+\.)?spankbang\.com/
                        (?:
                            (?P<id>[\da-z]+)/(?:video|play|embed)\b|
                            [\da-z]+-(?P<id_2>[\da-z]+)/playlist/[^/?#&]+
                        )
                    '''
    _TESTS = [{
        'url': 'https://spankbang.com/56b3d/video/the+slut+maker+hmv',
        'info_dict': {
            'id': '56b3d',
            'ext': 'mp4',
            'title': str,
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id') or mobj.group('id_2')
        self._set_country_cookie()
        webpage = self._download_webpage(
            url.replace(f'/{video_id}/embed', f'/{video_id}/video'),
            video_id, impersonate=True)

        if re.search(r'<[^>]+\b(?:id|class)=["\']video_removed', webpage):
            raise ExtractorError(f'Video {video_id} is not available', expected=True)

        formats = []

        def extract_format(format_id, format_url):
            f_url = url_or_none(format_url)
            if not f_url:
                return
            f = parse_resolution(format_id)
            ext = determine_ext(f_url)
            if format_id.startswith('m3u8') or ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    f_url, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
            elif format_id.startswith('mpd') or ext == 'mpd':
                formats.extend(self._extract_mpd_formats(f_url, video_id, mpd_id='dash', fatal=False))
            elif ext == 'mp4' or f.get('width') or f.get('height'):
                f.update({'url': f_url, 'format_id': format_id})
                formats.append(f)

        for fmobj in re.finditer(
                r'stream_url_(?P<id>[^\s=]+)\s*=\s*(["\'])(?P<url>(?:(?!\2).)+)\2', webpage):
            extract_format(fmobj.group('id'), fmobj.group('url'))

        if not formats:
            stream_key = self._search_regex(
                r'data-streamkey\s*=\s*(["\'])(?P<value>(?:(?!\1).)+)\1',
                webpage, 'stream key', group='value')
            stream = self._download_json(
                f'{self._BASE}/api/videos/stream', video_id,
                'Downloading stream JSON',
                data=urlencode_postdata({'id': stream_key, 'data': 0}),
                headers={'Referer': url, 'X-Requested-With': 'XMLHttpRequest'},
                impersonate=True)
            for format_id, format_url in stream.items():
                if format_url and isinstance(format_url, list):
                    format_url = format_url[0]
                extract_format(format_id, format_url)

        info = self._search_json_ld(webpage, video_id, default={})

        title = self._html_search_regex(
            r'(?s)<h1[^>]+\btitle=["\']([^"]+)["\']>', webpage, 'title', default=None)
        tags = re.findall(r'<a[^>]+href=["\'][^"\']+/tag/[^"\']+["\'][^>]*>([^<]+)</a>', webpage)

        return merge_dicts({
            'id': video_id,
            'title': title or video_id,
            'description': self._search_regex(
                r'<div[^>]+\bclass=["\']bottom[^>]+>\s*<p>[^<]*</p>\s*<p>([^<]+)',
                webpage, 'description', default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'uploader': self._html_search_regex(
                r'<svg[^>]+\bclass="(?:[^"]*?user[^"]*?)">.*?</svg>([^<]+)', webpage, 'uploader', default=None),
            'uploader_id': self._html_search_regex(
                r'<a[^>]+href="/profile/([^"]+)"', webpage, 'uploader_id', default=None),
            'duration': parse_duration(self._search_regex(
                r'<div[^>]+\bclass=["\']right_side[^>]+>\s*<span>([^<]+)', webpage, 'duration', default=None)),
            'view_count': str_to_int(self._search_regex(
                r'([\d,.]+)\s+plays', webpage, 'view count', default=None)),
            'tags': tags,
            'formats': formats,
            'age_limit': self._rta_search(webpage),
        }, info)


class SpankBangPlaylistIE(SpankBangBaseIE):
    IE_NAME = 'spankbang:playlist'
    IE_DESC = 'SpankBang — playlist (all videos)'
    _VALID_URL = r'https?://(?:[^/]+\.)?spankbang\.com/(?P<id>[\da-z]+)/playlist/(?P<display_id>[^/?#&]+)'
    _TEST = {
        'url': 'https://spankbang.com/ug0k/playlist/big+ass+titties',
        'info_dict': {'id': 'ug0k', 'title': 'Big Ass Titties'},
        'playlist_mincount': 20,
    }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        playlist_id = mobj.group('id')
        self._set_country_cookie()
        webpage = self._download_webpage(url, playlist_id, impersonate=True)

        entries = [self.url_result(
            urljoin(url, m.group('path')),
            ie=SpankBangIE.ie_key(), video_id=m.group('id'))
            for m in re.finditer(
                r'<a[^>]+\bhref=(["\'])(?P<path>/?[\da-z]+-(?P<id>[\da-z]+)/playlist/[^"\'](?:(?!\1).)*)\1',
                webpage)]

        title = traverse_obj(webpage, (
            {find_element(tag='h1', attr='data-testid', value='playlist-title')},
            {clean_html}, {trim_str(end=' Playlist')}))

        return self.playlist_result(entries, playlist_id, title)


class SpankBangProfileIE(SpankBangBaseIE):
    IE_NAME = 'spankbang:profile'
    IE_DESC = 'SpankBang — profile/channel videos (all pages)'
    _VALID_URL = r'https?://(?:[^/]+\.)?spankbang\.com/profile/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        profile_id = self._match_id(url)
        self._set_country_cookie()
        profile_url = f'{self._BASE}/profile/{profile_id}/videos/'
        webpage = self._download_webpage(profile_url, profile_id, impersonate=True)
        title = self._html_search_regex(
            r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=profile_id)
        entries = self._scrape_list_page(profile_url, profile_id, label='profile page')
        return self.playlist_result(entries, profile_id, f'SpankBang — {title}')


class SpankBangTagIE(SpankBangBaseIE):
    IE_NAME = 'spankbang:tag'
    IE_DESC = 'SpankBang — tag/category videos (all pages)'
    _VALID_URL = r'https?://(?:[^/]+\.)?spankbang\.com/(?:tag|category)/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        tag_id = self._match_id(url)
        self._set_country_cookie()
        tag_url = f'{self._BASE}/tag/{urllib.parse.quote(tag_id)}/'
        entries = self._scrape_list_page(tag_url, tag_id, label='tag page')
        return self.playlist_result(entries, tag_id, f'SpankBang — Tag: {tag_id}')


class SpankBangSearchIE(SpankBangBaseIE):
    IE_NAME = 'spankbang:search'
    IE_DESC = 'SpankBang — search results (all pages)'
    _VALID_URL = r'https?://(?:[^/]+\.)?spankbang\.com/s/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        query_id = self._match_id(url)
        query = urllib.parse.unquote_plus(query_id).replace('+', ' ')
        self._set_country_cookie()
        search_url = f'{self._BASE}/s/{urllib.parse.quote(query_id)}/'
        entries = self._scrape_list_page(search_url, query_id, label='search page')
        return self.playlist_result(entries, query_id, f'SpankBang — Search: {query}')


class SpankBangTrendingIE(SpankBangBaseIE):
    IE_NAME = 'spankbang:trending'
    IE_DESC = 'SpankBang — trending/popular/new videos (all pages)'
    _VALID_URL = r'https?://(?:[^/]+\.)?spankbang\.com/(?P<id>trending|popular|new)/?'

    def _real_extract(self, url):
        section_id = self._match_id(url)
        self._set_country_cookie()
        section_url = f'{self._BASE}/{section_id}/'
        entries = self._scrape_list_page(section_url, section_id, label=f'{section_id} page')
        return self.playlist_result(entries, section_id, f'SpankBang — {section_id.capitalize()}')
