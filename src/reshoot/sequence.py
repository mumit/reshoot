"""Edit the video's sequence without changing the recorded task. Shared by the CLI and studio."""
import json
import math
import tomllib
from pathlib import Path

from reshoot import timeline
from reshoot.workspace import put, quote, read_lines, save_many, tables


def outputs(cut, folder_of_takes):
    stem = Path(cut.get('output', 'demo-final.mp4')).stem
    return [str(Path(folder_of_takes) / f'{stem}-{p.get("name", p.get("preset", "landscape"))}.'
                f'{p.get("format", timeline.PRESETS.get(p.get("preset"), ({}, None))[0].get("format", "mp4"))}')
            for p in cut.get('export', [])]


def check_cut(path):
    """Structural edit validation, shared with the studio's existing appearance and card edits."""
    data = tomllib.loads(Path(path).read_text())
    if data.get('schema_version') != 1 or not isinstance(data.get('part'), list) or not data['part']:
        raise ValueError('the edit needs schema_version = 1 and at least one part')
    for part in data['part']:
        if 'card' in part:
            if not isinstance(part['card'], str) or not part['card'].strip():
                raise ValueError('a card needs words')
            seconds = part.get('duration', 2)
            if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= 30:
                raise ValueError('a card lasts more than 0 and at most 30 seconds')
        elif 'through' in part and ('end' in part or not isinstance(part['through'], str)):
            raise ValueError('Use a beat name for through, without end in the same part.')
    names = [Path(p).name for p in outputs(data, '.')]
    if len(set(names)) != len(names):
        raise ValueError('two exports would write the same file')
    for profile in data.get('export', []):
        if 'preset' in profile and profile['preset'] not in timeline.PRESETS:
            raise ValueError(f'unknown preset {profile["preset"]!r}')
        from reshoot.framing import resolve
        resolve(profile)
    if 'frame' in data:
        timeline.frame_style(data)
    if data.get('music') and not (Path(path).parent / data['music']).is_file():
        raise ValueError(f'no music file {data["music"]}')
    return data


def load(project, run=None):
    from reshoot import config, review
    from reshoot.artifacts import digest
    path = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    original = path.read_bytes()
    shoot, folder = config.read(path)
    edit = shoot.get('edit', {})
    if shoot.get('schema_version') != 1 or not edit.get('file') or Path(edit['file']).suffix != '.toml' or not edit.get('args'):
        raise ValueError('Sequencing needs a versioned project with a TOML edit and recorded takes.')
    edit_path = (folder / edit['file']).resolve()
    editable = [*(folder / take['web'] for take in shoot.get('take', []) if str(take.get('web', '')).endswith('.toml')),
                folder / 'styles.toml']
    before = {p.resolve(): p.read_bytes() if p.exists() else None for p in editable}
    before.update({path: original, edit_path: edit_path.read_bytes()})
    if run is None:
        run = next((root for root, report in review.runs(folder) if report.get('ok') and report.get('mode') != 'partial-preview'), None)
        if run is None:
            raise ValueError('Record a complete preview before choosing its beat cuts.')
    root, report = review.read(run)
    if not root.resolve().is_relative_to(review.runs_folder(folder)) or not report.get('ok') or report.get('mode') == 'partial-preview':
        raise ValueError('Choose a complete successful preview or final from this project.')
    named = {file['path'] for file in report.get('files', [])}
    sources, evidence = [], {root / 'run.json': digest(root / 'run.json')}
    for arg in edit['args']:
        relative = Path(arg)
        if relative.is_absolute() or '..' in relative.parts or relative.as_posix() not in named:
            raise ValueError('The edit names an unrecorded take. Record a fresh preview before choosing its beats.')
        source = root / relative
        for file in [source, *[source.with_suffix(suffix) for suffix in ('.take.json', '.beats.json', '.voice.json', '.timeline.json')]]:
            if file.exists() and str(file.relative_to(root)) not in named:
                raise ValueError('This run has unverified take metadata. Record a fresh preview.')
            evidence[file] = digest(file) if file.exists() else None
        try:
            beats = timeline.beat_bounds(source)
        except FileNotFoundError:
            beats = {}
        sources.append({'file': str(relative), 'path': source, 'beats': beats})
    return {'config': path, 'folder': folder, 'edit': edit_path, 'cut': tomllib.loads(before[edit_path].decode()),
            'before': before, 'root': root, 'report': report, 'sources': sources, 'evidence': evidence}


def part_source(part, sources):
    index = part.get('take', 0)
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(sources):
        raise ValueError('Choose a recorded take for this part.')
    return sources[index]


def replace_blocks(lines, spans, blocks):
    """Keep global tables and their comments in place while changing the ordered part blocks."""
    result, cursor = [], 0
    for i, (head, _, end) in enumerate(spans):
        result += lines[cursor:head]
        if i < len(blocks):
            result += blocks[i]
        if i == len(spans) - 1:
            for extra in blocks[len(spans):]:
                result += extra
        cursor = end
    return result + lines[cursor:]


def apply(data, change):
    from reshoot.artifacts import digest
    def guard():
        if any((digest(path) if path.exists() else None) != expected for path, expected in data['evidence'].items()):
            raise ValueError('The recording changed during the edit. Reload and choose a verified run.')
    guard()
    lines = read_lines(data['edit'])
    spans = tables(lines, '[[part]]')
    if len(spans) != len(data['cut']['part']) or any(line.lstrip().startswith(('[part.', '[[part.')) for line in lines):
        raise ValueError('This edit uses nested or custom part tables. Change the sequence in the file.')
    blocks = [lines[head:end] for head, _, end in spans]
    operation = change.get('operation')
    index = change.get('part')
    if operation != 'add' and (isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(blocks)):
        raise ValueError('Choose a part from this cut; reload if it changed.')
    if operation in ('range', 'add'):
        source_index = change.get('take') if operation == 'add' else data['cut']['part'][index].get('take', 0)
        source = part_source({'take': source_index}, data['sources'])
        start, through = change.get('start'), change.get('through')
        if start not in source['beats'] or through not in source['beats']:
            raise ValueError('Choose start and end beats from the recorded take.')
        if operation == 'range':
            if 'card' in data['cut']['part'][index]:
                raise ValueError('A title card has words and a duration, not a beat range.')
            block = blocks[index]
            for key, value in [('end', None), ('start', start), ('through', through)]:
                put(block, (1, len(block)), key, value)
        else:
            blocks.append(['[[part]]\n', f'take = {source_index}\n', f'start = {quote(start)}\n', f'through = {quote(through)}\n', '\n'])
    elif operation == 'move':
        destination = change.get('to')
        if isinstance(destination, bool) or not isinstance(destination, int) or not 0 <= destination < len(blocks):
            raise ValueError('Choose a position within this cut.')
        blocks.insert(destination, blocks.pop(index))
    elif operation == 'duplicate':
        blocks.insert(index + 1, list(blocks[index]))
    elif operation == 'remove':
        if len(blocks) == 1:
            raise ValueError('Keep at least one part in the video.')
        blocks.pop(index)
    else:
        raise ValueError('Choose a range, move, duplicate, remove or add operation.')
    text = ''.join(replace_blocks(lines, spans, blocks))
    def validate(path):
        cut = check_cut(path)
        for part in cut['part']:
            if 'card' not in part:
                timeline.part_range(part, part_source(part, data['sources'])['path'])
    save_many({data['edit']: (text, validate)}, data['before'], guard=guard)


def view(data):
    from reshoot.artifacts import digest
    ready = data['report'].get('inputs', {}).get('edit_sha256') == digest(data['edit'])
    movie = data['root'] / Path(data['sources'][0]['file']).parent / data['cut'].get('output', 'demo-final.mp4')
    mapped = {part['index']: part for part in timeline.read(movie).get('parts', [])} if ready and movie.exists() else {}
    parts = []
    for i, part in enumerate(data['cut']['part']):
        row = {'i': i, 'card': part.get('card'), 'take': part.get('take', 0), 'start': None, 'through': None,
               'play': mapped.get(i), 'error': None}
        if 'card' not in part:
            try:
                source = part_source(part, data['sources'])
                a, b, _ = timeline.part_range(part, source['path'])
                row.update(file=source['file'], seconds=b - a,
                           start=next((name for name, (start, _) in source['beats'].items() if abs(start - a) < .025), None),
                           through=next((name for name, (_, end) in source['beats'].items() if abs(end - b) < .025), None))
            except ValueError as error:
                row['error'] = str(error)
        else:
            row['seconds'] = part.get('duration', 2)
        parts.append(row)
    return {'parts': parts, 'sources': [{'i': i, 'file': s['file'], 'beats': list(s['beats'])}
                                       for i, s in enumerate(data['sources'])], 'pending': not ready}


def main(a):
    data = load(a.project, getattr(a, 'run_path', None))
    if a.operation == 'list':
        for row in view(data)['parts']:
            label = f'Card: {row["card"]}' if row['card'] is not None else f'Take {row["take"] + 1}: {row["start"] or "custom start"} through {row["through"] or "custom end"}'
            print(f'{row["i"] + 1}. {label}')
        for i, source in enumerate(data['sources'], 1):
            print(f'Take {i} ({source["file"]}) beats: ' + ', '.join(source['beats']))
        return 0
    change = {'operation': a.operation}
    if a.operation == 'add':
        change.update(take=a.take - 1, start=a.start, through=a.through)
    else:
        change['part'] = a.part - 1
        if a.operation == 'range':
            change.update(start=a.start, through=a.through)
        if a.operation == 'move':
            change['to'] = a.to - 1
    apply(data, change)
    print('Saved the video cut. The recorded task and checks are unchanged. Update preview to see it.')
    return 0
