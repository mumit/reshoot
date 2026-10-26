"""Bounded, read-only representative stills using the production caption/window/export renderers."""
import hashlib
import io
import json
import math
import re
import subprocess
import tempfile
import threading
import tomllib
from collections import OrderedDict
from pathlib import Path


def _json(root, name, named):
    if name not in named:
        raise ValueError('This recording has no editable clean take. Record a new preview first.')
    raw = (root / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != named[name]:
        raise ValueError('The recorded frame source changed. Reload before previewing.')
    return json.loads(raw)


def prepare(config, take, run, body):
    from reshoot import captions, framing, story, styles, timeline
    root, report = run
    named = {row['path']: row['sha256'] for row in report.get('files', [])}
    source = Path(take['out'])
    clean = str(source.with_suffix('.clean.mp4'))
    if clean not in named:
        raise ValueError('This recording has no editable clean take. Record a new preview first.')
    meta = _json(root, str(source.with_suffix('.take.json')), named)
    info = _json(root, str(source.with_suffix('.captions.json')), named)
    if meta.get('status') != 'completed' or meta.get('mode') == 'partial':
        raise ValueError('Make a complete preview before previewing its layout.')
    board_path = Path(config).parent / take['web']
    board = story.load(board_path)
    beat = next((row for row in board['beat'] if row['id'] == body.get('beat')), None)
    captured = next((row for row in meta.get('beats', []) if row['id'] == body.get('beat')), None)
    if beat is None or captured is None:
        raise ValueError('That step has no recorded frame. Update the preview first.')
    start, end = captured.get('start'), captured.get('end')
    if (any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (start, end))
            or not 0 <= start < end):
        raise ValueError('This step has no playable recorded interval.')
    draft = body.get('draft', {})
    if not isinstance(draft, dict) or set(draft) - {'caption', 'sub', 'look', 'frame', 'framing'}:
        raise ValueError('Choose caption, look or framing changes for the still.')
    text = {}
    for key in ('caption', 'sub'):
        value = draft.get(key, beat.get(key) or '')
        if not isinstance(value, str) or len(value) > 4000:
            raise ValueError('A preview caption takes up to 4000 characters.')
        text[key] = ' '.join(value.split())
    look = captions.style(board, board_path)
    change = draft.get('look', {})
    if not isinstance(change, dict) or set(change) - {'position', 'background', 'foreground'}:
        raise ValueError('Choose the caption position and colours.')
    for key in ('background', 'foreground'):
        if key in change and change[key] != look.get(key) and not re.fullmatch(r'#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})', str(change[key])):
            raise ValueError('Choose a caption colour such as #1d4ed8 or #1d4ed8e6.')
    look.update(change)
    if look.get('position', 'bottom') not in ('top', 'bottom'):
        raise ValueError('Caption position must be top or bottom.')
    for key in ('foreground', 'background'):
        if key in look:
            styles.colour(look[key])
    shoot = tomllib.loads(Path(config).read_text())
    edit = shoot.get('edit', {}).get('file')
    if shoot.get('edit', {}).get('script') or edit and Path(edit).suffix != '.toml':
        raise ValueError('Still layout previews need a TOML cut. Inspect the recorded export for a custom edit.')
    cut = tomllib.loads((Path(config).parent / edit).read_text()) if edit else {}
    enabled = 'frame' in cut
    window = {**styles.FRAME, **(timeline.frame_style(cut) if enabled else {})}
    change = draft.get('frame', {})
    if not isinstance(change, dict) or set(change) - {'enabled', 'background'}:
        raise ValueError('Choose whether to frame the page and its background.')
    enabled = change.get('enabled', enabled)
    window.update({key: value for key, value in change.items() if key != 'enabled'})
    validated = styles.validate({'schema_version': 1, 'name': 'Still', 'frame_enabled': enabled, 'frame': window})
    index = body.get('export', -1)
    if type(index) is not int or index < -1 or index >= len(cut.get('export', [])):
        raise ValueError('Choose an export from this project.')
    profile = None
    change = draft.get('framing', {})
    if not isinstance(change, dict) or set(change) - {'fit', 'focus', 'display_width'}:
        raise ValueError('Choose fit, focus or viewing width for the export.')
    if index >= 0:
        profile = framing.resolve({**cut['export'][index], **change})[0]
        if profile['width'] * profile['height'] > 16_000_000:
            raise ValueError('This export is too large for fast still feedback. Update and inspect its video.')
        profile = {key: profile[key] for key in ('width', 'height', 'fit', 'focus')}
    elif change:
        raise ValueError('Choose an export before changing its crop.')
    css_width = info.get('css_width')
    if isinstance(css_width, bool) or not isinstance(css_width, (int, float)) or not 0 < css_width <= 16384:
        raise ValueError('The recording has no usable caption sizing. Record a fresh preview.')
    from reshoot.journey import file_hash
    return {'source': str(root / clean), 'source_hash': named[clean], 'binding': body['binding'],
            'font_hash': file_hash(Path(look['font'])) if look.get('font') else None,
            'at': max(start, end - min(.1, (end - start) / 2)), 'text': text, 'look': look,
            'window': validated['frame'] if validated['frame_enabled'] else None,
            'profile': profile, 'css_width': css_width}


def _ff(args):
    try:
        return subprocess.run(['ffmpeg', '-v', 'error', '-y', *map(str, args)],
                              capture_output=True, check=True, timeout=10).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise ValueError('The still could not be rendered. Your recording and saved edits are kept.') from None


class Renderer:
    def __init__(self):
        self.lock, self.slot = threading.RLock(), threading.BoundedSemaphore(1)
        self.frames, self.images = OrderedDict(), OrderedDict()

    def cached(self, cache, key):
        with self.lock:
            result = cache.get(key)
            if result is not None:
                cache.move_to_end(key)
            return result

    def keep(self, cache, key, value, budget):
        with self.lock:
            cache[key] = value
            size = lambda item: len(item) if isinstance(item, bytes) else item.width * item.height * 3
            while cache and (len(cache) > 24 or sum(size(item) for item in cache.values()) > budget):
                cache.popitem(last=False)

    def render(self, request):
        from PIL import Image
        from reshoot import cut, framing, zoom
        key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        cached = self.cached(self.images, key)
        if cached is not None:
            return cached
        if not self.slot.acquire(blocking=False):
            raise ValueError('Still preview busy. Try the latest change again in a moment.')
        try:
            raw_key = (request['binding'], request['source_hash'], request['at'])
            frame = self.cached(self.frames, raw_key)
            if frame is None:
                png = _ff(['-ss', request['at'], '-i', request['source'], '-frames:v', 1, '-f', 'image2pipe', '-c:v', 'png', '-'])
                with Image.open(io.BytesIO(png)) as image:
                    if image.width * image.height > 16_000_000:
                        raise ValueError('This take is too large for fast still feedback. Inspect the video instead.')
                    frame = image.convert('RGB')
                self.keep(self.frames, raw_key, frame, 32 * 1024 * 1024)
            frame = frame.copy()
            if request['text']['caption']:
                cap = zoom.caption_image(zoom.plain(request['text']['caption']), zoom.plain(request['text']['sub']),
                                         frame.width, request['css_width'], request['look'])
                zoom.paste(frame, [(0, math.inf, cap)], 1, request['look'], request['css_width'])
            with tempfile.TemporaryDirectory(prefix='reshoot-still-') as folder:
                folder = Path(folder)
                source = folder / 'page.png'
                frame.save(source)
                if request['window']:
                    canvas, mask, geometry = cut.frame_layers(*frame.size, **request['window'])
                    canvas.save(folder / 'back.png'); mask.save(folder / 'mask.png')
                    rendered = folder / 'window.png'
                    _ff(['-i', folder / 'back.png', '-i', source, '-i', folder / 'mask.png',
                         '-filter_complex', cut.frame_filter(*geometry), '-frames:v', 1, rendered])
                    source = rendered
                if request['profile']:
                    profile = request['profile']
                    plan = framing.geometry(frame.size, profile['width'], profile['height'], profile['fit'], profile['focus'])
                    rendered = folder / 'export.png'
                    _ff(['-i', source, '-vf', framing.filter_for(plan), '-frames:v', 1, rendered])
                    source = rendered
                result = source.read_bytes()
            self.keep(self.images, key, result, 16 * 1024 * 1024)
            return result
        finally:
            self.slot.release()
