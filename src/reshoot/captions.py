"""Captions drawn after recording. A TOML take is recorded without them: OUT.clean.mp4 is the page as it was, and
OUT.captions.json says when each beat's caption was on screen. draw() puts the storyboard's captions on the clean
take as OUT.mp4, once after recording and again on a re-cut, so a caption's words and look can change without
recording again. Its timing stays the recording's: a caption shows while its beat does."""
import json, math, shutil, subprocess
from pathlib import Path


def timing(events, beats):
    """[{beat, start, end}] from the page's caption events, one for each beat recorded, in order. Times are seconds
    from the start of the take; the last caption's end is None, for the end of the video."""
    times = [t for t, ev in events if ev.get('kind') == 'caption']
    if len(times) != len(beats):
        raise ValueError(f'{len(times)} caption events for {len(beats)} beats')
    return [{'beat': beat, 'start': a, 'end': b} for beat, a, b in zip(beats, times, times[1:] + [None])]


def style(board, storyboard):
    """The storyboard's [caption] look, with its font found beside the storyboard."""
    look = dict(board.get('caption', {}))
    if look.get('font'):
        look['font'] = str(Path(storyboard).resolve().parent / look['font'])
    return look


def draw(take, board, storyboard, quiet=False):
    """Writes take (OUT.mp4) from OUT.clean.mp4 with the captions and caption look of board, the storyboard as it
    is now. A beat the storyboard no longer has keeps the caption it was recorded with. Returns the beats whose
    caption differs from the recording's, and "the [caption] look" when that changed since it was last drawn."""
    from PIL import Image
    from reshoot import cut, zoom
    from reshoot.artifacts import digest
    take = Path(take)
    clean, sidecar = take.with_suffix('.clean.mp4'), take.with_suffix('.captions.json')
    info = json.loads(sidecar.read_text())
    beats = {b['id']: b for b in board['beat']}
    rows, changed = [], []
    for row in info['captions']:
        beat = beats.get(row['beat'])
        text, sub = (beat.get('caption') or None, beat.get('sub') or None) if beat else (row['recorded'], row['recorded_sub'])
        if (text, sub) != (row['recorded'], row['recorded_sub']):
            changed.append(row['beat'])
        rows.append({**row, 'text': text, 'sub': sub})
    look = style(board, storyboard)
    width, height, _ = cut.probe(clean)
    css_w = info['css_width']
    caps = [(row['start'], math.inf if row['end'] is None else row['end'],
             zoom.caption_image(zoom.plain(row['text']), zoom.plain(row['sub']), width, css_w, look))
            for row in rows if row['text']]
    by_start = {start: image for start, _, image in caps}
    for row in rows:
        if row['text']:
            cap = by_start[row['start']]
            size = max(1, round(min(max(18, css_w * .023), 30) * width / css_w))
            margin = round(height * look.get('margin', .065))
            row['layout'] = {'box': [(width - cap.width) // 2, margin if look.get('position') == 'top' else height - margin - cap.height,
                                      cap.width, cap.height], 'font_px': size,
                             'smallest_font_px': max(1, round(size * .6)) if row['sub'] else size}
        else:
            row.pop('layout', None)
    temp = take.with_name(take.stem + '.partial.mp4')
    if not caps:
        shutil.copyfile(clean, temp)
    else:
        if not quiet:
            print(f'drawing {len(caps)} captions', flush=True)
        size = width * height * 3
        src = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', str(clean), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                               stdout=subprocess.PIPE)
        out = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s',
                                f'{width}x{height}', '-r', str(zoom.FPS), '-i', '-', '-vf', 'format=yuv420p',
                                '-color_range', 'tv', '-c:v', 'libx264', *zoom.quality(), '-movflags', '+faststart',
                                str(temp)], stdin=subprocess.PIPE)
        try:
            k = 0
            while len(data := src.stdout.read(size)) == size:
                t = k / zoom.FPS
                if any(a <= t < b + 0.35 for a, b, _ in caps):
                    frame = Image.frombytes('RGB', (width, height), data)
                    zoom.paste(frame, caps, t, look, css_w)
                    data = frame.tobytes()
                out.stdin.write(data)
                k += 1
        finally:
            out.stdin.close()
            src.stdout.close()
            if out.wait() | src.wait():
                temp.unlink(missing_ok=True)
                raise RuntimeError("ffmpeg couldn't draw the captions")
    temp.replace(take)
    if 'style' in info and info['style'] != board.get('caption', {}):
        changed.append('the [caption] look')
    info.update(captions=rows, style=board.get('caption', {}))
    sidecar.write_text(json.dumps(info, indent=2))
    meta = take.with_suffix('.take.json')
    if meta.exists():  # the take is the video with its captions, so its hash is the drawn one
        data = json.loads(meta.read_text())
        data['sha256'] = digest(take)
        meta.write_text(json.dumps(data, indent=2))
    return changed


def cues(take, start=0, end=None, offset=0):
    """The captions drawn on a take, for subtitles, moved like cut.cues: [(from, to, text)], or None when the take
    has no OUT.captions.json, as a Python storyboard's takes don't."""
    import re
    p = Path(take).with_suffix('.captions.json')
    if not p.exists():
        return None
    end = math.inf if end is None else end
    out = []
    for row in json.loads(p.read_text())['captions']:
        text = re.sub(r'<[^>]+>', '', row.get('text') or '')
        if not text:
            continue
        a, b = max(row['start'], start), min(math.inf if row['end'] is None else row['end'], end)
        if a < b:
            sub = re.sub(r'<[^>]+>', '', row.get('sub') or '')
            out.append((a - start + offset, b - start + offset, text + (f' ({sub})' if sub else '')))
    return out
