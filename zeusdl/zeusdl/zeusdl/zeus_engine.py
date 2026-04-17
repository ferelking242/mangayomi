"""
ZeusDL Extraction Engine
Provides clean JSON extraction, structured error output, JSON progress,
quality selection, fast mode, and silent embed support.
"""

import json
import sys
import uuid


def _flush(text):
    sys.stdout.write(text + '\n')
    sys.stdout.flush()


def _output_error(message, code='EXTRACTION_ERROR', task_id=None):
    obj = {
        'error': True,
        'message': message,
        'code': code,
    }
    if task_id:
        obj['id'] = task_id
    _flush(json.dumps(obj))


def _normalize_height_to_quality(height):
    if height is None:
        return 'unknown'
    return f'{height}p'


def _normalize_format(fmt):
    height = fmt.get('height')
    width = fmt.get('width')
    quality = fmt.get('format_note') or fmt.get('quality_label') or _normalize_height_to_quality(height)
    if not quality or quality == 'unknown':
        if height:
            quality = f'{height}p'
        elif width:
            quality = f'{width}w'
        else:
            quality = 'unknown'
    url = fmt.get('url') or fmt.get('manifest_url', '')
    ext = fmt.get('ext', '')
    return {
        'quality': quality,
        'url': url,
        'ext': ext,
        'width': width,
        'height': height,
        'fps': fmt.get('fps'),
        'vcodec': fmt.get('vcodec'),
        'acodec': fmt.get('acodec'),
        'filesize': fmt.get('filesize') or fmt.get('filesize_approx'),
        'tbr': fmt.get('tbr'),
        'format_id': fmt.get('format_id'),
    }


def _normalize_audio(fmt):
    return {
        'bitrate': fmt.get('abr') or fmt.get('tbr'),
        'url': fmt.get('url') or fmt.get('manifest_url', ''),
        'ext': fmt.get('ext', ''),
        'acodec': fmt.get('acodec'),
        'asr': fmt.get('asr'),
        'filesize': fmt.get('filesize') or fmt.get('filesize_approx'),
        'format_id': fmt.get('format_id'),
    }


def _build_structured_info(info, fast=False, task_id=None, quality_filter=None):
    formats = info.get('formats') or []
    if not formats and info.get('url'):
        formats = [info]

    video_streams = []
    audio_streams = []

    for fmt in formats:
        vcodec = fmt.get('vcodec', 'none')
        acodec = fmt.get('acodec', 'none')
        has_video = vcodec and vcodec != 'none'
        has_audio = acodec and acodec != 'none'

        if has_video:
            video_streams.append(_normalize_format(fmt))
        elif has_audio and not has_video:
            audio_streams.append(_normalize_audio(fmt))

    if quality_filter:
        wanted = quality_filter.lower().rstrip('p')
        try:
            wanted_height = int(wanted)
        except ValueError:
            wanted_height = None

        matched = []
        for s in video_streams:
            h = s.get('height')
            q = s.get('quality', '').lower().rstrip('p')
            if wanted_height and h == wanted_height:
                matched.append(s)
            elif q == wanted_height or q == quality_filter.lower():
                matched.append(s)
        if matched:
            video_streams = matched
        else:
            video_streams = video_streams[:1] if video_streams else []

    subtitles_raw = info.get('subtitles') or {}
    auto_subs_raw = info.get('automatic_captions') or {}
    all_subs = {**subtitles_raw, **auto_subs_raw}
    subtitles = []
    for lang, sub_list in all_subs.items():
        for sub in (sub_list or []):
            url = sub.get('url', '')
            if url:
                subtitles.append({
                    'lang': lang,
                    'ext': sub.get('ext', ''),
                    'url': url,
                    'name': sub.get('name', lang),
                })
                break

    result = {
        'id': task_id or info.get('id', ''),
        'video_id': info.get('id', ''),
        'title': info.get('title', ''),
    }

    if not fast:
        result.update({
            'duration': info.get('duration'),
            'thumbnail': info.get('thumbnail'),
            'description': info.get('description'),
            'uploader': info.get('uploader'),
            'uploader_url': info.get('uploader_url'),
            'upload_date': info.get('upload_date'),
            'view_count': info.get('view_count'),
            'like_count': info.get('like_count'),
            'webpage_url': info.get('webpage_url'),
            'extractor': info.get('extractor'),
            'age_limit': info.get('age_limit'),
        })

    result['streams'] = video_streams
    result['audio'] = audio_streams
    result['subtitles'] = subtitles

    return result


def extract_json(ydl, urls, fast=False, task_id=None, quality_filter=None):
    if not task_id:
        task_id = str(uuid.uuid4())[:8]

    for url in urls:
        try:
            info = ydl.extract_info(url, download=False)
            if info is None:
                _output_error('No information extracted', 'NO_INFO', task_id)
                continue

            if '_type' in info and info['_type'] == 'playlist':
                entries = info.get('entries') or []
                results = []
                for entry in entries:
                    if entry:
                        try:
                            structured = _build_structured_info(
                                entry, fast=fast, task_id=task_id, quality_filter=quality_filter)
                            results.append(structured)
                        except Exception as e:
                            results.append({'error': True, 'message': str(e), 'code': 'ENTRY_ERROR'})
                output = {
                    'id': task_id,
                    'type': 'playlist',
                    'title': info.get('title', ''),
                    'entries': results,
                }
                _flush(json.dumps(output))
            else:
                structured = _build_structured_info(
                    info, fast=fast, task_id=task_id, quality_filter=quality_filter)
                _flush(json.dumps(structured))

        except Exception as e:
            _output_error(str(e), 'EXTRACTION_ERROR', task_id)


def make_json_progress_hook(task_id=None):
    def hook(d):
        status = d.get('status', '')
        if status == 'downloading':
            out = {
                'status': 'downloading',
                'progress': None,
                'speed': d.get('speed'),
                'eta': d.get('eta'),
                'downloaded_bytes': d.get('downloaded_bytes'),
                'total_bytes': d.get('total_bytes') or d.get('total_bytes_estimate'),
            }
            total = out['total_bytes']
            downloaded = out['downloaded_bytes']
            if total and downloaded is not None:
                out['progress'] = round((downloaded / total) * 100, 1)
            if task_id:
                out['id'] = task_id
            _flush(json.dumps(out))
        elif status == 'finished':
            out = {
                'status': 'finished',
                'progress': 100.0,
                'downloaded_bytes': d.get('downloaded_bytes'),
                'total_bytes': d.get('total_bytes') or d.get('downloaded_bytes'),
                'elapsed': d.get('elapsed'),
            }
            if task_id:
                out['id'] = task_id
            _flush(json.dumps(out))
        elif status == 'error':
            out = {
                'status': 'error',
                'error': True,
                'message': 'Download failed',
                'code': 'DOWNLOAD_ERROR',
            }
            if task_id:
                out['id'] = task_id
            _flush(json.dumps(out))
    return hook


def select_format_by_quality(quality):
    height_str = quality.lower().rstrip('p')
    try:
        height = int(height_str)
        return f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/bestvideo+bestaudio/best'
    except ValueError:
        return 'bestvideo+bestaudio/best'
