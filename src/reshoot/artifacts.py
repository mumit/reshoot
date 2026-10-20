"""Small file-based run helpers; captured JPEG bytes stay on disk."""
import hashlib
import json
import tempfile
from pathlib import Path


class Frames:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix='reshoot-capture-')
        self.records = []

    def append(self, frame):
        at, data = frame
        path = None
        if data is not None:
            path = Path(self.temp.name) / f'{len(self.records):08}.jpg'
            path.write_bytes(data)
        self.records.append((at, path))

    def __len__(self):
        return len(self.records)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return (self[i] for i in range(*key.indices(len(self))))
        at, path = self.records[key]
        return at, path.read_bytes() if path else None

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def without_end(self):
        view = object.__new__(Frames)
        view.temp = self.temp
        view.records = [(at, path) for at, path in self.records if path is not None]
        return view

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.temp.cleanup()


def images(frames):
    return frames.without_end() if isinstance(frames, Frames) else [f for f in frames if f[1] is not None]


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
