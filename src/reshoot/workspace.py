"""Revision checks and reversible studio edits. External changes always take precedence."""
import hashlib
import threading
from pathlib import Path


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
