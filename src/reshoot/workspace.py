"""Revision checks and reversible studio edits. External changes always take precedence."""
import hashlib
import json
import re
import tomllib
import threading
from pathlib import Path


# Edits change the lines they must and leave the rest of a file, comments included, as it was.
def quote(value):
    if isinstance(value, dict):
        return '{' + ', '.join(json.dumps(k) + ' = ' + quote(v) for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ', '.join(quote(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False)  # JSON's strings, numbers, booleans and lists are TOML's too


def tables(lines, header):
    """[(header line, first line, end)] for each table under header, such as [caption] or [[part]], in order. A
    table ends at the next header."""
    found = []
    for n, line in enumerate(lines):
        text = line.strip()
        if text == header or (text.startswith(header) and text[len(header):].lstrip().startswith('#')):
            end = next((k for k in range(n + 1, len(lines)) if lines[k].lstrip().startswith('[')), len(lines))
            found.append((n, n + 1, end))
    return found


def block(lines, header, match=None):
    """(first line, end) of the first table under header whose keys pass match, or None."""
    for _, start, end in tables(lines, header):
        if match is None or match(tomllib.loads(''.join(lines[start:end]))):
            return start, end
    return None


def first_header(lines):
    return next((n for n, line in enumerate(lines) if line.lstrip().startswith('[')), len(lines))


def put(lines, span, key, value, after=None):
    """Sets key = value inside span, or removes it when value is None; a new key goes after the line `after`."""
    start, end = span
    found = next((k for k in range(start, end) if re.match(rf'\s*{key}\s*=', lines[k])), None)
    if found is not None and re.match(rf'\s*{key}\s*=\s*("""|\'\'\'|\[[^\]]*$)', lines[found]):
        raise ValueError(f'{key} takes more than one line here; change it in the file')
    line = f'{key} = {quote(value)}\n'
    if found is not None and value is not None:
        quoted, escaped = None, False
        for n, char in enumerate(lines[found]):
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\' and quoted == '"':
                    escaped = True
                elif char == quoted:
                    quoted = None
            elif char in ('"', "'"):
                quoted = char
            elif char == '#':
                line = line.rstrip('\n') + '  ' + lines[found][n:].rstrip('\n') + '\n'
                break
    if found is not None:
        lines[found:found + 1] = [line] if value is not None else []
    elif value is not None:
        at = next((k + 1 for k in range(start, end) if after and re.match(rf'\s*{after}\s*=', lines[k])), end)
        while at > start and not lines[at - 1].strip():  # before the blank lines that end the table
            at -= 1
        lines.insert(at, line)


def drop(lines, head, end):
    """Removes a table: its header and every line up to the next one."""
    del lines[head:end]


def read_lines(path):
    lines = Path(path).read_text().splitlines(keepends=True)
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    return lines


def save(path, lines, check, expected_sha256=None):
    """Writes lines to path only when check passes on them, so a bad change never reaches the file."""
    path = Path(path)
    import tempfile
    from reshoot.artifacts import digest
    if expected_sha256 and digest(path) != expected_sha256:
        raise ValueError('The storyboard changed. Record another preview before repairing it.')
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix='.' + path.name, suffix='.studio', delete=False) as f:
        f.write(''.join(lines))
        temp = Path(f.name)
    temp.chmod(path.stat().st_mode & 0o777)
    try:
        check(temp)
        if expected_sha256 and digest(path) != expected_sha256:
            raise ValueError('The storyboard changed during the repair. Your edits were kept.')
    except (ValueError, KeyError, TypeError, tomllib.TOMLDecodeError) as e:
        temp.unlink(missing_ok=True)
        raise ValueError(f'not saved: {e}') from None
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    temp.replace(path)


def save_many(changes, before, guard=None):
    """Validate every file before replacing any; roll back our writes if a later replacement fails.

    `before` includes None for a file that must not already exist. External edits are never rolled back.
    This is a checked group of replacements, not a crash-safe filesystem transaction.
    """
    import tempfile
    pending, written = {}, []
    def content(path):
        return path.read_bytes() if path.exists() else None
    try:
        for path, (text, check) in changes.items():
            with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix='.' + path.name,
                                             suffix='.studio', delete=False) as file:
                file.write(text)
                pending[path] = Path(file.name)
            if path.exists():
                pending[path].chmod(path.stat().st_mode & 0o777)
            check(pending[path])
        expected = dict(before)
        for path in changes:
            if guard:
                guard()
            if any(content(source) != original for source, original in expected.items()):
                raise ValueError('The project changed while applying the style. External edits were kept; reload and try again.')
            pending[path].replace(path)
            written.append(path)
            expected[path] = changes[path][0].encode()
        if guard:
            guard()
        if any(content(source) != original for source, original in expected.items()):
            raise ValueError('The project changed while applying the style. External edits were kept; reload and try again.')
    except BaseException:
        for path in reversed(written):
            if content(path) == changes[path][0].encode():
                if before[path] is None:
                    path.unlink()
                else:
                    pending[path].write_bytes(before[path])
                    pending[path].chmod(path.stat().st_mode & 0o777)
                    pending[path].replace(path)
        raise
    finally:
        for temp in pending.values():
            temp.unlink(missing_ok=True)


class History:
    def __init__(self, paths):
        self.paths = tuple(Path(p) for p in paths)
        self.lock = threading.RLock()
        self.undo, self.redo = [], []
        self.expected = self.snapshot()

    def snapshot(self):
        return {p: p.read_bytes() if p.is_file() else None for p in self.paths}

    def revision(self):
        h = hashlib.sha256()
        for p, content in self.snapshot().items():
            h.update(str(p).encode() + b'\0' + (content if content is not None else b'<missing>') + b'\0')
        return h.hexdigest()

    def check(self, revision):
        if revision != self.revision():
            raise ValueError('The project changed in another tab or editor. Reload before making more changes.')
        if self.snapshot() != self.expected:
            self.undo.clear()
            self.redo.clear()
            self.expected = self.snapshot()

    def restore(self, snapshot):
        for path, content in snapshot.items():
            if content is None:
                path.unlink(missing_ok=True)
            elif not path.is_file() or path.read_bytes() != content:
                temp = path.with_name('.' + path.name + '.restore')
                temp.write_bytes(content)
                temp.replace(path)

    def change(self, operation):
        before = self.snapshot()
        try:
            operation()
        except Exception:
            self.restore(before)
            raise
        after = self.snapshot()
        self.remember(before, after)

    def remember(self, before, after):
        if before != after:
            self.undo.append((before, after))
            self.undo[:] = self.undo[-50:]
            self.redo.clear()
        self.expected = after

    def move(self, direction):
        source, destination = (self.undo, self.redo) if direction == 'undo' else (self.redo, self.undo)
        if not source:
            raise ValueError(f'Nothing to {direction}.')
        before, after = source[-1]
        wanted, expected = (before, after) if direction == 'undo' else (after, before)
        if self.snapshot() != expected:
            raise ValueError('The project changed in an editor. Reload; those changes will be kept.')
        self.restore(wanted)
        source.pop()
        destination.append((before, after))
        self.expected = wanted
