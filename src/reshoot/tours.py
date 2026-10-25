"""Offline clickable tours of checked result frames, refreshed and reviewed with the video."""
import base64
import hashlib
import html
import json
import math
import re
from pathlib import Path


def words(value, label, maximum, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()) or len(value) > maximum or any(ord(c) < 32 and c != '\n' for c in value):
        raise ValueError(f'{label} needs plain text of at most {maximum} characters.')


def validate(spec, take_count):
    from reshoot.screenshots import validate as images
    if not isinstance(spec, dict) or set(spec) - {'name', 'title', 'step'}:
        raise ValueError('tour needs name, title and [[tour.step]] entries.')
    if not isinstance(spec.get('name'), str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', spec['name']):
        raise ValueError('Tour name needs 1 to 80 letters, digits, underscores or hyphens.')
    words(spec.get('title'), 'Tour title', 120)
    steps = spec.get('step')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 30:
        raise ValueError('A tour needs 1 to 30 checked steps.')
    for i, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) - {'take', 'beat', 'title', 'text', 'alt', 'width', 'crop', 'hotspot'}:
            raise ValueError('Unknown tour step field; use take, beat, title, text, alt, width, crop or hotspot.')
        images([{'name': f'step-{i + 1}', **{k: v for k, v in step.items() if k in ('take', 'beat', 'alt', 'width', 'crop')}}], take_count)
        words(step.get('title'), 'Step title', 120)
        words(step.get('text', ''), 'Step explanation', 1000, empty=True)
        if 'hotspot' in step and (not isinstance(step['hotspot'], list) or len(step['hotspot']) != 2 or any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in step['hotspot'])):
            raise ValueError('A click marker needs horizontal and vertical fractions from 0 to 1.')
    return spec


CSS = '''
:root { color-scheme:light dark; --bg:#f5f3ee; --panel:#fff; --ink:#202225; --muted:#565e67; --accent:#2847ba; --line:#cbd1da }
@media(prefers-color-scheme:dark) { :root { --bg:#111316; --panel:#1c2026; --ink:#f4f5f8; --muted:#b4bdca; --accent:#acbaff; --line:#465160 } }
* { box-sizing:border-box } body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 system-ui,sans-serif }
main { max-width:1120px; margin:auto; padding:clamp(16px,4vw,40px) } h1 { font-size:clamp(24px,4vw,36px); margin:0 0 8px; overflow-wrap:anywhere }
h2 { font-size:24px; margin:0 0 8px; overflow-wrap:anywhere } h2:focus { outline:none } p { white-space:pre-wrap; overflow-wrap:anywhere }
.eyebrow, footer, #progress { color:var(--muted) } .eyebrow { margin:0 0 8px } nav { display:flex; flex-wrap:wrap; gap:8px; margin:20px 0 }
a { color:var(--accent) } .pill { border:1px solid var(--line); border-radius:999px; padding:8px 14px; text-decoration:none; background:var(--panel) }
.pill[aria-current] { background:var(--accent); color:var(--bg) } :focus-visible { outline:3px solid var(--accent); outline-offset:4px }
.step { background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:clamp(14px,3vw,28px); margin-bottom:20px }
.step[hidden] { display:none } .screen { position:relative; margin:20px 16px; } .screen img { width:100%; height:auto; display:block; border-radius:8px }
.marker { position:absolute; transform:translate(-50%,-50%); min-width:40px; min-height:40px; border:3px solid #fff; border-radius:999px; display:grid; place-items:center; background:#2349c5; color:white; font-weight:700; text-decoration:none; box-shadow:0 2px 8px #0008 }
.controls { display:flex; flex-wrap:wrap; justify-content:space-between; gap:12px; margin-top:20px; position:sticky; bottom:0; background:var(--panel); padding:10px 0 } footer { margin-top:20px; font-size:14px }
@media print { .step[hidden] { display:block } nav,.controls,.marker { display:none } .step { break-inside:avoid } }
'''


def document(title, steps, root):
    escape = lambda value: html.escape(str(value), quote=True)
    script = (Path(__file__).with_name('tour.js')).read_text()
    script_hash = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    nav = ''.join(f'<a class="pill" href="#step-{i + 1}" data-go="{i}" data-step="{i}" aria-label="Step {i + 1}: {escape(step["title"])}">{i + 1}</a>' for i, step in enumerate(steps))
    sections = []
    for i, step in enumerate(steps):
        following = i + 1 if i + 1 < len(steps) else 0
        label = 'Next: ' + steps[following]['title'] if following else 'Restart tour'
        marker = ''
        if 'hotspot' in step:
            x, y = step['hotspot']
            marker = f'<a class="marker" style="left:{x * 100:g}%;top:{y * 100:g}%" href="#step-{following + 1}" data-go="{following}" aria-label="{escape(label)}">{i + 1}</a>'
        image = base64.b64encode((root / step['image']).read_bytes()).decode()
        previous = f'<a class="pill" href="#step-{i}" data-go="{i - 1}">Back</a>' if i else '<span></span>'
        sections.append(f'''<section class="step" id="step-{i + 1}" aria-labelledby="heading-{i + 1}">
<h2 id="heading-{i + 1}" tabindex="-1">{escape(step['title'])}</h2><p>{escape(step.get('text', ''))}</p>
<div class="screen"><img src="data:image/png;base64,{image}" width="{step['pixels'][0]}" height="{step['pixels'][1]}" alt="{escape(step['alt'])}">{marker}</div>
<div class="controls">{previous}<a class="pill" href="#step-{following + 1}" data-go="{following}">{'Next' if following else 'Restart tour'}</a></div></section>''')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'sha256-{script_hash}'; base-uri 'none'; form-action 'none'; connect-src 'none'">
<meta name="referrer" content="no-referrer"><title>{escape(title)}</title><style>{CSS}</style></head>
<body><main><p class="eyebrow">Interactive walkthrough · captured screens</p><h1>{escape(title)}</h1><p id="progress" role="status" aria-live="polite"></p>
<nav aria-label="Tour steps">{nav}</nav>{''.join(sections)}
<footer>Use Next, a numbered marker, or the arrow keys to explore. Interactions move between captured screens.</footer>
<noscript><p>JavaScript is off. Scroll to read every step.</p></noscript></main><script>{script}</script></body></html>'''


def render(root, spec, takes):
    from reshoot import screenshots
    from reshoot.artifacts import digest
    root = Path(root).resolve()
    validate(spec, len(takes))
    steps = []
    for i, step in enumerate(spec['step']):
        take = takes[step.get('take', 0)]
        if not str(take.get('web', '')).endswith('.toml'):
            raise ValueError('Tour steps need TOML browser takes.')
        shot, metadata, checks = screenshots.checked(root, take['out'], step['beat'])
        picture, source_pixels = screenshots.image(shot, {'width': 1280, **step})
        output = root / 'tours' / spec['name'] / f'{i + 1:02}.png'
        if not output.resolve().is_relative_to(root):
            raise ValueError('Tour assets must stay inside their run.')
        output.parent.mkdir(parents=True, exist_ok=True)
        picture.save(output)
        steps.append({**step, 'take': step.get('take', 0), 'image': str(output.relative_to(root)), 'sha256': digest(output),
                      'pixels': list(picture.size), 'source_pixels': source_pixels, 'result_checks': checks,
                      'source': str(shot.relative_to(root)), 'source_sha256': digest(shot),
                      'metadata': str(metadata.relative_to(root)), 'metadata_sha256': digest(metadata)})
    output = root / 'tours' / (spec['name'] + '.html')
    manifest = root / 'tours.json'
    if any(not path.resolve().is_relative_to(root) for path in (output, manifest)):
        raise ValueError('Tour output must stay inside its run.')
    output.write_text(document(spec['title'], steps, root))
    row = {'name': spec['name'], 'title': spec['title'], 'path': str(output.relative_to(root)), 'sha256': digest(output), 'steps': steps}
    manifest.write_text(json.dumps({'schema_version': 1, 'tours': [row]}, indent=2))
    return row


def listing(root, report):
    named = {item['path']: item['sha256'] for item in report.get('files', [])}
    if 'tours.json' not in named:
        return []
    data = json.loads((Path(root) / 'tours.json').read_text())
    if data.get('schema_version') != 1 or not isinstance(data.get('tours'), list) or len(data['tours']) != 1:
        raise ValueError('Unsupported tour manifest.')
    for tour in data['tours']:
        steps = tour.get('steps', [])
        validate({'name': tour.get('name'), 'title': tour.get('title'), 'step': [{k: row[k] for k in
                  ('take', 'beat', 'title', 'text', 'alt', 'width', 'crop', 'hotspot') if k in row} for row in steps]},
                 max((row.get('take', 0) for row in steps), default=0) + 1)
        if tour.get('path') != 'tours/' + tour['name'] + '.html' or tour['path'] not in named or named[tour['path']] != tour.get('sha256'):
            raise ValueError('Unbound tour output. Record or re-cut a fresh run.')
        for i, row in enumerate(steps):
            if row.get('image') != f'tours/{tour["name"]}/{i + 1:02}.png':
                raise ValueError('Unbound tour image.')
            for key, hash_key in [('image', 'sha256'), ('source', 'source_sha256'), ('metadata', 'metadata_sha256')]:
                if not isinstance(row.get(key), str) or row[key] not in named or named[row[key]] != row.get(hash_key):
                    raise ValueError('Unbound tour provenance. Record a fresh preview.')
    return data['tours']


def apply(project, change, expected=None):
    from reshoot import config, story
    from reshoot.workspace import block, drop, put, quote, read_lines, save_many, tables
    path = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    original = path.read_bytes()
    shoot, folder = config.read(path)
    if shoot.get('schema_version') != 1 or not isinstance(change, dict):
        raise ValueError('Tours need a versioned project and a tour operation.')
    before = {path: original}
    for source in [folder / 'styles.toml', *(folder / t['web'] for t in shoot.get('take', []) if str(t.get('web', '')).endswith('.toml')),
                   *([folder / shoot['edit']['file']] if shoot.get('edit', {}).get('file') else [])]:
        before[source.resolve()] = source.read_bytes() if source.exists() else None
    before.update(expected or {})
    lines = read_lines(path)
    operation, spec = change.get('operation'), shoot.get('tour')
    def step_default(index, beat_id):
        if type(index) is not int or not 0 <= index < len(shoot.get('take', [])):
            raise ValueError('Choose a browser take.')
        take = shoot['take'][index]
        if not str(take.get('web', '')).endswith('.toml'):
            raise ValueError('Choose a TOML browser take.')
        beat = next((b for b in story.load(folder / take['web'])['beat'] if b['id'] == beat_id), None)
        if not beat or not beat.get('expect'):
            raise ValueError('Choose a beat with result checks.')
        title = ' '.join((beat.get('purpose') or beat.get('caption') or beat_id).split())[:120]
        return {'take': index, 'beat': beat_id, 'title': title, 'text': '', 'alt': title}
    def text_for(step):
        return ['[[tour.step]]\n', *[f'{key} = {quote(value)}\n' for key, value in step.items()], '\n']
    if operation == 'create':
        if spec is not None:
            raise ValueError('A tour already exists. Edit it or disable it first.')
        index = next((i for i, take in enumerate(shoot.get('take', [])) if str(take.get('web', '')).endswith('.toml')), None)
        if index is None:
            raise ValueError('Choose a project with a TOML browser take.')
        beats = story.load(folder / shoot['take'][index]['web'])['beat']
        spec = {'name': change.get('name', 'demo-tour'), 'title': change.get('title', 'Explore the demo'),
                'step': [step_default(index, beat['id']) for beat in beats if beat.get('expect')]}
        validate(spec, len(shoot['take']))
        lines += ['\n', '[tour]\n', f'name = {quote(spec["name"])}\n', f'title = {quote(spec["title"])}\n', '\n']
        for step in spec['step']:
            lines += text_for(step)
    elif spec is None:
        raise ValueError('Create a tour from checked steps first.')
    elif operation == 'disable':
        for head, _, end in reversed(tables(lines, '[[tour.step]]')):
            drop(lines, head, end)
        head, _, end = tables(lines, '[tour]')[0]
        drop(lines, head, end)
    elif operation == 'title':
        for key in ('name', 'title'):
            if key in change:
                put(lines, block(lines, '[tour]'), key, change[key])
    elif operation == 'add':
        if not isinstance(change.get('settings', {}), dict):
            raise ValueError('Choose step words and image settings.')
        step = {k: v for k, v in {**step_default(change.get('take', 0), change.get('beat')), **change.get('settings', {})}.items() if v is not None}
        at = tables(lines, '[[tour.step]]')[-1][2]
        lines[at:at] = text_for(step)
    else:
        index = change.get('step')
        spans = tables(lines, '[[tour.step]]')
        if type(index) is not int or not 0 <= index < len(spans):
            raise ValueError('Choose an existing tour step.')
        head, start, end = spans[index]
        if operation == 'set':
            settings = change.get('settings')
            if not isinstance(settings, dict) or set(settings) - {'take', 'beat', 'title', 'text', 'alt', 'width', 'crop', 'hotspot'}:
                raise ValueError('Choose step words, image settings or click marker.')
            for key, value in settings.items():
                put(lines, tables(lines, '[[tour.step]]')[index][1:], key, value)
        elif operation == 'remove':
            if len(spans) == 1:
                raise ValueError('Keep at least one step, or disable the tour.')
            drop(lines, head, end)
        elif operation == 'move':
            target = change.get('to')
            if type(target) is not int or not 0 <= target < len(spans):
                raise ValueError('Choose a position in this tour.')
            if target == index:
                return
            saved = lines[head:end]
            drop(lines, head, end)
            remaining = tables(lines, '[[tour.step]]')
            at = remaining[target][0] if target < len(remaining) else remaining[-1][2]
            lines[at:at] = saved
        else:
            raise ValueError('Choose a tour operation.')
    def check(temp):
        data, _ = config.read(temp)
        if data.get('tour'):
            for step in data['tour']['step']:
                step_default(step.get('take', 0), step['beat'])
    save_many({path: (''.join(lines), check)}, before)


def main(a):
    change = {'operation': a.operation}
    if getattr(a, 'step', None) is not None:
        change['step'] = a.step - 1
    if getattr(a, 'to', None) is not None:
        change['to'] = a.to - 1
    if a.operation in ('create', 'title'):
        change.update({k: getattr(a, k) for k in ('name', 'title') if getattr(a, k, None) is not None})
    else:
        settings = {k: getattr(a, k) for k in ('title', 'text', 'alt', 'beat', 'width', 'crop') if getattr(a, k, None) is not None}
        if getattr(a, 'take', None) is not None:
            settings['take'] = a.take - 1
        if getattr(a, 'x', None) is not None or getattr(a, 'y', None) is not None:
            if a.x is None or a.y is None:
                raise ValueError('Give both --x and --y marker positions, from 0 to 100.')
            settings['hotspot'] = [a.x / 100, a.y / 100]
        if getattr(a, 'no_marker', False):
            settings['hotspot'] = None
        if a.operation == 'add':
            change.update(beat=settings.pop('beat', None), take=settings.pop('take', 0))
        change['settings'] = settings
    apply(a.project, change)
    print('Saved tour. Update preview to build the offline walkthrough from checked frames.')
    return 0
