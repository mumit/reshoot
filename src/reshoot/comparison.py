"""Read-only comparison of checked result frames from two exact local runs."""
import hashlib
import json
import re
import threading
from collections import OrderedDict
from pathlib import Path

_verified = OrderedDict()
_lock = threading.RLock()


def root_for(project, run_id):
    from reshoot.review import runs_folder
    if not isinstance(run_id, str) or not re.fullmatch(r'[0-9a-f]{32}', run_id):
        raise ValueError('Choose a local recording to compare.')
    folder = runs_folder(project).resolve()
    root = (folder / run_id).resolve()
    if root.parent != folder:
        raise ValueError('The recording is outside this project.')
    return root


def stamp(root, report):
    names = ['run.json', *[row['path'] for row in report.get('files', [])],
             'review/report.json', 'review/key.json', 'review/flags.json']
    values = []
    for name in names:
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise ValueError('A recording artifact is outside its run.')
        try:
            stat = path.stat()
            values.append((name, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))
        except FileNotFoundError:
            values.append((name, None))
    return tuple(values)


def read(project, run_id, binding):
    """Verify all run artifacts after a file change; repeated image loads reuse that verification."""
    from reshoot import review
    root = root_for(project, run_id)
    report = json.loads((root / 'run.json').read_text())
    if report.get('id') != run_id or not report.get('ok') or report.get('mode') == 'partial-preview' or report.get('record'):
        raise ValueError('Comparison needs a complete successful local recording with its media.')
    signature = stamp(root, report)
    if review.binding(root, report) != binding:
        raise ValueError('This recording or its scan changed. Reload before comparing it.')
    with _lock:
        if _verified.get(str(root)) != signature:
            _, report = review.read(root)
            if stamp(root, report) != signature:
                raise ValueError('The recording changed while loading. Reload to compare again.')
            _verified[str(root)] = signature
            _verified.move_to_end(str(root))
            while len(_verified) > 16:
                _verified.popitem(last=False)
    return root, report


def choices(project, current):
    from reshoot import review
    if not current or current[1].get('mode') == 'partial-preview':
        return {'choices': [], 'default': '', 'note': 'Make two complete recordings to compare checked result frames.'}
    rows, seen = [], False
    for root, report in review.runs(project):
        if root.name == current[1]['id']:
            seen = True
            continue
        if not seen or not report.get('ok') or report.get('mode') == 'partial-preview' or report.get('record'):
            continue
        try:
            root_for(project, root.name)
            if report.get('id') != root.name:
                continue
            stamp(root.resolve(), report)
            token = review.binding(root, report)
        except (ValueError, OSError, TypeError):
            continue
        rows.append({'id': root.name, 'binding': token, 'mode': report.get('mode', 'final'),
                     'accepted': report.get('review_status') == 'completed', 'finished_at': report['finished_at']})
        if len(rows) == 30:
            break
    selected = next((row for row in rows if row['accepted']), rows[0] if rows else None)
    return {'choices': rows, 'default': selected['id'] if selected else '',
            'note': 'Choose from up to 30 earlier complete local runs. An accepted run is preferred.' if rows else
                    'No earlier complete local recording is available. Record the task again to compare it.'}


def evidence(run):
    root, report = run
    named = {row['path']: row['sha256'] for row in report.get('files', [])}
    result = {}
    for name in sorted(named):
        if not name.endswith('.take.json'):
            continue
        path = root / name
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != named[name]:
            raise ValueError('Take evidence changed while loading. Reload before comparing.')
        data = json.loads(raw)
        prefix = data.get('story_id') or path.stem
        for beat in data.get('beats', []):
            key = str(prefix) + '/' + beat['id']
            if key in result:
                raise ValueError('Several takes share a story/beat ID. Give stories distinct IDs before comparing them.')
            checks = beat.get('expectations', [])
            frame, reason = None, 'No passing result checks for this step.'
            checked = (data.get('status') == 'completed' and data.get('mode') != 'partial'
                       and beat.get('status') == 'passed' and checks and all(row.get('status') == 'passed' for row in checks))
            if checked:
                source = path.with_suffix('').with_suffix('.mp4')
                expected = source.with_suffix('.evidence') / (beat['id'] + '.png')
                shot = (path.parent / beat.get('screenshot', '')).resolve()
                if shot == expected.resolve() and shot.is_relative_to(root) and str(shot.relative_to(root)) in named:
                    frame = {'path': str(shot.relative_to(root)), 'sha256': named[str(shot.relative_to(root))],
                             'checks': len(checks)}
                    reason = ''
                else:
                    reason = 'The checked frame is missing or not bound to this recording.'
            result[key] = {'id': beat['id'], 'purpose': beat.get('purpose') or beat['id'],
                           'status': beat.get('status', 'unverified'), 'frame': frame, 'reason': reason,
                           'definition': beat.get('definition_sha256'), 'start': beat.get('start'), 'end': beat.get('end'),
                           'results': [{k: value for k, value in row.items() if k != 'at'} for row in checks]}
    return result


def identity(run):
    from reshoot import review
    root, report = run
    return {'id': report['id'], 'binding': review.binding(root, report), 'mode': report.get('mode', 'final'),
            'status': review.status(root, report),
            'review': f'comparison-review/{report["id"]}/{review.binding(root, report)}/review.html'}


def model(project, current_id, current_binding, previous_id, previous_binding):
    if current_id == previous_id:
        raise ValueError('Choose a different earlier recording.')
    current = read(project, current_id, current_binding)
    previous = read(project, previous_id, previous_binding)
    before, after = evidence(previous), evidence(current)
    identities = {'previous': identity(previous), 'current': identity(current)}
    if identities['previous']['binding'] != previous_binding or identities['current']['binding'] != current_binding:
        raise ValueError('The scan changed while loading. Reload before comparing.')
    rows = []
    for key in dict.fromkeys([*before, *after]):
        old, new = before.get(key), after.get(key)
        if not ((old and old['results']) or (new and new['results'])):
            continue
        sides = {}
        for side, beat in [('previous', old), ('current', new)]:
            if beat is None:
                sides[side] = None
                continue
            value = {k: beat[k] for k in ('id', 'purpose', 'status', 'reason', 'start', 'end')}
            value['frame'] = None
            if beat['frame']:
                frame = beat['frame']
                run = identities[side]
                value['frame'] = {**frame, 'src': f'comparison-frame/{run["id"]}/{run["binding"]}/{frame["sha256"]}.png'}
            sides[side] = value
        frames = bool(old and new and old['frame'] and new['frame'])
        rows.append({'beat': key, **sides, 'change': 'added' if old is None else 'removed' if new is None else 'matched',
                     'frame_changed': old['frame']['sha256'] != new['frame']['sha256'] if frames else None,
                     'definition_changed': old['definition'] != new['definition'] if old and new and old['definition'] and new['definition'] else None,
                     'results_changed': old['results'] != new['results'] if old and new else None})
    return {**identities, 'beats': rows, 'note': 'Captured result frames retain privacy masks. They do not include later captions, zoom, framing, cards or cuts. Inspect the exports and scan evidence in both review pages.'}


def frame(project, run_id, binding, sha256):
    run = read(project, run_id, binding)
    selected = next((beat['frame'] for beat in evidence(run).values()
                     if beat['frame'] and beat['frame']['sha256'] == sha256), None)
    if selected is None:
        raise ValueError('No checked frame with this hash belongs to the recording.')
    raw = (run[0] / selected['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError('The checked frame changed. Reload to compare again.')
    return raw
