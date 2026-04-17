import re
import urllib.parse

from ..common import InfoExtractor
from ...utils import (
    clean_html,
    int_or_none,
    merge_dicts,
    parse_duration,
    str_or_none,
    unified_strdate,
    urljoin,
    url_or_none,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.hqporner.com/',
}

def _normalize_url(url):
    """Convert mobile URL to desktop URL."""
    return re.sub(r'https?://m\.hqporner\.com', 'https://www.hqporner.com', url)


# ---------------------------------------------------------------------------
# Single video extractor
# ---------------------------------------------------------------------------
class HQPornerIE(InfoExtractor):
    IE_NAME = 'hqporner'
    IE_DESC = 'HQPorner — single video'
    _VALID_URL = r'https?://(?:www\.|m\.)?hqporner\.com/hdporn/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.hqporner.com/hdporn/125696-pretty_mellow_and_sexy_in_yellow.html',
        'info_dict': {
            'id': '125696-pretty_mellow_and_sexy_in_yellow.html',
            'ext': 'mp4',
            'title': str,
            'age_limit': 18,
        },
        'skip': 'Live site test',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = _normalize_url(url)
        webpage = self._download_webpage(url, video_id, headers=_HEADERS)

        # ── Title ────────────────────────────────────────────────────────────
        title = (
            self._og_search_title(webpage, default=None)
            or self._html_search_regex(r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=video_id)
        )
        title = re.sub(r'\s*[-–|]\s*(?:HQ\s*Porner|hqporner)[^$]*$', '', title, flags=re.IGNORECASE).strip()

        # ── Embed URL from mydaddy.cc ─────────────────────────────────────────
        embed_url = self._search_regex(
            [
                r"url\s*[=:]\s*['\"]?((?:https?:)?//mydaddy\.cc/video/[a-f0-9]+/?)['\"]?",
                r'<iframe[^>]+src=["\']([^"\']*mydaddy\.cc/video/[^"\']+)["\']',
                r"['\"](?:https?:)?//(mydaddy\.cc/video/[a-f0-9]+/?)['\"]",
                r"/blocks/altplayer\.php\?i=((?://|https?://)mydaddy\.cc/video/[^&\"']+)",
            ],
            webpage, 'embed url', default=None,
        )
        if not embed_url:
            # fallback: scan all src/href for mydaddy
            m = re.search(r'((?:https?:)?//mydaddy\.cc/video/[a-f0-9]+/?)', webpage)
            if m:
                embed_url = m.group(1)

        formats = []

        if embed_url:
            # Normalize scheme
            if embed_url.startswith('//'):
                embed_url = 'https:' + embed_url
            embed_url = embed_url.split('&')[0]  # strip altplayer params

            embed_page = self._download_webpage(
                embed_url, video_id,
                note='Downloading embed page',
                headers={**_HEADERS, 'Referer': url},
                fatal=False,
            ) or ''

            def _clean_src(src):
                """Remove backslashes and trailing garbage, normalize scheme."""
                src = src.replace('\\', '').strip()
                if src.startswith('//'):
                    src = 'https:' + src
                return src

            seen_urls: set = set()

            def _add_format(src, label=None):
                src = _clean_src(src)
                if src in seen_urls:
                    return
                seen_urls.add(src)
                height_m = re.search(r'(\d{3,4})(?:p|\.mp4)', src if label is None else label)
                height = int_or_none(height_m.group(1)) if height_m else None
                fmt_id = label.strip() if label else (f'{height}p' if height else 'unknown')
                formats.append({
                    'url': src,
                    'format_id': fmt_id,
                    'height': height,
                    'ext': 'mp4',
                    'http_headers': {'Referer': embed_url},
                })

            # Pattern 1: src before title (most common in mydaddy.cc JS)
            for src, label in re.findall(
                r'<source\s+src=\\?["\']([^"\'\\]+)\\?["\'][^>]*title=\\?["\']([^"\'\\]+)\\?["\']',
                embed_page, re.IGNORECASE,
            ):
                _add_format(src, label)

            # Pattern 2: title before src
            if not seen_urls:
                for label, src in re.findall(
                    r'<source\s+[^>]*title=\\?["\']([^"\'\\]+)\\?["\'][^>]*src=\\?["\']([^"\'\\]+)\\?["\']',
                    embed_page, re.IGNORECASE,
                ):
                    _add_format(src, label)

            # Fallback: any bigcdn.cc MP4 URL in the JS
            if not seen_urls:
                for src in re.findall(r'((?:https?:)?//[^\s"\'<>\\]+bigcdn\.cc[^\s"\'<>\\]+\.mp4)', embed_page):
                    _add_format(src)

        # ── Fallback: scan main page for any MP4 ─────────────────────────────
        if not formats:
            for src in re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', webpage):
                formats.append({'url': src, 'ext': 'mp4'})

        # ── Sort formats best-first ───────────────────────────────────────────
        formats.sort(key=lambda f: f.get('height') or 0, reverse=True)

        # ── Metadata from main page ───────────────────────────────────────────
        thumbnail = (
            self._og_search_thumbnail(webpage, default=None)
            or self._search_regex(r'<video[^>]+poster=["\']([^"\']+)["\']', webpage, 'thumbnail', default=None)
        )

        duration = parse_duration(
            self._search_regex(
                r'<[^>]+class=["\'][^"\']*duration[^"\']*["\'][^>]*>([^<]+)<',
                webpage, 'duration', default=None,
            )
        ) or int_or_none(
            self._search_regex(r'data-(?:video-)?duration=["\'](\d+)["\']', webpage, 'duration', default=None)
        )

        view_count = int_or_none(re.sub(r'[,\s]', '', self._search_regex(
            r'(?:views?|watched)[^\d]*(\d[\d,\s]*)',
            webpage, 'view count', default='', flags=re.IGNORECASE,
        ) or ''))

        upload_date = unified_strdate(str_or_none(
            self._search_regex(
                r'(?:Added|Uploaded)[^\d]*(\d{4}[-/]\d{2}[-/]\d{2})',
                webpage, 'upload date', default=None,
            )
        ))

        tags = list(set(re.findall(
            r'href=["\'][^"\']*(?:/tag|/category|/pornstar|/actress|/studio)/[^"\']+["\']>([^<]+)<',
            webpage,
        )))

        description = clean_html(self._og_search_description(webpage, default=None))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'upload_date': upload_date,
            'tags': [t.strip() for t in tags if t.strip()],
            'formats': formats,
            'age_limit': 18,
        }


# ---------------------------------------------------------------------------
# Generic listing extractor (actress / studio / category / search / tag)
# ---------------------------------------------------------------------------
class HQPornerListingIE(InfoExtractor):
    IE_NAME = 'hqporner:listing'
    IE_DESC = 'HQPorner — actress / studio / category / tag listing'
    _VALID_URL = (
        r'https?://(?:www\.|m\.)?hqporner\.com/'
        r'(?P<section>actress|studio|category|tag|pornstar|director|channel)/(?P<id>[^/?#]+)'
    )
    _TESTS = [{
        'url': 'https://m.hqporner.com/actress/aletta-ocean',
        'info_dict': {'id': 'aletta-ocean', 'title': str},
        'playlist_mincount': 1,
        'skip': 'Live site test',
    }, {
        'url': 'https://m.hqporner.com/studio/free-brazzers-videos',
        'info_dict': {'id': 'free-brazzers-videos', 'title': str},
        'playlist_mincount': 1,
        'skip': 'Live site test',
    }, {
        'url': 'https://m.hqporner.com/category/milf',
        'info_dict': {'id': 'milf', 'title': str},
        'playlist_mincount': 1,
        'skip': 'Live site test',
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        playlist_id = mobj.group('id')
        section = mobj.group('section')
        url = _normalize_url(url)

        webpage = self._download_webpage(url, playlist_id, headers=_HEADERS, fatal=False) or ''
        title = (
            self._og_search_title(webpage, default=None)
            or self._html_search_regex(r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None)
            or f'{section.title()}: {playlist_id.replace("-", " ").title()}'
        )
        title = re.sub(r'\s*[-–|]\s*(?:HQ\s*Porner|hqporner)[^$]*$', '', title, flags=re.IGNORECASE).strip()

        entries = list(self._entries(url, playlist_id))
        return self.playlist_result(entries, playlist_id, title)

    def _entries(self, start_url, playlist_id):
        seen = set()
        page = 1
        next_url = start_url

        while next_url:
            webpage = self._download_webpage(
                next_url, playlist_id,
                note=f'Downloading page {page}',
                headers=_HEADERS,
                fatal=False,
            )
            if not webpage:
                break

            found_any = False
            for path in re.findall(r'href=["\'](/hdporn/[^"\'?#]+)["\']', webpage):
                vid_id = path.lstrip('/')
                if vid_id in seen:
                    continue
                seen.add(vid_id)
                found_any = True
                full_url = f'https://www.hqporner.com/{vid_id}'
                # Try to grab title from nearby alt text or card title
                slug = re.sub(r'^\d+-', '', path.rsplit('/', 1)[-1]).replace('_', ' ').replace('-', ' ')
                slug = re.sub(r'\.html$', '', slug).strip().title()
                yield {
                    '_type': 'url',
                    'url': full_url,
                    'ie_key': 'HQPorner',
                    'id': vid_id,
                    'title': slug or vid_id,
                    'age_limit': 18,
                }

            if not found_any:
                break

            # Pagination — HQPorner uses ?p=N or ?page=N
            next_page = self._search_regex(
                [
                    r'href=["\']([^"\']*[?&]p(?:age)?=\d+[^"\']*)["\'][^>]*>(?:Next|›|»|\d)',
                    r'<a[^>]+class=["\'][^"\']*next[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
                ],
                webpage, 'next page', default=None,
            )
            if not next_page:
                break

            next_url = urljoin('https://www.hqporner.com', next_page)
            page += 1


# ---------------------------------------------------------------------------
# Search extractor
# ---------------------------------------------------------------------------
class HQPornerSearchIE(InfoExtractor):
    IE_NAME = 'hqporner:search'
    IE_DESC = 'HQPorner — search results'
    _VALID_URL = r'https?://(?:www\.|m\.)?hqporner\.com/?\?(?:[^#]*&)?q=(?P<id>[^&#]+)'
    _TESTS = [{
        'url': 'https://m.hqporner.com/?q=freshporn',
        'info_dict': {'id': 'freshporn', 'title': 'Search: freshporn'},
        'playlist_mincount': 1,
        'skip': 'Live site test',
    }]

    def _real_extract(self, url):
        query_id = self._match_id(url)
        query = urllib.parse.unquote_plus(query_id)
        search_url = f'https://www.hqporner.com/?q={urllib.parse.quote_plus(query)}'
        entries = list(self._entries(search_url, query_id))
        return self.playlist_result(entries, query_id, f'Search: {query}')

    def _entries(self, start_url, playlist_id):
        seen = set()
        page = 1
        next_url = start_url

        while next_url:
            webpage = self._download_webpage(
                next_url, playlist_id,
                note=f'Downloading search page {page}',
                headers=_HEADERS,
                fatal=False,
            )
            if not webpage:
                break

            found_any = False
            for path in re.findall(r'href=["\'](/hdporn/[^"\'?#]+)["\']', webpage):
                vid_id = path.lstrip('/')
                if vid_id in seen:
                    continue
                seen.add(vid_id)
                found_any = True
                slug = re.sub(r'^\d+-', '', path.rsplit('/', 1)[-1]).replace('_', ' ').replace('-', ' ')
                slug = re.sub(r'\.html$', '', slug).strip().title()
                yield {
                    '_type': 'url',
                    'url': f'https://www.hqporner.com/{vid_id}',
                    'ie_key': 'HQPorner',
                    'id': vid_id,
                    'title': slug or vid_id,
                    'age_limit': 18,
                }

            if not found_any:
                break

            next_page = self._search_regex(
                r'href=["\']([^"\']*[?&]p(?:age)?=\d+[^"\']*)["\'][^>]*>(?:Next|›|»)',
                webpage, 'next page', default=None,
            )
            if not next_page:
                break

            next_url = urljoin('https://www.hqporner.com', next_page)
            page += 1
