"""Separate, reviewed action drafts. Applying one preserves every existing result check."""
import difflib
import hashlib
import json
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from reshoot.workspace import History, put, quote, save_many, tables


def context(project):
    from reshoot import studio
    from reshoot.config import read
    config, folder, take = studio.project(project)
    shoot, _ = read(config)
    paths = [config, *dict.fromkeys((folder / item['web']).resolve() for item in shoot.get('take', [])
                                   if str(item.get('web', '')).endswith('.toml')), folder / 'styles.toml']
    if shoot.get('edit', {}).get('file'):
        paths.append((folder / shoot['edit']['file']).resolve())
    return {'config':config, 'folder':folder, 'take':take, 'paths':paths, 'shoot':shoot,
            'board_path':(folder / take['web']).resolve()}


def name(path, folder):
    return str(path.relative_to(folder)) if path.is_relative_to(folder) else str(path)


def storage(folder):
    root = (folder / 'takes/demonstrations').resolve()
    if not root.is_relative_to(folder.resolve()):
        raise ValueError('Demonstration drafts must stay inside the project.')
    return root


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.draft-', delete=False) as file:
        pending = Path(file.name)
        file.write(json.dumps(data, indent=2).encode())
    try:
        pending.chmod(0o600); pending.replace(path)
    finally:
        pending.unlink(missing_ok=True)


def begin(project, beat, mode='replace', draft_id=None, expected_revision=None):
    from reshoot import story
    data = context(project)
    if mode not in ('replace', 'before', 'after'):
        raise ValueError('Choose replace, before or after for the demonstration.')
    history = History(data['paths'])
    if expected_revision is not None:
        history.check(expected_revision)
    before = history.snapshot()
    fresh = context(project)
    if fresh['paths'] != data['paths'] or fresh['shoot'] != data['shoot'] or fresh['take'] != data['take']:
        raise ValueError('The project changed before recording. Reload and demonstrate the current story.')
    board = story.load(data['board_path'])
    if not any(row['id'] == beat for row in board['beat']):
        raise ValueError('Choose an existing story step.')
    if len(before[data['board_path']]) > 2 * 1024 * 1024:
        raise ValueError('This story is too large for a reviewed step draft. Change it in the file.')
    ident = draft_id or uuid.uuid4().hex
    if not isinstance(ident, str) or not re.fullmatch(r'[0-9a-f]{32}', ident):
        raise ValueError('Choose a valid demonstration draft ID.')
    root = storage(data['folder']) / ident
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    source = root / 'before.toml'
    source.write_bytes(before[data['board_path']]); source.chmod(0o600)
    meta = {'schema_version':1, 'id':ident, 'config':data['config'].name,
            'story':name(data['board_path'], data['folder']), 'beat':beat, 'mode':mode, 'status':'recording',
            'created_at':datetime.now(timezone.utc).isoformat(),
            'expected':{name(path, data['folder']):hashlib.sha256(value).hexdigest() if value is not None else None
                        for path, value in before.items()}}
    write(root / 'draft.json', meta)
    if history.snapshot() != before:
        fail({**data, 'root':root, 'meta':meta}, ValueError('The source changed before recording. Record again from the current story.'))
        raise ValueError('The source changed before recording. The story is kept.')
    return {**data, 'root':root, 'meta':meta, 'board':story.load(source)}


def bounds(lines, board, beat):
    heads = tables(lines, '[[beat]]')
    if len(heads) != len(board['beat']):
        raise ValueError('This story uses complex table formatting. Change its actions in the file.')
    index = next(i for i, row in enumerate(board['beat']) if row['id'] == beat)
    start = heads[index][0]
    end = heads[index + 1][0] if index + 1 < len(heads) else len(lines)
    # Global tables after the last beat are not part of that beat.
    for i in range(start + 1, end):
        text = lines[i].strip().split('#', 1)[0].strip()
        if re.fullmatch(r'\[\[?[\w.-]+\]\]?', text) and not text.startswith(('[beat.', '[[beat.')):
            end = i; break
    return index, start, end


def _entries(header, rows):
    return [line for row in rows for line in ['\n', header + '\n', *[f'{key} = {quote(value)}\n' for key, value in row.items()]]]


def proposed(before, board, beat, mode, actions, checks, caption):
    lines = before.splitlines(keepends=True)
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    index, start, end = bounds(lines, board, beat)
    if mode == 'replace':
        # Include nested target/fallback tables in the action being removed.
        spans = []
        for head, _, _ in tables(lines, '[[beat.action]]'):
            if not start < head < end:
                continue
            stop = end
            for i in range(head + 1, end):
                text = lines[i].strip().split('#', 1)[0].strip()
                if re.fullmatch(r'\[\[?[\w.-]+\]\]?', text) and not text.startswith(('[beat.action.', '[[beat.action.')):
                    stop = i; break
            spans.append((head, stop))
        at = spans[0][0] if spans else next((head for head, _, _ in tables(lines, '[[beat.expect]]') if start < head < end), end)
        for head, stop in reversed(spans):
            del lines[head:stop]
        lines[at:at] = _entries('[[beat.action]]', actions)
        # Keep all existing checks byte for byte; add only explicit new checks.
        _, _, end = bounds(lines, board, beat)
        additions = [row for row in checks if row not in board['beat'][index].get('expect', [])]
        lines[end:end] = _entries('[[beat.expect]]', additions)
        span = tables(lines, '[[beat]]')[index][1:]
        put(lines, span, 'recording_issue', None)
    else:
        used = {row['id'] for row in board['beat']}
        base = 'step-' + beat[:40]
        ident, n = base, 2
        while ident in used:
            ident = f'{base}-{n}'; n += 1
        at = end if mode == 'after' else start
        inserted = ['\n', '[[beat]]\n', f'id = {quote(ident)}\n', f'caption = {quote(caption)}\n', 'hold = 1.5\n']
        lines[at:at] = [*inserted, *_entries('[[beat.action]]', actions), *_entries('[[beat.expect]]', checks), '\n']
    return ''.join(lines)


def validate_change(before, after, meta):
    old, new = before['beat'], after['beat']
    if {k:v for k,v in before.items() if k != 'beat'} != {k:v for k,v in after.items() if k != 'beat'}:
        raise ValueError('A step draft cannot change global story settings.')
    index = next(i for i, row in enumerate(old) if row['id'] == meta['beat'])
    if meta['mode'] == 'replace':
        if len(old) != len(new) or old[:index] != new[:index] or old[index+1:] != new[index+1:]:
            raise ValueError('A replacement cannot change other steps.')
        previous, current = old[index], new[index]
        if {k:v for k,v in previous.items() if k not in ('action', 'expect', 'recording_issue')} != {
                k:v for k,v in current.items() if k not in ('action', 'expect', 'recording_issue')}:
            raise ValueError('A replacement must preserve this step\'s words, timing and identity.')
        checks = previous.get('expect', [])
        if current.get('expect', [])[:len(checks)] != checks:
            raise ValueError('A replacement must preserve every existing result check.')
    else:
        at = index + (meta['mode'] == 'after')
        if len(new) != len(old) + 1 or new[:at] != old[:at] or new[at+1:] != old[at:]:
            raise ValueError('Adding a step cannot change existing steps.')
        current = new[at]
    if not current.get('action') or current.get('recording_issue'):
        raise ValueError('Demonstrate supported actions before saving this step.')


def finish(data, calls):
    from reshoot import rec, story
    root, meta = data['root'], data['meta']
    recorded = root / 'recorded.toml'
    rec.write_toml(recorded, data['board']['url'], data['board'].get('size', '1280x720@1'), calls)
    recorded.chmod(0o600)
    captured = story.load(recorded)['beat'][:-1]
    steps = rec.steps_from(calls, include_tab=True)
    if any(row.get('recording_issue') for row in captured) or any(row.get('secret') for row in steps) or any(ev['kind'] == 'blur' for _, ev in calls):
        raise ValueError('This demonstration has unsupported actions, password placeholders or new privacy blurs. Its sanitized draft is kept; change privacy settings in the story file and record supported demo actions again.')
    actions = [entry for row in captured for entry in row.get('action', [])]
    if not actions or len(actions) > 200:
        raise ValueError('Show between 1 and 200 actions for this step, then choose Done.')
    checks = ([entry for row in steps for entry in row.get('checks', [])] if meta['mode'] == 'replace'
              else captured[-1].get('expect', []))
    caption = next((row['caption'] for row in steps if row.get('caption')),
                   next((row.get('caption') for row in captured if row.get('caption')), 'Show the next result'))
    text = proposed((root / 'before.toml').read_text(), data['board'], meta['beat'], meta['mode'], actions, checks, caption)
    after = root / 'after.toml'
    after.write_text(text); after.chmod(0o600)
    validate_change(data['board'], story.load(after), meta)
    meta.update(status='proposed', message='Review the action changes, then use them or discard this draft.')
    write(root / 'draft.json', meta)
    return meta['id']


def fail(data, error):
    from reshoot.safety import redact
    data['meta'].update(status='failed', message=redact(str(error)) or 'Demonstration interrupted. Your story is kept.')
    write(data['root'] / 'draft.json', data['meta'])


def binding(root):
    values = []
    for name in ('draft.json', 'before.toml', 'recorded.toml', 'after.toml'):
        path = root / name
        if path.is_symlink():
            raise ValueError('A demonstration draft file is a symlink. Keep draft files inside their project.')
        values.append(hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None)
    return hashlib.sha256(json.dumps(values).encode()).hexdigest()


def read(project, ident, token=None):
    from reshoot import story
    if not isinstance(ident, str) or not re.fullmatch(r'[0-9a-f]{32}', ident):
        raise ValueError('Choose a valid demonstration draft.')
    data = context(project)
    base = storage(data['folder'])
    root = (base / ident).resolve()
    if root.parent != base:
        raise ValueError('The demonstration draft is outside this project.')
    current_token = binding(root)
    if token is not None and token != current_token:
        raise ValueError('The demonstration draft changed. Reload before using it.')
    meta = json.loads((root / 'draft.json').read_text())
    if (meta.get('schema_version') != 1 or meta.get('id') != ident or meta.get('config') != data['config'].name
            or meta.get('story') != name(data['board_path'], data['folder']) or meta.get('mode') not in ('replace', 'before', 'after')
            or meta.get('status') not in ('recording', 'failed', 'proposed', 'applied', 'discarded')
            or not isinstance(meta.get('expected'), dict)):
        raise ValueError('This draft does not describe the selected project and story.')
    sources = {name(path, data['folder']):path for path in data['paths']}
    if set(meta['expected']) != set(sources):
        raise ValueError('The project\'s source list changed. Record this demonstration again.')
    original = root / 'before.toml'
    if original.stat().st_size > 2 * 1024 * 1024 or hashlib.sha256(original.read_bytes()).hexdigest() != meta['expected'][meta['story']]:
        raise ValueError('The demonstration\'s original story changed.')
    before = story.load(original)
    if meta.get('beat') not in [row['id'] for row in before['beat']]:
        raise ValueError('The demonstration names a step outside its original story.')
    snapshot = History(data['paths']).snapshot()
    stale = any((hashlib.sha256(value).hexdigest() if value is not None else None) != meta['expected'][name(path, data['folder'])]
                for path, value in snapshot.items())
    after = None
    if meta['status'] == 'proposed':
        if (root / 'after.toml').stat().st_size > 2 * 1024 * 1024:
            raise ValueError('The proposed story is too large for review here.')
        after = story.load(root / 'after.toml')
        validate_change(before, after, meta)
    if binding(root) != current_token:
        raise ValueError('The demonstration changed while reading. Reload before using it.')
    return {**data, 'root':root, 'meta':meta, 'binding':current_token, 'before':before, 'after':after,
            'snapshot':snapshot, 'stale':stale}


def model(data):
    meta, root = data['meta'], data['root']
    diff = ''.join(difflib.unified_diff((root / 'before.toml').read_text().splitlines(keepends=True),
                                      (root / 'after.toml').read_text().splitlines(keepends=True),
                                      fromfile='Current story', tofile='Proposed story')) if data['after'] else ''
    index = next(i for i, row in enumerate(data['before']['beat']) if row['id'] == meta['beat'])
    old = data['before']['beat'][index]
    new = (data['after']['beat'][index + (meta['mode'] == 'after')] if data['after'] else {})
    return {'id':meta['id'], 'binding':data['binding'], 'beat':meta['beat'], 'mode':meta['mode'], 'status':meta['status'],
            'message':('The project changed during or after this demonstration. Keep the current files and record again.' if data['stale'] else meta.get('message', '')),
            'can_apply':meta['status'] == 'proposed' and not data['stale'] and len(diff) <= 120000,
            'diff':diff[:120000], 'stale':data['stale'],
            'previous_actions':[describe(row) for row in old.get('action', [])] if meta['mode'] == 'replace' else [],
            'proposed_actions':[describe(row) for row in new.get('action', [])]}


def describe(entry):
    """Short action words for a review; the full source diff stays available below them."""
    target = entry.get('target', {})
    label = target.get('name') or target.get('text') or target.get('css', '')
    for option in [target, *entry.get('fallbacks', [])]:
        match = re.search(r'\[(?:placeholder|aria-label)=["\']([^"\']+)', option.get('css', ''))
        if match:
            label = re.sub(r'\\(.)', r'\1', match[1]); break
    kind = entry['type']
    value = next((entry[key] for key in ('text', 'key', 'option', 'url', 'dy', 'checked') if key in entry), None)
    detail = f' {json.dumps(value, ensure_ascii=False)}' if value is not None else ''
    words = {'type':'Type', 'key':'Press', 'click':'Click', 'select':'Choose', 'check':'Set checked',
             'scroll':'Scroll', 'navigate':'Open'}.get(kind, kind.capitalize())
    return (words + detail + (f' · {label}' if label else ''))[:240]


def latest(project):
    data = context(project)
    for root in sorted(storage(data['folder']).glob('[0-9a-f]' * 32), key=lambda p:p.stat().st_mtime, reverse=True)[:30]:
        try:
            draft = read(project, root.name)
            if draft['meta']['status'] not in ('applied', 'discarded'):
                return model(draft)
        except (ValueError, OSError, KeyError, TypeError):
            continue
    return None


def apply(project, ident, token):
    from reshoot import story
    if not isinstance(token, str) or not re.fullmatch(r'[0-9a-f]{64}', token):
        raise ValueError('Reload and review the demonstrated changes before using them.')
    data = read(project, ident, token)
    if data['meta']['status'] != 'proposed' or data['stale']:
        raise ValueError('This demonstration is not ready to use. Keep your files and record it again.')
    meta_path = data['root'] / 'draft.json'
    meta = {**data['meta'], 'status':'applied', 'message':'Actions saved. Record a fresh preview to verify the complete task.'}
    before = {**data['snapshot'], **{data['root'] / key:(data['root'] / key).read_bytes()
                                   for key in ('draft.json', 'before.toml', 'recorded.toml', 'after.toml')}}
    if binding(data['root']) != token:
        raise ValueError('The demonstration changed. Reload before using it.')
    save_many({data['board_path']:(before[data['root'] / 'after.toml'].decode(), story.load),
               meta_path:(json.dumps(meta, indent=2), lambda path:json.loads(path.read_text()))}, before)
    return meta


def discard(project, ident, token):
    if not isinstance(token, str) or not re.fullmatch(r'[0-9a-f]{64}', token):
        raise ValueError('Reload before discarding this demonstration.')
    data = read(project, ident, token)
    path = data['root'] / 'draft.json'
    meta = {**data['meta'], 'status':'discarded', 'message':'Draft discarded. Current story kept.'}
    before = {path:path.read_bytes()}
    if binding(data['root']) != token:
        raise ValueError('The demonstration changed. Reload before discarding it.')
    save_many({path:(json.dumps(meta, indent=2), lambda p:json.loads(p.read_text()))}, before)
