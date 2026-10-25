"""Read legacy projects and isolate outputs for schema version 1 projects."""
import copy
import json
import re
import tomllib
import uuid
from pathlib import Path


def read(path):
    path = Path(path).resolve()
    data = tomllib.loads(path.read_text())
    version = data.get('schema_version', 0)
    if version not in (0, 1):
        raise ValueError('unsupported project schema_version')
    if version == 1 and (unknown := set(data) - {'schema_version', 'app', 'take', 'edit', 'check', 'keep', 'timeout', 'report', 'inputs', 'screenshot'}):
        raise ValueError('unknown reshoot.toml option: ' + ', '.join(sorted(unknown)) + '; guide/projects.md lists them')
    for i, take in enumerate(data.get('take', []), 1):
        if sum(k in take for k in ('web', 'tape', 'run')) != 1:
            raise ValueError(f'take {i} needs exactly one capture method')
        if 'web' in take and 'out' not in take:
            raise ValueError(f'take {i} needs an output')
    if data.get('timeout', 600) <= 0:
        raise ValueError('timeout must be positive')
    if 'screenshot' in data:
        from reshoot.screenshots import validate
        if version != 1:
            raise ValueError('Documentation screenshots need schema_version = 1.')
        validate(data['screenshot'], len(data.get('take', [])))
    return data, path.parent


def prepare(path):
    data, root = read(path)
    if not data.get('schema_version'):
        return data
    data = copy.deepcopy(data)
    run_id = uuid.uuid4().hex
    folder = root / 'takes' / 'runs' / run_id
    folder.mkdir(parents=True)
    def source(value):
        if value.startswith(('http://', 'https://')):
            return value
        return str((root / value).resolve())
    def output(value):
        p = Path(value)
        if p.is_absolute() or '..' in p.parts:
            raise ValueError('versioned outputs must be relative and stay within the run')
        return str(folder / p)
    for take in data.get('take', []):
        if 'web' in take:
            take['web'] = source(take['web'])
            if not Path(take['web']).is_file():
                raise ValueError('storyboard file missing')
            if Path(take['web']).suffix == '.toml':
                from reshoot.story import load
                load(take['web'])
            take['out'] = output(take['out'])
        elif 'tape' in take:
            tape = Path(source(take['tape']))
            text = tape.read_text()
            def replace(m):
                return 'Output ' + json.dumps(output(m[1]))
            text, count = re.subn(r'(?m)^Output\s+"([^"\n]+)"', replace, text)
            if not count:
                raise ValueError('versioned tapes need a quoted Output path')
            target = folder / tape.name
            target.write_text(text)
            take['tape'] = str(target)
        else:
            raise ValueError('versioned projects support web and tape takes; keep arbitrary run takes in a legacy project')
    data['inputs'] = [source(value) for value in data.get('inputs', [])]
    if any(not Path(value).is_file() or not Path(value).is_relative_to(root) for value in data['inputs']):
        raise ValueError('declared inputs must be existing files inside the project')
    if 'app' in data:
        data['app']['cwd'] = str(root)
    if edit := data.get('edit'):
        key = 'file' if 'file' in edit else 'script'
        edit[key] = source(edit[key])
        edit['args'] = [output(a) for a in edit.get('args', [])]
    if check := data.get('check'):
        check['review'] = str(folder / 'review')
        check['sources'] = [source(s) if s.startswith(('http://', 'https://')) else output(s) for s in check.get('sources', [])]
    data['report'] = str(folder / 'run.json')
    data['_root'], data['_run_id'], data['_run_dir'] = str(root), run_id, str(folder)
    # Candidates remain in this run. Explicit export is separate from recording.
    data['_exports'] = {output(src): source(dst) for src, dst in data.pop('keep', {}).items()}
    return data
