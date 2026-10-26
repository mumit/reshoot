"""Narration auditioning and audio balance, shared by the CLI and studio."""
import functools
import math
import platform
import re
import shlex
import shutil
import subprocess
import tomllib
from pathlib import Path

DEFAULTS = {'voice_volume': 1.0, 'music_volume': 0.25, 'duck': True}


def settings(value=None):
    if not isinstance(value if value is not None else {}, dict):
        raise ValueError('audio must be a table with voice_volume, music_volume and duck.')
    result = {**DEFAULTS, **(value or {})}
    if set(result) - set(DEFAULTS):
        raise ValueError('Unknown audio setting; use voice_volume, music_volume or duck.')
    for key, maximum in [('voice_volume', 2), ('music_volume', 1)]:
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= maximum:
            raise ValueError(f'{key} must be between 0 and {maximum}.')
    if type(result['duck']) is not bool:
        raise ValueError('duck must be true or false.')
    return result


def load(project):
    from reshoot.config import read
    config = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    original = config.read_bytes()
    shoot, folder = read(config)
    takes = [folder / t['web'] for t in shoot.get('take', []) if str(t.get('web', '')).endswith('.toml')]
    edit = shoot.get('edit', {}).get('file')
    if shoot.get('schema_version') != 1 or not takes or not edit or Path(edit).suffix != '.toml':
        raise ValueError('Audio controls need a versioned project with a TOML browser take and edit.')
    edit = (folder / edit).resolve()
    paths = [*takes, edit, folder / 'styles.toml']
    before = {p.resolve(): p.read_bytes() if p.exists() else None for p in paths}
    before[config] = original
    return config, folder, takes[0].resolve(), edit, before


def apply(project, change, expected=None):
    from reshoot import story
    from reshoot.sequence import check_cut
    from reshoot.workspace import block, first_header, put, read_lines, save_many
    if not isinstance(change, dict) or not change or set(change) - {'beat', 'text', 'engine', 'mix'}:
        raise ValueError('Change a narration line, voice or audio mix.')
    _, _, board_path, edit_path, before = load(project)
    before.update(expected or {})
    board = story.load(board_path)
    changes = {}
    if 'text' in change or 'beat' in change or 'engine' in change:
        lines = read_lines(board_path)
        if 'text' in change or 'beat' in change:
            beat, text = change.get('beat'), change.get('text')
            if beat not in [b['id'] for b in board['beat']]:
                raise ValueError('Choose a beat from this storyboard.')
            if not isinstance(text, str) or len(text) > 4000:
                raise ValueError('A narration line must be text of at most 4000 characters.')
            text = ' '.join(text.split())
            span = block(lines, '[voice]')
            if span:
                # Existing files may quote beat keys. Keep that spelling and its comment.
                key = next((m[1] for line in lines[span[0]:span[1]] if (m := re.match(
                    rf'\s*({re.escape(beat)}|"{re.escape(beat)}"|\'{re.escape(beat)}\')\s*=', line))), beat)
                put(lines, span, key, text or None)
            else:
                voice = dict(board.get('voice', {}))
                if text:
                    voice[beat] = text
                else:
                    voice.pop(beat, None)
                put(lines, (0, first_header(lines)), 'voice', voice or None)
        if 'engine' in change:
            engine = change['engine']
            if engine is not None and (not isinstance(engine, str) or not engine.strip() or len(engine) > 2000):
                raise ValueError('Choose a voice, or use the system default.')
            if engine:
                from reshoot.voice import engine_command
                try:
                    engine_command(engine)
                except SystemExit as error:
                    raise ValueError(str(error)) from None
            put(lines, (0, first_header(lines)), 'voice_engine', engine)
        changes[board_path] = (''.join(lines), story.load)
    if 'mix' in change:
        mix = change['mix']
        if not isinstance(mix, dict) or not mix or set(mix) - set(DEFAULTS):
            raise ValueError('Change voice_volume, music_volume or duck.')
        lines = read_lines(edit_path)
        current = tomllib.loads(''.join(lines))
        settings({**current.get('audio', {}), **mix})
        if block(lines, '[audio]'):
            for key, value in mix.items():
                put(lines, block(lines, '[audio]'), key, value)
        elif 'audio' in current:
            put(lines, (0, first_header(lines)), 'audio', {**current['audio'], **mix})
        else:
            lines += ['\n', '[audio]\n']
            for key, value in mix.items():
                put(lines, block(lines, '[audio]'), key, value)
        changes[edit_path] = (''.join(lines), check_cut)
    save_many(changes, before)


@functools.lru_cache(maxsize=1)
def voices():
    """Discover installed local voices only; custom project commands remain file/CLI settings."""
    result = {'': 'System default'}
    from importlib.util import find_spec
    if find_spec('kokoro'):
        from reshoot.kokoro import VOICES
        result.update({f'kokoro --voice {name}': f'Kokoro · {label}' for name, label in VOICES.items()})
    try:
        if platform.system() == 'Darwin' and shutil.which('say'):
            output = subprocess.run(['say', '-v', '?'], capture_output=True, text=True, timeout=5, check=True).stdout
            for line in output.splitlines():
                if match := re.match(r'(.+?)\s+([a-z]{2}_[A-Z]{2})\s+#', line):
                    name, language = match.groups()
                    result['say -v ' + shlex.quote(name.strip())] = f'{name.strip()} ({language})'
        else:
            command = next((name for name in ('espeak-ng', 'espeak') if shutil.which(name)), None)
            if command:
                output = subprocess.run([command, '--voices'], capture_output=True, text=True, timeout=5, check=True).stdout
                for line in output.splitlines()[1:]:
                    fields = line.split()
                    if len(fields) >= 4 and re.fullmatch(r'[\w+-]+', fields[3]):
                        result[command + ' -v ' + fields[3]] = f'{fields[3]} ({fields[1]})'
    except (OSError, subprocess.SubprocessError):
        pass
    return result


def audition_spec(project, beat):
    from reshoot import story, voice
    _, folder, path, _, _ = load(project)
    board = story.load(path)
    if beat not in [b['id'] for b in board['beat']]:
        raise ValueError('Choose a beat from this storyboard.')
    text = board.get('voice', {}).get(beat)
    if not text:
        raise ValueError('Save a narration line for this beat before auditioning it.')
    engine = board.get('voice_engine')
    try:
        key = voice.cache_key(text, engine)
    except SystemExit as error:
        raise ValueError(str(error)) from None
    return {'text': text, 'engine': engine, 'file': folder / 'takes' / 'voice-cache' / (key + '.wav'), 'key': key}


def audition(project, beat, expected_key=None):
    from reshoot import voice
    spec = audition_spec(project, beat)
    if expected_key is not None and expected_key != spec['key']:
        raise ValueError('The saved narration changed. Reload before auditioning it.')
    path, seconds = voice.prepare({beat: spec['text']}, spec['file'].parent, spec['engine'],
                                 cwd=spec['file'].parent.parent.parent)[beat]
    return Path(path), seconds


def main(a):
    if a.operation == 'audition':
        path, seconds = audition(a.project, a.beat, getattr(a, 'expected_key', None))
        print(f'{path}\n{seconds:.2f} seconds; this saved line will use the same cached voice when recording.')
        return 0
    change = {}
    if a.beat is not None or a.text is not None:
        change.update(beat=a.beat, text=a.text)
    if a.engine is not None:
        change['engine'] = a.engine or None
    mix = {k: getattr(a, k) for k in DEFAULTS if getattr(a, k) is not None}
    if mix:
        change['mix'] = mix
    apply(a.project, change)
    print('Saved audio settings. Update preview to hear the mix; narration or voice changes record the full task again.')
    return 0
