import re
import urllib.parse

from ..common import InfoExtractor
from ...utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    parse_duration,
    str_to_int,
    urljoin,
)


class XVideosBaseIE(InfoExtractor):
    """Base class for all XVideos extractors with shared utilities."""

    _BASE_URL = 'https://www.xvideos.com'
    _API_BASE = 'https://www.xvideos.com/api/json'

    @staticmethod
    def _entry_from_api(video):
        """Convert an API video object into a uniform ZeusDL entry dict."""
        video_id = str(video.get('id', ''))
        clean_id = re.sub(r'\D', '', video_id) or video_id  # numeric part
        url = f'https://www.xvideos.com/video{clean_id}/_'
        return {
            '_type': 'url',
            'id': video_id,
            'url': url,
            'ie_key': 'XVideos',
            'title': clean_html(video.get('u') or video.get('tf_title') or ''),
            'thumbnail': video.get('i') or video.get('if') or video.get('img'),
            'duration': int_or_none(video.get('d') or video.get('tf')),
            'view_count': int_or_none(video.get('nb_v') or video.get('nb_views')),
            'uploader': video.get('up') or video.get('cn') or video.get('channel'),
            'tags': video.get('ki') or [],
            'age_limit': 18,
        }

    def _fetch_api_page(self, endpoint, item_id, page=0, query=None):
        """Fetch a paginated API endpoint and return the parsed JSON."""
        url = f'{self._API_BASE}/{endpoint}/{page}'
        if query:
            url += '?' + urllib.parse.urlencode(query)
        return self._download_json(url, item_id, f'Downloading page {page}', fatal=False) or {}

    def _entries_from_list(self, endpoint, item_id, query=None):
        """Generator: yield entries from a paginated API list endpoint."""
        for page in range(0, 100):  # safety cap of 100 pages
            data = self._fetch_api_page(endpoint, item_id, page, query)
            videos = data.get('videos') or []
            if not videos:
                break
            for v in videos:
                yield self._entry_from_api(v)
            # Stop if we've seen all videos
            nb_total = int_or_none(data.get('nb_videos')) or 0
            fetched = (page + 1) * len(videos)
            if fetched >= nb_total or len(videos) < 32:
                break


class XVideosIE(XVideosBaseIE):
    IE_NAME = 'xvideos'
    IE_DESC = 'XVideos — single video'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:[^/]+\.)?xvideos2?\.com/video\.?|
                            (?:www\.)?xvideos\.es/video\.?|
                            (?:www|flashservice)\.xvideos\.com/embedframe/|
                            static-hw\.xvideos\.com/swf/xv-player\.swf\?.*?\bid_video=
                        )
                        (?P<id>[0-9a-z]+)
                    '''
    _TESTS = [{
        'url': 'https://xvideos.com/video.ucuvbkfda4e/a_beautiful_red-haired_stranger',
        'info_dict': {
            'id': 'ucuvbkfda4e',
            'ext': 'mp4',
            'title': str,
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(r'<h1 class="inlineError">(.+?)</h1>', webpage)
        if mobj:
            raise ExtractorError(f'{self.IE_NAME} said: {clean_html(mobj.group(1))}', expected=True)

        title = self._html_search_regex(
            (r'<title>(?P<title>.+?)\s+-\s+XVID',
             r'setVideoTitle\s*\(\s*(["\'])(?P<title>(?:(?!\1).)+)\1'),
            webpage, 'title', default=None,
            group='title') or self._og_search_title(webpage)

        thumbnails = []
        for preference, thumbnail_suffix in enumerate(('', '169')):
            thumbnail_url = self._search_regex(
                rf'setThumbUrl{thumbnail_suffix}\(\s*(["\'])(?P<thumbnail>(?:(?!\1).)+)\1',
                webpage, 'thumbnail', default=None, group='thumbnail')
            if thumbnail_url:
                thumbnails.append({'url': thumbnail_url, 'preference': preference})

        duration = int_or_none(self._og_search_property('duration', webpage, default=None)) or parse_duration(
            self._search_regex(
                r'<span[^>]+class=["\']duration["\'][^>]*>.*?(\d[^<]+)',
                webpage, 'duration', fatal=False))

        uploader = self._html_search_regex(
            r'<a[^>]+data-channel[^>]*>([^<]+)', webpage, 'uploader', default=None) or self._html_search_regex(
            r'Uploaded\s+by\s+<a[^>]+>([^<]+)', webpage, 'uploader', default=None)

        view_count = str_to_int(self._search_regex(
            r'([\d,.]+)\s+views', webpage, 'view count', default=None))

        tags = re.findall(r'<a[^>]+href=["\'][^"\']*keywords[^"\']*["\'][^>]*>([^<]+)</a>', webpage)

        formats = []

        video_url = urllib.parse.unquote(self._search_regex(
            r'flv_url=(.+?)&', webpage, 'video URL', default=''))
        if video_url:
            formats.append({'url': video_url, 'format_id': 'flv'})

        for kind, _, format_url in re.findall(
                r'setVideo([^(]+)\((["\'])(http.+?)\2\)', webpage):
            format_id = kind.lower()
            if format_id == 'hls':
                hls_formats = self._extract_m3u8_formats(
                    format_url, video_id, 'mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
                self._check_formats(hls_formats, video_id)
                formats.extend(hls_formats)
            elif format_id in ('urllow', 'urlhigh'):
                formats.append({
                    'url': format_url,
                    'format_id': '{}-{}'.format(determine_ext(format_url, 'mp4'), format_id[3:]),
                    'quality': -2 if format_id.endswith('low') else None,
                })

        return {
            'id': video_id,
            'title': title,
            'thumbnails': thumbnails,
            'duration': duration,
            'uploader': uploader,
            'view_count': view_count,
            'tags': tags,
            'formats': formats,
            'age_limit': 18,
        }


class XVideosQuickiesIE(XVideosBaseIE):
    IE_NAME = 'xvideos:quickies'
    IE_DESC = 'XVideos — quickie (short video from profile)'
    _VALID_URL = r'https?://(?P<domain>(?:[^/?#]+\.)?xvideos2?\.com)/(?:profiles/|amateur-channels/)?[^/?#]+#quickies/a/(?P<id>\w+)'

    def _real_extract(self, url):
        domain, id_ = self._match_valid_url(url).group('domain', 'id')
        return self.url_result(
            f'https://{domain}/video{"" if id_.isdecimal() else "."}{id_}/_',
            XVideosIE, id_)


class XVideosProfileIE(XVideosBaseIE):
    IE_NAME = 'xvideos:profile'
    IE_DESC = 'XVideos — user/profile video list with full pagination'
    _VALID_URL = r'https?://(?:[^/]+\.)?xvideos2?\.com/(?:profiles|amateur-channels)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.xvideos.com/profiles/lili_love',
        'info_dict': {
            'id': 'lili_love',
            'title': str,
        },
        'playlist_mincount': 5,
    }]

    def _real_extract(self, url):
        profile_id = self._match_id(url)
        webpage = self._download_webpage(url, profile_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=profile_id)

        # XVideos API endpoint for profile videos
        entries = self._entries_from_list(f'videos/profiles/{profile_id}', profile_id)
        return self.playlist_result(entries, profile_id, title)


class XVideosPornstarIE(XVideosBaseIE):
    IE_NAME = 'xvideos:pornstar'
    IE_DESC = 'XVideos — pornstar page (all videos, fully paginated)'
    _VALID_URL = r'https?://(?:[^/]+\.)?xvideos2?\.com/pornstar(?:-channels)?/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.xvideos.com/pornstar-channels/mia-malkova',
        'info_dict': {
            'id': 'mia-malkova',
            'title': str,
        },
        'playlist_mincount': 5,
    }]

    def _real_extract(self, url):
        star_id = self._match_id(url)
        webpage = self._download_webpage(url, star_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=star_id)

        # Try to get numeric ID from page for API
        numeric_id = self._search_regex(
            r'data-channel-id=["\'](\d+)["\']', webpage, 'channel id', default=None)

        if numeric_id:
            entries = self._entries_from_list(f'videos/channels/{numeric_id}', star_id)
        else:
            entries = self._entries_from_list(f'videos/pornstars/{star_id}', star_id)

        return self.playlist_result(entries, star_id, title)


class XVideosChannelIE(XVideosBaseIE):
    IE_NAME = 'xvideos:channel'
    IE_DESC = 'XVideos — channel video list (all pages)'
    _VALID_URL = r'https?://(?:[^/]+\.)?xvideos2?\.com/channels/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        webpage = self._download_webpage(url, channel_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=channel_id)

        numeric_id = self._search_regex(
            r'data-channel-id=["\'](\d+)["\']', webpage, 'channel id', default=channel_id)

        entries = self._entries_from_list(f'videos/channels/{numeric_id}', channel_id)
        return self.playlist_result(entries, channel_id, title)


class XVideosPlaylistIE(XVideosBaseIE):
    IE_NAME = 'xvideos:playlist'
    IE_DESC = 'XVideos — playlist/album (all pages)'
    _VALID_URL = r'https?://(?:[^/]+\.)?xvideos2?\.com/(?:[^/?#]+/)?favorite/(?P<id>\d+)(?:/[^/?#]*)?'

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=f'Playlist {playlist_id}')

        entries = self._entries_from_list(f'videos/playlists/{playlist_id}', playlist_id)
        return self.playlist_result(entries, playlist_id, title)


class XVideosCategoryIE(XVideosBaseIE):
    IE_NAME = 'xvideos:category'
    IE_DESC = 'XVideos — category page (browseable, all pages)'
    _VALID_URL = r'https?://(?:[^/]+\.)?xvideos2?\.com/c/(?P<id>[^/?#]+)/\d+'

    def _real_extract(self, url):
        category_id = self._match_id(url)
        # Category pages are scraped from HTML since no clean API exists
        webpage = self._download_webpage(url, category_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', default=category_id)

        def _get_entries():
            page_url = url
            for page_num in range(0, 50):
                if page_num > 0:
                    page_url = re.sub(r'/\d+$', f'/{page_num * 32}', url)
                page = self._download_webpage(page_url, category_id, f'Downloading page {page_num + 1}', fatal=False)
                if not page:
                    break
                items = re.findall(
                    r'<div[^>]+class=["\'][^"\']*thumb-block[^"\']*["\'][^>]*>.*?'
                    r'<a[^>]+href=["\'](?P<path>/video[^"\']+)["\'][^>]*>.*?'
                    r'<img[^>]+(?:src|data-src)=["\'](?P<thumb>[^"\']+)["\'][^>]*>.*?'
                    r'<p[^>]+class=["\'][^"\']*title[^"\']*["\'][^>]*>(?P<title>[^<]+)<',
                    page, re.DOTALL)
                if not items:
                    break
                for path, thumb, vtitle in items:
                    vid_id = re.search(r'/video\.?([0-9a-z]+)', path)
                    if vid_id:
                        yield {
                            '_type': 'url',
                            'id': vid_id.group(1),
                            'url': urljoin('https://www.xvideos.com', path),
                            'ie_key': 'XVideos',
                            'title': clean_html(vtitle),
                            'thumbnail': thumb,
                            'age_limit': 18,
                        }
                if len(items) < 30:
                    break

        return self.playlist_result(_get_entries(), category_id, title)


class XVideosSearchIE(XVideosBaseIE):
    IE_NAME = 'xvideos:search'
    IE_DESC = 'XVideos — search results (all pages)'
    _VALID_URL = r'https?://(?:[^/]+\.)?xvideos2?\.com/\?(?:[^#]*&)?k=(?P<id>[^&#]+)'

    def _real_extract(self, url):
        query_str = self._match_id(url)
        query = urllib.parse.unquote_plus(query_str)

        def _get_entries():
            for page in range(0, 50):
                search_url = f'https://www.xvideos.com/?k={urllib.parse.quote(query)}&p={page}'
                page_html = self._download_webpage(
                    search_url, query, f'Downloading search page {page + 1}', fatal=False)
                if not page_html:
                    break
                items = re.findall(
                    r'<div[^>]+id=["\']video_(?P<vid_id>[0-9a-z]+)["\'][^>]*>.*?'
                    r'href=["\'](?P<path>/video[^"\']+)["\'].*?'
                    r'<img[^>]+src=["\'](?P<thumb>[^"\']+)["\'].*?'
                    r'<strong[^>]*>(?P<vtitle>[^<]+)</strong>',
                    page_html, re.DOTALL)
                if not items:
                    break
                for vid_id, path, thumb, vtitle in items:
                    yield {
                        '_type': 'url',
                        'id': vid_id,
                        'url': urljoin('https://www.xvideos.com', path),
                        'ie_key': 'XVideos',
                        'title': clean_html(vtitle),
                        'thumbnail': thumb,
                        'age_limit': 18,
                    }
                if len(items) < 30:
                    break

        return self.playlist_result(
            _get_entries(),
            query,
            f'XVideos — Search: {query}')
