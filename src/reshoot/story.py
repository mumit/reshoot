"""Declarative storyboards with stable beats and explicit expected results.

A storyboard is a TOML file. `reshoot init` writes a complete one:

    schema_version = 1
    id = "notes"
    url = "http://127.0.0.1:8765/"
    size = "1280x720@1"            # CSS width x height @ device pixel ratio

    [[beat]]
    id = "search"                  # stable across releases, so runs can be compared
    caption = "Find the matching note"
    hold = 2.0                     # seconds to hold after the beat
    [[beat.action]]
    type = "type"                  # click, type, key, scroll, navigate, wait, upload
    target = {css = "#q"}          # or {test_id = "..."} or {role = "textbox", name = "Search"}
    text = "bike"
    [[beat.expect]]
    type = "count"                 # text, visible, count, value, url, checked
    target = {css = "#list li"}
    count = 1

Storyboards may also set theme, mobile, zoom, blur, setup, voice, seed, timeout and a [caption] style. A failed
expectation fails the take and saves evidence. guide/projects.md lists every field.
"""
import math
import re
import tomllib
from pathlib import Path

ACTIONS = {'click', 'type', 'key', 'scroll', 'navigate', 'wait', 'upload'}
EXPECT = {'text', 'visible', 'count', 'value', 'url', 'checked'}


def target(value):
    if not isinstance(value, dict) or sum(k in value for k in ('css', 'test_id', 'role')) != 1:
        raise ValueError('target needs exactly one of css, test_id, or role')
    if set(value) - {'css', 'test_id', 'role', 'name', 'frame', 'text'}:
        raise ValueError('unknown target option')
    if not all(isinstance(v, str) and v for v in value.values()):
        raise ValueError('target values must be nonempty strings')


def load(path):
    data = tomllib.loads(Path(path).read_text())
    if data.get('schema_version') != 1:
        raise ValueError('storyboard needs schema_version = 1')
    if set(data) - {'schema_version', 'id', 'url', 'size', 'theme', 'zoom', 'blur', 'beat', 'setup', 'voice', 'voice_engine', 'timeout', 'seed', 'mobile', 'caption'}:
        raise ValueError('unknown storyboard option')
    if not data.get('beat'):
        raise ValueError('storyboard has no beats')
    caption = data.get('caption', {})
    if set(caption) - {'position', 'margin', 'min_seconds', 'font', 'background', 'foreground'}:
        raise ValueError('unknown caption style option')
    if caption.get('position', 'bottom') not in ('top', 'bottom'):
        raise ValueError('caption position must be top or bottom')
    margin = caption.get('margin', .065)
    if not isinstance(margin, (int,float)) or not math.isfinite(margin) or not 0 <= margin < .4:
        raise ValueError('caption margin must be between 0 and 0.4')
    minimum = caption.get('min_seconds', 0)
    if not isinstance(minimum, (int,float)) or not math.isfinite(minimum) or minimum < 0:
        raise ValueError('caption min_seconds must be nonnegative')
    seen = set()
    for beat in data['beat']:
        name = beat.get('id', '')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', name) or name in seen:
            raise ValueError('beat IDs must be unique letters, digits, underscores, or hyphens')
        seen.add(name)
        if set(beat) - {'id', 'purpose', 'caption', 'sub', 'hold', 'action', 'expect', 'trim_wait', 'min_reading'}:
            raise ValueError(f'unknown option in beat {name}')
        hold = beat.get('hold', 1)
        if not isinstance(hold, (int, float)) or not math.isfinite(hold) or hold < 0:
            raise ValueError(f'invalid hold in beat {name}')
        reading = beat.get('min_reading', 0)
        if not isinstance(reading, (int, float)) or not math.isfinite(reading) or reading < 0:
            raise ValueError('min_reading must be nonnegative')
        if beat.get('trim_wait') and not beat.get('expect'):
            raise ValueError('trimmable waits need an expected result')
        for entry in beat.get('action', []):
            validate(entry, ACTIONS)
        for entry in beat.get('expect', []):
            validate(entry, EXPECT)
    for entry in data.get('setup', []):
        validate(entry, ACTIONS)
    if set(data.get('voice', {})) - seen:
        raise ValueError('voice names an unknown beat')
    if data.get('timeout', 600) <= 0:
        raise ValueError('story timeout must be positive')
    return data


def validate(entry, allowed):
    kind = entry.get('type')
    if kind not in allowed:
        raise ValueError(f'unsupported operation {kind!r}')
    options = {'click': set(), 'type': {'text', 'clear'}, 'key': {'key'}, 'scroll': {'dy'},
               'navigate': {'url'}, 'wait': set(), 'upload': {'file'}, 'text': {'contains'},
               'visible': set(), 'count': {'count'}, 'value': {'value'}, 'url': {'contains'}, 'checked': {'checked'}}
    if set(entry) - ({'type', 'target', 'timeout'} | options[kind]):
        raise ValueError('unknown operation option')
    if kind not in {'navigate', 'scroll', 'url'}:
        target(entry.get('target'))
    required = {'type': 'text', 'key': 'key', 'navigate': 'url', 'text': 'contains', 'count': 'count', 'value': 'value', 'upload': 'file', 'url': 'contains'}
    if kind in required and required[kind] not in entry:
        raise ValueError(f'{kind} needs {required[kind]}')
    timeout = entry.get('timeout', 10000)
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('operation timeout must be positive')
    if kind == 'count' and (not isinstance(entry['count'], int) or entry['count'] < 0):
        raise ValueError('expected count must be a nonnegative integer')
