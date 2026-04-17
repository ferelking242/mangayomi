import re
import urllib.parse

from ..common import InfoExtractor
from ...utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    merge_dicts,
    str_to_int,
    unified_strdate,
    url_or_none,
    urljoin,
)


class RedTubeBaseIE(InfoExtractor):
    """Shared utilities for all RedTube extractors."""

    _BASE = 'https://www.redtube.com'
    _API = 'https://api.redtube.com'

    @staticmethod
    def _uniform_entry(video_id, title, thumbnail=None, duration=None,
                       view_count=None, uploader=None, tags=None, upload_date=None):
        """Return a uniform ZeusDL video entry for RedTube list pages."""
        return {
            '_type': 'url',
            'id': str(video_id),
            'url': f'https://www.redtube.com/{video_id}',
            'ie_key': 'RedTube',
            'title': clean_html(title) if title else str(video_id),
            'thumbnail': thumbnail,
            'duration': int_or_none(duration),
            'view_count': int_or_none(str(view_count or '').replace(',', '')),
            'uploader': uploader,
            'tags': tags or [],
            'upload_date': upload_date,
            'age_limit': 18,
        }

    def _entries_from_api(self, params, list_id):
        """Paginate the RedTube public API and yield uniform entries."""
        base_params = dict(params)
        base_params.setdefault('output', 'json')
        base_params.setdefault('count', '16')

        for page in range(1, 200):
            base_params['page'] = page
            data = self._download_json(
                self._API,
                list_id,
                f'Downloading page {page}',
                query=base_params,
                fatal=False) or {}

            videos = data.get('videos') or []
            if not videos:
                break

            for v in videos:
                info = v.get('video') or v
                vid_id = str_to_int(info.get('video_id')) or info.get('id')
                if not vid_id:
                    continue
                tags = [t.get('tag_name') for t in (info.get('tags') or []) if t.get('tag_name')]
                yield self._uniform_entry(
                    video_id=vid_id,
                    title=info.get('title'),
                    thumbnail=info.get('thumb') or info.get('thumbnail'),
                    duration=info.get('duration'),
                    view_count=info.get('views'),
                    uploader=info.get('author') or info.get('channel'),
                    tags=tags,
                    upload_date=info.get('publish_date'),
                )

            total = int_or_none(data.get('count'))
            if total is not None and page * 16 >= total:
                break
            if len(videos) < 16:
                break

    def _scrape_video_list(self, start_url, list_id):
        """Fallback: scrape paginated HTML listing pages."""
        next_url = start_url
        page_num = 0
        while next_url:
            page_num += 1
            page = self._download_webpage(
                next_url, list_id, f'Downloading page {page_num}', fatal=False)
            if not page:
                break

            found = False
            for mobj in re.finditer(
                    r'<a[^>]+href=["\'](?P<path>/\d+)["\'][^>]*>\s*'
                    r'(?:.*?<img[^>]+src=["\'](?P<thumb>[^"\']+)["\'])?',
                    page, re.DOTALL):
                path = mobj.group('path')
                vid_id = re.search(r'/(\d+)', path)
                if not vid_id:
                    continue
                found = True
                thumb = mobj.group('thumb')
                yield {
                    '_type': 'url',
                    'id': vid_id.group(1),
                    'url': urljoin(self._BASE, path),
                    'ie_key': 'RedTube',
                    'thumbnail': thumb,
                    'age_limit': 18,
                }

            if not found:
                break

            # Find next page link
            next_mobj = re.search(
                r'<a[^>]+class=["\'][^"\']*next[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
                page)
            next_url = urljoin(self._BASE, next_mobj.group(1)) if next_mobj else None


class RedTubeIE(RedTubeBaseIE):
    IE_NAME = 'redtube'
    IE_DESC = 'RedTube — single video'
    _VALID_URL = r'https?://(?:(?:\w+\.)?redtube\.com(?:\.br)?/|embed\.redtube\.com/\?.*?\bid=)(?P<id>[0-9]+)'
    _EMBED_REGEX = [r'<iframe[^>]+?src=["\'](?P<url>(?:https?:)?//embed\.redtube\.com/\?.*?\bid=\d+)']
    _TESTS = [{
        'url': 'https://www.redtube.com/38864951',
        'info_dict': {
            'id': '38864951',
            'ext': 'mp4',
            'title': str,
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'{self._BASE}/{video_id}', video_id)

        ERRORS = (
            (('video-deleted-info', '>This video has been removed'), 'has been removed'),
            (('private_video_text', '>This video is private', '>Send a friend request to its owner to be able to view it'), 'is private'),
        )
        for patterns, message in ERRORS:
            if any(p in webpage for p in patterns):
                raise ExtractorError(f'Video {video_id} {message}', expected=True)

        info = self._search_json_ld(webpage, video_id, default={})

        if not info.get('title'):
            info['title'] = self._html_search_regex(
                (r'<h(\d)[^>]+class="(?:video_title_text|videoTitle|video_title)[^"]*">(?P<title>(?:(?!\1).)+)</h\1>',
                 r'(?:videoTitle|title)\s*:\s*(["\'])(?P<title>(?:(?!\1).)+)\1'),
                webpage, 'title', group='title',
                default=None) or self._og_search_title(webpage)

        formats = []
        sources = self._parse_json(
            self._search_regex(r'sources\s*:\s*({.+?})', webpage, 'source', default='{}'),
            video_id, fatal=False)
        if sources and isinstance(sources, dict):
            for format_id, format_url in sources.items():
                if format_url:
                    formats.append({
                        'url': format_url,
                        'format_id': format_id,
                        'height': int_or_none(format_id),
                    })
        medias = self._parse_json(
            self._search_regex(
                r'mediaDefinition["\']?\s*:\s*(\[.+?}\s*\])', webpage, 'media definitions', default='{}'),
            video_id, fatal=False)
        for media in medias if isinstance(medias, list) else []:
            format_url = url_or_none(media.get('videoUrl') or media.get('src'))
            if not format_url:
                continue
            format_id = media.get('format')
            quality = media.get('quality')
            if format_id == 'hls' or (format_id == 'mp4' and not quality):
                more_media = self._download_json(format_url, video_id, fatal=False)
            else:
                more_media = [media]
            for m in more_media if isinstance(more_media, list) else []:
                furl = url_or_none(m.get('videoUrl') or m.get('src'))
                if not furl:
                    continue
                fid = m.get('format')
                if fid == 'hls' or determine_ext(furl) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        furl, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id=fid or 'hls', fatal=False))
                    continue
                fid = m.get('quality')
                formats.append({'url': furl, 'ext': 'mp4', 'format_id': fid, 'height': int_or_none(fid)})
        if not formats:
            video_url = self._html_search_regex(
                r'<source src="(.+?)" type="video/mp4">', webpage, 'video URL')
            formats.append({'url': video_url, 'ext': 'mp4'})

        tags = re.findall(
            r'<a[^>]+href=["\'][^"\']+/tag/[^"\']+["\'][^>]*>([^<]+)</a>', webpage)
        uploader = self._html_search_regex(
            r'<a[^>]+class=["\'][^"\']*author[^"\']*["\'][^>]*>([^<]+)</a>',
            webpage, 'uploader', default=None)

        return merge_dicts(info, {
            'id': video_id,
            'ext': 'mp4',
            'thumbnail': self._og_search_thumbnail(webpage),
            'upload_date': unified_strdate(self._search_regex(
                r'<span[^>]+>(?:ADDED|Published on) ([^<]+)<', webpage, 'upload date', default=None)),
            'duration': int_or_none(self._og_search_property('video:duration', webpage, default=None)
                                    or self._search_regex(r'videoDuration\s*:\s*(\d+)', webpage, 'duration', default=None)),
            'view_count': str_to_int(self._search_regex(
                (r'<div[^>]*>Views</div>\s*<div[^>]*>\s*([\d,.]+)',
                 r'<span[^>]*>VIEWS</span>\s*</td>\s*<td>\s*([\d,.]+)',
                 r'<span[^>]+\bclass=["\']video_view_count[^>]*>\s*([\d,.]+)'),
                webpage, 'view count', default=None)),
            'uploader': uploader,
            'tags': tags,
            'formats': formats,
            'age_limit': 18,
        })


class RedTubeCategoryIE(RedTubeBaseIE):
    IE_NAME = 'redtube:category'
    IE_DESC = 'RedTube — category page (all pages, API-powered)'
    _VALID_URL = r'https?://(?:www\.)?redtube\.com/category/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        cat_id = self._match_id(url)
        entries = self._entries_from_api({'data': 'redtube.Videos.searchVideos', 'category': cat_id}, cat_id)
        return self.playlist_result(entries, cat_id, f'RedTube — Category: {cat_id}')


class RedTubeSearchIE(RedTubeBaseIE):
    IE_NAME = 'redtube:search'
    IE_DESC = 'RedTube — search results (all pages, API-powered)'
    _VALID_URL = r'https?://(?:www\.)?redtube\.com/\?(?:[^#]*&)?search=(?P<id>[^&#]+)'

    def _real_extract(self, url):
        query = urllib.parse.unquote_plus(self._match_id(url))
        entries = self._entries_from_api({'data': 'redtube.Videos.searchVideos', 'search': query}, query)
        return self.playlist_result(entries, query, f'RedTube — Search: {query}')


class RedTubeTagIE(RedTubeBaseIE):
    IE_NAME = 'redtube:tag'
    IE_DESC = 'RedTube — tag/keyword page (all pages, API-powered)'
    _VALID_URL = r'https?://(?:www\.)?redtube\.com/tag/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        tag_id = self._match_id(url)
        entries = self._entries_from_api({'data': 'redtube.Videos.searchVideos', 'tags[0][id]': tag_id}, tag_id)
        return self.playlist_result(entries, tag_id, f'RedTube — Tag: {tag_id}')


class RedTubePornstarIE(RedTubeBaseIE):
    IE_NAME = 'redtube:pornstar'
    IE_DESC = 'RedTube — pornstar/model page (all pages, API-powered)'
    _VALID_URL = r'https?://(?:www\.)?redtube\.com/pornstars/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        star_id = self._match_id(url)
        entries = self._entries_from_api({'data': 'redtube.Videos.searchVideos', 'star': star_id}, star_id)
        return self.playlist_result(entries, star_id, f'RedTube — Pornstar: {star_id}')


class RedTubeChannelIE(RedTubeBaseIE):
    IE_NAME = 'redtube:channel'
    IE_DESC = 'RedTube — uploader/channel page (HTML scrape, all pages)'
    _VALID_URL = r'https?://(?:www\.)?redtube\.com/(?:channels|users)/(?P<id>[^/?#]+)'

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        channel_url = f'{self._BASE}/users/{channel_id}/videos'
        entries = self._scrape_video_list(channel_url, channel_id)
        return self.playlist_result(entries, channel_id, f'RedTube — Channel: {channel_id}')
