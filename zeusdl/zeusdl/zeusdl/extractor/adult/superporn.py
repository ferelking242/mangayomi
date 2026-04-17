import re

from ..common import InfoExtractor
from ...utils import (
    clean_html,
    int_or_none,
    parse_duration,
    str_or_none,
    unified_strdate,
    urljoin,
)


class SuperPornIE(InfoExtractor):
    IE_NAME = 'superporn'
    IE_DESC = 'SuperPorn — single video'
    _VALID_URL = r'https?://(?:www\.)?superporn\.com/video/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.superporn.com/video/hot-stepfathers-exchange',
        'info_dict': {
            'id': 'hot-stepfathers-exchange',
            'ext': 'mp4',
            'title': 'Hot stepfathers exchange',
            'age_limit': 18,
        },
    }]

    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.superporn.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, headers=self._HEADERS)

        # Primary: JSON-LD VideoObject
        json_ld = self._search_json_ld(webpage, display_id, default={})

        title = (
            json_ld.get('title')
            or self._og_search_title(webpage, default=None)
            or self._html_search_regex(r'<title>([^<]+?)(?:\s*-\s*SuperPorn)?</title>', webpage, 'title')
        )

        # Direct MP4 source from <source> tag
        video_url = self._search_regex(
            r'<source\s+src="([^"]+)"[^>]+type="video/mp4"', webpage, 'video URL', fatal=False)
        if not video_url:
            video_url = self._search_regex(
                r'<source\s+src="([^"]+)"', webpage, 'video URL', fatal=True)

        # Duration: data attribute (seconds) or JSON-LD (ISO 8601)
        duration = int_or_none(self._search_regex(
            r'data-video-duration="(\d+)"', webpage, 'duration', default=None))
        if duration is None:
            duration = json_ld.get('duration') or parse_duration(
                self._html_search_meta('duration', webpage, default=None))

        thumbnail = (
            json_ld.get('thumbnails', [{'url': None}])[0].get('url')
            or json_ld.get('thumbnail')
            or self._og_search_thumbnail(webpage, default=None)
        )

        upload_date = unified_strdate(str_or_none(
            json_ld.get('upload_date') or json_ld.get('timestamp')
            or self._search_regex(r'"uploadDate"\s*:\s*"([^"]+)"', webpage, 'upload date', default=None)
        ))

        description = (
            json_ld.get('description')
            or clean_html(self._og_search_description(webpage, default=None))
        )

        # Tags and categories from anchor links
        tags = list(set(
            re.findall(r'href="[^"]*?/tag/[^"]+">([^<]+)<', webpage)
            + re.findall(r'href="[^"]*?/category/[^"]+">([^<]+)<', webpage)
        ))

        # View count
        view_count = int_or_none(self._search_regex(
            r'"interactionCount"\s*:\s*"?(\d+)"?', webpage, 'view count', default=None))

        # Embed ID for reference
        embed_id = self._search_regex(r'/embed/(\d+)', webpage, 'embed id', default=display_id)

        return {
            'id': embed_id or display_id,
            'display_id': display_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'thumbnail': thumbnail,
            'description': description,
            'duration': duration,
            'upload_date': upload_date,
            'tags': tags,
            'view_count': view_count,
            'age_limit': 18,
            'http_headers': {'Referer': 'https://www.superporn.com/'},
        }


class SuperPornSeriesIE(InfoExtractor):
    IE_NAME = 'superporn:series'
    IE_DESC = 'SuperPorn — series playlist'
    _VALID_URL = r'https?://(?:www\.)?superporn\.com/series/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.superporn.com/series/the-best-fresh-porn',
        'info_dict': {
            'id': 'the-best-fresh-porn',
            'title': str,
        },
        'playlist_mincount': 1,
    }]

    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.superporn.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    def _real_extract(self, url):
        series_id = self._match_id(url)
        entries = list(self._entries(url, series_id))

        title = self._og_search_title(
            self._download_webpage(url, series_id, headers=self._HEADERS, note='Downloading series page'),
            default=series_id,
        )
        title = re.sub(r'\s*[-–|]\s*SuperPorn.*$', '', title).strip()

        return self.playlist_result(entries, series_id, title)

    def _entries(self, url, series_id):
        base_url = url.split('?')[0]
        seen_urls = set()

        for page in range(1, 50):
            page_url = f'{base_url}?page={page}' if page > 1 else base_url
            webpage = self._download_webpage(
                page_url, series_id,
                note=f'Downloading series page {page}',
                headers=self._HEADERS,
                fatal=False,
            )
            if not webpage:
                break

            video_links = re.findall(
                r'href="(https?://(?:www\.)?superporn\.com/video/[\w-]+)"',
                webpage,
            )
            video_links = list(dict.fromkeys(video_links))  # deduplicate preserving order

            new_links = [l for l in video_links if l not in seen_urls]
            if not new_links:
                break

            for link in new_links:
                seen_urls.add(link)
                slug = link.rstrip('/').rsplit('/', 1)[-1]
                yield {
                    '_type': 'url',
                    'url': link,
                    'ie_key': 'SuperPorn',
                    'id': slug,
                    'title': slug.replace('-', ' ').title(),
                    'age_limit': 18,
                }

            # No pagination links → only one page
            if not re.search(r'page=\d+', webpage):
                break
