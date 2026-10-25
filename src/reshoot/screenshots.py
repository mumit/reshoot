"""Stable documentation PNGs from checked browser result frames, with run-bound provenance."""
import json
import math
import re
import tomllib
from pathlib import Path


def validate(specs, take_count):
    if not isinstance(specs, list) or len(specs) > 50:
        raise ValueError('screenshot must be a list of at most 50 named screenshots.')
    names = set()
    for spec in specs:
        if not isinstance(spec, dict) or set(spec) - {'name', 'take', 'beat', 'alt', 'width', 'crop'}:
            raise ValueError('Unknown screenshot field; use name, take, beat, alt, width or crop.')
        name = spec.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', name) or name.casefold() in names:
            raise ValueError('Screenshot names must be unique letters, digits, underscores or hyphens, at most 80 characters.')
        names.add(name.casefold())
        index = spec.get('take', 0)
        if type(index) is not int or not 0 <= index < take_count:
            raise ValueError('Choose an existing browser take for the screenshot.')
        if not isinstance(spec.get('beat'), str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', spec['beat']):
            raise ValueError('A screenshot needs a beat ID.')
        alt = spec.get('alt')
        if not isinstance(alt, str) or not alt.strip() or len(alt) > 300 or any(ord(c) < 32 for c in alt):
            raise ValueError('Describe the screenshot in alt text, on one line of at most 300 characters.')
        if 'width' in spec and (type(spec['width']) is not int or not 160 <= spec['width'] <= 3840):
            raise ValueError('Screenshot width must be between 160 and 3840 pixels.')
        if 'crop' in spec:
            box = spec['crop']
            if not isinstance(box, list) or len(box) != 4 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                    or not math.isfinite(v) or not 0 <= v <= 1 for v in box):
                raise ValueError('Screenshot crop is [left, top, width, height], as fractions from 0 to 1.')
            x, y, width, height = box
            if width <= 0 or height <= 0 or x + width > 1.0000001 or y + height > 1.0000001:
                raise ValueError('Screenshot crop must have positive dimensions and stay inside the captured page.')
    return specs


def checked(root, take, beat_id):
    """Only a complete native take's checked beat can supply a documentation image."""
    root = Path(root).resolve()
    source = (root / take).resolve()
    if not source.is_relative_to(root):
        raise ValueError('Screenshot source must stay in its run.')
    metadata = source.with_suffix('.take.json')
    if not metadata.is_file():
        raise ValueError('Screenshot needs a recorded TOML browser take. Record a fresh preview.')
    data = json.loads(metadata.read_text())
    beat = next((b for b in data.get('beats', []) if b.get('id') == beat_id), None)
    checks = (beat or {}).get('expectations', [])
    if data.get('status') != 'completed' or data.get('mode') == 'partial' or not beat or beat.get('status') != 'passed' or not checks or any(c.get('status') != 'passed' for c in checks):
        raise ValueError(f'Screenshot beat {beat_id!r} needs a complete recording with passing result checks.')
    shot = (source.parent / beat.get('screenshot', '')).resolve()
    expected = (source.with_suffix('.evidence') / (beat_id + '.png')).resolve()
    if shot != expected or not shot.is_relative_to(root) or not shot.is_file():
        raise ValueError('Screenshot result frame is missing or outside the run. Record a fresh preview.')
    return shot, metadata, len(checks)


def render(root, specs, takes):
    from PIL import Image
    from reshoot.artifacts import digest
    root = Path(root).resolve()
    validate(specs, len(takes))
    rows = []
    for spec in specs:
        take = takes[spec.get('take', 0)]
        if 'web' not in take or not str(take['web']).endswith('.toml'):
            raise ValueError('Documentation screenshots need TOML browser takes.')
        shot, metadata, checks = checked(root, take['out'], spec['beat'])
        with Image.open(shot) as original:
            image = original.convert('RGB')
        sw, sh = image.size
        x, y, width, height = spec.get('crop', [0, 0, 1, 1])
        box = [round(x * sw), round(y * sh), round((x + width) * sw), round((y + height) * sh)]
        if box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError('Screenshot crop is smaller than a pixel. Choose a larger region.')
        image = image.crop(box)
        if spec.get('width', image.width) < image.width:
            target = spec['width']
            image = image.resize((target, max(1, round(image.height * target / image.width))), Image.Resampling.LANCZOS)
        output = root / 'screenshots' / (spec['name'] + '.png')
        if not output.resolve().is_relative_to(root):
            raise ValueError('Screenshot output must stay inside its run.')
        output.parent.mkdir(exist_ok=True)
        image.save(output)
        rows.append({**spec, 'take': spec.get('take', 0), 'path': str(output.relative_to(root)),
                     'sha256': digest(output), 'source': str(shot.relative_to(root)), 'source_sha256': digest(shot),
                     'metadata': str(metadata.relative_to(root)), 'metadata_sha256': digest(metadata),
                     'result_checks': checks, 'pixels': list(image.size), 'source_pixels': [sw, sh]})
    if specs:
        if not (root / 'screenshots.json').resolve().is_relative_to(root):
            raise ValueError('Screenshot manifest must stay inside its run.')
        (root / 'screenshots.json').write_text(json.dumps({'schema_version': 1, 'screenshots': rows}, indent=2))
    return rows


def listing(root, report):
    """Only explicitly bound PNG exports are deliverables; evidence/posters are not."""
    named = {item['path']: item['sha256'] for item in report.get('files', [])}
    if 'screenshots.json' not in named:
        return []
    data = json.loads((Path(root) / 'screenshots.json').read_text())
    rows = data.get('screenshots', [])
    if data.get('schema_version') != 1 or not isinstance(rows, list):
        raise ValueError('Unsupported documentation screenshot manifest.')
    validate([{k: row[k] for k in ('name', 'take', 'beat', 'alt', 'width', 'crop') if k in row} for row in rows],
             max((row.get('take', 0) for row in rows), default=0) + 1)
    for row in rows:
        if row.get('path') != 'screenshots/' + row['name'] + '.png' or row['path'] not in named or named[row['path']] != row.get('sha256'):
            raise ValueError('Unbound documentation screenshot. Record or re-cut a fresh run.')
        if any(not isinstance(row.get(key), str) or row[key] not in named or named[row[key]] != row.get(key + '_sha256') for key in ('source', 'metadata')):
            raise ValueError('Unbound screenshot provenance. Record a fresh preview.')
    return rows


def apply(project, operation, name, settings=None, expected=None):
    from reshoot import config, story
    from reshoot.workspace import drop, put, read_lines, save_many, tables
    path = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    original = path.read_bytes()
    shoot, folder = config.read(path)
    if shoot.get('schema_version') != 1:
        raise ValueError('Screenshots need a versioned project.')
    before = {path: original}
    for source in [folder / 'styles.toml', *(folder / t['web'] for t in shoot.get('take', []) if str(t.get('web', '')).endswith('.toml')),
                   *([folder / shoot['edit']['file']] if shoot.get('edit', {}).get('file') else [])]:
        before[source.resolve()] = source.read_bytes() if source.exists() else None
    before.update(expected or {})
    specs = shoot.get('screenshot', [])
    index = next((i for i, spec in enumerate(specs) if spec['name'] == name), None)
    lines = read_lines(path)
    if operation == 'remove':
        if index is None:
            raise ValueError('Choose a configured screenshot.')
        head, _, end = tables(lines, '[[screenshot]]')[index]
        drop(lines, head, end)
    elif operation in ('set', 'add'):
        if operation == 'add' and index is not None:
            raise ValueError('This screenshot name already exists. Edit its settings or choose another name.')
        if not isinstance(settings, dict) or set(settings) - {'take', 'beat', 'alt', 'width', 'crop'}:
            raise ValueError('Choose screenshot take, beat, alt text, width or crop.')
        spec = {**(specs[index] if index is not None else {}), **settings, 'name': name}
        spec = {k: v for k, v in spec.items() if v is not None}
        validate([spec], len(shoot.get('take', [])))
        take = shoot['take'][spec.get('take', 0)]
        if not str(take.get('web', '')).endswith('.toml'):
            raise ValueError('Choose a TOML browser take for the screenshot.')
        beat = next((b for b in story.load(folder / take['web'])['beat'] if b['id'] == spec['beat']), None)
        if not beat or not beat.get('expect'):
            raise ValueError('Choose a beat with result checks for the screenshot.')
        if index is None:
            lines += ['\n', '[[screenshot]]\n']
            index = len(specs)
        for key in ('name', 'take', 'beat', 'alt', 'width', 'crop'):
            put(lines, tables(lines, '[[screenshot]]')[index][1:], key, spec.get(key))
    else:
        raise ValueError('Set or remove a screenshot.')
    save_many({path: (''.join(lines), config.read)}, before)


def main(a):
    if a.operation == 'list':
        from reshoot.config import read
        path = Path(a.project) if Path(a.project).suffix == '.toml' else Path(a.project) / 'reshoot.toml'
        for spec in read(path)[0].get('screenshot', []):
            print(f'{spec["name"]}: take {spec.get("take", 0) + 1}, beat {spec["beat"]}: {spec["alt"]}')
        return 0
    values = {k: v for k, v in [('take', a.take - 1 if getattr(a, 'take', None) is not None else None),
              ('beat', getattr(a, 'beat', None)), ('alt', getattr(a, 'alt', None)), ('width', getattr(a, 'width', None)),
              ('crop', getattr(a, 'crop', None))] if v is not None}
    if getattr(a, 'native', False):
        values['width'] = None
    if getattr(a, 'full_frame', False):
        values['crop'] = None
    apply(a.project, a.operation, a.name, values)
    print('Saved documentation screenshots. Update preview to render them from checked result frames.')
    return 0
