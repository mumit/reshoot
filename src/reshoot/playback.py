"""Pinned export videos and beat appearances for read-only revision playback."""
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import quote


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _mapping(root, name, expected, beats, named):
    from reshoot import timeline
    path = root / name
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('The export timeline changed. Reload before comparing.')
    mapping = json.loads(raw)
    duration = mapping.get('duration')
    segments = mapping.get('segments')
    if not _number(duration) or duration <= 0 or not isinstance(segments, list):
        raise ValueError('The export has an invalid timeline.')
    rows = []
    for row in segments:
        if (not isinstance(row, dict) or not isinstance(row.get('source'), str)
                or not all(_number(row.get(key)) for key in ('start', 'end', 'source_start', 'source_end'))
                or not 0 <= row['start'] < row['end'] <= duration + .1
                or not 0 <= row['source_start'] < row['source_end']):
            raise ValueError('The export has invalid timeline segments.')
        source = Path(timeline._found(row['source'], path.parent))
        # Title cards can name temporary files. Only known in-run takes map to steps.
        if source.is_relative_to(root) and str(source.relative_to(root)) in named:
            rows.append({**row, 'source': str(source)})
    appearances = {}
    for key, beat in beats.items():
        start, end = beat.get('start'), beat.get('end')
        if not all(_number(value) for value in (start, end)) or not 0 <= start < end:
            continue
        found = timeline.occurrences(rows, beat['source'], start, end)
        if found:
            appearances[key] = found
    return duration, appearances


def exports(run, beats):
    from reshoot import review
    root, report = run
    named = {row['path']: row['sha256'] for row in report.get('files', [])}
    token = review.binding(root, report)
    videos = []
    for name in review.exports(root, report):
        if Path(name).suffix.lower() not in ('.mp4', '.mov'):
            continue
        timeline = str(Path(name).with_suffix('.timeline.json'))
        duration, appearances = None, {}
        note = 'This recording has no saved export timeline. Use the video controls to compare it.'
        if timeline in named:
            duration, appearances = _mapping(root, timeline, named[timeline], beats, named)
            note = '' if appearances else 'No recorded steps appear in this export. Use the video controls.'
        videos.append({'name': name, 'sha256': named[name], 'duration': duration, 'beats': appearances, 'note': note,
                       'src': f'comparison-media/{report["id"]}/{token}/{quote(name)}'})
    return videos


def media(project, run_id, binding, name):
    """Return only a verified exported video; send_file checks the bytes again when serving ranges."""
    from reshoot import comparison, review
    root, report = comparison.read(project, run_id, binding)
    if Path(name).suffix.lower() not in ('.mp4', '.mov') or name not in review.exports(root, report):
        raise ValueError('Choose an exported video from this recording.')
    expected = next(row['sha256'] for row in report['files'] if row['path'] == name)
    return root, expected
