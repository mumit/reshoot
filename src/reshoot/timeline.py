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


def write(video, segments, duration, parts=None):
    data = {'schema_version': 1, 'duration': duration, 'segments': segments}
    if parts is not None:
        data['parts'] = parts
    Path(video).with_suffix('.timeline.json').write_text(json.dumps(data, indent=2))


def trim(source, start, end, out, factor=1):
    if start < 0 or end <= start or factor <= 0:
        raise ValueError('invalid edit range or speed')
    rows = []
    for row in read(source)['segments']:
        a, b = max(start, row['start']), min(end, row['end'])
        if b <= a:
            continue
        scale = (row['source_end']-row['source_start']) / (row['end']-row['start'])
        rows.append({**row, 'source': row['source'], 'source_start': row['source_start'] + (a-row['start'])*scale,
                     'source_end': row['source_start'] + (b-row['start'])*scale,
                     'start': (a-start)/factor, 'end': (b-start)/factor})
    write(out, rows, (end-start)/factor)


def copy(source, out):
    mapping = read(source)
    write(out, mapping['segments'], mapping['duration'], mapping.get('parts'))


def beat_bounds(source):
    """Recorded beat intervals. Older takes with start markers end at the next marker or the take's end."""
    length = read(source)['duration']
    path = Path(source).with_suffix('.take.json')
    rows = json.loads(path.read_text()).get('beats', []) if path.exists() else []
    if not rows:
        from reshoot import cut
        markers = sorted(cut.beats(source).items(), key=lambda row: row[1])
        rows = [{'id': name, 'start': start, 'end': markers[i + 1][1] if i + 1 < len(markers) else length}
                for i, (name, start) in enumerate(markers)]
    result = {}
    for row in rows:
        name, start, end = row.get('id'), row.get('start'), row.get('end')
        if (not isinstance(name, str) or name in result or any(isinstance(v, bool) or not isinstance(v, (int, float))
            or not math.isfinite(v) for v in (start, end)) or not 0 <= start <= end <= length + .1):
            raise ValueError('The recording has invalid beat boundaries. Record a fresh preview.')
        result[name] = (min(start, length), min(end, length))
    return result


def part_range(part, source):
    """Resolve a cut, including its last beat with `through`, and protect complete narration lines."""
    from reshoot import cut
    length = read(source)['duration']
    def at(value):
        if isinstance(value, str):
            markers = cut.beats(source)
            if value not in markers:
                raise ValueError(f'No recorded beat {value!r}. Record a preview after changing the story.')
            return markers[value]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Cut boundaries must be beat names or seconds.')
        return value
    start = at(part.get('start', 0))
    if 'through' in part:
        if 'end' in part:
            raise ValueError('A part uses either end (exclusive) or through (inclusive), not both.')
        if not isinstance(part['through'], str) or part['through'] not in (bounds := beat_bounds(source)):
            raise ValueError('Choose an end beat from the recording, or record a fresh preview.')
        end = bounds[part['through']][1]
    else:
        end = at(part.get('end', length))
    speed = part.get('speed', 1)
    if (isinstance(speed, bool) or not isinstance(speed, (int, float)) or
        not all(math.isfinite(v) for v in (start, end, speed)) or start < 0 or end <= start or end > length + .1 or speed <= 0):
        raise ValueError('Choose a nonempty cut with its end after its start, within the recorded take.')
    spoken = cut.lines(source, 0, length)
    overlap = [line for line in spoken if line[0] < end and line[0] + line[1] > start]
    if any(at < start < at + seconds or at < end < at + seconds for at, seconds, _, _ in overlap):
        raise ValueError('The cut would split a narration line. Include the complete spoken beat.')
    if speed != 1 and (not part.get('label') or overlap):
        raise ValueError('speed changes need a label and cannot shorten narration')
    return start, min(end, length), speed


def occurrences(segments, source, start, end):
    """Every appearance of a source interval in an edited video, including trims and repeated beats."""
    found, previous_end = [], None
    for row in segments:
        if Path(row['source']).resolve() != Path(source).resolve():
            continue
        a, b = max(start, row['source_start']), min(end, row['source_end'])
        if b <= a:
            continue
        scale = (row['end'] - row['start']) / (row['source_end'] - row['source_start'])
        output = [row['start'] + (a - row['source_start']) * scale,
                  row['start'] + (b - row['source_start']) * scale]
        if found and abs(found[-1][1] - output[0]) < .001 and previous_end is not None and abs(previous_end - a) < .001:
            found[-1][1] = output[1]
        else:
            found.append(output)
        previous_end = b
    return found


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


def frame_style(board):
    """The [frame] table as cut.frame's settings, with its background taken from [style] when it has none."""
    style, frame = board.get('style', {}), board['frame']
    if not isinstance(frame, dict):
        raise ValueError('frame must be a table, such as [frame] with padding = 0.06')
    if unknown := set(frame) - {'background', 'padding', 'radius', 'shadow', 'bar', 'bar_color'}:
        raise ValueError('unknown frame option: ' + ', '.join(sorted(unknown)) + '; use background, padding, radius, '
                         'shadow, bar or bar_color')
    settings = {'background': style.get('background', '#1d2433'), **frame}
    if not 0 <= settings.get('padding', 0.06) <= 0.25:
        raise ValueError('frame padding must be between 0 and 0.25 of the width')
    if not 0 <= settings.get('radius', 12) <= 64:
        raise ValueError('frame radius must be between 0 and 64 pixels')
    return settings


def edit(a):
    import tempfile
    import tomllib
    from reshoot import cut
    board = tomllib.loads(Path(a.script).read_text())
    from reshoot.audio import settings
    mix = settings(board.get('audio'))
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
        clips, part_rows, offset = [], [], 0
        for i, part in enumerate(board['part']):
            if 'card' in part:
                width, height, _ = cut.probe(sources[0])
                seconds = part.get('duration', 2)
                if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
                    raise ValueError('card duration must be positive')
                style = board.get('style', {})
                font_path = (Path(a.script).resolve().parent / style['font']) if style.get('font') else None
                background = style.get('background', '#0e0d0c')  # a gradient's top colour, for a card
                card = cut.Card(width, height, background if isinstance(background, str) else background[0], font_path=font_path)
                card.text(None, int(height*.4), part['card'], min(64, max(18, height//10)), fill=style.get('foreground', 'white'))
                if style.get('logo'):
                    from PIL import Image
                    logo = Image.open(Path(a.script).resolve().parent / style['logo']).convert('RGBA')
                    logo.thumbnail((width//5, height//5))
                    card.im.paste(logo, ((width-logo.width)//2, int(height*.1)), logo)
                clip = Path(temp) / f'{i}.mp4'
                cut.still(card.save(Path(temp) / f'{i}.png'), seconds, clip)
                clips.append(clip)
                part_rows.append({'index': i, 'start': offset, 'end': offset + read(clip)['duration'], 'kind': 'card',
                                  'text_layout': card.text_layout})
                offset = part_rows[-1]['end']
                continue
            index = part.get('take', 0)
            if not isinstance(index, int) or index < 0 or index >= len(sources):
                raise ValueError('edit names an unknown take')
            source = sources[index]
            start, end, speed = part_range(part, source)
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
            if 'frame' in board:
                clip = cut.frame(clip, Path(temp) / f'{i}-framed.mp4', **frame_style(board))
            clips.append(clip)
            part_rows.append({'index': i, 'start': offset, 'end': offset + read(clip)['duration'], 'kind': 'take', 'take': index})
            offset = part_rows[-1]['end']
        silent = cut.concat(clips, Path(temp) / 'final.mp4')
        lines = []
        for row in read(silent)['segments']:
            lines += cut.lines(row['source'], row['source_start'], row['source_end'], row['start'])
        music = str((Path(a.script).resolve().parent / board['music']).resolve()) if board.get('music') else None
        if lines:
            voice = cut.voice_track(lines, Path(temp) / 'voice.wav', cut.duration(silent))
            cut.add_audio(silent, output, voice=voice, music=music, **mix)
        elif music:
            cut.add_audio(silent, output, music=music, **mix)
        else:
            import shutil
            shutil.copyfile(silent, output)
            copy(silent, output)
    mapping = read(output)
    write(output, mapping['segments'], mapping['duration'], part_rows)
    cut.write_srt(cues(output), output.with_suffix('.srt'))
    cut.ff('-ss', cut.duration(output) * .75, '-i', output, '-frames:v', 1, output.with_suffix('.poster.png'))
    from reshoot import framing, readability
    width, height, _ = cut.probe(output)
    readability.write(output, {}, framing.geometry((width, height), width, height))
    for profile in board.get('export', []):
        export(output, profile)
    print(output)


# Export presets: a shape and format for a place to post, and that place's limits, which the export is checked
# against. The limits were read on 2026-10-24 from each platform's own pages; check them again before relying on a
# change:
#   X:        https://docs.x.com/x-api/media/quickstart/best-practices (an account without Premium)
#   LinkedIn: https://www.linkedin.com/help/linkedin/answer/a548372
#   GitHub:   https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files
X = {'platform': 'X', 'seconds': (0.5, 1200), 'max_bytes': 8_000_000_000, 'long': (32, 1280), 'short': (32, 1024),
     'aspect': 3, 'fps': (1, 60)}
LINKEDIN = {'platform': 'LinkedIn', 'seconds': (3, 900), 'min_bytes': 75_000, 'max_bytes': 5_000_000_000,
            'long': (256, 4096), 'short': (144, 2304), 'aspect': 2.4, 'fps': (10, 60)}
GITHUB = {'platform': 'GitHub', 'max_bytes': 10_000_000}  # images, GIFs, and videos on a free plan
PRESETS = {
    'readme': ({'format': 'gif', 'width': 800, 'height': 450, 'fps': 15}, GITHUB),
    'readme-video': ({'format': 'mp4', 'width': 1280, 'height': 720, 'fps': 30}, GITHUB),
    'x': ({'format': 'mp4', 'width': 1280, 'height': 720, 'fps': 30}, X),
    'x-square': ({'format': 'mp4', 'width': 720, 'height': 720, 'fps': 30}, X),
    'x-portrait': ({'format': 'mp4', 'width': 720, 'height': 1280, 'fps': 30}, X),
    'linkedin': ({'format': 'mp4', 'width': 1920, 'height': 1080, 'fps': 30}, LINKEDIN),
    'linkedin-square': ({'format': 'mp4', 'width': 1080, 'height': 1080, 'fps': 30}, LINKEDIN),
    'linkedin-portrait': ({'format': 'mp4', 'width': 1080, 'height': 1350, 'fps': 30}, LINKEDIN),
}


def within(output, profile, limits):
    """Fail an export that breaks the limits of the place its preset is for, naming the limit."""
    from reshoot import cut
    where = limits['platform']
    seconds, size = cut.duration(output), output.stat().st_size
    w, h, fps = profile['width'], profile['height'], profile['fps']
    problems = []
    if 'seconds' in limits and not limits['seconds'][0] <= seconds <= limits['seconds'][1]:
        problems.append(f'it is {seconds:.1f} s; {where} takes {limits["seconds"][0]:g} to {limits["seconds"][1]:g} s')
    if size > limits.get('max_bytes', math.inf) or size < limits.get('min_bytes', 0):
        problems.append(f'it is {size:,} bytes; {where} takes ' + (f'{limits["min_bytes"]:,} to ' if 'min_bytes' in limits
                        else 'at most ') + f'{limits["max_bytes"]:,}')
    for side, value, (low, high) in (('long', max(w, h), limits.get('long', (0, math.inf))),
                                     ('short', min(w, h), limits.get('short', (0, math.inf)))):
        if not low <= value <= high:
            problems.append(f'its {side} side is {value} px; {where} takes {low} to {high}')
    if max(w, h) / min(w, h) > limits.get('aspect', math.inf):
        problems.append(f'its shape is {w}x{h}; {where} takes at most {limits["aspect"]:g}:1')
    if 'fps' in limits and not limits['fps'][0] <= fps <= limits['fps'][1]:
        problems.append(f'it is {fps} fps; {where} takes {limits["fps"][0]} to {limits["fps"][1]}')
    if problems:
        raise ValueError(f'export {profile["name"]} does not fit {where}: ' + '; '.join(problems))


def export(video, profile):
    from reshoot import cut, framing, readability
    profile, limits = framing.resolve(profile)
    width, height, name, kind, fps = (profile[k] for k in ('width', 'height', 'name', 'format', 'fps'))
    minimum = profile['min_reading']
    if any(end-start+.001 < minimum for start, end, text in cues(video) if text):
        raise ValueError('an exported caption is shorter than min_reading')
    output = Path(video).with_name(Path(video).stem + '-' + name + '.' + kind)
    plan = framing.geometry(cut.probe(video)[:2], width, height, profile['fit'], profile['focus'])
    if kind == 'gif':
        cut.gif(video, 0, cut.duration(video), output, fps=fps, width=width, height=height,
                fit=profile['fit'], focus=profile['focus'])
        copy(video, output)
    else:
        vf = framing.filter_for(plan)
        cut.ff('-i', video, '-vf', vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', fps, '-c:a', 'aac', '-movflags', '+faststart', output)
        copy(video, output)
    framing.map_video(output, plan)
    cut.write_srt(cues(output), output.with_suffix('.srt'))
    at = profile.get('poster_at', min(max(0, cut.duration(output)-.05), cut.duration(output)*.75))
    if not isinstance(at, (int, float)) or not math.isfinite(at) or not 0 <= at < cut.duration(output):
        raise ValueError('poster_at must be within the export')
    cut.ff('-ss', at, '-i', output, '-frames:v', 1, output.with_suffix('.poster.png'))
    if profile.get('max_bytes') is not None and output.stat().st_size > profile['max_bytes']:
        raise ValueError('export exceeds its configured max_bytes')
    if limits:
        within(output, {**profile, 'name': name, 'width': width, 'height': height, 'fps': fps}, limits)
    readability.write(output, profile, plan)
    return output
