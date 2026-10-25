"""Describe whether saved project edits are represented in the displayed recording."""
import functools
import hashlib
import json
import tomllib
from pathlib import Path

LABELS = {'project': 'Project settings', 'story': 'Story', 'edit': 'Cut, look or audio', 'input': 'Demo data',
          'capture_asset': 'Files used by the task', 'caption_asset': 'Caption font', 'soundtrack': 'Music',
          'edit_asset': 'Card images or fonts'}


@functools.lru_cache(maxsize=256)
def _digest(path, size, modified, changed):
    from reshoot.artifacts import digest
    return digest(path)


def file_hash(path):
    try:
        stat = path.stat()
        return _digest(str(path), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns) if path.is_file() else None
    except OSError:
        return None


def snapshot(project):
    path = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    raw = path.read_bytes()
    data = tomllib.loads(raw.decode())
    if data.get('schema_version') != 1:
        return None
    root, rows = path.parent, []
    def add(key, kind, source):
        source = Path(source).resolve()
        from reshoot.safety import describe
        rows.append({'key': key, 'kind': kind,
                     'path': str(source.relative_to(root)) if source.is_relative_to(root) else describe(str(source)),
                     'sha256': file_hash(source)})
    rows.append({'key': 'project', 'kind': 'project', 'path': path.name, 'sha256': hashlib.sha256(raw).hexdigest()})
    for i, take in enumerate(data.get('take', [])):
        source = take.get('web') or take.get('tape')
        if not source:
            continue
        board_path = root / source
        add(f'take:{i}', 'story', board_path)
        if 'web' in take and board_path.suffix == '.toml' and board_path.is_file():
            board = tomllib.loads(board_path.read_text())
            if board.get('caption', {}).get('font'):
                add(f'caption-font:{i}', 'caption_asset', board_path.parent / board['caption']['font'])
            actions = [*board.get('setup', []), *(action for beat in board.get('beat', []) for action in beat.get('action', []))]
            for n, action in enumerate(actions):
                if action.get('type') == 'upload' and action.get('file'):
                    add(f'upload:{i}:{n}', 'capture_asset', board_path.parent / action['file'])
    edit = data.get('edit', {}).get('file') or data.get('edit', {}).get('script')
    if edit:
        edit_path = root / edit
        add('edit', 'edit', edit_path)
        if edit_path.suffix == '.toml' and edit_path.is_file():
            cut = tomllib.loads(edit_path.read_text())
            if cut.get('music'):
                add('music', 'soundtrack', edit_path.parent / cut['music'])
            for name in ('font', 'logo'):
                if cut.get('style', {}).get(name):
                    add('card-' + name, 'edit_asset', edit_path.parent / cut['style'][name])
    for i, source in enumerate(data.get('inputs', [])):
        add(f'input:{i}', 'input', root / source)
    fingerprint = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return {'schema_version': 1, 'sha256': fingerprint, 'files': rows}


def changed(before, after):
    old = {row['key']: row for row in (before or {}).get('files', [])}
    new = {row['key']: row for row in (after or {}).get('files', [])}
    return sorted({(new.get(key) or old[key])['kind'] for key in old.keys() | new.keys() if old.get(key) != new.get(key)})


def capture_inputs(before, current):
    """Bind fixture/upload bytes after app reset, without adopting concurrent edits to recording scripts."""
    if not before or not current:
        return before
    refreshed = {row['key']: row for row in current['files'] if row['kind'] in ('input', 'capture_asset')}
    rows = [refreshed.get(row['key'], row) if row['kind'] in ('input', 'capture_asset') else row for row in before['files']]
    return {**before, 'files': rows, 'sha256': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()}


def capture_changes(project, run, current=None):
    """A re-cut may use new words/assets while retaining an older captured task and demo data."""
    from reshoot import story
    from reshoot.studio import recorded_as
    path = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    data = tomllib.loads(path.read_text())
    root, report = run
    inputs, kinds = report.get('inputs', {}), set()
    captured_config = inputs.get('recording_config_sha256')
    actual_config = hashlib.sha256(json.dumps({k: v for k, v in data.items() if k in ('app', 'take', 'inputs')}, sort_keys=True).encode()).hexdigest()
    if captured_config and captured_config != actual_config:
        kinds.add('project')
    if 'fixtures' in inputs and [row['sha256'] for row in inputs['fixtures']] != [file_hash(path.parent / source) for source in data.get('inputs', [])]:
        kinds.add('input')
    capture_state = inputs.get('capture_state')
    if capture_state:
        old = {row['key']: row for row in capture_state['files'] if row['kind'] in ('input', 'capture_asset')}
        new = {row['key']: row for row in (current or snapshot(project))['files'] if row['kind'] in ('input', 'capture_asset')}
        kinds.update((new.get(key) or old[key])['kind'] for key in old.keys() | new.keys() if old.get(key) != new.get(key))
    for take in data.get('take', []):
        if not str(take.get('web', '')).endswith('.toml'):
            source = take.get('web') or take.get('tape')
            originals = {row['sha256'] for row in inputs.get('stories', [])}
            if source and originals and file_hash(path.parent / source) not in originals:
                kinds.add('story')
            continue
        if not take.get('out'):
            continue
        meta_path = (root / take['out']).with_suffix('.take.json')
        if not meta_path.is_file():
            continue
        board = story.load(path.parent / take['web'])
        meta = json.loads(meta_path.read_text())
        original = meta.get('recording_settings_sha256')
        if original and original != hashlib.sha256(json.dumps(story.recording_settings(board), sort_keys=True).encode()).hexdigest():
            kinds.add('story')
        caps_path = meta_path.with_name(meta_path.name.removesuffix('.take.json') + '.captions.json')
        caps = json.loads(caps_path.read_text()) if caps_path.is_file() else {}
        rows = {row['beat']: row for row in caps.get('captions', [])}
        beats = meta.get('beats', [])
        if [beat['id'] for beat in beats] != [beat['id'] for beat in board['beat']] or any(
                previous.get('definition_sha256') and recorded_as(now, rows.get(now['id'])) != previous['definition_sha256']
                for previous, now in zip(beats, board['beat'])):
            kinds.add('story')
    return sorted(kinds)


def state(project, run):
    if not run:
        return {'known': True, 'pending': False, 'phase': 'empty', 'title': 'Make your first preview',
                'detail': 'Record the task, then shape the result here.', 'changes': [], 'next': 'update'}
    _, report = run
    before = report.get('inputs', {}).get('render_state')
    current = snapshot(project)
    known = bool(before and current)
    kinds = sorted(set(changed(before, current) if known else []) | set(capture_changes(project, run, current)))
    missing = bool(current and any(row['sha256'] is None for row in current['files']))
    pending = bool(kinds) or bool(known and before['sha256'] != current['sha256']) or missing
    if not known:
        # Old runs remain reviewable as exact recordings, without claiming a full source comparison.
        inputs = report.get('inputs', {})
        files = {row['key']: row for row in (current or {}).get('files', [])}
        pending |= any(inputs.get(old) and inputs[old] != files.get(key, {}).get('sha256')
                       for old, key in [('config_sha256', 'project'), ('edit_sha256', 'edit')])
    if pending:
        return {'known': known, 'pending': True, 'phase': 'pending', 'title': 'Saved edits are not in this recording yet',
                'detail': 'Update the preview to see your changes, or make a fresh final.',
                'changes': [LABELS[kind] for kind in kinds], 'next': 'update'}
    if not known:
        return {'known': False, 'pending': False, 'phase': 'unknown', 'title': 'Earlier recording',
                'detail': 'This version cannot compare all saved sources for this older run. Update preview to sync them.',
                'changes': [], 'next': 'update'}
    mode = report.get('mode', 'final')
    accepted = report.get('review_status') == 'completed'
    if report.get('review_status') == 'failed':
        return {'known': True, 'pending': False, 'phase': 'rejected', 'title': 'This recording was rejected',
                'detail': 'Fix the story or demo data, then record again.', 'changes': [], 'next': 'update'}
    return {'known': True, 'pending': False, 'phase': 'accepted' if accepted else 'preview' if mode != 'final' else 'review',
            'title': 'Accepted recording' if accepted else 'Your saved edits are in this preview' if mode != 'final' else 'Final ready for review',
            'detail': 'Download the shown exports when you need them.' if accepted else
                      'Make a final when the preview looks right.' if mode != 'final' else
                      'Watch the exports and inspect the scan evidence, then accept this recording.',
            'changes': [], 'next': 'download' if accepted else 'run' if mode != 'final' else 'review'}
