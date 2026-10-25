"""Measured export feedback with explicit coverage limits; not a readability or accessibility verdict."""
import json
import math
from pathlib import Path
from reshoot import framing, timeline


def visible(box, width, height):
    x, y, w, h = box
    return max(0, min(width, x + w) - max(0, x)) * max(0, min(height, y + h) - max(0, y)) / max(1, w * h)


def inspect(video, profile, plan):
    from reshoot import cut
    data = timeline.read(video)
    width, height = plan['width'], plan['height']
    display = profile.get('display_width', max(160, min(width, 640)))
    factor = display / width
    app, caps, cards, issues, notes, cache = [], [], [], [], [], {}
    sampled, legacy, truncated = 0, False, False
    def issue(kind, message, at=None, beat=None):
        nonlocal truncated
        key = (kind, beat, round(at or 0, 1))
        if len(issues) >= 30:
            truncated = True
        if len(issues) < 30 and not any(item['_key'] == key for item in issues):
            issues.append({'kind': kind, 'message': message, 'at': round(at, 3) if at is not None else None,
                           'beat': beat, '_key': key})
    def note(message):
        if message not in notes:
            notes.append(message)
    for segment in data['segments']:
        source = Path(segment['source'])
        if source not in cache:
            def load(suffix):
                path = source.with_suffix(suffix)
                return json.loads(path.read_text()) if path.exists() else {}
            cache[source] = (load('.take.json'), load('.captions.json'), cut.probe(source)[:2])
        meta, captions, (sw, sh) = cache[source]
        legacy = legacy or (not meta.get('capture', {}).get('zoom') and not any('layout' in b for b in meta.get('beats', [])))
        if segment.get('spatial_unknown'):
            note('Custom placement was not measured; inspect its text and crop visually.')
            continue
        spatial = segment.get('spatial', {'sx': 1, 'sy': 1, 'x': 0, 'y': 0})
        start, end = segment['source_start'], segment['source_end']
        time_scale = (segment['end'] - segment['start']) / (end - start)
        def at(source_time):
            return segment['start'] + (source_time - start) * time_scale
        for caption in captions.get('captions', []):
            a, b = max(start, caption['start']), min(end, caption['end'] if caption['end'] is not None else end)
            if b <= a or not caption.get('text'):
                continue
            layout = caption.get('layout')
            if layout:
                caps.append(layout.get('smallest_font_px', layout['font_px']) * spatial['sy'] * factor)
                if visible(framing.rect(layout['box'], spatial), width, height) < .98:
                    issue('caption-crop', 'A caption box crosses the crop. Move the crop or use Fit.', at((a + b) / 2), caption['beat'])
        if meta.get('capture', {}).get('zoom'):
            note('App text and checked-result bounds were not measured through camera zoom. Inspect zoomed frames.')
            continue
        for beat in meta.get('beats', []):
            layout = beat.get('layout', {})
            if not layout or layout.get('unavailable') or 'viewport' not in layout:
                continue
            sample_at = beat['end'] - min(.05, (beat['end'] - beat['start']) / 4)
            if not start <= sample_at < end:
                continue
            vw, vh = layout['viewport']
            if layout.get('skipped_transforms'):
                note('Scaled or rotated app text was skipped; inspect it visually.')
            convert = {'sx': sw / vw, 'sy': sh / vh, 'x': 0, 'y': 0}
            sampled += 1
            for text in layout.get('text', []):
                box = framing.rect(framing.rect(text['box'], convert), spatial)
                if visible(box, width, height) > .2:
                    app.append(text['font_px'] * convert['sy'] * spatial['sy'] * factor)
            for box in layout.get('checked', []):
                if visible(box, vw, vh) < .98:
                    issue('result-source-clip', 'Result-check bounds extend outside the recorded page. Inspect the checked content when recording.', at(sample_at), beat['id'])
                    continue
                box = framing.rect(framing.rect(box, convert), spatial)
                if visible(box, width, height) < .98:
                    issue('result-crop', 'Result-check bounds extend outside the crop. Inspect the checked content or use Fit.', at(sample_at), beat['id'])
    for part in data.get('parts', []):
        for sample in part.get('text_layout', []):
            cards.append(sample['font_px'] * factor)
            if visible(sample['box'], width, height) < .98:
                issue('card-crop', 'Title-card text extends outside the crop. Move the crop or use Fit.', (part['start'] + part['end']) / 2)
    rates = []
    for a, b, text in timeline.cues(video):
        rate = len(' '.join(text.split())) / max(.01, b - a)
        rates.append(rate)
        if rate > 18:
            issue('reading-time', f'A subtitle has about {rate:.0f} characters per second. Consider a longer hold or fewer words.', (a + b) / 2)
    small_app = sorted(app)[max(0, math.floor((len(app) - 1) * .1))] if app else None
    if small_app is not None and small_app < 12:
        issue('small-app-text', f'Small app-text samples are about {small_app:.1f} px at this viewing width. Inspect them; a narrower recording can enlarge the app.')
    if caps and min(caps) < 14:
        issue('small-caption', f'Caption text is as small as {min(caps):.1f} px, including second lines. Inspect it at viewing size.')
    if cards and min(cards) < 14:
        issue('small-card', f'Title-card text is as small as {min(cards):.1f} px at viewing size.')
    if display > width:
        issue('display-upscale', 'The viewing width exceeds the encoded width. Enlarging the player cannot restore detail.')
    if not app:
        note('App text was not measured in the included result holds. Inspect it visually.')
        if legacy:
            note('Older recordings need a fresh preview for main-page font samples.')
    if not caps:
        note('No measured caption boxes were included; legacy or externally drawn captions need visual inspection.')
    note('Font sizes are estimates at the chosen viewing width. Samples cover main-page result holds, not every frame, iframe or canvas.')
    note('Text checks use matched words where possible; other result-check bounds can include extra content.')
    note('Small-text and reading-time thresholds are editing hints, not a readability or accessibility pass.')
    if truncated:
        note('Only the first 30 editing hints are listed; inspect the whole export.')
    for item in issues:
        item.pop('_key')
    return {'schema_version': 1, 'width': width, 'height': height, 'display_width': display,
            'fit': plan['fit'], 'focus': plan['focus'], 'sampled_holds': sampled,
            'thresholds': {'small_app_font_px': 12, 'small_caption_font_px': 14, 'characters_per_second': 18},
            'metrics': {'app_font_p10_px': round(small_app, 1) if small_app is not None else None,
                        'caption_min_px': round(min(caps), 1) if caps else None,
                        'card_min_px': round(min(cards), 1) if cards else None,
                        'max_characters_per_second': round(max(rates), 1) if rates else None},
            'issues': issues, 'notes': notes}


def write(video, profile, plan):
    data = inspect(video, profile, plan)
    Path(video).with_suffix('.readability.json').write_text(json.dumps(data, indent=2))
    return data
