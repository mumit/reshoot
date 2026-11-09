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
    if mode == 'preview' and not accepted and not report.get('recut_from') and len(list(run[0].parent.glob('*/run.json'))) == 1:
        checks = report.get('expectations_count', 0)
        passed = f', and {"its result check" if checks == 1 else "both result checks" if checks == 2 else f"all {checks} result checks"} passed' if checks else ''
        return {'known': True, 'pending': False, 'phase': 'preview', 'first': True, 'title': 'Your first demo is ready',
                'detail': f'Recorded in {round(report.get("seconds", 0))} seconds{passed}. Watch it, try a new caption, '
                          'or choose Make final when it looks right.', 'changes': [], 'next': 'run'}
    return {'known': True, 'pending': False, 'phase': 'accepted' if accepted else 'preview' if mode != 'final' else 'review',
            'title': 'Accepted recording' if accepted else 'Your preview is up to date' if mode != 'final' else 'Final ready for review',
            'detail': 'Download the shown exports when you need them.' if accepted else
                      'Make a final when the preview looks right.' if mode != 'final' else
                      'Watch the exports and inspect the scan evidence, then accept this recording.',
            'changes': [], 'next': 'download' if accepted else 'run' if mode != 'final' else 'review'}


ACTION_LABELS = {
    'update': 'Update preview', 'run': 'Make final', 'create': 'Continue creation',
    'setup': 'Check again', 'session': 'Review saved history', 'review': 'Review this final',
    'download': 'Get your files', 'preview': 'Record app again', 'from': 'Record from here',
    'recut': 'Re-cut', 'repair': 'Repair control', 'demonstrate': 'Show changed actions',
    'audition': 'Audition saved line', 'edit': 'Edit the project', 'accept': 'Accept this recording',
    'cancel': 'Cancel update',
}
RECORDING_ACTIONS = {'update', 'run', 'preview', 'from', 'recut', 'repair', 'demonstrate'}
CREATION_BLOCKS = {'update', 'run', 'preview', 'from', 'recut'}


def permissions(*, creating=False, tools=None, session=None, job=None, has_run=False,
                pending=False, mode='final'):
    """Capabilities shared by page controls, HTTP guards and status output.

    Tool readiness may be unknown for read-only inspection. Execution checks the
    actual tools. Browsing/downloading earlier evidence never needs recording tools.
    """
    busy = bool(job and job.get('running'))
    actions = {}
    for kind, label in ACTION_LABELS.items():
        reason = ''
        if kind == 'cancel':
            if job is None:
                reason = 'Live jobs are not observed here. Use the studio to cancel an update.'
            elif not (busy and job.get('cancelable', True)):
                reason = 'No cancellable job is running.'
        elif kind in ('review', 'download'):
            if not has_run:
                reason = 'Record a complete preview or final first.'
        elif busy:
            reason = 'An update is running. Wait for it or cancel before changing the project.'
        elif kind == 'session':
            if not session:
                reason = 'No saved history needs recovery.'
        elif session:
            reason = 'Resolve the saved editing history first.'
        elif kind in RECORDING_ACTIONS | {'create'} and tools is not None and not tools['ok']:
            reason = 'Fix the recording tools, then choose Check again.'
        elif creating and kind in CREATION_BLOCKS:
            reason = 'Finish the first preview with Continue creation.'
        elif kind == 'create' and not creating:
            reason = 'No paused creation here. Use Update preview to refresh this project.'
        elif kind in ('recut', 'accept') and not has_run:
            reason = 'Record a complete preview or final first.'
        elif kind == 'accept' and pending:
            reason = 'Saved edits are not in this recording yet. Update preview or make a final before accepting here.'
        elif kind == 'accept' and mode != 'final':
            reason = 'This is a preview. Make a final before accepting here.'
        actions[kind] = {'kind': kind, 'label': label, 'enabled': not reason, 'reason': reason}
    return actions


def workflow(saved, *, creating=False, tools=None, failure=None, session=None, has_run=False,
             job=None, mode='final'):
    """Compose independent lifecycles; never persist this derived display state."""
    out = dict(saved)
    continuation = 'create' if creating else 'update'
    tools_missing = tools is not None and not tools['ok']
    out['actions'] = permissions(creating=creating, tools=tools, session=session, job=job,
                                has_run=has_run, pending=saved.get('pending', False), mode=mode)
    out['continuation'] = out['actions'][continuation]
    if creating:
        out.update(phase='creation', next='create', title='Continue your first demo',
                   detail='Your story is saved. Choose Continue creation to make its preview.')
    if failure:
        again = ACTION_LABELS[continuation]
        if failure.get('repaired'):
            detail = f'Control updated. Choose {again} to verify the original task and result checks.'
        elif failure.get('stale'):
            detail = f'The story changed since this failure. Choose {again} to get current evidence.'
        else:
            detail = f'Fix the step it stopped on, below, then choose {again}.'
        out.update(title='The latest recording stopped' if has_run else 'The first preview stopped',
                   phase='stopped', next=continuation,
                   detail=detail + (' The video is the last recording that worked.' if has_run else ''))
    if tools_missing:
        out.update(phase='setup', next='setup', title='Recording tools need attention',
                   detail='Fix the recording tools, then choose Check again.')
    if session:
        out.update(phase='recovery', next='session', title=session['title'], detail=session['detail'])
    busy = bool(job and job.get('running'))
    if busy:
        cancelling = job.get('state') == 'cancelling'
        kept = 'Your previous recording is kept.' if has_run else 'Your saved story is kept.'
        out.update(phase='busy', next='cancel', title='Cancelling the update' if cancelling else 'An update is running',
                   detail=('Wait for it to finish. ' if not job.get('cancelable', True) else
                           'Wait for it to finish, or cancel the update. ') + kept)
    if creating or failure or tools_missing or session or busy:
        out.pop('first', None)
    out['action'] = out['actions'][out['next']]
    out['states'] = {
        'source': saved.get('states', {}).get('source', saved.get('phase', 'unknown')),
        'creation': 'pending' if creating else 'inactive',
        'tools': 'unknown' if tools is None else 'blocked' if tools_missing else 'ready',
        'history': 'recovery' if session else 'ready',
        'failure': 'none' if not failure else 'repaired' if failure.get('repaired') else
                   'stale' if failure.get('stale') else 'active',
        'job': job.get('state', 'running' if busy else 'idle') if job else 'unobserved',
    }
    return out


def recorded_as(beat, row):
    """Whether a storyboard beat still has the actions, checks and holds it was recorded with: its definition hash,
    with the captions it was recorded with put back, since those are drawn again on a re-cut."""
    probe = dict(beat)
    if row is not None:
        for key, value in (('caption', row.get('recorded')), ('sub', row.get('recorded_sub'))):
            if value is None:
                probe.pop(key, None)
            else:
                probe[key] = value
    return hashlib.sha256(json.dumps(probe, sort_keys=True).encode()).hexdigest()


def update_kind(folder, config, take, run):
    """Caption and edit changes reuse a take; recording changes replay the app. Fail closed when unsure."""
    from reshoot import story
    from reshoot.artifacts import digest
    from reshoot.config import read
    if not run:
        return 'preview', 'Recording the first preview.'
    root, report = run
    if capture_changes(config, run):
        return 'preview', 'The task, timing, narration or demo data changed; recording a fresh preview.'
    shoot, _ = read(config)
    capture_config = {k: v for k, v in shoot.items() if k in ('app', 'take', 'inputs')}
    if report.get('inputs', {}).get('recording_config_sha256') != hashlib.sha256(json.dumps(capture_config, sort_keys=True).encode()).hexdigest():
        return 'preview', 'Project settings changed; recording a new preview.'
    recorded = report.get('inputs', {}).get('fixtures', [])
    if [r['sha256'] for r in recorded] != [digest(Path(folder) / p) for p in shoot.get('inputs', [])]:
        return 'preview', 'Demo data changed; recording a new preview.'
    # A multi-take project may have changes outside the first storyboard shown here.
    if len(shoot.get('take', [])) != 1:
        return 'preview', 'Recording all takes in this project.'
    source = root / take['out']
    meta_path, caps_path = source.with_suffix('.take.json'), source.with_suffix('.captions.json')
    if not meta_path.exists() or not caps_path.exists():
        return 'preview', 'Recording a take with editable captions.'
    board = story.load(Path(folder) / take['web'])
    meta, caps = json.loads(meta_path.read_text()), json.loads(caps_path.read_text())
    rows = {r['beat']: r for r in caps['captions']}
    beats = {b['id']: b for b in meta['beats']}
    if list(beats) != [b['id'] for b in board['beat']] or any(
            recorded_as(b, rows.get(b['id'])) != beats[b['id']].get('definition_sha256') for b in board['beat']):
        return 'preview', 'Actions, checks or timing changed; recording a new preview.'
    original = meta.get('recording_settings_sha256')
    settings = story.recording_settings(board)
    if original != hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest():
        return 'preview', 'Recording settings changed; recording a new preview.'
    words_changed = any((b.get('caption') or None, b.get('sub') or None) !=
                        (rows[b['id']].get('text', rows[b['id']].get('recorded')),
                         rows[b['id']].get('sub', rows[b['id']].get('recorded_sub'))) for b in board['beat'])
    edit_changed = shoot.get('edit', {}).get('file') and report.get('inputs', {}).get('edit_sha256') != digest(Path(folder) / shoot['edit']['file'])
    sources_changed = changed(report.get('inputs', {}).get('render_state'), snapshot(config)) if report.get('inputs', {}).get('render_state') else []
    if not (words_changed or caps.get('style', {}) != board.get('caption', {}) or edit_changed or sources_changed
            or report.get('inputs', {}).get('config_sha256') != digest(config)):
        return 'preview', 'Recording the app again for a fresh preview.'
    return 'recut', 'Updating captions and the edit using the existing recording.'
