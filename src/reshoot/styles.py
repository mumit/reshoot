"""Reusable caption, title-card and browser-frame looks. Applying a style materializes ordinary project settings."""
import copy
import math
import re
import tomllib
from pathlib import Path

from reshoot.workspace import block, first_header, put, quote, read_lines, save_many

CAPTION = {'position': 'bottom', 'margin': 0.065, 'background': '#0e0d0cc8', 'foreground': '#ffffff'}
CARD = {'background': '#0e0d0c', 'foreground': '#ffffff'}
FRAME = {'background': '#1d2433', 'padding': 0.06, 'radius': 12, 'shadow': True, 'bar': True, 'bar_color': '#2b2f36'}
LIBRARY = 'styles.toml'


def starting(name, description, caption=None, card=None, frame=None):
    return {'schema_version': 1, 'name': name, 'description': description,
            'caption': {**CAPTION, **(caption or {})}, 'card': {**CARD, **(card or {})},
            'frame_enabled': frame is not None, 'frame': {**FRAME, **(frame or {})}}


BUILTINS = {
    'focus': starting('Focus', 'Keep the app large, with quiet dark captions.'),
    'midnight': starting('Midnight', 'A blue gradient and a framed browser for a product reveal.',
                         caption={'background': '#172554f2'}, card={'background': '#172554'},
                         frame={'background': ['#253a6a', '#101726'], 'padding': 0.045, 'bar_color': '#1e293b'}),
    'paper': starting('Paper', 'Warm light captions and a soft, minimal browser frame.',
                     caption={'background': '#f4f1eaf2', 'foreground': '#1d1b18'},
                     card={'background': '#f4f1ea', 'foreground': '#1d1b18'},
                     frame={'background': '#e5dfd3', 'bar_color': '#f4f1ea', 'padding': 0.04, 'radius': 10}),
}


def colour(value, alpha=True):
    from PIL import ImageColor
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError('Style colours must be colour strings, such as #172554.')
    try:
        rgba = ImageColor.getcolor(value, 'RGBA')
    except (ValueError, TypeError):
        raise ValueError(f'Invalid style colour {value!r}.') from None
    if not alpha and rgba[3] != 255:
        raise ValueError('Card and frame colours must be opaque.')
    return rgba


def background(value):
    if isinstance(value, list):
        if len(value) != 2:
            raise ValueError('A style gradient needs exactly two colours.')
        for item in value:
            colour(item, alpha=False)
    else:
        colour(value, alpha=False)


def validate(data):
    """Closed, portable schema: no fonts, paths, scripts, story content, timing or export settings."""
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('A style needs schema_version = 1.')
    if set(data) - {'schema_version', 'name', 'description', 'caption', 'card', 'frame_enabled', 'frame'}:
        raise ValueError('Unknown style option; use name, description, caption, card, frame_enabled and frame.')
    name = data.get('name')
    if not isinstance(name, str) or not name.strip() or len(name) > 60 or any(ord(c) < 32 for c in name):
        raise ValueError('Give the style a name of 1 to 60 characters.')
    if not isinstance(data.get('description', ''), str) or len(data.get('description', '')) > 200:
        raise ValueError('A style description takes at most 200 characters.')
    result = starting(name.strip(), data.get('description', ''))
    for section, defaults in [('caption', CAPTION), ('card', CARD), ('frame', FRAME)]:
        values = data.get(section, {})
        if not isinstance(values, dict) or set(values) - defaults.keys():
            raise ValueError(f'Unknown {section} style option; use ' + ', '.join(defaults) + '.')
        result[section].update(copy.deepcopy(values))
    result['frame_enabled'] = data.get('frame_enabled', 'frame' in data)
    if not isinstance(result['frame_enabled'], bool):
        raise ValueError('frame_enabled must be true or false.')
    caption = result['caption']
    if caption['position'] not in ('top', 'bottom'):
        raise ValueError('Caption position must be top or bottom.')
    for section, key, limit in [('caption', 'margin', 0.4), ('frame', 'padding', 0.25), ('frame', 'radius', 64)]:
        number = result[section][key]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or not 0 <= number <= limit:
            raise ValueError(f'{section} {key} must be between 0 and {limit}.')
    for key in ('shadow', 'bar'):
        if not isinstance(result['frame'][key], bool):
            raise ValueError(f'Frame {key} must be true or false.')
    colour(caption['background'])
    colour(caption['foreground'])
    background(result['card']['background'])
    colour(result['card']['foreground'], alpha=False)
    background(result['frame']['background'])
    colour(result['frame']['bar_color'], alpha=False)
    return result


def read(path):
    return validate(tomllib.loads(Path(path).read_text()))


def dumps(data):
    data = validate(data)
    lines = [f'{key} = {quote(data[key])}\n' for key in ('schema_version', 'name', 'description', 'frame_enabled')]
    for section in ('caption', 'card', 'frame'):
        lines += [f'\n[{section}]\n', *[f'{key} = {quote(value)}\n' for key, value in data[section].items()]]
    return ''.join(lines)


def project(path):
    from reshoot.config import read as config_read
    config = Path(path) if Path(path).suffix == '.toml' else Path(path) / 'reshoot.toml'
    config = config.resolve()
    shoot, folder = config_read(config)
    boards = list(dict.fromkeys((folder / take['web']).resolve() for take in shoot.get('take', [])
                               if str(take.get('web', '')).endswith('.toml')))
    edit = shoot.get('edit', {}).get('file')
    if shoot.get('schema_version') != 1 or not boards or not edit or Path(edit).suffix != '.toml':
        raise ValueError('Visual styles need a versioned project with a TOML browser storyboard and edit file.')
    edit = (folder / edit).resolve()
    library = folder / LIBRARY
    if library in [config, edit, *boards] or edit in boards:
        raise ValueError('The style library, storyboard and edit file need separate paths.')
    return config, folder, boards, edit


def library(path):
    path = Path(path)
    if not path.exists():
        return {}
    data = tomllib.loads(path.read_text())
    if data.get('schema_version') != 1 or set(data) - {'schema_version', 'styles'} or not isinstance(data.get('styles', {}), dict):
        raise ValueError('The style library needs schema_version = 1 and a [styles] table.')
    result = {}
    for key, value in data.get('styles', {}).items():
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,59}', key) or key in BUILTINS:
            raise ValueError('Saved style names must use letters, numbers and hyphens and differ from the starting styles.')
        result[key] = validate(value)
    return result


def choices(folder):
    return {**copy.deepcopy(BUILTINS), **library(Path(folder) / LIBRARY)}


def resolve(value, folder):
    available = choices(folder)
    if value in available:
        return available[value]
    path = Path(value).expanduser()
    if path.is_file():
        return read(path)
    raise ValueError(f'No style {value!r}. Choose a listed style or a style TOML file.')


def snapshot(path, name='My style'):
    from reshoot import story, timeline
    _, _, boards, edit = project(path)
    board = story.load(boards[0])
    cut = tomllib.loads(edit.read_text())
    data = starting(name, '')
    data['caption'].update({k: v for k, v in board.get('caption', {}).items() if k in CAPTION})
    data['card'].update({k: v for k, v in cut.get('style', {}).items() if k in CARD})
    data['frame_enabled'] = 'frame' in cut
    if data['frame_enabled']:
        data['frame'].update(timeline.frame_style(cut))
    return validate(data)


def signature(spec):
    spec = copy.deepcopy(spec)
    for section in ('caption', 'card', 'frame'):
        for key, value in spec[section].items():
            if key in ('background', 'foreground', 'bar_color'):
                spec[section][key] = [colour(c) for c in value] if isinstance(value, list) else colour(value)
    return {key: spec[key] for key in ('caption', 'card', 'frame_enabled')} | (
        {'frame': spec['frame']} if spec['frame_enabled'] else {})


def selected(path, options):
    from reshoot import story
    current = snapshot(path)
    _, _, boards, _ = project(path)
    # A whole-project label must not describe only its first take.
    for board in boards:
        caption = {**CAPTION, **{k: v for k, v in story.load(board).get('caption', {}).items() if k in CAPTION}}
        if signature({**current, 'caption': caption}) != signature(current):
            return None
    return next((key for key, spec in options.items() if signature(current) == signature(spec)), None)


def set_table(lines, header, values):
    if block(lines, header) is None:
        at = first_header(lines)
        lines[at:at] = [header + '\n', '\n']
    for key, value in values.items():
        put(lines, block(lines, header), key, value)


def apply(path, spec):
    from reshoot import story, timeline
    from reshoot.config import read as config_read
    spec = validate(spec)
    config_path = (Path(path) if Path(path).suffix == '.toml' else Path(path) / 'reshoot.toml').resolve()
    config_before = config_path.read_bytes()
    config, _, boards, edit = project(path)
    before = {config: config_before, **{p: p.read_bytes() for p in [*boards, edit]}}
    changes = {}
    for board in boards:
        lines = read_lines(board)
        set_table(lines, '[caption]', spec['caption'])
        changes[board] = (''.join(lines), story.load)
    lines = read_lines(edit)
    set_table(lines, '[style]', spec['card'])
    if spec['frame_enabled']:
        set_table(lines, '[frame]', spec['frame'])
    elif span := block(lines, '[frame]'):
        del lines[span[0] - 1:span[1]]
    def check_edit(temp):
        data = tomllib.loads(temp.read_text())
        if data.get('schema_version') != 1 or not data.get('part'):
            raise ValueError('The edit needs schema_version = 1 and at least one part.')
        if 'frame' in data:
            timeline.frame_style(data)
    changes[edit] = (''.join(lines), check_edit)
    config_read(config)
    save_many(changes, before)


def save(path, name, output=None, replace=False):
    config, folder, boards, edit = project(path)
    before = {p: p.read_bytes() for p in [config, *boards, edit]}
    spec = snapshot(path, name)
    destination = Path(output).resolve() if output else folder / LIBRARY
    if destination in before:
        raise ValueError('A style export cannot overwrite a project source file.')
    if output and destination == (folder / LIBRARY).resolve():
        raise ValueError('Choose another export file; styles.toml is the project style library.')
    before[destination] = destination.read_bytes() if destination.exists() else None
    if output:
        if destination.exists() and not replace:
            raise ValueError('The style file exists. Choose another path or pass --replace.')
        text, check = dumps(spec), read
    else:
        saved = library(destination)
        key = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        if not key or key in BUILTINS:
            raise ValueError('Choose a different name from the starting styles, using some letters or numbers.')
        if key in saved and not replace:
            raise ValueError('A saved style already has this name. Choose another name or pass --replace.')
        lines = read_lines(destination) if destination.exists() else ['schema_version = 1\n', '\n', '[styles]\n']
        set_table(lines, '[styles]', {key: spec})
        text, check = ''.join(lines), library
    save_many({destination: (text, check)}, before)
    return destination


def main(a):
    _, folder, _, _ = project(a.project)
    if a.operation == 'list':
        for key, spec in choices(folder).items():
            print(f'{key}: {spec["name"]}' + (f': {spec["description"]}' if spec.get('description') else ''))
    elif a.operation == 'apply':
        spec = resolve(a.style, folder)
        apply(a.project, spec)
        print(f'Applied {spec["name"]}. Update the preview with reshoot recut or in the studio.')
    else:
        output = save(a.project, a.name, a.out, a.replace)
        print(f'Saved style to {output}')
    return 0
