"""`reshoot studio`: a page on this computer for seeing a demo's latest run beat by beat and shaping it. It shows the
video with its beats on a timeline, each beat's frame, result checks and caption, what the scan found, and the
exports side by side with the limits of where each is going. Captions and their look, title cards, the frame, music
and the export presets are edited in place and written to storyboard.toml and edit.toml; a re-cut shows them in
seconds. A beat whose actions changed is recorded again from that beat, and the run can be recorded again or
accepted from the page. The files stay the source of truth: an agent or an editor can change them while the studio is
open, and the page shows what is on disk when it loads.

    reshoot studio            # the project in ./demo
    reshoot studio app/demo --port 8800 --no-open

It serves on 127.0.0.1 behind a random address and takes changes only from its own page, like `review --serve`.
"""
import hashlib, html, json, os, re, subprocess, sys, threading, tomllib
from pathlib import Path

AUDIO = ('.mp3', '.m4a', '.aac', '.wav', '.ogg', '.flac')


def project(path):
    """The reshoot.toml for a project folder or the file itself, its folder and its first TOML web take."""
    path = Path(path)
    config = path if path.suffix == '.toml' else path / 'reshoot.toml'
    if not config.is_file():
        raise ValueError(f'no {config}: name the project folder, such as reshoot studio demo')
    from reshoot.config import read
    shoot, folder = read(config)
    if not shoot.get('schema_version'):
        raise ValueError('the studio needs a versioned project, with schema_version = 1 in reshoot.toml')
    take = next((t for t in shoot.get('take', []) if str(t.get('web', '')).endswith('.toml')), None)
    if not take:
        raise ValueError('the studio needs a take with a TOML storyboard, such as web = "storyboard.toml"')
    return config.resolve(), folder, take


# Edits change the lines they must and leave the rest of a file, comments included, as it was.
def quote(value):
    return json.dumps(value, ensure_ascii=False)  # JSON's strings, numbers, booleans and lists are TOML's too


def tables(lines, header):
    """[(header line, first line, end)] for each table under header, such as [caption] or [[part]], in order. A
    table ends at the next header."""
    found = []
    for n, line in enumerate(lines):
        if line.strip() == header:
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


def save(path, lines, check):
    """Writes lines to path only when check passes on them, so a bad change never reaches the file."""
    path = Path(path)
    temp = path.with_name('.' + path.name + '.studio')
    temp.write_text(''.join(lines))
    try:
        check(temp)
    except (ValueError, KeyError, TypeError, tomllib.TOMLDecodeError) as e:
        raise ValueError(f'not saved: {e}') from None
    finally:
        text = temp.read_text()
        temp.unlink()
    path.write_text(text)


COLOUR = re.compile(r'#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})')


def edit(board, change):
    """Applies one change from the page to storyboard.toml: a beat's caption or second line, or the caption look."""
    from reshoot import story
    lines = read_lines(board)
    if change.get('beat') is not None:
        def this(keys):
            return keys.get('id') == change['beat']
        if not block(lines, '[[beat]]', this):
            raise ValueError(f'no beat {change["beat"]!r} in the storyboard')
        for key in ('caption', 'sub'):
            if key in change:
                value = change[key]
                if value is not None and not isinstance(value, str):
                    raise ValueError(f'{key} must be text')
                put(lines, block(lines, '[[beat]]', this), key, (' '.join(value.split()) or None) if value else None,
                    after='id' if key == 'caption' else 'caption')
    if 'look' in change:
        for key, value in change['look'].items():
            if key not in ('position', 'background', 'foreground'):
                raise ValueError(f'the studio does not change [caption] {key}')
            if key == 'position' and value not in ('top', 'bottom', None):
                raise ValueError('position must be top or bottom')
            if key != 'position' and value and not COLOUR.fullmatch(value):
                raise ValueError(f'{key} must be a colour such as #1d4ed8, or #1d4ed8e6 with its opacity')
            span = block(lines, '[caption]')
            if span is None and value:
                lines += ['\n', '[caption]\n']
                span = (len(lines), len(lines))
            if span:
                put(lines, span, key, value or None)
    save(board, lines, story.load)


def outputs(cut, folder_of_takes):
    """The path, beside the takes, of each export an edit file makes, in order, as [check] sources names them."""
    from reshoot import timeline
    stem = Path(cut.get('output', 'demo-final.mp4')).stem
    found = []
    for profile in cut.get('export', []):
        preset = timeline.PRESETS.get(profile.get('preset'), ({}, None))[0]
        name = profile.get('name', profile.get('preset', 'landscape'))
        found.append(str(Path(folder_of_takes) / f'{stem}-{name}.{profile.get("format", preset.get("format", "mp4"))}'))
    return found


def check_cut(path):
    """What `reshoot edit` would refuse in an edit file, found before it is written."""
    from reshoot import timeline
    cut = tomllib.loads(Path(path).read_text())
    if cut.get('schema_version') != 1 or not cut.get('part'):
        raise ValueError('the edit needs schema_version = 1 and at least one part')
    for part in cut['part']:
        if 'card' in part:
            if not isinstance(part['card'], str) or not part['card'].strip():
                raise ValueError('a card needs words')
            seconds = part.get('duration', 2)
            if not isinstance(seconds, (int, float)) or not 0 < seconds <= 30:
                raise ValueError('a card lasts more than 0 and at most 30 seconds')
    names = [Path(p).name for p in outputs(cut, '.')]
    if len(set(names)) != len(names):
        raise ValueError('two exports would write the same file')
    for profile in cut.get('export', []):
        if 'preset' in profile and profile['preset'] not in timeline.PRESETS:
            raise ValueError(f'unknown preset {profile["preset"]!r}')
    if 'frame' in cut:
        timeline.frame_style(cut)
    if cut.get('music') and not (Path(path).parent / cut['music']).is_file():
        raise ValueError(f'no music file {cut["music"]}')


def edit_cut(path, config, change):
    """Applies one change from the page to edit.toml: a title card, the frame and its background, the music, or an
    export's preset. When the exports change, [check] sources in reshoot.toml follows, so each is still scanned."""
    from reshoot import timeline
    lines = read_lines(path)
    before = tomllib.loads(''.join(lines))
    parts = tables(lines, '[[part]]')
    if 'card' in change:
        if not isinstance(change['card'], int) or not 0 <= change['card'] < len(parts):
            raise ValueError('no such part')
        head, start, end = parts[change['card']]
        if 'card' not in tomllib.loads(''.join(lines[start:end])):
            raise ValueError('that part is a take, not a card')
        if change.get('remove'):
            drop(lines, head, end)
        else:
            if 'text' in change:
                put(lines, (start, end), 'card', ' '.join(str(change['text']).split()))
            if 'duration' in change:
                put(lines, tables(lines, '[[part]]')[change['card']][1:], 'duration', change['duration'], after='card')
    if change.get('add_card') in ('start', 'end'):
        text = ' '.join(str(change.get('text') or 'Your title').split())
        card = ['[[part]]\n', f'card = {quote(text)}\n', 'duration = 2\n', '\n']
        at = parts[0][0] if change['add_card'] == 'start' else parts[-1][2]
        if change['add_card'] == 'end' and at and lines[at - 1].strip():
            card.insert(0, '\n')
        lines[at:at] = card
    if 'frame' in change:
        frame = tables(lines, '[frame]')
        if change['frame'] and not frame:
            lines[parts[0][0]:parts[0][0]] = ['[frame]\n', 'padding = 0.06\n', '\n']
        elif not change['frame'] and frame:
            drop(lines, *frame[0][::2])
    if 'background' in change:
        value = change['background'] or None
        if value and not COLOUR.fullmatch(value):
            raise ValueError('the background must be a colour such as #1d2433')
        span = block(lines, '[style]')
        if span is None and value:
            at = first_header(lines)
            lines[at:at] = ['[style]\n', '\n']
            span = (at + 1, at + 1)
        if span:
            put(lines, span, 'background', value)
    if 'music' in change:
        put(lines, (0, first_header(lines)), 'music', change['music'] or None, after='output')
    exports = tables(lines, '[[export]]')
    if 'export' in change:
        if not isinstance(change['export'], int) or not 0 <= change['export'] < len(exports):
            raise ValueError('no such export')
        head, start, end = exports[change['export']]
        if change.get('remove'):
            drop(lines, head, end)
        else:
            if change.get('preset') not in timeline.PRESETS:
                raise ValueError(f'unknown preset {change.get("preset")!r}')
            lines[start:end] = [f'preset = {quote(change["preset"])}\n', '\n']
    if change.get('add_export'):
        if change['add_export'] not in timeline.PRESETS:
            raise ValueError(f'unknown preset {change["add_export"]!r}')
        lines += ['\n', '[[export]]\n', f'preset = {quote(change["add_export"])}\n']
    save(path, lines, check_cut)
    sources(config, before, tomllib.loads(Path(path).read_text()), change)


def sources(config, before, after, change):
    """Keeps [check] sources naming the exports after one was changed, added or removed."""
    from reshoot.config import read
    shoot, _ = read(config)
    check, edit = shoot.get('check'), shoot.get('edit', {})
    if not check or not edit.get('args'):
        return
    where = Path(edit['args'][0]).parent
    old, new = outputs(before, where), outputs(after, where)
    if old == new:
        return
    listed = list(check.get('sources', []))
    if 'export' in change and not change.get('remove'):
        listed = [new[change['export']] if s == old[change['export']] else s for s in listed]
    elif 'export' in change:
        listed = [s for s in listed if s != old[change['export']]]
    else:
        listed += [s for s in new if s not in old]
    if listed != check.get('sources', []):
        lines = read_lines(config)
        put(lines, block(lines, '[check]'), 'sources', listed)
        save(config, lines, read)


class Job:
    """A reshoot command started from the page: a re-cut or a recording, one at a time."""
    def __init__(self):
        self.kind, self.lines, self.code, self.lock, self.n, self.beat = None, [], None, threading.Lock(), 0, None

    def running(self):
        return self.kind is not None and self.code is None

    def start(self, kind, cmd, cwd, beat=None):
        with self.lock:
            if self.running():
                raise ValueError(f'a {self.kind} is still running')
            self.kind, self.lines, self.code, self.n, self.beat = kind, [], None, self.n + 1, beat
        def go():
            from reshoot.safety import redact
            try:
                proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:
                    self.lines.append(redact(line.rstrip()).replace(str(cwd) + '/', ''))
                self.code = proc.wait()
            except OSError as e:
                self.lines.append(str(e))
                self.code = 1
        threading.Thread(target=go, daemon=True).start()

    def json(self):
        return {'n': self.n, 'kind': self.kind, 'beat': self.beat, 'running': self.running(), 'code': self.code,
                'lines': self.lines[-400:]}


def current(folder, partial=False):
    """The newest run that worked, as (root, report), or None. A partial preview, recorded from one beat on, is
    left out unless partial asks for one only."""
    from reshoot import review
    for root, report in review.runs(folder):
        if report.get('ok') and (report.get('mode') == 'partial-preview') == partial:
            try:
                return review.read(root)
            except (OSError, ValueError):
                continue
    return None


def place(segments, source, t):
    """Where source time t of a take is in a cut, or None when the cut leaves it out."""
    for row in segments:
        if Path(row['source']).resolve() == source and row['source_start'] <= t <= row['source_end']:
            scale = (row['end'] - row['start']) / (row['source_end'] - row['source_start'] or 1)
            return row['start'] + (t - row['source_start']) * scale
    return None


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


def fits(limits, seconds, size):
    """The limits of where an export is going, in words, beside its own."""
    if not limits:
        return None
    mb = lambda n: f'{n / 1e9:g} GB' if n >= 1e9 else f'{n / 1e6:g} MB'
    rules = []
    if 'seconds' in limits:
        rules.append(f'{limits["seconds"][0]:g} to {limits["seconds"][1]:g} s')
    rules.append(f'up to {mb(limits["max_bytes"])}')
    return f'{limits["platform"]} takes {" and ".join(rules)}; this is {seconds:.1f} s and {size / 1e6:.1f} MB'


def view(folder, take, config):
    """What the page shows: the storyboard's beats and the edit, joined to the latest run's where there is one."""
    from reshoot import cut as cuts, review, story, timeline
    from reshoot.artifacts import digest
    from reshoot.check import findings, load
    from reshoot.config import read
    board_path = Path(folder) / take['web']
    board = story.load(board_path)
    shoot, _ = read(config)
    edit_path = Path(folder) / shoot['edit']['file'] if shoot.get('edit', {}).get('file') else None
    data = {'story': board_path.name, 'look': board.get('caption', {}), 'run': None, 'beats': [], 'findings': [],
            'edit': None}
    if edit_path and edit_path.is_file():
        cut = tomllib.loads(edit_path.read_text())
        parts = cut.get('part', [])
        music = []
        for where, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d != 'takes' and not d.startswith('.') and d != 'node_modules']
            music += [os.path.relpath(Path(where) / f, edit_path.parent) for f in files if f.lower().endswith(AUDIO)]
        music.sort()
        data['edit'] = {'file': edit_path.name, 'cards': [
            {'i': i, 'text': p['card'], 'duration': p.get('duration', 2),
             'where': 'opening' if i == 0 else 'closing' if i == len(parts) - 1 else 'middle'}
            for i, p in enumerate(parts) if 'card' in p],
            'frame': 'frame' in cut, 'background': cut.get('style', {}).get('background', ''),
            'music': cut.get('music', ''), 'music_choices': music,
            'exports': [{'i': i, 'preset': p.get('preset'), 'name': p.get('name', p.get('preset', 'landscape')),
                         'file': Path(o).name} for i, (p, o) in enumerate(zip(cut.get('export', []), outputs(cut, '.')))],
            'pending': False}
    run = current(folder)
    recorded, drawn, rows, look_drawn = {}, {}, {}, None
    if run:
        root, report = run
        if data['edit'] and report.get('inputs', {}).get('edit_sha256'):
            data['edit']['pending'] = report['inputs']['edit_sha256'] != digest(edit_path)
        clips = [p for p in review.exports(root, report) if p.endswith('.mp4')]
        video = clips[0] if clips else take['out']
        segments = timeline.read(root / video)['segments']
        source = (root / take['out']).resolve()
        meta = load(source.with_suffix('.take.json'), {})
        sidecar = load(source.with_suffix('.captions.json'), None)
        if sidecar:
            rows = {row['beat']: row for row in sidecar['captions']}
            drawn = {name: (row.get('text'), row.get('sub')) for name, row in rows.items()}
            look_drawn = sidecar.get('style', {})
        for beat in meta.get('beats', []):
            a = place(segments, source, beat.get('start', 0))
            b = place(segments, source, beat.get('end', beat.get('start', 0)))
            if a is None and b is not None:
                a = min((r['start'] for r in segments if Path(r['source']).resolve() == source), default=b)
            shot = beat.get('screenshot')
            recorded[beat['id']] = {
                'start': a, 'end': b if b is not None or a is None else timeline.read(root / video)['duration'],
                'status': beat.get('status'), 'frame': str(Path(take['out']).parent / shot) if shot else None,
                'checks': [c.get('status') for c in beat.get('expectations', [])],
                'definition': beat.get('definition_sha256')}
        names = review.named(root, report)
        key, flags = load(root / 'review' / 'key.json', {}), load(root / 'review' / 'flags.json', {})
        for name, (found, labels) in findings(flags).items():
            times = []
            for label in labels:
                m = re.fullmatch(r'local source ([0-9a-f]{12})@([0-9.]+)s', str((key.get(label) or [''])[0]))
                if m and names.get(m[1]) == video:
                    times.append(float(m[2]))
            data['findings'].append({'name': name, 'found': found, 'frames': len(labels), 'times': times})
        presets = {e['file']: e['preset'] for e in (data['edit'] or {}).get('exports', [])}
        exports = []
        for path in review.exports(root, report):
            w, h, seconds = cuts.probe(root / path)
            size = (root / path).stat().st_size
            preset = presets.get(Path(path).name)
            exports.append({'path': path, 'bytes': size, 'width': w, 'height': h, 'seconds': seconds,
                            'preset': preset, 'fits': fits(timeline.PRESETS[preset][1] if preset else None, seconds, size)})
        data['run'] = {'id': report['id'], 'status': review.status(root, report), 'video': video,
                       'duration': timeline.read(root / video)['duration'], 'mode': report.get('mode', 'final'),
                       'recut_from': report.get('recut_from'), 'accepted': report.get('review_status') == 'completed',
                       'exports': exports, 'captions_drawn': sidecar is not None}
    for beat in board['beat']:
        row = {'id': beat['id'], 'purpose': beat.get('purpose'), 'caption': beat.get('caption') or '',
               'sub': beat.get('sub') or '', **recorded.get(beat['id'], {})}
        if beat['id'] in drawn:
            row['pending'] = drawn[beat['id']] != (beat.get('caption') or None, beat.get('sub') or None)
        if row.get('definition'):
            row['changed'] = recorded_as(beat, rows.get(beat['id'])) != row['definition']
        data['beats'].append(row)
    data['look_pending'] = look_drawn is not None and look_drawn != board.get('caption', {})
    return data


def server(a):
    """The studio's server, not yet serving, its address and the take it shapes."""
    import http.server, secrets
    from urllib.parse import unquote
    from reshoot import review
    config, folder, take = project(a.project)
    token = secrets.token_urlsafe(16)
    job = Job()
    prefix = f'/{token}/'
    cli = [sys.executable, '-m', 'reshoot.cli']

    def edit_file():
        from reshoot.config import read
        shoot, _ = read(config)
        if not shoot.get('edit', {}).get('file'):
            raise ValueError('this project has no edit file')
        return Path(folder) / shoot['edit']['file']

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = self.path.split('?', 1)[0]
            if not path.startswith(prefix):
                return review.reply(self, 404, b'not found', 'text/plain')
            name = unquote(path[len(prefix):])
            if name == '':
                run = current(folder)
                accept = review.panel(*run) if run else ''
                seen = job.n - job.running()  # the last job this page already shows the outcome of
                return review.reply(self, 200, page(view(folder, take, config), accept, seen).encode())
            if name == 'job.json':
                out = job.json()
                if job.kind == 'from' and job.code == 0 and (partial := current(folder, partial=True)):
                    out['take'] = f'runs/{partial[1]["id"]}/' + take['out']
                return review.reply(self, 200, json.dumps(out).encode(), 'application/json')
            if name.startswith('run/') and (run := current(folder)):
                return review.send_file(self, run[0], name[4:])
            if m := re.fullmatch(r'runs/([0-9a-f]{32})/(.+)', name):
                return review.send_file(self, review.runs_folder(folder) / m[1], m[2])
            review.reply(self, 404, b'not found', 'text/plain')

        do_HEAD = do_GET

        def do_POST(self):
            action = self.path[len(prefix):] if self.path.startswith(prefix) else ''
            if action not in ('edit', 'cut', 'job', 'accept'):
                return review.reply(self, 404, b'not found', 'text/plain')
            body = review.from_page(self, prefix + action)
            if body is None:
                return
            try:
                if action == 'edit':
                    edit(Path(folder) / take['web'], body)
                    out = {'ok': True}
                elif action == 'cut':
                    edit_cut(edit_file(), config, body)
                    out = {'ok': True}
                elif action == 'job':
                    run = current(folder)
                    kind, beat = body.get('kind'), body.get('beat')
                    commands = {'recut': [*cli, 'recut', str(run[0]) if run else '', '--config', str(config)],
                                'preview': [*cli, 'preview', str(config)], 'run': [*cli, 'run', str(config)],
                                'from': [*cli, 'preview', str(config), '--from', str(beat)]}
                    if kind not in commands:
                        raise ValueError('unknown job')
                    if kind == 'recut' and not run:
                        raise ValueError('nothing to re-cut: record a run first')
                    if kind == 'from':
                        from reshoot import story
                        if beat not in [b['id'] for b in story.load(Path(folder) / take['web'])['beat']]:
                            raise ValueError(f'no beat {beat!r} in the storyboard')
                    job.start(kind, commands[kind], folder, beat)
                    out = {'ok': True}
                else:
                    run = current(folder)
                    if not run:
                        raise ValueError('no run to accept')
                    code, text = review.accept_from_page(str(run[0]), body)
                    print(text.rstrip(), flush=True)
                    out = {'code': code, 'output': text}
            except ValueError as e:
                out = {'ok': False, 'error': str(e), 'code': 2, 'output': str(e)}
            review.reply(self, 200, json.dumps(out).encode(), 'application/json')

    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', a.port or 0), Handler)
    return httpd, f'http://127.0.0.1:{httpd.server_address[1]}{prefix}', take


def serve(a):
    import webbrowser
    httpd, url, take = server(a)
    print(f'The studio is at {url}\nIt changes {take["web"]} and the edit file as you edit; press Ctrl-C to stop.',
          flush=True)
    if not a.no_open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Stopped.')
    finally:
        httpd.server_close()
    return 0


def page(data, accept, seen=0):
    from reshoot import timeline
    e = lambda v: html.escape(str(v if v is not None else ''), quote=True)
    run = data['run']
    seconds = lambda t: f'{t:.1f} s'
    pending = '<p class="pending"{}>Not in the video yet: re-cut to see it.</p>'
    beats = []
    for n, beat in enumerate(data['beats']):
        checks = beat.get('checks') or []
        passed = sum(c == 'passed' for c in checks)
        state = 'failed' if 'failed' in checks else 'passed' if checks else 'unverified'
        when = (f'{seconds(beat["start"])} to {seconds(beat["end"])}' if beat.get('start') is not None
                else 'not in this cut' if run and 'status' in beat else 'not recorded yet')
        frame = f'<img src="run/{e(beat["frame"])}" alt="The last frame of {e(beat["id"])}" loading="lazy">' if beat.get('frame') else '<div class="noframe">No frame yet</div>'
        changed = beat.get('changed')
        beats.append(f'''<li class="beat {state}" data-beat="{e(beat['id'])}" data-start="{e(beat.get('start'))}" data-end="{e(beat.get('end'))}">
  <button class="play" type="button" title="Play this beat"{'' if beat.get('start') is not None else ' disabled'}>{frame}<span>&#9654;</span></button>
  <div class="body">
    <div class="head"><strong>{n + 1}. {e(beat['id'])}</strong><span class="when">{when}</span></div>
    {f'<p class="purpose">{e(beat["purpose"])}</p>' if beat.get('purpose') else ''}
    <p class="checks">{f'{passed} of {len(checks)} result checks passed' if checks else 'No result checks'}</p>
    <label>Caption <input name="caption" value="{e(beat['caption'])}" placeholder="No caption"></label>
    <label>Second line <input name="sub" value="{e(beat['sub'])}" placeholder="None"></label>
    {pending.format('' if beat.get('pending') else ' hidden')}
    <p class="redo{' changed' if changed else ''}">{'Its actions, checks or hold changed since this recording. ' if changed else ''}<button type="button" data-from="{e(beat['id'])}" title="Start the app, replay the beats before this one off camera, and record from here">Record from here</button></p>
  </div>
</li>''')
    look = data['look']
    marks = ''
    if run:
        d = run['duration'] or 1
        marks = ''.join(f'<button class="seg {"failed" if "failed" in (b.get("checks") or []) else "passed" if b.get("checks") else "unverified"}" '
                        f'style="left:{100 * b["start"] / d:.3f}%;width:{max(.5, 100 * (b["end"] - b["start"]) / d):.3f}%" data-beat="{e(b["id"])}" title="{e(b["id"])}">'
                        f'<span>{e(b["id"])}</span></button>' for b in data['beats'] if b.get('start') is not None and b.get('end') is not None)
        marks += ''.join(f'<i class="flag" style="left:{100 * t / d:.3f}%" title="{e(f["name"])}: {e(f["found"])}"></i>'
                         for f in data['findings'] for t in f['times'])
    findings = ''.join(f'<li><strong>{e(f["name"])}</strong> {e(f["found"])}: {f["frames"]} frame{"s" if f["frames"] != 1 else ""}'
                       + ''.join(f' <button type="button" class="seek" data-t="{t}">{t:g} s</button>' for t in sorted(f['times'])[:6])
                       + '</li>' for f in data['findings'])
    options = lambda chosen: ''.join(f'<option value="{e(p)}"{" selected" if p == chosen else ""}>{e(p)}</option>' for p in timeline.PRESETS)
    shapes = []
    for x in (run or {}).get('exports', []):
        media = (f'<img src="run/{e(x["path"])}" alt="{e(Path(x["path"]).name)}" loading="lazy">' if x['path'].endswith('.gif')
                 else f'<video src="run/{e(x["path"])}" muted controls preload="metadata"></video>')
        shapes.append(f'''<figure class="shape"><div class="media" style="aspect-ratio:{x['width']}/{x['height']}">{media}</div>
<figcaption><a href="run/{e(x['path'])}" target="_blank">{e(Path(x['path']).name)}</a><br>{x['width']}&times;{x['height']}, {x['seconds']:.1f} s, {x['bytes'] / 1e6:.1f} MB
{f'<br><span class="fits">{e(x["fits"])}</span>' if x.get('fits') else ''}</figcaption></figure>''')
    cut = data['edit']
    if cut:
        cards = ''.join(f'''<li class="card" data-part="{c['i']}"><label>{c['where'].capitalize()} card <input name="text" value="{e(c['text'])}"></label>
<label class="short">Seconds <input name="duration" type="number" min="0.5" max="30" step="0.5" value="{e(c['duration'])}"></label>
<button type="button" class="remove" title="Remove this card">Remove</button></li>''' for c in cut['cards'])
        background = cut['background'] if isinstance(cut['background'], str) else ''
        music = ''.join(f'<option value="{e(m)}"{" selected" if m == cut["music"] else ""}>{e(m)}</option>' for m in cut['music_choices'])
        if cut['music'] and cut['music'] not in cut['music_choices']:
            music += f'<option value="{e(cut["music"])}" selected>{e(cut["music"])}</option>'
        exports = ''.join(f'''<li class="export" data-export="{x['i']}"><label>{e(x['file'])} <select name="preset">{'' if x['preset'] else '<option selected>custom</option>'}{options(x['preset'])}</select></label>
<button type="button" class="remove" title="Stop making this export">Remove</button></li>''' for x in cut['exports'])
        edit_box = f'''<div class="cut"><h2>The edit</h2><p class="hint">Saved to {e(cut['file'])} as you change it.</p>
<h3>Title cards</h3><ul class="cards">{cards or '<li class="hint">No cards.</li>'}</ul>
<p><button type="button" data-add-card="start">Add an opening card</button> <button type="button" data-add-card="end">Add a closing card</button></p>
<h3>Frame</h3><label class="check"><input type="checkbox" name="frame"{' checked' if cut['frame'] else ''}> A browser window round the page, on a background</label>
<label>Background <input name="background" value="{e(background)}" placeholder="#1d2433"{' disabled title="A gradient: change it in the file"' if not isinstance(cut['background'], str) else ''}></label>
<h3>Music</h3><label>Track <select name="music"><option value="">None</option>{music}</select></label>
{'' if cut['music_choices'] else '<p class="hint">Put a sound file in the project folder to choose it here.</p>'}
<h3>Exports</h3><ul class="exports-edit">{exports}</ul>
<label>Add an export <select name="add_export"><option value="">Choose a preset</option>{options(None)}</select></label>
{pending.format('' if cut['pending'] else ' hidden')}</div>'''
    else:
        edit_box = ''
    if run:
        top = (f'<p class="status">Run {e(run["id"][:8])}{" (a re-cut of " + e(run["recut_from"][:8]) + ")" if run["recut_from"] else ""}'
               f': {e(run["status"])}.</p><video id="video" src="run/{e(run["video"])}" controls preload="auto"></video>'
               f'<div class="timeline" aria-label="Beats in the video">{marks}<b id="head"></b></div>')
        if not run['captions_drawn']:
            top += '<p class="note">This run was recorded with its captions in the page, so a re-cut keeps them: record again to change them.</p>'
    else:
        top = '<p class="status">No run has worked yet. Record a preview to see the demo here.</p>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>reshoot studio</title><link rel="icon" href="data:,"><style>{STYLE}</style></head><body data-seen="{seen}">
<header><h1>reshoot studio</h1><span class="story">{e(data['story'])}</span>
<div class="actions"><button type="button" data-job="recut"{'' if run else ' disabled'} title="Edit and scan this run's takes again, with the captions and edit as they are now">Re-cut</button>
<button type="button" data-job="preview" title="Start the app and record a quick preview">Record a preview</button>
<button type="button" data-job="run" title="Start the app and record a final">Record</button></div></header>
<section id="job" hidden><p id="job-title"></p><video id="job-take" controls hidden></video><pre id="job-log"></pre></section>
<main><section class="watch">{top}
{f'<div class="shapes"><h2>Exports</h2><div class="grid">{"".join(shapes)}</div></div>' if shapes else ''}
{f'<div class="found"><h2>What the scan found</h2><ul>{findings}</ul></div>' if findings else ''}
<div class="accept">{accept}</div></section>
<section class="side"><div class="look"><h2>Caption look</h2>
<label>Place <select name="position"><option value="bottom"{' selected' if look.get('position', 'bottom') == 'bottom' else ''}>Bottom</option><option value="top"{' selected' if look.get('position') == 'top' else ''}>Top</option></select></label>
<label>Background <input name="background" value="{e(look.get('background', ''))}" placeholder="#0e0d0cc8"></label>
<label>Text <input name="foreground" value="{e(look.get('foreground', ''))}" placeholder="white"></label>
{pending.format('' if data['look_pending'] else ' hidden')}</div>
{edit_box}
<div class="beats"><h2>Beats</h2><p class="hint">Edits are saved to {e(data['story'])} as you leave a field.</p><ol>{''.join(beats)}</ol></div></section></main>
<p id="toast" role="status"></p>
<script>{SCRIPT}</script></body></html>'''


STYLE = '''
:root { --bg:#f6f5f2; --panel:#fff; --ink:#1d1b18; --muted:#6b665e; --line:#e3e0da; --accent:#1d4ed8; --ok:#15803d;
  --bad:#b91c1c; --idle:#a8a29e; --seg-ink:#fff; color-scheme: light dark; }
@media (prefers-color-scheme: dark) { :root { --bg:#131211; --panel:#1c1b19; --ink:#f1efe9; --muted:#a49e94;
  --line:#2e2c29; --accent:#7aa2ff; --ok:#4ade80; --bad:#f87171; --idle:#57534e; --seg-ink:#0b0b0a; } }
* { box-sizing:border-box } body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif }
header { display:flex; flex-wrap:wrap; gap:12px; align-items:center; padding:14px 20px; border-bottom:1px solid var(--line); background:var(--panel); position:sticky; top:0; z-index:2 }
h1 { font-size:17px; margin:0 } h2 { font-size:15px; margin:0 0 8px } h3 { font-size:13px; margin:14px 0 4px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em }
.story { color:var(--muted) } .actions { margin-left:auto; display:flex; gap:8px; flex-wrap:wrap }
button { font:inherit; border:1px solid var(--line); background:var(--panel); color:var(--ink); border-radius:8px; padding:6px 12px; cursor:pointer }
button:hover:not(:disabled) { border-color:var(--accent) } button:disabled { opacity:.5; cursor:default }
main { display:grid; grid-template-columns:minmax(0,1.4fr) minmax(320px,1fr); gap:20px; padding:20px; max-width:1500px; margin:auto }
@media (max-width:900px) { main { grid-template-columns:1fr; padding:16px } }
.watch > * + *, .side > * + * { margin-top:16px }
.watch > div, .side > div:not(.beats) { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px }
video { width:100%; border-radius:10px; background:#000; display:block }
.timeline { position:relative; height:34px; background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; margin-top:8px }
.seg { position:absolute; top:4px; bottom:4px; border-radius:5px; padding:0 6px; border:0; overflow:hidden; text-align:left; font-size:12px; color:var(--seg-ink); white-space:nowrap }
.seg.passed { background:var(--ok) } .seg.failed { background:var(--bad) } .seg.unverified { background:var(--idle) }
.flag { position:absolute; top:0; bottom:0; width:2px; background:var(--bad) }
#head { position:absolute; top:0; bottom:0; width:2px; background:var(--accent); left:0; pointer-events:none }
.status { margin:0; font-weight:600 } .note, .hint { color:var(--muted); margin:6px 0 }
label { display:block; margin-top:8px; font-size:13px; color:var(--muted) } label.check { color:var(--ink) }
input:not([type=radio]):not([type=checkbox]), select { display:block; width:100%; margin-top:3px; font:inherit; color:var(--ink); background:var(--bg); border:1px solid var(--line); border-radius:7px; padding:6px 8px }
.cards, .exports-edit { list-style:none; margin:0; padding:0 }
.card, .export { display:flex; gap:8px; align-items:end; flex-wrap:wrap } .card > label:first-child, .export > label { flex:1 1 200px }
.card .short { flex:0 0 90px } .card .remove, .export .remove { margin-bottom:1px }
.beats ol { list-style:none; margin:0; padding:0; display:grid; gap:12px }
.beat { display:grid; grid-template-columns:150px 1fr; gap:12px; background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--idle); border-radius:12px; padding:12px }
.beat.passed { border-left-color:var(--ok) } .beat.failed { border-left-color:var(--bad) } .beat.now { outline:2px solid var(--accent) }
@media (max-width:520px) { .beat { grid-template-columns:1fr } }
.play { position:relative; padding:0; overflow:hidden; aspect-ratio:16/9; align-self:start; background:var(--bg) }
.play img { width:100%; height:100%; object-fit:cover; display:block } .play span { position:absolute; inset:auto 6px 6px auto; background:#000a; color:#fff; border-radius:50%; width:26px; height:26px; display:grid; place-items:center; font-size:11px }
.noframe { display:grid; place-items:center; height:100%; color:var(--muted); font-size:12px }
.head { display:flex; justify-content:space-between; gap:8px } .when, .checks, .purpose { color:var(--muted); font-size:13px; margin:2px 0 }
.pending { color:var(--accent); font-size:13px; margin:8px 0 0; font-weight:600 }
.redo { margin:8px 0 0; font-size:13px; color:var(--muted) } .redo button { padding:3px 10px; font-size:13px }
.redo.changed { color:var(--bad); font-weight:600 } .redo.changed button { border-color:var(--bad) }
.found li { margin:4px 0 } .seek { padding:1px 8px; font-size:12px }
.grid { display:flex; flex-wrap:wrap; gap:14px; align-items:flex-end } .shape { margin:0; flex:0 1 auto }
.shape .media { height:170px; max-width:100%; background:#000; border-radius:8px; overflow:hidden }
.shape img, .shape video { width:100%; height:100%; object-fit:contain; border-radius:0 }
.shape figcaption { font-size:12px; color:var(--muted); margin-top:6px; max-width:300px } .fits { color:var(--ok) }
#job { margin:16px 20px 0; background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 14px }
#job-take { max-width:640px; margin:6px 0 }
#job-log { max-height:220px; overflow:auto; font-size:12px; white-space:pre-wrap; margin:6px 0 0 }
#toast { position:fixed; bottom:16px; left:50%; transform:translateX(-50%); background:var(--ink); color:var(--bg); padding:8px 14px; border-radius:8px; opacity:0; transition:opacity .2s; pointer-events:none; max-width:calc(100% - 32px) }
#toast.on { opacity:1 }
.accept fieldset { border:1px solid var(--line); border-radius:8px; margin:10px 0 } .accept fieldset label { color:var(--ink) }
'''

SCRIPT = '''(() => {
  const video = document.getElementById('video'), head = document.getElementById('head');
  const toast = text => { const t = document.getElementById('toast'); t.textContent = text; t.classList.add('on'); clearTimeout(t.timer); t.timer = setTimeout(() => t.classList.remove('on'), 2600); };
  const post = (what, body) => fetch(what, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)}).then(r => r.json());
  let stopAt = null;
  const play = (from, to) => { if (!video) return; stopAt = to; video.currentTime = from; video.play(); };
  if (video) video.addEventListener('timeupdate', () => {
    if (stopAt != null && video.currentTime >= stopAt) { video.pause(); stopAt = null; }
    head.style.left = (100 * video.currentTime / (video.duration || 1)) + '%';
    document.querySelectorAll('.beat').forEach(b => b.classList.toggle('now', b.dataset.start !== '' && video.currentTime >= +b.dataset.start && video.currentTime < +b.dataset.end));
  });
  const beat = id => document.querySelector(`.beat[data-beat="${CSS.escape(id)}"]`);
  document.querySelectorAll('.beat .play').forEach(b => b.onclick = () => { const li = b.closest('.beat'); play(+li.dataset.start, +li.dataset.end); });
  document.querySelectorAll('.seg').forEach(s => s.onclick = () => { const li = beat(s.dataset.beat); play(+li.dataset.start, +li.dataset.end); li.scrollIntoView({block: 'nearest', behavior: 'smooth'}); });
  document.querySelectorAll('.seek').forEach(s => s.onclick = () => { if (video) { stopAt = null; video.currentTime = +s.dataset.t; video.pause(); } });
  const saved = (out, where) => { if (!out.ok) return toast(out.error); toast('Saved'); const p = where.querySelector('.pending'); if (p) p.hidden = false; };
  document.querySelectorAll('.beat input').forEach(input => input.addEventListener('change', () => {
    const li = input.closest('.beat');
    post('edit', {beat: li.dataset.beat, [input.name]: input.value}).then(out => saved(out, li));
  }));
  document.querySelectorAll('.look input, .look select').forEach(input => input.addEventListener('change', () => {
    post('edit', {look: {[input.name]: input.value}}).then(out => saved(out, input.closest('.look')));
  }));
  // Changes to the edit file. One that adds or removes a card or an export reloads, to show it in the list.
  const cut = document.querySelector('.cut');
  const change = (body, reload) => post('cut', body).then(out => { saved(out, cut); if (out.ok && reload) setTimeout(() => location.reload(), 400); });
  if (cut) {
    cut.querySelectorAll('.card input').forEach(input => input.addEventListener('change', () =>
      change({card: +input.closest('.card').dataset.part, [input.name]: input.name === 'duration' ? +input.value : input.value})));
    cut.querySelectorAll('.card .remove').forEach(b => b.onclick = () => change({card: +b.closest('.card').dataset.part, remove: true}, true));
    cut.querySelectorAll('[data-add-card]').forEach(b => b.onclick = () => change({add_card: b.dataset.addCard}, true));
    cut.querySelector('[name=frame]').addEventListener('change', e => change({frame: e.target.checked}));
    cut.querySelector('[name=background]').addEventListener('change', e => change({background: e.target.value}));
    cut.querySelector('[name=music]').addEventListener('change', e => change({music: e.target.value}));
    cut.querySelectorAll('.export select').forEach(s => s.addEventListener('change', () => change({export: +s.closest('.export').dataset.export, preset: s.value}, true)));
    cut.querySelectorAll('.export .remove').forEach(b => b.onclick = () => change({export: +b.closest('.export').dataset.export, remove: true}, true));
    cut.querySelector('[name=add_export]').addEventListener('change', e => e.target.value && change({add_export: e.target.value}, true));
  }
  const box = document.getElementById('job'), log = document.getElementById('job-log'), title = document.getElementById('job-title'), take = document.getElementById('job-take');
  const names = {recut: 'Re-cutting', preview: 'Recording a preview', run: 'Recording', from: 'Recording from a beat'};
  const watch = () => fetch('job.json').then(r => r.json()).then(job => {
    if (!job.kind) return;
    box.hidden = false; log.textContent = job.lines.join('\\n'); log.scrollTop = log.scrollHeight;
    document.querySelectorAll('[data-job], [data-from]').forEach(b => b.disabled = job.running);
    const what = job.kind === 'from' ? `Recording from ${job.beat}` : names[job.kind];
    if (job.running) { title.textContent = what + '...'; take.hidden = true; return setTimeout(watch, 700); }
    if (job.kind === 'from') {
      title.textContent = job.code === 0 ? `${what} worked. Here is the take, from ${job.beat} on; when it looks right, record the run.` : what + ' failed.';
      if (job.take && take.getAttribute('src') !== job.take) { take.src = job.take; take.hidden = false; }
      return;
    }
    title.textContent = job.code === 0 ? what + ' worked. Loading the new run...' : what + ' failed; the page still shows the last run that worked.';
    if (job.code === 0 && job.n > +document.body.dataset.seen) setTimeout(() => location.reload(), 600);
  });
  document.querySelectorAll('[data-job]').forEach(b => b.onclick = () => post('job', {kind: b.dataset.job}).then(out => out.ok ? watch() : toast(out.error)));
  document.querySelectorAll('[data-from]').forEach(b => b.onclick = () => post('job', {kind: 'from', beat: b.dataset.from}).then(out => {
    if (!out.ok) return toast(out.error); box.scrollIntoView({behavior: 'smooth'}); watch(); }));
  watch();
})();'''
