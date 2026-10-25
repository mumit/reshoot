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
import hashlib, html, json, math, os, re, signal, subprocess, sys, threading, tomllib
from pathlib import Path
from reshoot.workspace import quote, tables, block, first_header, put, drop, read_lines, save
from reshoot.sequence import outputs, check_cut

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
        if 'hold' in change:
            value = change['hold']
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Hold must be a nonnegative number of seconds.')
            put(lines, block(lines, '[[beat]]', this), 'hold', value, after='id')
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
        if value:
            from reshoot.styles import colour
            colour(value, alpha=False)
        span = block(lines, '[style]')
        if span is None and value:
            at = first_header(lines)
            lines[at:at] = ['[style]\n', '\n']
            span = (at + 1, at + 1)
        if span:
            put(lines, span, 'background', value)
    if 'foreground' in change:
        value = change['foreground'] or None
        if value and not COLOUR.fullmatch(value):
            raise ValueError('the card text must be a colour such as #ffffff')
        if value:
            from reshoot.styles import colour
            colour(value, alpha=False)
        if block(lines, '[style]') is None:
            at = first_header(lines)
            lines[at:at] = ['[style]\n', '\n']
        put(lines, block(lines, '[style]'), 'foreground', value)
    if 'frame_background' in change:
        from reshoot.styles import background
        background(change['frame_background'])
        if block(lines, '[frame]') is None:
            raise ValueError('Turn on the browser frame before changing its background.')
        put(lines, block(lines, '[frame]'), 'background', change['frame_background'])
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
            previous = tomllib.loads(''.join(lines[start:end]))
            kept = {k: v for k, v in previous.items() if k in ('name', 'fit', 'focus', 'display_width', 'max_bytes', 'min_reading', 'poster_at')}
            lines[start:end] = [f'preset = {quote(change["preset"])}\n', *[f'{k} = {quote(v)}\n' for k, v in kept.items()], '\n']
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
        self.proc, self.cancelled = None, False
        self.result = None

    def running(self):
        return self.kind is not None and self.code is None

    def start(self, kind, cmd, cwd, beat=None, on_done=None, result=None):
        with self.lock:
            if self.running():
                raise ValueError(f'a {self.kind} is still running')
            self.kind, self.lines, self.code, self.n, self.beat = kind, [], None, self.n + 1, beat
            self.proc, self.cancelled = None, False
            self.result = result
        def go():
            from reshoot.safety import redact
            try:
                proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                        start_new_session=True)
                self.proc = proc
                if self.cancelled:
                    self.cancel()
                for line in proc.stdout:
                    self.lines.append(redact(line.rstrip()).replace(str(cwd) + '/', ''))
                code = proc.wait()
                if code == 0 and not self.cancelled and on_done:
                    on_done()
                self.code = 130 if self.cancelled else code
            except Exception as e:
                self.lines.append(redact(str(e)))
                self.code = 1
        threading.Thread(target=go, daemon=True).start()

    def cancel(self):
        self.cancelled = True
        proc = self.proc
        if proc and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGINT)
            except ProcessLookupError:
                return
            def stop():
                if proc.poll() is None:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            timer = threading.Timer(12, stop)
            timer.daemon = True
            timer.start()

    def json(self):
        return {'n': self.n, 'kind': self.kind, 'beat': self.beat, 'running': self.running(), 'code': self.code,
                'lines': self.lines[-400:], 'cancelled': self.cancelled,
                **(self.result if self.code == 0 and not self.cancelled and self.result else {})}


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


def failed(folder, take, config):
    """The newest failure, until a complete recording succeeds. Its media stays pinned like successful runs."""
    from reshoot import review
    from reshoot.artifacts import digest
    for root, report in review.runs(folder):
        if report.get('mode') == 'partial-preview' and report.get('ok'):
            continue
        if report.get('ok'):
            return None
        try:
            root, report = review.read(root)
            path = root / Path(take['out']).with_suffix('.take.json')
            meta = json.loads(path.read_text()) if path.exists() else {}
            failure = meta.get('failure') or {}
            board = Path(folder) / take['web']
            audit = root / 'repair.json'
            repair = json.loads(audit.read_text()) if audit.exists() else {}
            current_sha = digest(board)
            image = meta.get('failure_screenshot')
            return {'id': report['id'], 'binding': review.binding(root, report),
                    'message': meta.get('error') or '; '.join(report.get('errors', [])),
                    'image': str(Path(take['out']).parent / image) if image else None,
                    'repairable': failure.get('kind') in ('missing-target', 'ambiguous-target'), 'beat': failure.get('beat'),
                    'visual_repair': not failure.get('target', {}).get('frame'),
                    'candidates': failure.get('candidates', []),
                    'candidate_labels': failure.get('candidate_labels', []),
                    'repaired': repair.get('after') == current_sha,
                    'stale': (meta.get('story_sha256') is not None and meta['story_sha256'] != current_sha) or
                             (report.get('inputs', {}).get('config_sha256') is not None and report['inputs']['config_sha256'] != digest(config))}
        except (OSError, ValueError):
            continue
    return None


def view(folder, take, config, run=None):
    """What the page shows: the storyboard's beats and the edit, joined to the latest run's where there is one."""
    from reshoot import cut as cuts, review, story, timeline
    from reshoot.artifacts import digest
    from reshoot.check import findings, load
    from reshoot.config import read
    board_path = Path(folder) / take['web']
    board = story.load(board_path)
    shoot, _ = read(config)
    take = next((item for item in shoot.get('take', []) if item.get('web') == take['web'] and item.get('out') == take['out']), take)
    recording_size = take.get('size', board.get('size', '1280x720@1'))
    edit_path = Path(folder) / shoot['edit']['file'] if shoot.get('edit', {}).get('file') else None
    data = {'story': board_path.name, 'look': board.get('caption', {}), 'run': None, 'beats': [], 'findings': [],
            'edit': None, 'failure': failed(folder, take, config), 'recording_size': recording_size}
    from reshoot import audio, styles
    data['voices'] = audio.voices()
    data['voice_engine'] = board.get('voice_engine', '')
    data['styles'], data['styles_error'], data['current_style'] = {}, '', None
    try:
        data['styles'] = styles.choices(folder)
        data['current_style'] = styles.selected(config, data['styles'])
    except (ValueError, OSError) as error:
        data['styles_error'] = str(error)
    if edit_path and edit_path.is_file():
        from reshoot import framing
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
            'foreground': cut.get('style', {}).get('foreground', ''),
            'frame_background': timeline.frame_style(cut)['background'] if 'frame' in cut else '#1d2433',
            'music': cut.get('music', ''), 'music_choices': music,
            'audio': audio.settings(cut.get('audio')),
            'exports': [{'i': i, 'preset': p.get('preset'), 'name': p.get('name', p.get('preset', 'landscape')),
                         'framing': framing.describe(p),
                         'file': Path(o).name} for i, (p, o) in enumerate(zip(cut.get('export', []), outputs(cut, '.')))],
            'pending': False}
    run = run or current(folder)
    recorded, drawn, rows, look_drawn, recorded_voice = {}, {}, {}, None, {}
    if run:
        root, report = run
        if data['edit'] and report.get('inputs', {}).get('edit_sha256'):
            data['edit']['pending'] = report['inputs']['edit_sha256'] != digest(edit_path)
        clips = [p for p in review.exports(root, report) if p.endswith('.mp4')]
        master = str(Path(shoot.get('edit', {}).get('args', [take['out']])[0]).parent / cut.get('output', 'demo-final.mp4')) if data['edit'] else take['out']
        video = master if master in clips else clips[0] if clips else take['out']
        segments = timeline.read(root / video)['segments']
        source = (root / take['out']).resolve()
        recorded_voice = {row['beat']: row for row in load(source.with_suffix('.voice.json'), [])}
        meta = load(source.with_suffix('.take.json'), {})
        sidecar = load(source.with_suffix('.captions.json'), None)
        if sidecar:
            rows = {row['beat']: row for row in sidecar['captions']}
            drawn = {name: (row.get('text'), row.get('sub')) for name, row in rows.items()}
            look_drawn = sidecar.get('style', {})
        for beat in meta.get('beats', []):
            appearances = timeline.occurrences(segments, source, beat.get('start', 0), beat.get('end', beat.get('start', 0)))
            a, b = appearances[0] if appearances else (None, None)
            shot = beat.get('screenshot')
            recorded[beat['id']] = {
                'start': a, 'end': b, 'appearances': appearances,
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
        preferred = [master, *[str(Path(master).parent / profile['file']) for profile in (data['edit'] or {}).get('exports', [])]]
        order = {path: i for i, path in enumerate(preferred)}
        for path in sorted(review.exports(root, report), key=lambda path: (order.get(path, len(order)), path)):
            w, h, seconds = cuts.probe(root / path)
            size = (root / path).stat().st_size
            preset = presets.get(Path(path).name)
            quality_path = Path(path).with_suffix('.readability.json')
            quality = load(root / quality_path, None) if str(quality_path) in {f['path'] for f in report.get('files', [])} else None
            exports.append({'path': path, 'bytes': size, 'width': w, 'height': h, 'seconds': seconds,
                            'readability': quality,
                            'poster': str(Path(path).with_suffix('.poster.png')) if (root / Path(path).with_suffix('.poster.png')).exists() else None,
                            'preset': preset, 'fits': fits(timeline.PRESETS[preset][1] if preset else None, seconds, size)})
        poster = str(Path(video).with_suffix('.poster.png'))
        if not (root / poster).exists():
            poster = next((b['frame'] for b in recorded.values() if b.get('frame')), None) if video == take['out'] else None
        data['run'] = {'id': report['id'], 'status': review.status(root, report), 'video': video,
                       'duration': timeline.read(root / video)['duration'], 'mode': report.get('mode', 'final'),
                       'recut_from': report.get('recut_from'), 'accepted': report.get('review_status') == 'completed',
                       'exports': exports, 'captions_drawn': sidecar is not None,
                       'binding': review.binding(root, report),
                       'poster': poster,
                       'sheets': [str(p.relative_to(root)) for p in sorted((root / 'review').glob('[0-9]*.jpg'))]}
    for beat in board['beat']:
        spoken = board.get('voice', {}).get(beat['id'], '')
        previous_voice = recorded_voice.get(beat['id'], {})
        narration_pending = bool(run) and spoken != previous_voice.get('text', '')
        if run and spoken and not narration_pending:
            from reshoot.voice import cache_key
            try:
                narration_pending = Path(previous_voice.get('file', '')).stem != cache_key(spoken, board.get('voice_engine'))
            except SystemExit:
                narration_pending = True
        row = {'id': beat['id'], 'purpose': beat.get('purpose'), 'caption': beat.get('caption') or '',
               'sub': beat.get('sub') or '', 'hold': beat.get('hold', 1),
               'narration': spoken, 'narration_pending': narration_pending,
               'issue': beat.get('recording_issue'), **recorded.get(beat['id'], {})}
        if beat['id'] in drawn:
            row['pending'] = drawn[beat['id']] != (beat.get('caption') or None, beat.get('sub') or None)
        if row.get('definition'):
            row['changed'] = recorded_as(beat, rows.get(beat['id'])) != row['definition']
        data['beats'].append(row)
    data['look_pending'] = look_drawn is not None and look_drawn != board.get('caption', {})
    data['sequence'], data['sequence_error'] = None, ''
    if run and edit_path:
        from reshoot import sequence
        try:
            data['sequence'] = sequence.view(sequence.load(config, run[0]))
        except (ValueError, OSError) as error:
            data['sequence_error'] = str(error)
    return data


def update_kind(folder, config, take, run):
    """Caption and edit changes reuse a take; recording changes replay the app. Fail closed when unsure."""
    from reshoot import story
    from reshoot.artifacts import digest
    from reshoot.config import read
    if not run:
        return 'preview', 'Recording the first preview.'
    root, report = run
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
    if not (words_changed or caps.get('style', {}) != board.get('caption', {}) or edit_changed
            or report.get('inputs', {}).get('config_sha256') != digest(config)):
        return 'preview', 'Recording the app again for a fresh preview.'
    return 'recut', 'Updating captions and the edit using the existing recording.'


def server(a):
    """The studio's server, not yet serving, its address and the take it shapes."""
    import http.server, secrets
    from urllib.parse import unquote
    from reshoot import review
    config, folder, take = project(a.project)
    from reshoot.config import read
    from reshoot.workspace import History
    shoot, _ = read(config)
    editable = [config, *dict.fromkeys((Path(folder) / t['web']).resolve() for t in shoot.get('take', [])
                                     if str(t.get('web', '')).endswith('.toml')), Path(folder) / 'styles.toml']
    if shoot.get('edit', {}).get('file'):
        editable.append(Path(folder) / shoot['edit']['file'])
    history = History(editable)
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
                with history.lock:
                    history.check(history.revision())
                    run = current(folder)
                    accept = review.panel(*run, final_action='Make final') if run else ''
                    seen = job.n - job.running()
                    data = view(folder, take, config, run)
                    data.update(revision=history.revision(), undo=bool(history.undo), redo=bool(history.redo))
                    return review.reply(self, 200, page(data, accept, seen).encode())
            if name == 'job.json':
                out = job.json()
                if job.kind == 'from' and job.code == 0 and (partial := current(folder, partial=True)):
                    out['take'] = f'runs/{partial[1]["id"]}/' + take['out']
                return review.reply(self, 200, json.dumps(out).encode(), 'application/json')
            if name == 'style.toml':
                from reshoot import styles
                try:
                    with history.lock:
                        text = styles.dumps(styles.snapshot(config, 'My style'))
                    return review.reply(self, 200, text.encode(), 'application/toml')
                except (ValueError, OSError) as error:
                    return review.reply(self, 400, str(error).encode(), 'text/plain')
            if re.fullmatch(r'auditions/[0-9a-f]{64}\.wav', name):
                return review.send_file(self, Path(folder) / 'takes' / 'voice-cache', name.split('/')[1])
            if m := re.fullmatch(r'runs/([0-9a-f]{32})/(.+)', name):
                return review.send_file(self, review.runs_folder(folder) / m[1], m[2])
            review.reply(self, 404, b'not found', 'text/plain')

        do_HEAD = do_GET

        def do_POST(self):
            action = self.path[len(prefix):] if self.path.startswith(prefix) else ''
            if action not in ('edit', 'cut', 'style', 'sequence', 'framing', 'audio', 'job', 'accept', 'undo', 'redo', 'cancel'):
                return review.reply(self, 404, b'not found', 'text/plain')
            body = review.from_page(self, prefix + action)
            if body is None:
                return
            with history.lock:
                self.mutate(action, body)

        def mutate(self, action, body):
            try:
                if action == 'cancel':
                    job.cancel()
                    return review.reply(self, 200, b'{"ok":true}', 'application/json')
                if job.running():
                    raise ValueError('An update is running. Wait for it or cancel before changing the project.')
                history.check(body.get('revision'))
                if action == 'edit':
                    history.change(lambda: edit(Path(folder) / take['web'], body))
                    out = {'ok': True}
                elif action == 'cut':
                    history.change(lambda: edit_cut(edit_file(), config, body))
                    out = {'ok': True}
                elif action == 'sequence':
                    from reshoot import sequence
                    run = self.displayed(body)
                    before = history.snapshot()
                    data = sequence.load(config, run[0])
                    data['before'].update(before)
                    sequence.apply(data, body)
                    history.remember(before, history.snapshot())
                    out = {'ok': True}
                elif action == 'framing':
                    from reshoot import framing
                    before = history.snapshot()
                    if 'size' in body:
                        framing.recording(config, body['size'], expected=before)
                    else:
                        framing.apply(config, body.get('export'), body.get('settings'), expected=before)
                    history.remember(before, history.snapshot())
                    out = {'ok': True}
                elif action == 'audio':
                    from reshoot import audio
                    change = body.get('change')
                    if not isinstance(change, dict):
                        raise ValueError('Choose a narration or mix change.')
                    if 'engine' in change:
                        from reshoot import story
                        if change['engine'] is not None and not isinstance(change['engine'], str):
                            raise ValueError('Choose an installed voice.')
                        current_engine = story.load(Path(folder) / take['web']).get('voice_engine')
                        if (change['engine'] or '') not in audio.voices() and change['engine'] != current_engine:
                            raise ValueError('Choose an installed voice. Custom speech commands are edited in the storyboard.')
                    before = history.snapshot()
                    audio.apply(config, change, expected=before)
                    history.remember(before, history.snapshot())
                    out = {'ok': True}
                elif action == 'style':
                    from reshoot import styles
                    before = history.snapshot()
                    operation = body.get('operation')
                    if operation == 'save':
                        styles.save(config, body.get('name'))
                    elif operation == 'apply':
                        # The page selects only listed styles; arbitrary local paths are CLI-only.
                        spec = styles.choices(folder).get(body.get('key'))
                        if spec is None:
                            raise ValueError('This style is no longer available. Reload to choose a style.')
                        styles.apply(config, spec)
                    elif operation == 'import':
                        text = body.get('text')
                        if not isinstance(text, str) or len(text) > 16384:
                            raise ValueError('Choose a style TOML file smaller than 16 KB.')
                        styles.apply(config, styles.validate(tomllib.loads(text)))
                    else:
                        raise ValueError('Choose, save or import a style.')
                    history.remember(before, history.snapshot())
                    out = {'ok': True}
                elif action in ('undo', 'redo'):
                    history.move(action)
                    out = {'ok': True}
                elif action == 'job':
                    run = self.displayed(body) if body.get('run_id') else None
                    kind, beat = body.get('kind'), body.get('beat')
                    reason = ''
                    if kind == 'update':
                        kind, reason = update_kind(folder, config, take, run)
                    commands = {'recut': [*cli, 'recut', str(run[0]) if run else '', '--config', str(config)],
                                'preview': [*cli, 'preview', str(config)], 'run': [*cli, 'run', str(config)],
                                'from': [*cli, 'preview', str(config), '--from', str(beat)]}
                    on_done, result = None, None
                    if kind == 'audition':
                        from reshoot import audio
                        spec = audio.audition_spec(config, beat)
                        commands['audition'] = [*cli, 'audio', 'audition', beat, '--project', str(config), '--expected-key', spec['key']]
                        result = {'audio': 'auditions/' + spec['key'] + '.wav'}
                    if kind == 'repair':
                        from reshoot import repair
                        failure_id = body.get('failure_run_id', '')
                        if not re.fullmatch(r'[0-9a-f]{32}', failure_id):
                            raise ValueError('Reload to choose a failed recording.')
                        failed_root, failed_report = review.read(review.runs_folder(folder) / failure_id)
                        if body.get('failure_binding') != review.binding(failed_root, failed_report):
                            raise ValueError('The failure evidence changed. Reload before repairing it.')
                        diagnosis = repair.load(failed_root, config)
                        method = body.get('method')
                        if method not in ('apply', 'pick'):
                            raise ValueError('Choose a suggested replacement or select one in the app.')
                        before = history.snapshot()
                        def remember_repair():
                            with history.lock:
                                audit = json.loads((failed_root / 'repair.json').read_text())
                                after = history.snapshot()
                                board_path = diagnosis['board_path']
                                from reshoot.artifacts import digest
                                if (audit['before'] == diagnosis['meta']['story_sha256'] and
                                    audit['after'] == digest(board_path) and all(
                                        after[p] == before[p] for p in before if p != board_path)):
                                    history.remember(before, after)
                        on_done = remember_repair
                        commands['repair'] = [*cli, 'repair', str(failed_root), '--config', str(config), '--' + method]
                    if kind not in commands:
                        raise ValueError('unknown job')
                    if kind == 'recut' and not run:
                        raise ValueError('nothing to re-cut: record a run first')
                    if kind == 'from':
                        from reshoot import story
                        if beat not in [b['id'] for b in story.load(Path(folder) / take['web'])['beat']]:
                            raise ValueError(f'no beat {beat!r} in the storyboard')
                    job.start(kind, commands[kind], folder, beat, on_done=on_done, result=result)
                    out = {'ok': True, 'reason': reason}
                else:
                    run = self.displayed(body)
                    code, text = review.accept_from_page(str(run[0]), body)
                    print(text.rstrip(), flush=True)
                    out = {'code': code, 'output': text}
                out.update(revision=history.revision(), undo=bool(history.undo), redo=bool(history.redo))
            except (ValueError, OSError) as e:
                out = {'ok': False, 'error': str(e), 'code': 2, 'output': str(e)}
            review.reply(self, 200, json.dumps(out).encode(), 'application/json')

        def displayed(self, body):
            run_id = body.get('run_id', '')
            if not re.fullmatch(r'[0-9a-f]{32}', run_id):
                raise ValueError('Reload to choose a recording.')
            root, report = review.read(review.runs_folder(folder) / run_id)
            if body.get('binding') != review.binding(root, report):
                raise ValueError('This recording or its scan changed. Reload and review it again.')
            return root, report

    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', a.port or 0), Handler)
    httpd.reshoot_job = job
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
        httpd.reshoot_job.cancel()
        httpd.server_close()
    return 0


def page(data, accept, seen=0):
    from reshoot import timeline
    e = lambda v: html.escape(str(v if v is not None else ''), quote=True)
    run = data['run']
    failure = data.get('failure')
    failure_box = ''
    if failure:
        image = (f'<details><summary>Failure frame</summary><img src="runs/{e(failure["id"])}/{e(failure["image"])}" '
                 'alt="The page when the recording stopped" loading="lazy"></details>') if failure.get('image') else ''
        if failure['repaired']:
            message = 'Control updated. Update preview to verify the original task and result checks.'
            buttons = ''
        elif failure['stale']:
            message = 'The story changed since this failure. Update preview to get current evidence.'
            buttons = ''
        else:
            message = failure['message']
            buttons = ('<button type="button" data-repair="apply">Use suggested control</button> '
                       if failure.get('candidates') else '') + ('<button type="button" data-repair="pick">Choose replacement in app</button>'
                                                               if failure.get('repairable') and failure.get('visual_repair', True) else '')
        labels = failure.get('candidate_labels', [])
        suggestions = ''.join(f'<p>Suggested control: <strong>{e(labels[i] if i < len(labels) else "Replacement control")}</strong></p>'
                              f'<details><summary>Control details</summary><code>{e(json.dumps(target))}</code></details>'
                              for i, target in enumerate(failure.get('candidates', [])) if not failure['stale'])
        failure_box = (f'<div class="failure" data-failure="{e(failure["id"])}" data-binding="{e(failure["binding"])}">'
                       f'<h2>{"Repair ready to verify" if failure["repaired"] else "Recording needs attention"}</h2>'
                       f'<p>{e(message)}</p>{suggestions}<p>{buttons}</p>{image}</div>')
    seconds = lambda t: f'{t:.1f} s'
    pending = '<p class="pending"{}>Saved. Update preview to see this change.</p>'
    beats = []
    for n, beat in enumerate(data['beats']):
        checks = beat.get('checks') or []
        passed = sum(c == 'passed' for c in checks)
        state = 'failed' if 'failed' in checks else 'passed' if checks else 'unverified'
        when = (f'{seconds(beat["start"])} to {seconds(beat["end"])}' if beat.get('start') is not None
                else 'not in this cut' if run and 'status' in beat else 'not recorded yet')
        if len(beat.get('appearances', [])) > 1:
            when += f' · {len(beat["appearances"])} appearances'
        frame = f'<img src="run/{e(beat["frame"])}" alt="The last frame of {e(beat["id"])}" loading="lazy">' if beat.get('frame') else '<div class="noframe">No frame yet</div>'
        changed = beat.get('changed')
        beats.append(f'''<li class="beat {state}" data-beat="{e(beat['id'])}" data-start="{e(beat.get('start'))}" data-end="{e(beat.get('end'))}" data-appearances="{e(json.dumps(beat.get('appearances', [])))}">
  <button class="play" type="button" title="Play this beat"{'' if beat.get('start') is not None else ' disabled'}>{frame}<span>&#9654;</span></button>
  <div class="body">
    <div class="head"><strong>{n + 1}. {e(beat['id'])}</strong><span class="when">{when}</span></div>
    {f'<p class="purpose">{e(beat["purpose"])}</p>' if beat.get('purpose') else ''}
    <p class="checks">{f'{passed} of {len(checks)} result checks passed' if checks else 'No result checks'}</p>
    <label>Caption <input name="caption" value="{e(beat['caption'])}" placeholder="No caption"></label>
    <label>Second line <input name="sub" value="{e(beat['sub'])}" placeholder="None"></label>
    <label>Hold result (seconds) <input name="hold" type="number" min="0" step="0.5" value="{e(beat['hold'])}"></label>
    <details class="narration"><summary>Narration{': update needed' if beat.get('narration_pending') else ': added' if beat.get('narration') else ''}</summary>
    <form class="narration-form"><label>Spoken words <textarea name="text" maxlength="4000" rows="3" placeholder="Optional voiceover for this step">{e(beat.get('narration', ''))}</textarea></label>
    <p class="hint">The beat waits for this line. Save, then audition it before recording. Empty words remove the line.</p>
    {('<p class="narration-pending">Narration changed. Update preview records the task again to use these words and this voice.</p>') if beat.get('narration_pending') else ''}
    <button type="submit">Save narration</button> <button type="reset">Reset</button>
    <button type="button" data-audition="{e(beat['id'])}"{'' if beat.get('narration') else ' disabled'}>Audition saved line</button></form></details>
    {f'<p class="error">{e(beat["issue"])}</p>' if beat.get('issue') else ''}
    {pending.format('' if beat.get('pending') else ' hidden')}
    <p class="redo{' changed' if changed else ''}">{'Its actions, checks or hold changed since this recording. ' if changed else ''}<button type="button" data-from="{e(beat['id'])}" title="Start the app, replay the beats before this one off camera, and record from here">Record from here</button></p>
  </div>
</li>''')
    look = data['look']
    marks = ''
    if run:
        d = run['duration'] or 1
        marks = ''.join(f'<button class="seg {"failed" if "failed" in (b.get("checks") or []) else "passed" if b.get("checks") else "unverified"}" '
                        f'style="left:{100 * a / d:.3f}%;width:{max(.5, 100 * (z - a) / d):.3f}%" data-beat="{e(b["id"])}" data-start="{a}" data-end="{z}" title="{e(b["id"])}">'
                        f'<span>{e(b["id"])}</span></button>' for b in data['beats'] for a, z in b.get('appearances', []))
        marks += ''.join(f'<i class="flag" style="left:{100 * t / d:.3f}%" title="{e(f["name"])}: {e(f["found"])}"></i>'
                         for f in data['findings'] for t in f['times'])
    findings = ''.join(f'<li><strong>{e(f["name"])}</strong> {e(f["found"])}: {f["frames"]} frame{"s" if f["frames"] != 1 else ""}'
                       + ''.join(f' <button type="button" class="seek" data-t="{t}">{t:g} s</button>' for t in sorted(f['times'])[:6])
                       + '</li>' for f in data['findings'])
    options = lambda chosen: ''.join(f'<option value="{e(p)}"{" selected" if p == chosen else ""}>{e(p)}</option>' for p in timeline.PRESETS)
    shapes = []
    for x in (run or {}).get('exports', []):
        media = (f'<img src="run/{e(x["path"])}" alt="{e(Path(x["path"]).name)}" loading="lazy">' if x['path'].endswith('.gif')
                 else f'<video src="run/{e(x["path"])}"' + (f' poster="run/{e(x["poster"])}"' if x.get('poster') else '') + ' muted controls preload="metadata"></video>')
        quality = x.get('readability')
        viewing = quality['display_width'] if quality else max(160, min(x['width'], 640))
        def inspect_button(label, at=None):
            return f'<button type="button" data-inspect="run/{e(x["path"])}" data-view="{viewing}" data-time="{e(at)}">{e(label)}</button>'
        feedback = ''
        if quality:
            metrics = quality['metrics']
            sizes = [f'{label}: about {metrics[key]:g} px' for key, label in [('app_font_p10_px', 'Small app-text samples'),
                     ('caption_min_px', 'Smallest caption text'), ('card_min_px', 'Smallest title text')] if metrics.get(key) is not None]
            issues = ''.join(f'<li>{e(item["message"])}' + (f' {inspect_button(str(item["at"]) + " s", item["at"])}' if item.get('at') is not None and x['path'].endswith('.mp4') else '') + '</li>' for item in quality['issues'])
            feedback = f'''<div class="readability"><p>Measured at {viewing} px viewing width.</p><p>{e('; '.join(sizes))}</p>
{'<ul>' + issues + '</ul>' if issues else '<p>No measured hints here. Inspect the export to judge it.</p>'}
<details><summary>What was measured</summary>{''.join(f'<p>{e(note)}</p>' for note in quality['notes'])}</details></div>'''
        else:
            feedback = '<p class="hint">This older run has no readability measurements. Update preview to measure captions; record again for app-text samples.</p>'
        shapes.append(f'''<figure class="shape"><div class="media" style="aspect-ratio:{x['width']}/{x['height']}">{media}</div>
<figcaption><a href="run/{e(x['path'])}" target="_blank">{e(Path(x['path']).name)}</a><br>{x['width']}&times;{x['height']}, {x['seconds']:.1f} s, {x['bytes'] / 1e6:.1f} MB
{f'<br><span class="fits">{e(x["fits"])}</span>' if x.get('fits') else ''}<p>{inspect_button('Inspect at viewing size')}</p>{feedback}</figcaption></figure>''')
    cut = data['edit']
    sequence_box = ''
    if data.get('sequence'):
        sequence = data['sequence']
        def beat_options(names, selected):
            return ('<option value="">Choose a beat (current boundary is custom)</option>' if selected not in names else '') + ''.join(
                f'<option value="{e(name)}"{" selected" if name == selected else ""}>{e(name)}</option>' for name in names)
        part_boxes = []
        for part in sequence['parts']:
            i, playback = part['i'], part['play']
            is_card = part['card'] is not None
            label = f'Title: {part["card"]}' if is_card else f'Take {part["take"] + 1}: {part.get("file", "unavailable")}'
            controls = f'''<button type="button" data-part-play data-start="{e((playback or {}).get('start'))}" data-end="{e((playback or {}).get('end'))}"{'' if playback else ' disabled'}>Play part {i + 1}</button>
<button type="button" data-sequence="move" data-to="{i - 1}" aria-label="Move part {i + 1} earlier"{' disabled' if i == 0 else ''}>Earlier</button>
<button type="button" data-sequence="move" data-to="{i + 1}" aria-label="Move part {i + 1} later"{' disabled' if i == len(sequence['parts']) - 1 else ''}>Later</button>
<button type="button" data-sequence="duplicate" aria-label="Duplicate part {i + 1}">Duplicate</button>
<button type="button" data-sequence="remove" aria-label="Remove part {i + 1}"{' disabled' if len(sequence['parts']) == 1 else ''}>Remove</button>'''
            ranges = ''
            if not is_card and isinstance(part['take'], int) and 0 <= part['take'] < len(sequence['sources']):
                names = sequence['sources'][part['take']]['beats']
                ranges = f'''<form class="range-form"><label>From beat <select name="start">{beat_options(names, part['start'])}</select></label>
<label>Through beat (included) <select name="through">{beat_options(names, part['through'])}</select></label>
<button type="submit">Save range</button><button type="reset">Reset</button></form>'''
            elif is_card:
                ranges = f'<p class="hint">{part["seconds"]:g} seconds. <button type="button" data-edit-card="{i}">Edit title card</button></p>'
            part_boxes.append(f'''<li class="sequence-part" data-part="{i}"><strong>{i + 1}. {e(label)}</strong>
{ranges}{f'<p class="error">{e(part["error"])}</p>' if part['error'] else ''}<div class="part-actions">{controls}</div></li>''')
        sources = [s for s in sequence['sources'] if s['beats']]
        source_options = ''.join(f'<option value="{s["i"]}">Take {s["i"] + 1}: {e(s["file"])}</option>' for s in sources)
        first_names = sources[0]['beats'] if sources else []
        add = f'''<form id="add-clip"><h3>Add a clip</h3><label>Recorded take <select name="take">{source_options}</select></label>
<div class="range-form"><label>From beat <select name="start">{beat_options(first_names, first_names[0])}</select></label>
<label>Through beat (included) <select name="through">{beat_options(first_names, first_names[-1])}</select></label></div>
<button type="submit">Add clip to end</button> <button type="reset">Reset</button></form>''' if sources else '<p class="hint">Record takes with beat markers to add clips by name.</p>'
        sequence_box = f'''<div class="sequence" data-sources="{e(json.dumps(sequence['sources']))}"><h2>Your cut</h2>
<p class="hint">Choose what appears in the video and its order. Recording still runs the whole task and its result checks.</p>
<ol class="sequence-parts">{''.join(part_boxes)}</ol>{add}
<p class="hint">Through includes the beat and its result hold. Update preview to see the saved cut and enable part playback. Undo restores each edit.</p>
{pending.format('' if sequence['pending'] else ' hidden')}</div>'''
    elif cut:
        sequence_box = '<div class="sequence"><h2>Your cut</h2><p class="hint">Record a complete preview to choose and arrange its beats.</p>' + (
            f'<p class="error">{e(data["sequence_error"])}</p>' if data.get('sequence_error') else '') + '</div>'
    styles_box = ''
    if data.get('styles'):
        from reshoot import styles
        def css_colour(value):
            return '#' + ''.join(f'{part:02x}' for part in styles.colour(value))
        choices = []
        for key, spec in data['styles'].items():
            frame = spec['frame']
            background = frame['background'] if spec['frame_enabled'] else spec['card']['background']
            background = ('linear-gradient(' + ','.join(css_colour(c) for c in background) + ')'
                          if isinstance(background, list) else css_colour(background))
            caption = spec['caption']
            selected = key == data.get('current_style')
            choices.append(f'''<button type="button" class="style-choice" data-style="{e(key)}" aria-pressed="{str(selected).lower()}">
<span class="style-sketch{' framed' if spec['frame_enabled'] else ''}" aria-hidden="true" style="--style-bg:{e(background)};--caption-bg:{css_colour(caption['background'])};--caption-fg:{css_colour(caption['foreground'])};--bar-bg:{css_colour(frame['bar_color'])}">
<span class="sketch-window"><span class="sketch-bar"></span><span class="sketch-line"></span><span class="sketch-line"></span></span>
<span class="sketch-caption {e(caption['position'])}">Your caption</span></span>
<strong>{e(spec['name'])}</strong><span class="hint">{e(spec.get('description') or 'Saved in this project.')}</span></button>''')
        current_name = data['styles'].get(data.get('current_style'), {}).get('name', 'Custom look')
        styles_box = f'''<div class="visual-styles"><h2>Visual styles</h2><p id="current-style">Current: {e(current_name)}</p>
<p class="hint">Choose a look for captions, title cards and browser framing. These are style sketches; Update preview shows your video.</p>
<div class="style-grid">{''.join(choices)}</div>
<form id="save-style"><label>Save this look as <input name="style-name" placeholder="My launch style" maxlength="60" required></label><button type="submit">Save style</button></form>
<label>Import a style <input type="file" id="import-style" accept=".toml"></label>
<a href="style.toml" download="reshoot-style.toml" id="download-style">Download current style</a>
<p class="hint">Saved looks are available in this project. Import a downloaded style to use it in another project. Undo restores an applied look in one step.</p></div>'''
    elif data.get('styles_error'):
        styles_box = f'<div class="visual-styles"><h2>Visual styles</h2><p class="error">{e(data["styles_error"])}</p></div>'
    if cut:
        cards = ''.join(f'''<li class="card" data-part="{c['i']}"><label>{c['where'].capitalize()} card <input name="text" value="{e(c['text'])}"></label>
<label class="short">Seconds <input name="duration" type="number" min="0.5" max="30" step="0.5" value="{e(c['duration'])}"></label>
<button type="button" class="remove" title="Remove this card">Remove</button></li>''' for c in cut['cards'])
        background = cut['background'] if isinstance(cut['background'], str) else ''
        frame_background = cut['frame_background']
        frame_top = frame_background[0] if isinstance(frame_background, list) else frame_background
        frame_end = frame_background[1] if isinstance(frame_background, list) else ''
        music = ''.join(f'<option value="{e(m)}"{" selected" if m == cut["music"] else ""}>{e(m)}</option>' for m in cut['music_choices'])
        if cut['music'] and cut['music'] not in cut['music_choices']:
            music += f'<option value="{e(cut["music"])}" selected>{e(cut["music"])}</option>'
        export_rows = []
        for x in cut['exports']:
            framing = x['framing']
            if framing.get('error'):
                form = f'<p class="error">{e(framing["error"])} Fix these export fields in {e(cut["file"])}.</p>'
            else:
                crop = framing['fit'] == 'crop'
                guide = ''
                if run and run.get('poster'):
                    guide = f'''<button type="button" class="crop-guide" aria-label="Choose crop focus; keyboard users can use the position fields"{'' if crop else ' disabled'}>
<img src="run/{e(run['poster'])}" alt="Crop guide from the rendered video"><span class="crop-window"></span></button>
<p class="hint">Crop guide from this run. Click to aim; Update preview renders your choice.</p>'''
                form = f'''<form class="export-framing" data-export="{x['i']}" data-width="{framing['width']}" data-height="{framing['height']}">
<label>Framing <select name="fit"><option value="contain"{'' if crop else ' selected'}>Fit: keep the whole video</option><option value="crop"{' selected' if crop else ''}>Crop: fill the shape</option></select></label>
{guide}<div class="range-form"><label>Horizontal position (%) <input name="focus_x" type="number" min="0" max="100" step="any" value="{framing['focus'][0] * 100:g}"{'' if crop else ' disabled'} required></label>
<label>Vertical position (%) <input name="focus_y" type="number" min="0" max="100" step="any" value="{framing['focus'][1] * 100:g}"{'' if crop else ' disabled'} required></label></div>
<label>Viewing width (px) <input name="display_width" type="number" min="160" max="1920" step="1" value="{framing['display_width']}" required></label>
<p class="hint">0 is left or top; 100 is right or bottom. Viewing width changes inspection and measurements, not the encoded size.</p>
<button type="submit">Save framing</button> <button type="reset">Reset</button></form>'''
            export_rows.append(f'''<li class="export" data-export="{x['i']}"><label>{e(x['file'])} <select name="preset">{'' if x['preset'] else '<option selected>custom</option>'}{options(x['preset'])}</select></label>
<button type="button" class="remove" title="Stop making this export">Remove</button>{form}</li>''')
        exports = ''.join(export_rows)
        sizes = {data['recording_size']: 'Current: ' + data['recording_size'],
                 '960x540@1.5': 'Wide view: 960 x 540', '640x480@2': 'Compact view: 640 x 480',
                 '390x844@2': 'Portrait view: 390 x 844'}
        recording_box = f'''<form class="recording-view"><h3>Recording view</h3>
<label>First browser take <select name="size">{''.join(f'<option value="{e(value)}"{" selected" if value == data["recording_size"] else ""}>{e(label)}</option>' for value, label in sizes.items())}</select></label>
<p class="hint">A narrower view can enlarge app text. Saving this view makes Update preview record the whole task again; its actions and checks stay intact.</p>
<button type="submit">Save recording view</button> <button type="reset">Reset</button></form>'''
        audio_box = f'''<details class="audio-controls"><summary>Audio</summary>
<label>Voice <select data-voice>{''.join(f'<option value="{e(command)}"{" selected" if command == data.get("voice_engine", "") else ""}>{e(label)}</option>' for command, label in data.get('voices', {'': 'System default'}).items())}{f'<option value="{e(data["voice_engine"])}" selected>Project voice (configured in storyboard)</option>' if data.get('voice_engine') and data['voice_engine'] not in data.get('voices', {}) else ''}</select></label>
<p class="hint">Add spoken words under each step's Narration. Changing words or voice makes Update preview record the task again, keeping every result check.</p>
<label>Music track <select name="music"><option value="">None</option>{music}</select></label>
{'' if cut['music_choices'] else '<p class="hint">Put a sound file in the project folder to choose it here.</p>'}
<form class="audio-mix"><label>Narration level (%) <input name="voice_volume" type="number" min="0" max="200" step="any" required value="{e(cut['audio']['voice_volume'] * 100)}"></label>
<label>Music level (%) <input name="music_volume" type="number" min="0" max="100" step="any" required value="{e(cut['audio']['music_volume'] * 100)}"></label>
<label class="check"><input type="checkbox" name="duck"{' checked' if cut['audio']['duck'] else ''}> Lower music while narration speaks</label>
<p class="hint">100% keeps the source level; 0% mutes it. Muted narration still keeps its timing and subtitles. Save the balance, then Update preview to listen. Peaks are limited before encoding.</p>
<button type="submit">Save balance</button> <button type="reset">Reset</button></form>
{pending.format('' if cut['pending'] else ' hidden')}</details>'''
        edit_box = f'''<div class="cut"><h2>The edit</h2><p class="hint">Saved to {e(cut['file'])} as you change it.</p>
{recording_box}
<h3>Title cards</h3><ul class="cards">{cards or '<li class="hint">No cards.</li>'}</ul>
<p><button type="button" data-add-card="start">Add an opening card</button> <button type="button" data-add-card="end">Add a closing card</button></p>
<label>Card background <input name="background" value="{e(background)}" placeholder="#0e0d0c"{' disabled title="A gradient: change it in the file"' if not isinstance(cut['background'], str) else ''}></label>
<label>Card text <input name="foreground" value="{e(cut['foreground'])}" placeholder="#ffffff"></label>
<h3>Frame</h3><label class="check"><input type="checkbox" name="frame"{' checked' if cut['frame'] else ''}> A browser window round the page, on a background</label>
<label>Frame background <input name="frame_background" value="{e(frame_top)}" placeholder="#1d2433"></label>
<label>Gradient end (optional) <input name="frame_background_end" value="{e(frame_end)}" placeholder="Leave empty for one colour"></label>
<h3>Exports</h3><ul class="exports-edit">{exports}</ul>
<label>Add an export <select name="add_export"><option value="">Choose a preset</option>{options(None)}</select></label>
{pending.format('' if cut['pending'] else ' hidden')}</div>'''
    else:
        edit_box = audio_box = ''
    if run:
        top = (f'<p class="status">Run {e(run["id"][:8])}{" (a re-cut of " + e(run["recut_from"][:8]) + ")" if run["recut_from"] else ""}'
               f': {e(run["status"])}.</p><video id="video" src="run/{e(run["video"])}"' +
               (f' poster="run/{e(run["poster"])}"' if run.get('poster') else '') + ' controls preload="auto"></video>'
               f'<div class="timeline" aria-label="Beats in the video">{marks}<b id="head"></b></div>')
        if not run['captions_drawn']:
            top += '<p class="note">This run was recorded with its captions in the page, so a re-cut keeps them: record again to change them.</p>'
        if failure:
            top = '<p class="note">Previous successful recording. Update preview to verify the current story.</p>' + top
    else:
        top = '<p class="status">No run has worked yet. Record a preview to see the demo here.</p>'
    sheets = ''.join(f'<a href="run/{e(s)}" target="_blank"><img loading="lazy" src="run/{e(s)}" alt="Scan sheet {i + 1}"></a>'
                     for i, s in enumerate((run or {}).get('sheets', [])))
    evidence = (f'<details class="scan"><summary>Inspect scan sheets</summary><p>Open a sheet at full size to inspect the frames.</p>{sheets}</details>' if sheets else '')
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>reshoot studio</title><link rel="icon" href="data:,"><style>{STYLE}</style></head><body data-seen="{seen}">
<header><h1>reshoot studio</h1><span class="story">{e(data['story'])}</span>
<div class="actions"><button type="button" data-history="undo"{'' if data.get('undo') else ' disabled'}>Undo</button>
<button type="button" data-history="redo"{'' if data.get('redo') else ' disabled'}>Redo</button>
<button type="button" class="primary" data-job="update">Update preview</button>
<button type="button" data-job="run" title="Record the full-size video for review">Make final</button>
<details class="advanced"><summary>More</summary><button type="button" data-job="recut"{'' if run else ' disabled'} title="Edit and scan this run's takes again, with the captions and edit as they are now">Re-cut</button>
<button type="button" data-job="preview" title="Start the app and record a quick preview">Record a preview</button>
</details></div></header>
<p id="save-error" class="error" role="alert" hidden></p>
<section id="job" hidden><p id="job-title"></p><button type="button" id="cancel">Cancel update</button><video id="job-take" controls hidden></video><audio id="audition-player" controls hidden></audio><details><summary>Progress details</summary><pre id="job-log"></pre></details></section>
<main><section class="watch">{failure_box}{top}
{f'<div class="shapes"><h2>Exports</h2><p class="hint">Measurements describe this rendered run. Update preview to measure saved changes.</p><div class="grid">{"".join(shapes)}</div></div>' if shapes else ''}
{f'<div class="found"><h2>What the scan found</h2><ul>{findings}</ul></div>' if findings else ''}
{evidence}
<div class="accept">{accept}</div></section>
<section class="side"><div class="beats"><h2>Your story</h2><p class="hint">Choose a step to play it. Captions and timing save as you leave a field.</p><ol>{''.join(beats)}</ol></div>
{audio_box}
{sequence_box}
<details class="styling"><summary>Style and exports</summary>{styles_box}<div class="look"><h2>Caption look</h2>
<label>Place <select name="position"><option value="bottom"{' selected' if look.get('position', 'bottom') == 'bottom' else ''}>Bottom</option><option value="top"{' selected' if look.get('position') == 'top' else ''}>Top</option></select></label>
<label>Background <input name="background" value="{e(look.get('background', ''))}" placeholder="#0e0d0cc8"></label>
<label>Text <input name="foreground" value="{e(look.get('foreground', ''))}" placeholder="#ffffff"></label>
{pending.format('' if data['look_pending'] else ' hidden')}</div>
{edit_box}
</details></section></main>
<p id="toast" role="status"></p>
<dialog id="export-inspector"><form method="dialog"><button>Close</button></form><h2>Inspect the rendered export</h2><p id="inspector-size"></p><div class="inspection-rail"></div></dialog>
<script>{SCRIPT}</script></body></html>'''
    if run:
        document = document.replace('run/', f'runs/{run["id"]}/')
    return document.replace('data-seen="', f'data-revision="{e(data.get("revision", ""))}" '
                            f'data-run="{e((run or {}).get("id", ""))}" '
                            f'data-binding="{e((run or {}).get("binding", ""))}" data-seen="', 1)


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
@media (min-width:1100px) and (min-height:700px) {
  .watch { position:sticky; top:80px; align-self:start; max-height:calc(100dvh - 100px); overflow-y:auto; scrollbar-gutter:stable; overscroll-behavior:contain }
}
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
.primary { background:var(--accent); color:var(--panel); border-color:var(--accent); font-weight:600 }
.advanced { position:relative } .advanced[open] { display:flex; gap:6px; align-items:center }
summary { cursor:pointer; font-weight:600 } .styling, .audio-controls { background:var(--panel); padding:14px; border:1px solid var(--line); border-radius:12px }
.styling > div { margin-top:14px } .error { color:var(--bad); font-weight:600 }
#save-error { margin:12px 20px; padding:12px; border:1px solid var(--bad); border-radius:8px }
.scan img { max-width:100%; display:block; margin-top:10px } .watch { min-width:0 }
[data-unsaved] { outline:2px solid var(--bad) }
.failure { border-left:4px solid var(--bad) !important } .failure p { overflow-wrap:anywhere }
.failure img { width:100%; max-height:340px; object-fit:contain; margin-top:10px }
.style-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:10px }
.style-choice { display:flex; flex-direction:column; align-items:stretch; text-align:left; gap:8px; padding:8px; min-width:0 }
.style-choice[aria-pressed=true] { outline:2px solid var(--accent); outline-offset:1px }
.style-choice .hint { font-size:12px; font-weight:400; line-height:1.4 }
.style-sketch { display:block; position:relative; height:100px; overflow:hidden; background:var(--style-bg); border-radius:6px }
.sketch-window { position:absolute; inset:0; background:#f8fafc }
.framed .sketch-window { inset:12px 10px; border-radius:5px; box-shadow:0 3px 8px #0003; overflow:hidden }
.sketch-bar { display:none; height:10px; background:var(--bar-bg) } .framed .sketch-bar { display:block }
.sketch-line { display:block; width:65%; height:6px; margin:14px 12px 0; background:#cbd5e1; border-radius:3px }
.sketch-line + .sketch-line { width:45%; margin-top:6px }
.sketch-caption { position:absolute; bottom:8px; left:50%; transform:translateX(-50%); white-space:nowrap; padding:4px 7px; border-radius:4px; background:var(--caption-bg); color:var(--caption-fg); font-size:10px }
.sketch-caption.top { top:8px; bottom:auto }
#save-style { display:flex; align-items:end; gap:8px; margin:16px 0 10px } #save-style label { flex:1; min-width:0 }
#save-style button { flex-shrink:0; margin-bottom:8px }
.sequence-parts { list-style:none; padding:0; margin:12px 0; display:grid; gap:12px }
.sequence-part { padding:12px; border:1px solid var(--line); border-radius:8px; overflow-wrap:anywhere }
.part-actions { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px } .part-actions button { font-size:12px; padding:5px 8px }
.range-form { display:flex; flex-wrap:wrap; gap:8px; align-items:end; margin:8px 0 }
.range-form label { flex:1 1 120px; min-width:0 } .range-form button { font-size:13px; margin-bottom:1px }
#add-clip { border-top:1px solid var(--line); padding-top:8px }
.export-framing { flex:1 0 100%; border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:10px }
.crop-guide { display:block; padding:0; position:relative; overflow:hidden; width:100%; margin-top:10px; cursor:crosshair; border-radius:6px }
.crop-guide img { display:block; width:100%; pointer-events:none } .crop-window { position:absolute; border:2px solid #fbbf24; box-shadow:0 0 0 400px #0006; pointer-events:none }
.crop-guide:disabled .crop-window { display:none }
.readability { font-size:12px; line-height:1.5 } .readability li { margin:6px 0 } .readability button { font-size:11px; padding:2px 5px }
#export-inspector { color:var(--ink); background:var(--panel); border:1px solid var(--line); border-radius:12px; max-width:calc(100vw - 32px); max-height:calc(100vh - 32px); padding:16px }
#export-inspector::backdrop { background:#0009 } #export-inspector form { display:flex; justify-content:end; margin-bottom:12px }
.inspection-rail { overflow:auto; max-width:calc(100vw - 80px); max-height:calc(100vh - 180px) }
.inspection-rail img, .inspection-rail video { max-width:none; display:block; border-radius:0 }
.narration { margin:12px 0 } .narration summary { cursor:pointer; font-weight:600 }
.narration textarea { width:100%; resize:vertical; min-height:72px; font:inherit; color:var(--ink); background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:8px; box-sizing:border-box }
.audio-mix { border:1px solid var(--line); border-radius:8px; padding:12px; margin:12px 0 }
#audition-player { display:block; width:min(100%, 440px); margin-top:10px } #audition-player[hidden] { display:none }
'''

SCRIPT = '''(() => {
  document.querySelectorAll('details.styling, details.advanced, details.narration, details.audio-controls').forEach(box => {
    const key = location.pathname + ':' + box.className + ':' + (box.closest('.beat')?.dataset.beat || '');
    box.open = sessionStorage.getItem(key) === 'open';
    box.addEventListener('toggle', () => sessionStorage.setItem(key, box.open ? 'open' : 'closed'));
  });
  const video = document.getElementById('video'), head = document.getElementById('head');
  const toast = text => { const t = document.getElementById('toast'); t.textContent = text; t.classList.add('on'); clearTimeout(t.timer); t.timer = setTimeout(() => t.classList.remove('on'), 2600); };
  const error = text => { const box = document.getElementById('save-error'); box.textContent = text; box.hidden = !text; };
  let queue = Promise.resolve();
  const post = (what, body, requireSaved = false) => {
    const request = () => {
      const ownForm = what === 'sequence' && body.operation === 'range' ? document.querySelector(`.sequence-part[data-part="${body.part}"] .range-form`)
        : what === 'sequence' && body.operation === 'add' ? document.getElementById('add-clip')
        : what === 'framing' && body.size != null ? document.querySelector('.recording-view')
        : what === 'framing' ? document.querySelector(`.export-framing[data-export="${body.export}"]`)
        : what === 'audio' && body.change.beat != null ? document.querySelector(`.beat[data-beat="${CSS.escape(body.change.beat)}"] .narration-form`)
        : what === 'audio' && body.change.mix ? document.querySelector('.audio-mix') : null;
      const unsaved = [...document.querySelectorAll('[data-unsaved]')].some(input => !ownForm || !ownForm.contains(input));
      if ((requireSaved || ['job', 'undo', 'redo', 'style', 'sequence', 'framing', 'audio'].includes(what)) && unsaved) {
        const message = 'Fix the unsaved field before updating, undoing or changing the layout.';
        error(message); return {ok: false, error: message};
      }
      return fetch(what, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({run_id: document.body.dataset.run, binding: document.body.dataset.binding,
        revision: document.body.dataset.revision, ...body})}).then(r => r.json()).then(out => {
          if (out.revision) document.body.dataset.revision = out.revision;
          if (out.ok === false) error(out.error);
          else { if (!document.querySelector('[data-unsaved]')) error(''); document.querySelectorAll('[data-history]').forEach(b => { b.disabled = !out[b.dataset.history]; b.dataset.enabled = out[b.dataset.history] ? '1' : ''; }); }
          return out;
        }).catch(() => { const message = 'Could not save. Check that the studio is running, then try again.';
          error(message); return {ok: false, error: message}; });
    };
    queue = queue.then(request);
    return queue;
  };
  document.querySelectorAll('[data-history]').forEach(b => { b.dataset.enabled = b.disabled ? '' : '1'; b.onclick = () => post(b.dataset.history, {}).then(out => { if (out.ok) location.reload(); }); });
  document.querySelectorAll('[data-repair]').forEach(button => button.onclick = () => {
    const failure = button.closest('.failure');
    post('job', {kind: 'repair', method: button.dataset.repair, failure_run_id: failure.dataset.failure,
      failure_binding: failure.dataset.binding}).then(out => { if (out.ok) watch(); });
  });
  const styleChange = body => post('style', body, true).then(out => { if (out.ok) location.reload(); });
  const customStyle = () => {
    const label = document.getElementById('current-style'); if (label) label.textContent = 'Current: Custom look';
    document.querySelectorAll('[data-style]').forEach(button => button.setAttribute('aria-pressed', 'false'));
  };
  document.querySelectorAll('[data-style]').forEach(button => button.onclick = () => styleChange({operation: 'apply', key: button.dataset.style}));
  const saveStyle = document.getElementById('save-style');
  if (saveStyle) saveStyle.onsubmit = event => { event.preventDefault(); styleChange({operation: 'save', name: saveStyle.elements['style-name'].value}); };
  const importStyle = document.getElementById('import-style');
  if (importStyle) importStyle.onchange = async () => {
    const file = importStyle.files[0]; if (!file) return;
    if (file.size > 16384) { error('Choose a style TOML file smaller than 16 KB.'); importStyle.value = ''; return; }
    try { await styleChange({operation: 'import', text: await file.text()}); }
    catch (_) { error('Could not read the style file. Choose it again.'); }
    importStyle.value = '';
  };
  const downloadStyle = document.getElementById('download-style');
  if (downloadStyle) downloadStyle.onclick = event => {
    if (document.querySelector('[data-unsaved]')) { event.preventDefault(); error('Fix the unsaved field before downloading this look.'); }
  };
  let stopAt = null;
  const play = (from, to) => { if (!video) return; stopAt = to; video.currentTime = from; video.play(); };
  if (video) video.addEventListener('timeupdate', () => {
    if (stopAt != null && video.currentTime >= stopAt) { video.pause(); stopAt = null; }
    head.style.left = (100 * video.currentTime / (video.duration || 1)) + '%';
    document.querySelectorAll('.beat').forEach(b => b.classList.toggle('now', JSON.parse(b.dataset.appearances || '[]').some(([start, end]) => video.currentTime >= start && video.currentTime < end)));
  });
  const beat = id => document.querySelector(`.beat[data-beat="${CSS.escape(id)}"]`);
  document.querySelectorAll('.beat .play').forEach(b => b.onclick = () => { const li = b.closest('.beat'); play(+li.dataset.start, +li.dataset.end); });
  document.querySelectorAll('.seg').forEach(s => s.onclick = () => { const li = beat(s.dataset.beat); play(+s.dataset.start, +s.dataset.end); li.scrollIntoView({block: 'nearest', behavior: 'smooth'}); });
  document.querySelectorAll('[data-part-play]').forEach(button => button.onclick = () => play(+button.dataset.start, +button.dataset.end));
  const inspector = document.getElementById('export-inspector');
  document.querySelectorAll('[data-inspect]').forEach(button => button.onclick = () => {
    if (video) video.pause();
    const rail = inspector.querySelector('.inspection-rail'); rail.replaceChildren();
    const gif = button.dataset.inspect.endsWith('.gif');
    const media = document.createElement(gif ? 'img' : 'video');
    const width = Math.max(160, Math.min(1920, +button.dataset.view || 640));
    media.style.width = width + 'px'; media.style.height = 'auto';
    if (gif) media.alt = 'Rendered export at viewing size';
    else { media.controls = true; media.preload = 'metadata'; media.playsInline = true; }
    media.src = button.dataset.inspect; rail.append(media);
    document.getElementById('inspector-size').textContent = width + ' px viewing width. Scroll if it does not fit; the image is not scaled down to the panel.';
    inspector.showModal();
    if (!gif && button.dataset.time !== '') media.addEventListener('loadedmetadata', () => {
      media.currentTime = +button.dataset.time; media.play().catch(() => {});
    }, {once: true});
  });
  inspector.addEventListener('close', () => { const media = inspector.querySelector('video'); if (media) media.pause(); });
  const recordingView = document.querySelector('.recording-view');
  if (recordingView) {
    recordingView.elements.size.onchange = () => recordingView.elements.size.dataset.unsaved = '1';
    recordingView.onreset = () => { delete recordingView.elements.size.dataset.unsaved; if (!document.querySelector('[data-unsaved]')) error(''); };
    recordingView.onsubmit = event => { event.preventDefault(); post('framing', {size: recordingView.elements.size.value}, true)
      .then(out => { if (out.ok) location.reload(); }); };
  }
  document.querySelectorAll('.export-framing').forEach(form => {
    const guide = form.querySelector('.crop-guide'), image = guide && guide.querySelector('img');
    const focusX = form.elements.focus_x, focusY = form.elements.focus_y;
    const updateGuide = () => {
      const crop = form.elements.fit.value === 'crop';
      focusX.disabled = !crop; focusY.disabled = !crop; if (guide) guide.disabled = !crop;
      if (!image || !image.naturalWidth) return;
      const sw = image.naturalWidth, sh = image.naturalHeight, width = +form.dataset.width, height = +form.dataset.height;
      const scale = Math.max(width / sw, height / sh), rw = Math.ceil(sw * scale / 2) * 2, rh = Math.ceil(sh * scale / 2) * 2;
      const box = guide.querySelector('.crop-window');
      box.style.left = ((rw - width) * (+focusX.value / 100) / rw * 100) + '%';
      box.style.top = ((rh - height) * (+focusY.value / 100) / rh * 100) + '%';
      box.style.width = width / rw * 100 + '%'; box.style.height = height / rh * 100 + '%';
    };
    form.querySelectorAll('input, select').forEach(input => input.addEventListener('change', () => { input.dataset.unsaved = '1'; updateGuide(); }));
    form.addEventListener('reset', () => {
      form.querySelectorAll('[data-unsaved]').forEach(input => delete input.dataset.unsaved);
      if (!document.querySelector('[data-unsaved]')) error(''); setTimeout(updateGuide, 0);
    });
    if (image) { image.addEventListener('load', updateGuide); updateGuide(); }
    if (guide) guide.onclick = event => {
      if (!event.detail || !image.naturalWidth) return;
      const box = image.getBoundingClientRect(), width = +form.dataset.width, height = +form.dataset.height;
      const scale = Math.max(width / image.naturalWidth, height / image.naturalHeight);
      const rw = Math.ceil(image.naturalWidth * scale / 2) * 2, rh = Math.ceil(image.naturalHeight * scale / 2) * 2;
      const aim = (point, total, kept) => total === kept ? 50 : Math.round(Math.max(0, Math.min(1, (point * total - kept / 2) / (total - kept))) * 100);
      focusX.value = aim((event.clientX - box.left) / box.width, rw, width);
      focusY.value = aim((event.clientY - box.top) / box.height, rh, height);
      focusX.dataset.unsaved = '1'; focusY.dataset.unsaved = '1'; updateGuide();
    };
    form.onsubmit = event => { event.preventDefault();
      post('framing', {export: +form.dataset.export, settings: {fit: form.elements.fit.value,
        focus: [+focusX.value / 100, +focusY.value / 100], display_width: +form.elements.display_width.value}}, true)
        .then(out => { if (out.ok) location.reload(); });
    };
  });
  const sequence = document.querySelector('.sequence');
  document.querySelectorAll('.sequence form').forEach(form => {
    form.querySelectorAll('select').forEach(input => input.onchange = () => input.dataset.unsaved = '1');
    form.addEventListener('reset', () => {
      form.querySelectorAll('[data-unsaved]').forEach(input => delete input.dataset.unsaved);
      if (!document.querySelector('[data-unsaved]')) error('');
    });
  });
  const sequenceChange = body => post('sequence', body, true).then(out => { if (out.ok) location.reload(); });
  document.querySelectorAll('[data-sequence]').forEach(button => button.onclick = () => sequenceChange({operation: button.dataset.sequence,
    part: +button.closest('[data-part]').dataset.part, ...(button.dataset.to == null ? {} : {to: +button.dataset.to})}));
  document.querySelectorAll('.sequence-part .range-form').forEach(form => form.onsubmit = event => {
    event.preventDefault(); sequenceChange({operation: 'range', part: +form.closest('[data-part]').dataset.part,
      start: form.elements.start.value, through: form.elements.through.value});
  });
  const addClip = document.getElementById('add-clip');
  if (addClip) {
    const sources = JSON.parse(sequence.dataset.sources);
    const optionsForTake = () => {
      const names = sources.find(source => source.i === +addClip.elements.take.value).beats;
      ['start', 'through'].forEach(key => {
        const select = addClip.elements[key]; select.replaceChildren(...names.map(name => new Option(name, name)));
        select.value = names[key === 'start' ? 0 : names.length - 1];
      });
    };
    addClip.elements.take.addEventListener('change', optionsForTake);
    addClip.addEventListener('reset', () => setTimeout(optionsForTake, 0));
    addClip.onsubmit = event => { event.preventDefault(); sequenceChange({operation: 'add', take: +addClip.elements.take.value,
      start: addClip.elements.start.value, through: addClip.elements.through.value}); };
  }
  document.querySelectorAll('[data-edit-card]').forEach(button => button.onclick = () => {
    document.querySelector('.styling').open = true;
    const input = document.querySelector(`.cut .card[data-part="${button.dataset.editCard}"] input[name=text]`);
    if (input) { input.scrollIntoView({block: 'center'}); input.focus(); }
  });
  const pendingSequence = () => {
    if (sequence) { const pending = sequence.querySelector('.pending'); if (pending) pending.hidden = false; }
    document.querySelectorAll('[data-part-play]').forEach(button => button.disabled = true);
  };
  document.querySelectorAll('.seek').forEach(s => s.onclick = () => { if (video) { stopAt = null; video.currentTime = +s.dataset.t; video.pause(); } });
  const saved = (out, where, input) => { if (!out.ok) return toast(out.error); if (input) delete input.dataset.unsaved;
    if (!document.querySelector('[data-unsaved]')) error(''); toast('Saved'); const p = where.querySelector('.pending'); if (p) p.hidden = false; };
  document.querySelectorAll('.beat input').forEach(input => input.addEventListener('change', () => {
    const li = input.closest('.beat');
    input.dataset.unsaved = '1';
    post('edit', {beat: li.dataset.beat, [input.name]: input.name === 'hold' ? +input.value : input.value}).then(out => saved(out, li, input));
  }));
  document.querySelectorAll('.look input, .look select').forEach(input => input.addEventListener('change', () => {
    input.dataset.unsaved = '1';
    post('edit', {look: {[input.name]: input.value}}).then(out => { saved(out, input.closest('.look'), input); if (out.ok) customStyle(); });
  }));
  // Changes to the edit file. One that adds or removes a card or an export reloads, to show it in the list.
  const cut = document.querySelector('.cut');
  document.querySelectorAll('.narration-form, .audio-mix').forEach(form => {
    form.querySelectorAll('textarea, input').forEach(input => input.addEventListener('input', () => input.dataset.unsaved = '1'));
    form.addEventListener('reset', () => {
      form.querySelectorAll('[data-unsaved]').forEach(input => delete input.dataset.unsaved);
      if (!document.querySelector('[data-unsaved]')) error('');
    });
    form.onsubmit = event => {
      event.preventDefault();
      const change = form.matches('.narration-form') ? {beat: form.closest('.beat').dataset.beat, text: form.elements.text.value}
        : {mix: {voice_volume: +form.elements.voice_volume.value / 100, music_volume: +form.elements.music_volume.value / 100, duck: form.elements.duck.checked}};
      post('audio', {change}).then(out => { if (out.ok) location.reload(); });
    };
  });
  const voiceChoice = document.querySelector('[data-voice]');
  const savedVoice = voiceChoice ? voiceChoice.value : '';
  if (voiceChoice) voiceChoice.onchange = () => {
    post('audio', {change: {engine: voiceChoice.value || null}}).then(out => {
      if (out.ok) location.reload(); else voiceChoice.value = savedVoice;
    });
  };
  const change = (body, reload, input) => {
    if (input) input.dataset.unsaved = '1';
    return post('cut', body, reload).then(out => { saved(out, cut, input); if (out.ok) pendingSequence(); if (out.ok && reload) setTimeout(() => location.reload(), 400); return out; });
  };
  if (cut) {
    cut.querySelectorAll('.card input').forEach(input => input.addEventListener('change', () =>
      change({card: +input.closest('.card').dataset.part, [input.name]: input.name === 'duration' ? +input.value : input.value}, false, input)));
    cut.querySelectorAll('.card .remove').forEach(b => b.onclick = () => change({card: +b.closest('.card').dataset.part, remove: true}, true));
    cut.querySelectorAll('[data-add-card]').forEach(b => b.onclick = () => change({add_card: b.dataset.addCard}, true));
    cut.querySelector('[name=frame]').addEventListener('change', e => change({frame: e.target.checked}, false, e.target).then(out => { if (out.ok) customStyle(); }));
    ['background', 'foreground'].forEach(name => cut.querySelector(`[name=${name}]`).addEventListener('change', e =>
      change({[name]: e.target.value}, false, e.target).then(out => { if (out.ok) customStyle(); })));
    ['frame_background', 'frame_background_end'].forEach(name => cut.querySelector(`[name=${name}]`).addEventListener('change', e => {
      const top = cut.querySelector('[name=frame_background]').value, end = cut.querySelector('[name=frame_background_end]').value;
      change({frame_background: end ? [top, end] : top}, false, e.target).then(out => {
        if (out.ok) { delete cut.querySelector('[name=frame_background]').dataset.unsaved; delete cut.querySelector('[name=frame_background_end]').dataset.unsaved; customStyle(); }
      });
    }));
    document.querySelector('.audio-controls [name=music]').addEventListener('change', e => change({music: e.target.value}, false, e.target));
    cut.querySelectorAll('.export select[name=preset]').forEach(s => s.addEventListener('change', () => change({export: +s.closest('.export').dataset.export, preset: s.value}, true)));
    cut.querySelectorAll('.export .remove').forEach(b => b.onclick = () => change({export: +b.closest('.export').dataset.export, remove: true}, true));
    cut.querySelector('[name=add_export]').addEventListener('change', e => e.target.value && change({add_export: e.target.value}, true));
  }
  const box = document.getElementById('job'), log = document.getElementById('job-log'), title = document.getElementById('job-title'), take = document.getElementById('job-take');
  const auditionPlayer = document.getElementById('audition-player');
  auditionPlayer.addEventListener('play', () => { if (video) video.pause(); });
  if (video) video.addEventListener('play', () => auditionPlayer.pause());
  const names = {recut: 'Re-cutting', preview: 'Recording a preview', run: 'Recording', from: 'Recording from a beat', repair: 'Repairing control', audition: 'Preparing narration'};
  const watch = () => fetch('job.json').then(r => r.json()).then(job => {
    if (!job.kind) return;
    box.hidden = false; log.textContent = job.lines.join('\\n'); log.scrollTop = log.scrollHeight;
    document.getElementById('cancel').hidden = !job.running;
    document.querySelectorAll('[data-job], [data-from], [data-repair], .side input, .side textarea, .side select, .side button, [data-history]').forEach(button => {
      if (job.running) {
        if (!('jobDisabled' in button.dataset)) button.dataset.jobDisabled = button.disabled ? '1' : '';
        button.disabled = true;
      } else if ('jobDisabled' in button.dataset) {
        button.disabled = button.dataset.jobDisabled === '1'; delete button.dataset.jobDisabled;
      }
    });
    const what = job.kind === 'from' ? `Recording from ${job.beat}` : names[job.kind];
    if (job.running) { title.textContent = what + '...'; take.hidden = true; auditionPlayer.pause(); auditionPlayer.hidden = true; return setTimeout(watch, 700); }
    if (job.kind === 'audition') {
      title.textContent = job.cancelled ? 'Narration audition cancelled.' : job.code === 0 ? `Narration for ${job.beat}. Listen before updating the preview.` : 'Narration audition failed. Your saved story and previous recording are kept; see progress details.';
      if (job.audio) {
        const fresh = auditionPlayer.getAttribute('src') !== job.audio;
        if (fresh) auditionPlayer.src = job.audio;
        auditionPlayer.hidden = false;
        if (fresh && job.n > +document.body.dataset.seen) { if (video) video.pause(); auditionPlayer.play().catch(() => {}); }
      }
      return;
    }
    if (job.kind === 'from') {
      title.textContent = job.code === 0 ? `${what} worked. Here is the take, from ${job.beat} on; when it looks right, record the run.` : what + ' failed.';
      if (job.take && take.getAttribute('src') !== job.take) { take.src = job.take; take.hidden = false; }
      return;
    }
    title.textContent = job.cancelled ? 'Update cancelled. Your previous recording is kept.' : job.code === 0 ? what + ' worked. Loading the new run...' : what + ' failed; the page still shows the last run that worked.';
    if (job.code === 0 && job.n > +document.body.dataset.seen) setTimeout(() => location.reload(), 600);
  });
  document.getElementById('cancel').onclick = () => post('cancel', {}).then(watch);
  document.querySelectorAll('[data-audition]').forEach(button => button.onclick = () => post('job', {kind: 'audition', beat: button.dataset.audition}).then(out => {
    if (out.ok) { box.scrollIntoView({behavior: 'smooth'}); watch(); }
  }));
  document.querySelectorAll('[data-job]').forEach(b => b.onclick = () => post('job', {kind: b.dataset.job}).then(out => { if (out.ok) { if (out.reason) toast(out.reason); watch(); } }));
  document.querySelectorAll('[data-from]').forEach(b => b.onclick = () => post('job', {kind: 'from', beat: b.dataset.from}).then(out => {
    if (!out.ok) return toast(out.error); box.scrollIntoView({behavior: 'smooth'}); watch(); }));
  watch();
})();'''
