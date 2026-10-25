"""Destination geometry and validated export framing, shared by MP4, GIF, the CLI and studio."""
import json
import math
import re
import tomllib
from pathlib import Path


def resolve(profile):
    from reshoot.timeline import PRESETS
    if not isinstance(profile, dict) or set(profile) - {'preset', 'name', 'format', 'width', 'height', 'fit', 'focus',
            'display_width', 'fps', 'max_bytes', 'min_reading', 'poster_at'}:
        raise ValueError('Unknown export setting; guide/projects.md lists export fields.')
    preset = profile.get('preset')
    if preset is not None and preset not in PRESETS:
        raise ValueError(f'unknown export preset {preset!r}; use ' + ', '.join(PRESETS))
    defaults, limits = PRESETS[preset] if preset else ({}, None)
    result = {'name': preset or 'landscape', 'format': 'mp4', 'width': 1280, 'height': 720,
              **defaults, **{k: v for k, v in profile.items() if k != 'preset'}}
    if not isinstance(result['name'], str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', result['name']):
        raise ValueError('profile needs a safe name and positive even dimensions')
    if any(type(result[k]) is not int or result[k] <= 0 or result[k] % 2 for k in ('width', 'height')):
        raise ValueError('profile needs a safe name and positive even dimensions')
    if result['format'] not in ('mp4', 'gif'):
        raise ValueError('profile format must be mp4 or gif')
    result.setdefault('fps', 15 if result['format'] == 'gif' else 60)
    if type(result['fps']) is not int or not 1 <= result['fps'] <= 120:
        raise ValueError('profile fps must be between 1 and 120')
    if 'max_bytes' in result and (type(result['max_bytes']) is not int or result['max_bytes'] <= 0):
        raise ValueError('max_bytes must be a positive integer')
    minimum = result.setdefault('min_reading', 0)
    if isinstance(minimum, bool) or not isinstance(minimum, (int, float)) or not math.isfinite(minimum) or minimum < 0:
        raise ValueError('profile min_reading must be nonnegative')
    if result.setdefault('fit', 'contain') not in ('contain', 'crop'):
        raise ValueError('profile fit must be contain or crop')
    focus = result.setdefault('focus', [0.5, 0.5])
    if not isinstance(focus, (list, tuple)) or len(focus) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float))
            or not math.isfinite(v) or not 0 <= v <= 1 for v in focus):
        raise ValueError('focus needs horizontal and vertical fractions between 0 and 1')
    result['focus'] = list(focus)
    viewing = result.setdefault('display_width', max(160, min(result['width'], 640)))
    if type(viewing) is not int or not 160 <= viewing <= 1920:
        raise ValueError('display_width must be between 160 and 1920 pixels')
    return result, limits


def geometry(source, width, height, fit='contain', focus=(.5, .5)):
    """Even pixel geometry, including chroma-aligned offsets, used by both renderers and feedback."""
    sw, sh = source
    resolve({'width': width, 'height': height, 'fit': fit, 'focus': list(focus)})
    ratio = (max if fit == 'crop' else min)(width / sw, height / sh)
    rounding = math.ceil if fit == 'crop' else math.floor
    rw, rh = max(2, rounding(sw * ratio / 2) * 2), max(2, rounding(sh * ratio / 2) * 2)
    if fit == 'crop':
        x, y = -(round((rw - width) * focus[0] / 2) * 2), -(round((rh - height) * focus[1] / 2) * 2)
    else:
        x, y = (width - rw) // 4 * 2, (height - rh) // 4 * 2
    return {'width': width, 'height': height, 'scaled_width': rw, 'scaled_height': rh,
            'sx': rw / sw, 'sy': rh / sh, 'x': x, 'y': y, 'fit': fit, 'focus': list(focus)}


def filter_for(plan):
    operation = (f'crop={plan["width"]}:{plan["height"]}:{-plan["x"]}:{-plan["y"]}' if plan['fit'] == 'crop' else
                 f'pad={plan["width"]}:{plan["height"]}:{plan["x"]}:{plan["y"]}')
    return f'scale={plan["scaled_width"]}:{plan["scaled_height"]}:flags=lanczos,{operation},setsar=1'


def describe(profile):
    try:
        return resolve(profile)[0]
    except ValueError as error:
        return {'error': str(error)}


def rect(box, transform):
    x, y, width, height = box
    return [x * transform['sx'] + transform['x'], y * transform['sy'] + transform['y'],
            width * transform['sx'], height * transform['sy']]


def map_video(video, transform):
    from reshoot import timeline
    data = timeline.read(video)
    for row in data['segments']:
        previous = row.get('spatial', {'sx': 1, 'sy': 1, 'x': 0, 'y': 0})
        row['spatial'] = {'sx': previous['sx'] * transform['sx'], 'sy': previous['sy'] * transform['sy'],
                          'x': previous['x'] * transform['sx'] + transform['x'],
                          'y': previous['y'] * transform['sy'] + transform['y']}
    for part in data.get('parts', []):
        for sample in part.get('text_layout', []):
            sample['box'] = rect(sample['box'], transform)
            sample['font_px'] *= transform['sy']
    timeline.write(video, data['segments'], data['duration'], data.get('parts'))


def apply(project, index, settings, expected=None):
    from reshoot.config import read
    from reshoot.sequence import check_cut
    from reshoot.workspace import put, read_lines, tables, save_many
    config = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    original = config.read_bytes()
    shoot, folder = read(config)
    edit = shoot.get('edit', {}).get('file')
    if shoot.get('schema_version') != 1 or not edit or Path(edit).suffix != '.toml':
        raise ValueError('Destination framing needs a versioned project with a TOML edit.')
    path = (folder / edit).resolve()
    before = {p.resolve(): p.read_bytes() if p.exists() else None for p in [folder / 'styles.toml',
              *(folder / t['web'] for t in shoot.get('take', []) if str(t.get('web', '')).endswith('.toml'))]}
    before.update({config: original, path: path.read_bytes()})
    before.update(expected or {})
    lines = read_lines(path)
    cut = tomllib.loads(''.join(lines))
    if type(index) is not int or not 0 <= index < len(cut.get('export', [])):
        raise ValueError('Choose an export from this project.')
    if not isinstance(settings, dict) or not settings or set(settings) - {'fit', 'focus', 'display_width'}:
        raise ValueError('Change fit, focus or display_width for this export.')
    resolve({**cut['export'][index], **settings})
    for key, value in settings.items():
        put(lines, tables(lines, '[[export]]')[index][1:], key, value)
    save_many({path: (''.join(lines), check_cut)}, before)


def recording(project, size, expected=None):
    from reshoot import config as config_module, web
    from reshoot.workspace import put, read_lines, tables, save_many
    if not isinstance(size, str):
        raise ValueError('Choose a recording size such as 640x480@2.')
    web.parse_size(size)
    config = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    original = config.read_bytes()
    shoot, folder = config_module.read(config)
    index = next((i for i, take in enumerate(shoot.get('take', [])) if str(take.get('web', '')).endswith('.toml')), None)
    if shoot.get('schema_version') != 1 or index is None:
        raise ValueError('Choose a versioned project with a TOML browser take.')
    before = {config: original}
    for take in shoot.get('take', []):
        if str(take.get('web', '')).endswith('.toml'):
            path = (folder / take['web']).resolve()
            before[path] = path.read_bytes()
    if shoot.get('edit', {}).get('file'):
        path = (folder / shoot['edit']['file']).resolve()
        before[path] = path.read_bytes()
    path = folder / 'styles.toml'
    before[path] = path.read_bytes() if path.exists() else None
    before.update(expected or {})
    lines = read_lines(config)
    put(lines, tables(lines, '[[take]]')[index][1:], 'size', size)
    save_many({config: (''.join(lines), config_module.read)}, before)


def main(a):
    from reshoot import review
    if a.operation == 'check':
        root, report = review.read(a.run_path)
        found = False
        for file in report['files']:
            if file['path'].endswith('.readability.json'):
                data = json.loads((root / file['path']).read_text())
                print(file['path'] + f' (viewing width {data["display_width"]} px)')
                for key, label in [('app_font_p10_px', 'Small app-text samples'), ('caption_min_px', 'Smallest caption text'),
                                   ('card_min_px', 'Smallest title text')]:
                    if data['metrics'].get(key) is not None:
                        print(f'  {label}: about {data["metrics"][key]:g} px')
                for issue in data['issues']:
                    print('  ' + issue['message'])
                for note in data['notes']:
                    print('  ' + note)
                found = True
        if not found:
            raise ValueError('This run has no readability measurements. Update its preview with this version of reshoot.')
        return 0
    if a.operation == 'record':
        recording(a.project, a.size)
        print('Saved the recording view. Update preview will record the full task again with its checks.')
        return 0
    settings = {key: value for key, value in [('fit', a.fit), ('display_width', a.display_width)] if value is not None}
    if a.x is not None or a.y is not None:
        if a.x is None or a.y is None:
            raise ValueError('Give both --x and --y crop positions, from 0 to 100.')
        settings['focus'] = [a.x / 100, a.y / 100]
    apply(a.project, a.export - 1, settings)
    print('Saved export framing. Update preview to render it and measure readability.')
    return 0
