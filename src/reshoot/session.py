"""Local studio history checkpoints. Recovery never replaces current source files."""
import base64
import hashlib
import json
import os
import re
import tempfile
import uuid
import zipfile
from contextlib import contextmanager
from pathlib import Path

from reshoot.workspace import History

MAX_BYTES = 32 * 1024 * 1024


class Session(History):
    def __init__(self, config, paths):
        self.config = Path(config).resolve()
        self.root = self.config.parent
        key = hashlib.sha256(self.config.name.encode()).hexdigest()[:12]
        self.file = self.root / 'takes' / 'studio' / f'history-{key}.json'
        self.token, self.saved, self.problem, self.pending = None, None, '', False
        super().__init__([Path(path).resolve() for path in paths])
        self.refresh(self.paths)

    def names(self):
        return [str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path) for path in self.paths]

    @contextmanager
    def storage(self):
        # The project supports macOS and Linux. A per-operation OS lock also
        # serializes different studio servers; no stale lock survives a crash.
        import fcntl
        self.file.parent.mkdir(parents=True, exist_ok=True)
        with self.file.with_suffix('.lock').open('a+b') as lock:
            os.chmod(lock.name, 0o600)
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def version(self):
        from reshoot.artifacts import digest
        if self.file.is_symlink():
            raise ValueError('The studio history file is a symlink. Move it aside before opening the studio.')
        return digest(self.file) if self.file.exists() else None

    def encode(self):
        blobs = {}
        def snapshot(values):
            refs = []
            for path in self.paths:
                content = values[path]
                key = hashlib.sha256(content).hexdigest() if content is not None else None
                if key is not None:
                    blobs[key] = base64.b64encode(content).decode('ascii')
                refs.append(key)
            return refs
        out = {'schema_version': 1, 'generation': uuid.uuid4().hex, 'paths': self.names(),
               'expected': snapshot(self.expected),
               'undo': [[snapshot(before), snapshot(after)] for before, after in self.undo],
               'redo': [[snapshot(before), snapshot(after)] for before, after in self.redo]}
        out['blobs'] = blobs
        return json.dumps(out, separators=(',', ':')).encode()

    @staticmethod
    def decode(raw):
        try:
            data = json.loads(raw)
            names = data['paths']
            if (data['schema_version'] != 1 or not isinstance(names, list) or not names or len(names) > 512
                    or any(not isinstance(name, str) or not name or '\x00' in name for name in names)
                    or len(set(names)) != len(names)):
                raise ValueError('invalid source list')
            blobs = {}
            for key, encoded in data['blobs'].items():
                content = base64.b64decode(encoded, validate=True)
                if hashlib.sha256(content).hexdigest() != key:
                    raise ValueError('a saved source hash does not match')
                blobs[key] = content
            def snapshot(refs):
                if not isinstance(refs, list) or len(refs) != len(names):
                    raise ValueError('invalid source snapshot')
                return [None if key is None else blobs[key] for key in refs]
            def stack(rows):
                if not isinstance(rows, list) or len(rows) > 50:
                    raise ValueError('invalid history length')
                return [(snapshot(before), snapshot(after)) for before, after in rows]
            expected, undo, redo = snapshot(data['expected']), stack(data['undo']), stack(data['redo'])
            if len(undo) + len(redo) > 50:
                raise ValueError('invalid history length')
            for rows, start, end in [(undo, 1, 0), (redo, 0, 1)]:
                cursor = expected
                for pair in reversed(rows):
                    if pair[start] != cursor:
                        raise ValueError('saved history is not continuous')
                    cursor = pair[end]
            return {'paths': names, 'expected': expected, 'undo': undo, 'redo': redo}
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            raise ValueError(f'The saved editing history could not be read: {error}.') from None

    def load(self):
        self.token = self.version()
        self.saved, self.problem = None, ''
        self.undo.clear(); self.redo.clear()
        self.expected = self.snapshot()
        if self.token is None:
            self.pending = False
            return
        try:
            if self.file.stat().st_size > MAX_BYTES:
                raise ValueError('The saved editing history exceeds 32 MB.')
            self.saved = self.decode(self.file.read_bytes())
        except (ValueError, OSError) as error:
            self.problem = str(error)
        if not self.problem and self.can_resume():
            self.restore_history()
            self.saved = None
            self.pending = False
        else:
            # There is no Undo/Redo to recover after an empty checkpoint.
            self.pending = bool(self.problem or self.saved['undo'] or self.saved['redo'])

    def restore_history(self):
        """Attach matching history without changing files or writing a new checkpoint."""
        def snapshot(values):
            return dict(zip(self.paths, values))
        self.undo = [(snapshot(before), snapshot(after)) for before, after in self.saved['undo']]
        self.redo = [(snapshot(before), snapshot(after)) for before, after in self.saved['redo']]
        self.expected = snapshot(self.saved['expected'])

    def refresh(self, paths):
        with self.storage():
            paths = tuple(Path(path).resolve() for path in paths)
            changed = paths != self.paths or self.snapshot() != self.expected
            self.paths = paths
            if changed or self.version() != self.token:
                self.load()

    def can_resume(self):
        return bool(self.saved and self.saved['paths'] == self.names()
                    and self.saved['expected'] == list(self.snapshot().values()))

    def info(self):
        if not self.pending:
            return None
        same = self.can_resume()
        changed = []
        if self.saved:
            current = dict(zip(self.names(), self.snapshot().values()))
            old = dict(zip(self.saved['paths'], self.saved['expected']))
            changed = [Path(name).name for name in old.keys() | current.keys()
                       if name not in old or name not in current or old[name] != current[name]]
        return {'resume': same, 'token': self.token, 'download': bool(self.saved),
                'undo': len(self.saved['undo']) if self.saved else 0,
                'redo': len(self.saved['redo']) if self.saved else 0,
                'title': 'Resume your editing session?' if same else 'Saved session differs from this project' if self.saved else
                         'Saved editing history could not be read',
                'detail': 'Your files match the saved session. Resume its Undo and Redo, or start a new history.' if same else
                          'Your current files have been kept. Download the saved source copy to compare, or start with the current files.' if self.saved else
                          'Your current files have been kept. Start with these files and archive the unreadable history.',
                'changed': sorted(set(changed)), 'problem': self.problem}

    @contextmanager
    def transaction(self, recovery=False):
        with self.storage():
            if self.version() != self.token:
                raise ValueError('The editing session changed in another studio. Reload before continuing.')
            if self.pending and not recovery:
                raise ValueError('Choose how to resume the saved editing session before making changes.')
            yield

    def checkpoint(self):
        raw = self.encode()
        if len(raw) > MAX_BYTES:
            self.checkpoint_failed('Project files are saved, but editing history exceeds 32 MB.')
            raise ValueError(self.problem + ' Reload before continuing.')
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.file.parent, prefix='.history-', delete=False) as output:
                temp = Path(output.name)
                output.write(raw)
                output.flush(); os.fsync(output.fileno())
            temp.replace(self.file)
            directory = os.open(self.file.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError as error:
            self.checkpoint_failed(f'Project files are saved, but editing history could not be stored: {error}.')
            raise OSError(self.problem + ' Reload before continuing.') from None
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        self.token = hashlib.sha256(raw).hexdigest()

    def checkpoint_failed(self, message):
        try:
            self.load()
        except OSError:
            self.saved = None
        self.pending, self.problem = True, message

    def recover(self, choice, token):
        if not self.pending or (token or None) != self.token:
            raise ValueError('The saved session changed. Reload before choosing recovery.')
        if choice == 'resume':
            if not self.can_resume():
                raise ValueError('The project changed since this session was saved. Current files have been kept; reload to compare.')
            self.restore_history()
        elif choice == 'fresh':
            # Retain the old checkpoint, including an unreadable one, for manual recovery.
            archive = self.file.with_name(self.file.stem + '-archived-' + uuid.uuid4().hex + '.json')
            if self.file.exists():
                self.file.replace(archive)
                archive.chmod(0o600)
            self.token = None
            self.undo.clear(); self.redo.clear()
        else:
            raise ValueError('Choose Resume history or Start with current files.')
        self.expected = (dict(zip(self.paths, self.saved['expected'])) if choice == 'resume' else self.snapshot())
        self.checkpoint()
        self.pending, self.saved, self.problem = False, None, ''

    def check(self, revision):
        if revision != self.revision():
            raise ValueError('The project changed in another tab or editor. Reload before making more changes.')
        current = self.snapshot()
        if current != self.expected:
            if self.undo or self.redo or self.pending:
                raise ValueError('The project changed in another tab or editor. Reload before making more changes.')
            self.expected = current

    def remember(self, before, after):
        super().remember(before, after)
        if before != after:
            self.checkpoint()

    def move(self, direction):
        super().move(direction)
        self.checkpoint()

    def source_copy(self, token):
        if not self.pending or token != self.token or not self.saved:
            raise ValueError('The saved session changed. Reload before downloading its source copy.')
        output = tempfile.TemporaryFile()
        try:
            with zipfile.ZipFile(output, 'w') as archive:
                for i, (name, content) in enumerate(zip(self.saved['paths'], self.saved['expected'])):
                    if content is not None:
                        filename = re.sub(r'[^\w. -]', '_', name.replace('\\', '/').split('/')[-1])
                        if filename in ('', '.', '..'):
                            filename = 'source'
                        archive.writestr(f'sources/{i + 1}/{filename}', content)
                archive.writestr('README.txt', 'Saved project source from the last editing checkpoint.\n'
                                 'These files have not replaced the current project. Compare before copying.\n'
                                 'This download contains source, not reviewed media.\n')
            output.seek(0)
            return output
        except BaseException:
            output.close()
            raise
