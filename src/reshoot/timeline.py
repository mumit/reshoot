"""Edit maps connect source times to exports, subtitles, and review links."""
import json
import math
from pathlib import Path


def read(video):
    p = Path(video).with_suffix('.timeline.json')
    if p.exists():
        return json.loads(p.read_text())
    from reshoot.cut import duration
    d = duration(video)
    return {'schema_version': 1, 'duration': d, 'segments': [{'source': str(Path(video).resolve()), 'source_start': 0, 'source_end': d, 'start': 0, 'end': d}]}


def write(video, segments, duration):
    Path(video).with_suffix('.timeline.json').write_text(json.dumps({'schema_version': 1, 'duration': duration, 'segments': segments}, indent=2))


def trim(source, start, end, out, factor=1):
    if start < 0 or end <= start or factor <= 0:
        raise ValueError('invalid edit range or speed')
    rows = []
    for row in read(source)['segments']:
        a, b = max(start, row['start']), min(end, row['end'])
        if b <= a:
            continue
        scale = (row['source_end']-row['source_start']) / (row['end']-row['start'])
        rows.append({'source': row['source'], 'source_start': row['source_start'] + (a-row['start'])*scale,
                     'source_end': row['source_start'] + (b-row['start'])*scale,
                     'start': (a-start)/factor, 'end': (b-start)/factor})
    write(out, rows, (end-start)/factor)


def copy(source, out):
    mapping = read(source)
    write(out, mapping['segments'], mapping['duration'])


def concat(sources, out):
    rows, offset = [], 0
    for source in sources:
        mapping = read(source)
        rows += [{**row, 'start': row['start']+offset, 'end': row['end']+offset} for row in mapping['segments']]
        offset += mapping['duration']
    write(out, rows, offset)


def cues(video):
    from reshoot import cut
    out = []
    for row in read(video)['segments']:
        source = row['source']
        scale = (row['end']-row['start'])/(row['source_end']-row['source_start'])
        for start, end, text in cut.cues(source, 0, cut.duration(source)):
            a, b = max(start, row['source_start']), min(end, row['source_end'])
            if a < b:
                out.append((row['start']+(a-row['source_start'])*scale, row['start']+(b-row['source_start'])*scale, text))
    return sorted(out)



def waiting_ranges(source, start, end, keep=.8):
    """Only shorten explicitly marked, verified holds, preserving reading and speech."""
    from reshoot import cut
    path = Path(source).with_suffix('.take.json')
    if not path.exists():
        return []
    rows = json.loads(path.read_text()).get('beats', [])
    speech = cut.lines(source, 0, cut.duration(source))
    ranges = []
    for beat in rows:
        if not beat.get('trim_wait') or beat.get('status') != 'passed' or 'verified_at' not in beat:
            continue
        a, b = beat['verified_at'], beat['end']
        retain = max(keep, beat.get('min_reading', 0))
        if a < start or b > end or b-a <= retain+.05:
            continue
        if any(at < b and at+seconds > a for at, seconds, _, _ in speech):
            continue
        ranges.append((a+retain, b))
    return sorted(ranges)


def label_clip(source, output, text, temp):
    from reshoot import cut
    from PIL import Image, ImageDraw
    width, height, _ = cut.probe(source)
    margin = max(4, round(min(width, height)*.05))
    font = cut.font(max(12, min(28, height//12)))
    image = Image.new('RGBA', (width, height))
    draw = ImageDraw.Draw(image)
    lines = cut.wrap_text(text, font, width-4*margin, draw)
    line_height = font.size*1.3
    bottom = 2*margin+len(lines)*line_height
    if bottom > height-margin:
        raise ValueError('edit label does not fit the frame')
    draw.rounded_rectangle((margin, margin, width-margin, bottom), radius=margin, fill=(0,0,0,190))
    for n, line in enumerate(lines):
        draw.text((2*margin, margin+n*line_height), line, font=font, fill='white')
    file = Path(temp) / (Path(output).stem + '.png')
    image.save(file)
    cut.ff('-i', source, '-loop', 1, '-i', file, '-filter_complex', '[0:v][1:v]overlay=0:0:shortest=1', *cut.ENC, output)
    copy(source, output)
    return output


def edit(a):
    import tempfile
    import tomllib
    from reshoot import cut
    board = tomllib.loads(Path(a.script).read_text())
    if board.get('schema_version') != 1 or not board.get('part'):
        raise ValueError('edit file needs schema_version=1 and parts')
    sources = [Path(arg).resolve() for arg in a.args]
    if not sources:
        raise ValueError('pass the take paths after the edit file')
    output = Path(board.get('output', 'demo-final.mp4'))
    if output.is_absolute() or '..' in output.parts:
        raise ValueError('edit output must stay beside the first take')
    output = sources[0].parent / output
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        clips = []
        for i, part in enumerate(board['part']):
            if 'card' in part:
                width, height, _ = cut.probe(sources[0])
                seconds = part.get('duration', 2)
                if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
                    raise ValueError('card duration must be positive')
                style = board.get('style', {})
                font_path = (Path(a.script).resolve().parent / style['font']) if style.get('font') else None
                card = cut.Card(width, height, style.get('background', '#0e0d0c'), font_path=font_path)
                card.text(None, int(height*.4), part['card'], min(64, max(18, height//10)), fill=style.get('foreground', 'white'))
                if style.get('logo'):
                    from PIL import Image
                    logo = Image.open(Path(a.script).resolve().parent / style['logo']).convert('RGBA')
                    logo.thumbnail((width//5, height//5))
                    card.im.paste(logo, ((width-logo.width)//2, int(height*.1)), logo)
                clip = Path(temp) / f'{i}.mp4'
                cut.still(card.save(Path(temp) / f'{i}.png'), seconds, clip)
                clips.append(clip)
                continue
            index = part.get('take', 0)
            if not isinstance(index, int) or index < 0 or index >= len(sources):
                raise ValueError('edit names an unknown take')
            source = sources[index]
            def at(value):
                return float(value) if isinstance(value, (int, float)) else cut.beats(source)[value]
            start, end = at(part.get('start', 0)), at(part.get('end', cut.duration(source)))
            speed = part.get('speed', 1)
            if not all(math.isfinite(x) for x in (start, end, speed)) or start < 0 or end <= start or end > cut.duration(source)+.1 or speed <= 0:
                raise ValueError('invalid edit range or speed')
            spoken = cut.lines(source, 0, cut.duration(source))
            overlap = [line for line in spoken if line[0] < end and line[0]+line[1] > start]
            if any(at < start < at+seconds or at < end < at+seconds for at, seconds, _, _ in overlap):
                raise ValueError('edit would cut a narration line')
            if speed != 1 and (not part.get('label') or overlap):
                raise ValueError('speed changes need a label and cannot shorten narration')
            clip = Path(temp) / f'{i}.mp4'
            waits = waiting_ranges(source, start, end) if board.get('trim_waits') else []
            if waits and speed != 1:
                raise ValueError('split wait trimming and speed changes into separate parts')
            if waits:
                retained, cursor = [], start
                for n, (a, b) in enumerate(waits):
                    if a > cursor:
                        retained.append(cut.trim(source, cursor, a, Path(temp) / f'{i}-wait-{n}.mp4'))
                    cursor = b
                if cursor < end:
                    retained.append(cut.trim(source, cursor, end, Path(temp) / f'{i}-tail.mp4'))
                cut.concat(retained, clip)
                marked = Path(temp) / f'{i}-wait-labeled.mp4'
                label_clip(clip, marked, 'Wait shortened', temp)
                clip = marked
            elif speed == 1:
                cut.trim(source, start, end, clip)
            else:
                cut.speed(source, start, end, speed, clip)
                labeled = clip.with_name(f'{i}-labeled.mp4')
                label_clip(clip, labeled, part['label'], temp)
                clip = labeled
            clips.append(clip)
        silent = cut.concat(clips, Path(temp) / 'final.mp4')
        lines = []
        for row in read(silent)['segments']:
            lines += cut.lines(row['source'], row['source_start'], row['source_end'], row['start'])
        music = str((Path(a.script).resolve().parent / board['music']).resolve()) if board.get('music') else None
        if lines:
            voice = cut.voice_track(lines, Path(temp) / 'voice.wav', cut.duration(silent))
            cut.add_audio(silent, output, voice=voice, music=music)
        elif music:
            cut.add_audio(silent, output, music=music)
        else:
            import shutil
            shutil.copyfile(silent, output)
            copy(silent, output)
    cut.write_srt(cues(output), output.with_suffix('.srt'))
    for profile in board.get('export', []):
        export(output, profile)
    print(output)


def export(video, profile):
    from reshoot import cut
    width, height = profile.get('width', 1280), profile.get('height', 720)
    name = profile.get('name', 'landscape')
    import re
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', name) or not all(isinstance(x, int) and x > 0 and x % 2 == 0 for x in (width, height)):
        raise ValueError('profile needs a safe name and positive even dimensions')
    kind = profile.get('format', 'mp4')
    if kind not in ('mp4', 'gif'):
        raise ValueError('profile format must be mp4 or gif')
    fps = profile.get('fps', 15 if kind == 'gif' else 60)
    if not isinstance(fps, int) or not 1 <= fps <= 120:
        raise ValueError('profile fps must be between 1 and 120')
    budget = profile.get('max_bytes')
    if budget is not None and (not isinstance(budget, int) or budget <= 0):
        raise ValueError('max_bytes must be a positive integer')
    minimum = profile.get('min_reading', 0)
    if not isinstance(minimum, (int,float)) or not math.isfinite(minimum) or minimum < 0:
        raise ValueError('profile min_reading must be nonnegative')
    if any(end-start+.001 < minimum for start, end, text in cues(video) if text):
        raise ValueError('an exported caption is shorter than min_reading')
    output = Path(video).with_name(Path(video).stem + '-' + name + '.' + kind)
    if kind == 'gif':
        cut.gif(video, 0, cut.duration(video), output, fps=fps, width=width, height=height, fit=profile.get('fit', 'contain'))
        copy(video, output)
    else:
        fit = profile.get('fit', 'contain')
        if fit not in ('contain', 'crop'):
            raise ValueError('profile fit must be contain or crop')
        vf = f'scale={width}:{height}:force_original_aspect_ratio=' + ('increase' if fit == 'crop' else 'decrease')
        vf += f',crop={width}:{height}' if fit == 'crop' else f',pad={width}:{height}:(ow-iw)/2:(oh-ih)/2'
        cut.ff('-i', video, '-vf', vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', fps, '-c:a', 'aac', '-movflags', '+faststart', output)
        copy(video, output)
    cut.write_srt(cues(output), output.with_suffix('.srt'))
    at = profile.get('poster_at', min(max(0, cut.duration(output)-.05), cut.duration(output)*.75))
    if not isinstance(at, (int, float)) or not math.isfinite(at) or not 0 <= at < cut.duration(output):
        raise ValueError('poster_at must be within the export')
    cut.ff('-ss', at, '-i', output, '-frames:v', 1, output.with_suffix('.poster.png'))
    if profile.get('max_bytes') is not None and output.stat().st_size > profile['max_bytes']:
        raise ValueError('export exceeds its configured max_bytes')
    return output
