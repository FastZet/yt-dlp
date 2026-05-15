import re

from .common import InfoExtractor
from .generic import GenericIE
from ..utils import (
    int_or_none,
    js_to_json,
    parse_duration,
    parse_resolution,
    urljoin,
)


class FpoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fpo\.xxx/video/(?P<id>\d+)/(?P<display_id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.fpo.xxx/video/967869/mxxwanna-babe-mia-fuck-rob-fuck/',
        'md5': 'c108a66ad80adbe475ac6b63653daf9e',
        'info_dict': {
            'id': '967869',
            'display_id': 'mxxwanna-babe-mia-fuck-rob-fuck',
            'title': 'Wanna Chill? – Mia Melano',
            'ext': 'mp4',
            'uploader': 'RageBull',
            'duration': 2015,
            'view_count': int,
            'age_limit': 18,
            'thumbnail': 'https://www.fpo.xxx/contents/videos_screenshots/967000/967869/preview.jpg',
        },
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, video_id)

        flashvars = self._search_json(
            r'(?s:<script\b[^>]*>.*?var\s+flashvars\s*=)',
            webpage, 'flashvars', video_id, transform_source=js_to_json)

        title = self._html_search_regex(
            r'<(?:h1|title)>(?:Video: )?(.+?)</(?:h1|title)>', webpage, 'title')

        url_keys = list(filter(re.compile(r'^video_(?:url|alt_url\d*)$').match, flashvars.keys()))
        formats = []
        for key in url_keys:
            if '/get_file/' not in flashvars[key]:
                continue
            format_id = flashvars.get(f'{key}_text', key)
            formats.append({
                'url': urljoin(url, GenericIE._kvs_get_real_url(flashvars[key], flashvars.get('license_code'))),
                'format_id': format_id,
                'ext': 'mp4',
                **(parse_resolution(format_id) or parse_resolution(flashvars[key])),
                'http_headers': {'Referer': 'https://www.fpo.xxx/'},
            })
            if not formats[-1].get('height'):
                if format_id and format_id.lower() in ('lq', 'sd', 'low'):
                    formats[-1]['quality'] = -1
                else:
                    formats[-1]['quality'] = 1

        uploader = self._html_search_meta('ya:ovs:login', webpage, 'uploader', default=None)
        duration = parse_duration(self._html_search_regex(
            [r'<meta[^>]+property="video:duration"[^>]+content="([^"]+)"',
             r'<meta\s+itemprop="duration"\s+content="([^"]+)"'],
            webpage, 'duration', default=None))
        view_count = int_or_none(self._html_search_meta('ya:ovs:views_total', webpage, 'view count', default=None))

        return {
            'id': flashvars.get('video_id') or video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': urljoin(url, flashvars.get('preview_url')) if flashvars.get('preview_url') else None,
            'formats': formats,
            'uploader': uploader,
            'duration': duration,
            'view_count': view_count,
            'age_limit': 18,
        }
