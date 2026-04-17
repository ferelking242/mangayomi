"""
freeonlinek.top extractor.

freeonlinek.top is a thin iframe wrapper around moviestv.my.
The entire site is a single page that embeds the real player from
moviestv.my inside a fullscreen iframe.

Extraction strategy:
  1. Fetch the freeonlinek.top URL.
  2. Extract the iframe src (the real player URL on moviestv.my or
     another host).
  3. Hand it off to the generic extractor or the appropriate IE.
"""

import re

from .common import InfoExtractor
from ..utils import ExtractorError, url_or_none


class FreeOnlineKIE(InfoExtractor):
    IE_NAME = 'freeonlinek'
    IE_DESC = 'freeonlinek.top'

    _VALID_URL = r'https?://(?:www\.)?freeonlinek\.top(?P<id>/[^?#]*)?'

    _TESTS = [{
        'url': 'https://freeonlinek.top/',
        'info_dict': {
            'id': '/',
        },
        'skip': 'Site content depends on what moviestv.my is currently serving',
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url) or '/'
        webpage = self._download_webpage(url, page_id)

        iframe_src = self._search_regex(
            r'<iframe[^>]+id=["\']main-iframe["\'][^>]+src=["\']([^"\']+)["\']'
            r'|<iframe[^>]+src=["\']([^"\']+)["\'][^>]+id=["\']main-iframe["\']',
            webpage, 'iframe src', default=None,
        )

        if not iframe_src:
            iframe_src = self._search_regex(
                r'<iframe[^>]+src=["\'](?P<src>https?://[^"\'<>\s]+)["\']',
                webpage, 'iframe src', default=None,
            )

        if not iframe_src:
            raise ExtractorError(
                'Could not find the embedded player iframe on freeonlinek.top. '
                'The site content may have changed.',
                expected=True,
            )

        iframe_src = url_or_none(iframe_src)
        if not iframe_src:
            raise ExtractorError('Invalid iframe URL extracted.', expected=True)

        self.to_screen(f'[freeonlinek] Redirecting to embedded player: {iframe_src}')
        return self.url_result(iframe_src, video_id=page_id)
