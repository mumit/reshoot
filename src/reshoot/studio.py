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
from reshoot.expectations import without_check, update_check, explain

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
    if 'remove_expect' in change:
        lines = without_check(lines, change.get('beat'), change['remove_expect'], change.get('expect'))
    if 'update_expect' in change:
        if 'remove_expect' in change:
            raise ValueError('Choose whether to correct or remove the check.')
        lines = update_check(lines, change.get('beat'), change['update_expect'], change.get('expect'), change.get('value'))
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
            check = None  # the result check that failed, said plainly, so the page can offer to remove it
            for beat in meta.get('beats', []):
                bad = next((i for i, x in enumerate(beat.get('expectations') or []) if x.get('status') == 'failed'), None)
                if bad is not None:
                    from reshoot import story
                    beats = story.load(board)['beat']
                    n = next((k for k, b in enumerate(beats) if b.get('id') == beat['id']), None)
                    expects = beats[n].get('expect', []) if n is not None else []
                    if n is not None and bad < len(expects):
                        error = beat['expectations'][bad].get('error', '')
                        check = {'beat': beat['id'], 'index': bad, 'expect': expects[bad], 'detail': error,
                                 'message': explain(n + 1, beat['id'], expects[bad], error)}
                    break
            return {'id': report['id'], 'binding': review.binding(root, report), 'check': check,
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
    from reshoot import create, setup
    tools = setup.current(config)
    try:
        creation = create.load(folder)
        data['create_error'] = ''
    except ValueError as error:
        creation = None
        data['create_error'] = str(error)
    pending_creation = creation and creation['stage'] != 'done'
    data['setup'] = tools if not tools['ok'] or pending_creation or not run and not current(folder) else None
    data['creation_pending'] = bool(pending_creation)
    data['needs_demonstration'] = bool(creation and creation['stage'] == 'record')
    data['resume_command'] = create.resume_command(folder) if pending_creation else ''
    from reshoot import comparison
    data['comparison'] = comparison.choices(folder, run or current(folder))
    from reshoot import audio, screenshots, styles, tours
    data['tour_spec'], data['tours'] = shoot.get('tour'), []
    take_index = next(i for i, item in enumerate(shoot['take']) if item.get('web') == take['web'] and item.get('out') == take['out'])
    data['screenshot_specs'] = shoot.get('screenshot', [])
    data['screenshot_take'] = take_index
    data['screenshots'] = []
    data['screenshot_beats'] = [{'id': beat['id'], 'alt': beat.get('purpose') or beat.get('caption') or 'Result of ' + beat['id']}
                               for beat in board['beat'] if beat.get('expect')]
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
        data['screenshots'] = screenshots.listing(root, report)
        data['tours'] = tours.listing(root, report)
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
            if not appearances and beat.get('start') is not None and beat.get('end', beat['start']) == beat['start']:
                at = place(segments, source, beat['start'])  # a step that takes no time, such as the last one
                appearances = [] if at is None else [[at, at]]
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
            if path.endswith(('.png', '.html')):
                continue
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
               'issue': beat.get('recording_issue'), 'expects': len(beat.get('expect', [])), **recorded.get(beat['id'], {})}
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
    data['journey'] = workflow(config, folder, take, run, context=data)
    data['downloads'] = []
    if run:
        from reshoot.delivery import files
        try:
            data['downloads'] = files(*run)
        except ValueError:
            pass
    return data


def workflow(config, folder, take, run, context=None, session=None):
    from reshoot import create, journey, setup
    state = journey.state(config, run)
    if context is None:
        creation = create.load(folder)
        creating = bool(creation and creation['stage'] != 'done')
        context = {'creation_pending': creating,
                   'setup': setup.current(config) if creating or not run else None,
                   'failure': failed(folder, take, config)}
    state = journey.workflow(state, creating=context.get('creation_pending', False), tools=context.get('setup'),
                             failure=context.get('failure'), session=session, has_run=bool(run))
    kind, reason = update_kind(folder, config, take, run)
    state.update(update_kind=kind, update_detail=reason)
    return state


def update_kind(folder, config, take, run):
    """Caption and edit changes reuse a take; recording changes replay the app. Fail closed when unsure."""
    from reshoot import story
    from reshoot.artifacts import digest
    from reshoot.config import read
    if not run:
        return 'preview', 'Recording the first preview.'
    root, report = run
    from reshoot import journey
    if journey.capture_changes(config, run):
        return 'preview', 'The task, timing, narration or demo data changed; recording a fresh preview.'
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
    sources_changed = journey.changed(report.get('inputs', {}).get('render_state'), journey.snapshot(config)) if report.get('inputs', {}).get('render_state') else []
    if not (words_changed or caps.get('style', {}) != board.get('caption', {}) or edit_changed or sources_changed
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
    from reshoot.session import Session
    shoot, _ = read(config)
    editable = [config, *dict.fromkeys((Path(folder) / t['web']).resolve() for t in shoot.get('take', [])
                                     if str(t.get('web', '')).endswith('.toml')), Path(folder) / 'styles.toml']
    if shoot.get('edit', {}).get('file'):
        editable.append(Path(folder) / shoot['edit']['file'])
    history = Session(config, editable)
    token = secrets.token_urlsafe(16)
    job = Job()
    prefix = f'/{token}/'
    cli = [sys.executable, '-m', 'reshoot.cli']

    def refresh_project():
        _, current_folder, current_take = project(config)
        data, _ = read(config)
        paths = [config, *dict.fromkeys((current_folder / item['web']).resolve() for item in data.get('take', [])
                                       if str(item.get('web', '')).endswith('.toml')), current_folder / 'styles.toml']
        if data.get('edit', {}).get('file'):
            paths.append(current_folder / data['edit']['file'])
        if not job.running():
            history.refresh(paths)
        return current_take

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
                    active_take = refresh_project()
                    run = current(folder)
                    accept = review.panel(*run, final_action='Make final') if run else ''
                    seen = job.n - job.running()
                    data = view(folder, active_take, config, run)
                    data.update(revision=history.revision(), undo=bool(history.undo), redo=bool(history.redo),
                                session=history.info())
                    return review.reply(self, 200, page(data, accept, seen).encode())
            if name == 'job.json':
                out = job.json()
                if job.kind == 'from' and job.code == 0 and (partial := current(folder, partial=True)):
                    out['take'] = f'runs/{partial[1]["id"]}/' + take['out']
                return review.reply(self, 200, json.dumps(out).encode(), 'application/json')
            if name == 'comparison.json':
                from urllib.parse import parse_qs, urlsplit
                try:
                    from reshoot import comparison
                    query = {key: values[0] for key, values in parse_qs(urlsplit(self.path).query).items()}
                    result = comparison.model(folder, query.get('run_id'), query.get('binding'),
                                              query.get('previous_id'), query.get('previous_binding'))
                    return review.reply(self, 200, json.dumps(result).encode(), 'application/json')
                except (ValueError, OSError, TypeError, KeyError) as error:
                    return review.reply(self, 409, json.dumps({'error': str(error)}).encode(), 'application/json')
            if m := re.fullmatch(r'comparison-frame/([0-9a-f]{32})/([0-9a-f]{64})/([0-9a-f]{64})\.png', name):
                try:
                    from reshoot import comparison
                    return review.reply(self, 200, comparison.frame(folder, *m.groups()), 'image/png')
                except (ValueError, OSError, TypeError, KeyError) as error:
                    return review.reply(self, 409, str(error).encode(), 'text/plain')
            if m := re.fullmatch(r'comparison-review/([0-9a-f]{32})/([0-9a-f]{64})/(.+)', name):
                try:
                    from reshoot import comparison
                    root, report = comparison.read(folder, m[1], m[2])
                    target = (root / m[3]).resolve()
                    if not target.is_relative_to(root):
                        raise ValueError('Review evidence must stay in its run.')
                    expected = {item['path']: item['sha256'] for item in report.get('files', [])}.get(str(target.relative_to(root)))
                    return review.send_file(self, root, m[3], expected_sha256=expected)
                except (ValueError, OSError, TypeError, KeyError) as error:
                    return review.reply(self, 409, str(error).encode(), 'text/plain')
            if name == 'session.zip':
                from urllib.parse import parse_qs, urlsplit
                try:
                    token = parse_qs(urlsplit(self.path).query).get('token', [''])[0]
                    with history.lock, history.transaction(recovery=True), history.source_copy(token) as archive:
                        archive.seek(0, 2); length = archive.tell(); archive.seek(0)
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/zip')
                        self.send_header('Content-Length', str(length))
                        self.send_header('Content-Disposition', 'attachment; filename="reshoot-saved-sources.zip"')
                        self.send_header('Cache-Control', 'no-store')
                        self.end_headers()
                        if self.command != 'HEAD':
                            import shutil
                            shutil.copyfileobj(archive, self.wfile)
                    return
                except (BrokenPipeError, ConnectionResetError):
                    return
                except (ValueError, OSError) as error:
                    return review.reply(self, 409, str(error).encode(), 'text/plain')
            if name == 'state.json':
                from urllib.parse import parse_qs, urlsplit
                try:
                    query = {key: values[0] for key, values in parse_qs(urlsplit(self.path).query).items()}
                    with history.lock:
                        active_take = refresh_project()
                        run = self.displayed(query) if query.get('run_id') else None
                        state = workflow(config, folder, active_take, run, session=history.info())
                        state['external'] = query.get('revision') != history.revision()
                        state['revision'] = history.revision()
                        state['session_pending'] = history.pending
                    return review.reply(self, 200, json.dumps(state).encode(), 'application/json')
                except (ValueError, OSError) as error:
                    return review.reply(self, 409, json.dumps({'error': str(error)}).encode(), 'application/json')
            if m := re.fullmatch(r'download/([0-9a-f]{32})/([0-9a-f]{64})/exports.zip', name):
                try:
                    from reshoot.delivery import bundle
                    run = review.read(review.runs_folder(folder) / m[1])
                    if review.binding(*run) != m[2]:
                        raise ValueError('This recording or its scan changed. Reload before downloading.')
                    with bundle(*run) as archive:
                        archive.seek(0, 2); length = archive.tell(); archive.seek(0)
                        mode = 'preview' if run[1].get('mode', 'final') != 'final' else 'final'
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/zip')
                        self.send_header('Content-Length', str(length))
                        self.send_header('Content-Disposition', f'attachment; filename="reshoot-{mode}-{m[1][:8]}.zip"')
                        self.send_header('Cache-Control', 'no-store')
                        self.end_headers()
                        if self.command != 'HEAD':
                            import shutil
                            shutil.copyfileobj(archive, self.wfile, length=1024 * 1024)
                    return
                except (BrokenPipeError, ConnectionResetError):
                    return
                except (ValueError, OSError) as error:
                    return review.reply(self, 409, str(error).encode(), 'text/plain')
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
            if action not in ('edit', 'cut', 'style', 'sequence', 'framing', 'audio', 'screenshot', 'tour', 'job', 'accept', 'undo', 'redo', 'cancel', 'session'):
                return review.reply(self, 404, b'not found', 'text/plain')
            body = review.from_page(self, prefix + action)
            if body is None:
                return
            with history.lock:
                try:
                    if action == 'cancel':
                        return self.mutate(action, body)
                    with history.transaction(recovery=action == 'session'):
                        self.mutate(action, body)
                except (ValueError, OSError) as error:
                    return review.reply(self, 200, json.dumps({'ok': False, 'error': str(error),
                                                               'code': 2, 'output': str(error)}).encode(), 'application/json')

        def mutate(self, action, body):
            try:
                if action == 'cancel':
                    job.cancel()
                    return review.reply(self, 200, b'{"ok":true}', 'application/json')
                if job.running():
                    raise ValueError('An update is running. Wait for it or cancel before changing the project.')
                # GET refreshes tracked paths. Mutations validate that same set
                # without acquiring the storage lock recursively.
                _, _, take = project(config)
                history.check(body.get('revision'))
                if action == 'session':
                    history.recover(body.get('choice'), body.get('session_token'))
                    out = {'ok': True}
                elif action == 'edit':
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
                elif action == 'screenshot':
                    from reshoot import screenshots
                    before = history.snapshot()
                    screenshots.apply(config, body.get('operation'), body.get('name'), body.get('settings'), expected=before)
                    history.remember(before, history.snapshot())
                    out = {'ok': True}
                elif action == 'tour':
                    from reshoot import tours
                    before = history.snapshot()
                    tours.apply(config, body.get('change'), expected=before)
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
                    from reshoot import create
                    try:
                        creation = create.load(folder)
                    except ValueError:
                        creation = None
                    if creation and creation['stage'] != 'done' and kind in ('update', 'preview', 'run', 'from', 'recut'):
                        raise ValueError('Creation is paused. Use Continue creation in Recording tools to finish your saved task first.')
                    if kind == 'update':
                        kind, reason = update_kind(folder, config, take, run)
                    commands = {'recut': [*cli, 'recut', str(run[0]) if run else '', '--config', str(config)],
                                'preview': [*cli, 'preview', str(config)], 'run': [*cli, 'run', str(config)],
                                'from': [*cli, 'preview', str(config), '--from', str(beat)]}
                    if kind == 'setup':
                        commands['setup'] = [sys.executable, '-m', 'reshoot.setup', str(config)]
                    elif kind == 'create':
                        from reshoot import create
                        creation = create.load(folder)
                        if not creation or creation['stage'] == 'done':
                            raise ValueError('No paused creation here. Use Update preview to refresh this project.')
                        commands['create'] = [*cli, 'create', '--resume', '--directory', str(folder), '--no-studio']
                    if kind in ('preview', 'run', 'from', 'recut', 'repair'):
                        from reshoot import setup
                        if not setup.current(config)['ok']:
                            raise ValueError('Recording tools need attention. Open Recording tools and choose Check again before updating.')
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
                            with history.lock, history.transaction():
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
                    from reshoot import journey
                    if journey.state(config, run)['pending']:
                        raise ValueError('Saved edits are not in this recording yet. Update preview or make a final before accepting here.')
                    code, text = review.accept_from_page(str(run[0]), body)
                    print(text.rstrip(), flush=True)
                    out = {'code': code, 'output': text}
                run = self.displayed(body) if body.get('run_id') else None
                out.update(revision=history.revision(), undo=bool(history.undo), redo=bool(history.redo),
                           journey=workflow(config, folder, take, run, session=history.info()))
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
    from reshoot import expectations, journey, timeline
    e = lambda v: html.escape(str(v if v is not None else ''), quote=True)
    run = data['run']
    failure = data.get('failure')
    state = journey.workflow(data.get('journey', {'title': 'Shape your demo', 'detail': '', 'pending': False,
                             'phase': 'unknown', 'next': 'update', 'changes': [], 'update_detail': ''}),
                             creating=data.get('creation_pending', False), tools=data.get('setup'),
                             failure=failure, session=data.get('session'), has_run=bool(run))
    failure_box = ''
    if failure:
        again = state['continuation']['label']
        image = (f'<details><summary>Failure frame</summary><img src="runs/{e(failure["id"])}/{e(failure["image"])}" '
                 'alt="The page when the recording stopped" loading="lazy"></details>') if failure.get('image') else ''
        if failure['repaired']:
            message = state['detail']
            buttons = ''
        elif failure['stale']:
            message = state['detail']
            buttons = ''
        elif failure.get('check'):
            check = failure['check']
            message = (check['message'] + ' If that is the result you meant to show, fix the app or its demo data. If '
                       f'the check is wrong, correct its expected result below, then choose {again}.')
            correction = expectations.form(check)
            if not correction:
                message = check['message'] + f' Fix the app or the check in the storyboard, then choose {again}.'
            buttons = (correction + '<details><summary>Remove a check that is not needed</summary>'
                       '<p>This removes this proof of the task. The next recording still has to pass its remaining checks. Undo restores it.</p>'
                       f'<button type="button" data-remove-check data-beat="{e(check["beat"])}" data-index="{check["index"]}" '
                       f'data-expect="{e(json.dumps(check["expect"]))}">Remove this check</button></details>')
        else:
            message = failure['message'][:1].upper() + failure['message'][1:]
            label = (failure.get('candidate_labels') or [None])[0]
            use = f'Use "{label}"' if label else 'Use suggested control'
            buttons = (f'<button type="button" data-repair="apply">{e(use)}</button> '
                       if failure.get('candidates') else '') + ('<button type="button" data-repair="pick">Choose replacement in app</button>'
                                                               if failure.get('repairable') and failure.get('visual_repair', True) else '')
        labels = failure.get('candidate_labels', [])
        suggestions = ''.join((f'<p>Suggested control: <strong>{e(labels[i] if i < len(labels) else "Replacement control")}</strong></p>'
                               if i >= len(labels) or f'"{labels[i]}"' not in failure['message'] else '') +
                              f'<details><summary>Control details</summary><code>{e(json.dumps(target))}</code></details>'
                              for i, target in enumerate(failure.get('candidates', [])) if not failure['stale'])
        detail = (f'<details><summary>Details</summary><pre>{e(failure["check"]["detail"])}</pre></details>'
                  if failure.get('check') and not failure['stale'] else '')
        failure_box = (f'<div class="failure" data-failure="{e(failure["id"])}" data-binding="{e(failure["binding"])}">'
                       f'<h2>{"Repair ready to verify" if failure["repaired"] else "Recording needs attention"}</h2>'
                       f'<p>{e(message)}</p>{suggestions}{buttons}{detail}{image}</div>')
    seconds = lambda t: f'{t:.1f} s'
    pending = '<p class="pending"{}>Saved. Update preview to see this change.</p>'
    beats = []
    shot_beats = {beat['id'] for beat in data.get('screenshot_beats', [])}
    for n, beat in enumerate(data['beats']):
        checks = beat.get('checks') or []
        passed = sum(c == 'passed' for c in checks)
        check_state = 'failed' if 'failed' in checks else 'passed' if checks else 'unverified'
        when = (f'at {seconds(beat["start"])}' if beat.get('start') is not None and beat["start"] == beat["end"]
                else f'{seconds(beat["start"])} to {seconds(beat["end"])}' if beat.get('start') is not None
                else 'not in this cut' if run and 'status' in beat else 'not recorded yet')
        if len(beat.get('appearances', [])) > 1:
            when += f' · {len(beat["appearances"])} appearances'
        frame = f'<img src="run/{e(beat["frame"])}" alt="The last frame of {e(beat["id"])}" loading="lazy">' if beat.get('frame') else '<div class="noframe">No frame yet</div>'
        changed = beat.get('changed')
        beats.append(f'''<li class="beat {check_state}" data-beat="{e(beat['id'])}" data-start="{e(beat.get('start'))}" data-end="{e(beat.get('end'))}" data-appearances="{e(json.dumps(beat.get('appearances', [])))}">
  <button class="play" type="button" title="Play this beat"{'' if beat.get('start') is not None else ' disabled'}>{frame}<span>&#9654;</span></button>
  <div class="body">
    <div class="head"><strong>{n + 1}. {e(beat['id'])}</strong><span class="when">{when}</span></div>
    {f'<p class="purpose">{e(beat["purpose"])}</p>' if beat.get('purpose') else ''}
    <p class="checks">{f'{passed} of {len(checks)} result checks passed' if checks else
                       f'{beat["expects"]} result check{"" if beat["expects"] == 1 else "s"}, not run yet' if beat.get('expects') else 'No result checks'}</p>
    {f'<button type="button" data-shot-beat="{e(beat["id"])}">Use for docs</button>' if beat['id'] in shot_beats and run else ''}
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
    screenshot_forms = []
    for spec in data.get('screenshot_specs', []):
        crop = spec.get('crop', [0, 0, 1, 1])
        source = next((row['source'] for row in data.get('screenshots', []) if row['name'] == spec['name'] and row['beat'] == spec['beat'] and row['take'] == spec.get('take', 0)), None)
        if source is None and spec.get('take', 0) == data.get('screenshot_take', 0):
            source = next((beat.get('frame') for beat in data['beats'] if beat['id'] == spec['beat']), None)
        crop_fields = ''.join(f'<label>{label} (%) <input name="crop_{key}" type="number" min="0" max="100" step="any" value="{value * 100:g}" required></label>'
                              for key, label, value in zip(('x', 'y', 'w', 'h'), ('Left', 'Top', 'Width', 'Height'), crop))
        crop_guide = (f'<div class="shot-crop-guide" aria-label="Drag to choose a crop; use the percentage fields with a keyboard"><img src="run/{e(source)}" alt="Captured page used for this screenshot" draggable="false"><span></span></div>' if source else '')
        screenshot_forms.append(f'''<form class="screenshot-form" data-operation="set" data-name="{e(spec['name'])}" data-take="{spec.get('take', 0)}" data-beat="{e(spec['beat'])}">
<strong>{e(spec['name'])}.png</strong><p class="hint">Take {spec.get('take', 0) + 1}, beat {e(spec['beat'])}.</p>
<label>Alt text <textarea name="alt" rows="2" maxlength="300" required>{e(spec['alt'])}</textarea></label>
<label>Maximum width (px; blank keeps captured size) <input name="width" type="number" min="160" max="3840" step="1" value="{e(spec.get('width', ''))}"></label>
<details class="shot-crop"><summary>Crop</summary><p class="hint">Drag a rectangle on the captured page or enter percentages. Save and Update preview to inspect the PNG.</p>{crop_guide}<div class="range-form">{crop_fields}</div><button type="button" data-whole-shot>Use whole captured page</button></details>
<button type="submit">Save screenshot</button> <button type="reset">Reset</button>
<button type="button" data-remove-shot="{e(spec['name'])}">Remove screenshot</button></form>''')
    eligible = data.get('screenshot_beats', [])
    new_shot = (f'''<form class="screenshot-form" id="add-screenshot" data-operation="add" data-take="{data.get('screenshot_take', 0)}" data-beats="{e(json.dumps(eligible))}">
<h3>Add a screenshot</h3><label>Checked result <select name="beat">{''.join(f'<option value="{e(beat["id"])}">{e(beat["id"])}</option>' for beat in eligible)}</select></label>
<label>File name (without .png) <input name="name" required maxlength="80" pattern="[a-zA-Z0-9_-]+" placeholder="search-result"></label>
<label>Alt text <textarea name="alt" rows="2" maxlength="300" required placeholder="Describe the visible result"></textarea></label>
<label>Maximum width (px; blank keeps captured size) <input name="width" type="number" min="160" max="3840" step="1"></label>
<button type="submit">Save screenshot</button> <button type="reset">Reset</button></form>'''
                if eligible else '<p class="hint">Add a result check to a story step to use its captured frame for documentation.</p>')
    screenshot_box = f'''<details class="screenshots-controls"><summary>Documentation screenshots</summary>
<p class="hint">Choose a checked result and describe it. Update preview makes a PNG from its captured page frame, then includes it in scanning and review. The cursor may be visible; video captions, framing and zoom are not added.</p>
{''.join(screenshot_forms)}{new_shot}</details>'''
    shot_images = ''.join(f'''<figure><a href="run/{e(row['path'])}"><img src="run/{e(row['path'])}" alt="{e(row['alt'])}" loading="lazy"></a>
<figcaption><strong>{e(row['name'])}.png</strong> · {row['pixels'][0]} × {row['pixels'][1]}<br>{e(row['alt'])}</figcaption>
<button type="button" data-inspect="run/{e(row['path'])}" data-view="{row['pixels'][0]}" data-time="" data-alt="{e(row['alt'])}">Inspect PNG at image size</button>
<a href="run/{e(row['path'])}" download="{e(row['name'])}.png">Download PNG</a></figure>''' for row in data.get('screenshots', []))
    spec = data.get('tour_spec')
    tour_forms = []
    if spec:
        for i, step in enumerate(spec['step']):
            marker = step.get('hotspot', [.5, .5])
            rendered = next((row for tour in data.get('tours', []) for row in tour['steps']
                             if row['take'] == step.get('take', 0) and row['beat'] == step['beat'] and row.get('crop') == step.get('crop')), None)
            image = rendered['image'] if rendered else next((beat.get('frame') for beat in data['beats']
                    if step.get('take', 0) == data.get('screenshot_take') and beat['id'] == step['beat'] and not step.get('crop')), None)
            guide = (f'<button type="button" class="tour-point" aria-label="Choose click marker position; keyboard users can use the percentage fields"><img src="run/{e(image)}" alt="Captured screen for this tour step"><span>{i + 1}</span></button>' if image else '<p class="hint">Update preview to see this step image and choose a marker on it.</p>')
            tour_forms.append(f'''<li class="tour-step" data-step="{i}"><strong>{i + 1}. Take {step.get('take', 0) + 1}, beat {e(step['beat'])}</strong>
<form class="tour-form" data-operation="set" data-step="{i}"><label>Step title <input name="title" maxlength="120" required value="{e(step['title'])}"></label>
<label>Explanation <textarea name="text" rows="3" maxlength="1000">{e(step.get('text', ''))}</textarea></label>
<label>Image alt text <textarea name="alt" rows="2" maxlength="300" required>{e(step['alt'])}</textarea></label>
<details class="tour-marker"><summary>Click marker</summary><p class="hint">Optional: click the image to position a marker that moves to the next captured step. Next and keyboard navigation always work.</p>
{guide}<label class="check"><input name="marker" type="checkbox"{' checked' if 'hotspot' in step else ''}> Show a click marker</label>
<div class="range-form"><label>Horizontal (%) <input name="x" type="number" min="0" max="100" step="any" required value="{marker[0] * 100:g}"></label>
<label>Vertical (%) <input name="y" type="number" min="0" max="100" step="any" required value="{marker[1] * 100:g}"></label></div></details>
<button type="submit">Save step</button> <button type="reset">Reset</button></form>
<div class="part-actions"><button type="button" data-tour-op="move" data-to="{i - 1}"{' disabled' if i == 0 else ''}>Earlier</button>
<button type="button" data-tour-op="move" data-to="{i + 1}"{' disabled' if i + 1 == len(spec['step']) else ''}>Later</button>
<button type="button" data-tour-op="remove"{' disabled' if len(spec['step']) == 1 else ''}>Remove step</button></div></li>''')
        tour_box = f'''<details class="tour-controls"><summary>Clickable tour</summary><p class="hint">A single offline HTML file of checked screens. These interactions explore the recording. Save changes, then Update preview to build it.</p>
<form class="tour-form" id="tour-title" data-operation="title"><label>Tour title <input name="title" maxlength="120" required value="{e(spec['title'])}"></label><button type="submit">Save title</button> <button type="reset">Reset</button></form>
<ol class="tour-steps">{''.join(tour_forms)}</ol>
<form class="tour-form" id="tour-add" data-operation="add" data-take="{data.get('screenshot_take', 0)}"><label>Add a checked step <select name="beat">{''.join(f'<option value="{e(beat["id"])}">{e(beat["id"])}</option>' for beat in eligible)}</select></label>
<button type="submit"{'' if eligible else ' disabled'}>Add step</button></form><p><button type="button" data-disable-tour>Stop exporting this tour</button></p></details>'''
    else:
        tour_box = f'''<details class="tour-controls"><summary>Clickable tour</summary><p class="hint">Make one offline HTML walkthrough from the checked steps. Viewers explore captured screens with Next, arrow keys or optional click markers.</p>
<form class="tour-form" id="tour-create" data-operation="create"><label>Tour title <input name="title" maxlength="120" required value="Explore the demo"></label>
<label>File name (without .html) <input name="name" maxlength="80" pattern="[a-zA-Z0-9_-]+" required value="demo-tour"></label>
<button type="submit"{'' if eligible else ' disabled'}>Create from checked steps</button><button type="reset">Reset</button></form></details>'''
    tour_previews = ''.join(f'''<article><h3>{e(tour['title'])}</h3><p>{len(tour['steps'])} captured steps · works offline</p>
<p><a href="run/{e(tour['path'])}" target="_blank" rel="noopener">Open walkthrough</a> · <a href="run/{e(tour['path'])}" download="{e(tour['name'])}.html">Download HTML</a></p>
<iframe src="run/{e(tour['path'])}" title="{e(tour['title'])}" sandbox="allow-scripts" loading="lazy"></iframe></article>''' for tour in data.get('tours', []))
    look = data['look']
    marks = ''
    if run:
        d = run['duration'] or 1
        marks = ''.join(f'<button class="seg {"failed" if "failed" in (b.get("checks") or []) else "passed" if b.get("checks") else "unverified"}" '
                        f'style="left:{100 * a / d:.3f}%;width:{max(.5, 100 * (z - a) / d):.3f}%" data-beat="{e(b["id"])}" data-start="{a}" data-end="{z}" title="{e(b["id"])}">'
                        f'<span>{e(b["id"])}</span></button>' for b in data['beats'] for a, z in b.get('appearances', []) if z > a)
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
               f'<div class="timeline" aria-label="Beats in the video"{"" if marks else " hidden"}>{marks}<b id="head"></b></div>')
        if not run['captions_drawn']:
            top += '<p class="note">This run was recorded with its captions in the page, so a re-cut keeps them: record again to change them.</p>'
        if failure:
            top = '<p class="note">Previous successful recording. Update preview to verify the current story.</p>' + top
    else:
        top = ('' if failure else '<p class="status">Your preview will appear here after setup and creation.</p>' if data.get('creation_pending') else
               '<p class="status">No run has worked yet. Record a preview to see the demo here.</p>')
    sheets = ''.join(f'<a href="run/{e(s)}" target="_blank"><img loading="lazy" src="run/{e(s)}" alt="Scan sheet {i + 1}"></a>'
                     for i, s in enumerate((run or {}).get('sheets', [])))
    evidence = (f'<details class="scan"><summary>Inspect scan sheets</summary><p>Open a sheet at full size to inspect the frames.</p>{sheets}</details>' if sheets else '')
    session = data.get('session')
    tools = data.get('setup')
    tools_box = ''
    if tools:
        def tool_rows(items):
            return ''.join(f'<li><strong>{e(item["label"])}</strong>: {e(item["status"])}'
                           f'<p>{e(item["detail"])}</p>' +
                           (f'<p class="fix">{e(item["action"])}</p>' if item['status'] in ('missing', 'failed') else '') + '</li>'
                           for item in items)
        problems = [item for item in tools['checks'] if item['status'] in ('missing', 'failed')]
        checks = tool_rows(problems)
        all_checks = tool_rows(tools['checks'])
        ready = (' class="primary"' if state['action']['kind'] == 'create' else '') if state['actions']['create']['enabled'] else ' disabled'
        go_on = f'<button type="button" data-job="create"{ready}>Continue creation</button>' if data.get('creation_pending') else ''
        continuation = go_on + (f'<p>Or restart from a terminal: <code>{e(data["resume_command"])}</code></p>' if go_on else '')
        if tools['ok'] and not data.get('create_error'):  # nothing to fix: one line, and the way to go on
            tools_box = f'''<section id="setup-panel" class="journey tools-ready" data-phase="ready" tabindex="-1"><p><strong>Recording tools are ready.</strong>
<button type="button" data-job="setup">Check again</button> {go_on}</p>
<details><summary>All tool checks ({len(tools['checks'])})</summary><ul>{all_checks}</ul></details></section>'''
        else:
            tools_box = f'''<section id="setup-panel" class="journey" data-phase="{'ready' if tools['ok'] else 'pending'}" tabindex="-1"><h2>Recording tools</h2>
<p>{('Synthetic tool checks passed. Continue when you are ready.' if tools.get('probed') else 'Tools are installed. Check again tests them; continuing creation also tests them before using your app.') if tools['ok'] else 'Your project is saved. Fix the items below, then check again.'}</p>
{f'<p class="error">{e(data["create_error"])}</p>' if data.get('create_error') else ''}
<ul>{checks}</ul><p class="hint">Run installation fixes in a terminal. If PATH, browser settings or the Python environment change, restart reshoot. Nothing is installed by these buttons.</p>
<button type="button" data-job="setup">Check again</button>{continuation}
<details><summary>All tool checks ({len(tools['checks'])})</summary><ul>{all_checks}</ul></details>
<p class="hint">Check again tests only a temporary made-up page, video and text. It does not use your app, validate face detection or approve media.</p>
{f'<p class="hint">Last checked: {e(tools["checked_at"])}</p>' if tools.get('checked_at') else ''}</section>'''
    recovery = ''
    if session:
        copy = (f'<a href="session.zip?token={e(session["token"])}" download="reshoot-saved-sources.zip">Download saved source copy</a>'
                if session['download'] else '')
        resume = ('<button type="button" data-session="resume" class="primary">Resume history</button>'
                  if session['resume'] else '')
        changes = f'<p>Changed files: {e(", ".join(session["changed"]))}</p>' if session['changed'] else ''
        problem = f'<p class="error">{e(session["problem"])}</p>' if session['problem'] else ''
        recovery = f'''<section id="session-recovery" class="journey" aria-labelledby="session-title" data-token="{e(session['token'])}">
<h2 id="session-title">{e(session['title'])}</h2><p>{e(session['detail'])}</p>{changes}{problem}
<p>Undo: {session['undo']} {'step' if session['undo'] == 1 else 'steps'} · Redo: {session['redo']} {'step' if session['redo'] == 1 else 'steps'}</p>{resume}
<button type="button" data-session="fresh">Start with current files</button> {copy}
<p class="hint">Starting fresh keeps a local archive of the previous history. Neither choice replaces the files you have now.</p></section>'''
    comparison = data.get('comparison', {'choices': [], 'default': '', 'note': 'Make two recordings to compare.'})
    comparison_options = ''.join(f'<option value="{e(row["id"])}" data-binding="{e(row["binding"])}"{(" selected" if row["id"] == comparison["default"] else "")}>'
                      f'{"Accepted · " if row["accepted"] else ""}{e(row["id"][:8])} · {e(row["finished_at"][:19].replace("T", " "))} UTC · {e(row["mode"])}</option>'
                      for row in comparison['choices'])
    compare_box = f'''<details id="compare-panel" class="compare-panel"><summary>Compare revisions</summary>
<p>{e(comparison['note'])}</p>
{f'<label>Earlier recording <select id="comparison-source">{comparison_options}</select></label><button type="button" id="compare-refresh">Compare frames</button>' if comparison_options and run else ''}
<p class="hint">Both sides stay tied to the chosen recordings. Comparing does not change the story or accept either run.</p>
<p id="comparison-status" role="status"></p><div id="comparison-results" aria-busy="false"></div></details>'''
    nav = [*([('setup-panel', 'Tools')] if tools else []), ('preview-panel', 'Preview'), ('story-panel', 'Story'), ('compare-panel', 'Compare'), *([('cut-panel', 'Cut')] if data.get('edit') else []),
           ('look-panel', 'Look'), *([('audio-panel', 'Audio')] if data.get('edit') else []),
           ('screenshots-panel', 'Screenshots'), ('tour-panel', 'Tour'), ('review-panel', 'Review'), ('download-panel', 'Download')]
    if not run:  # before a first working recording, only the story and its preview can do anything
        nav = [row for row in nav if row[0] in ('setup-panel', 'preview-panel', 'story-panel')]
    optional = {'compare-panel', 'audio-panel', 'screenshots-panel', 'tour-panel'}
    nav_link = lambda target, label: f'<a href="#{target}" data-jump="{target}">{label}</a>'
    navigation = ''.join(nav_link(target, label) for target, label in nav if target not in optional)
    extra = ''.join(nav_link(target, label) for target, label in nav if target in optional)
    if extra:
        navigation += f'<details class="more-tools"><summary>More tools</summary><div>{extra}</div></details>'
    download_rows = ''.join(f'<li><a href="run/{e(item["source"])}" download="{e(item["name"])}">{e(item["name"])}</a></li>' for item in data.get('downloads', []))
    downloads = (f'''<section id="download-panel" class="downloads" tabindex="-1"><h2>Your files</h2>
<p>{'Preview' if run['mode'] != 'final' else 'Final'} exports from recording {e(run['id'][:8])}. Saved edits appear after you update the recording.</p>
<a class="download-all" data-bundle href="download/{run['id']}/{run['binding']}/exports.zip">Download all exports (.zip)</a>
<p class="hint">Includes the rendered exports, video subtitles, image Markdown and a file manifest. Downloading does not accept or publish them.</p>
<details><summary>Download individual files</summary><ul>{download_rows}</ul></details></section>'''
                 if run and download_rows else '<section id="download-panel" class="downloads" tabindex="-1"><h2>Your files</h2><p>Record a complete preview to download its exports here.</p></section>')
    # Section links keep the full editor available and open the chosen panel without a page reload.
    audio_box = audio_box.replace('<details class="audio-controls"', '<details id="audio-panel" class="audio-controls"', 1)
    screenshot_box = screenshot_box.replace('<details class="screenshots-controls"', '<details id="screenshots-panel" class="screenshots-controls"', 1)
    tour_box = tour_box.replace('<details class="tour-controls"', '<details id="tour-panel" class="tour-controls"', 1)
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>reshoot studio</title><link rel="icon" href="data:,"><style>{STYLE}</style></head><body{'' if run else ' data-first="1"'} data-seen="{seen}" data-journey="{e(json.dumps(state))}" data-studio-pending="{'1' if state['pending'] else ''}">
<header><h1>reshoot studio</h1><span class="story">{e(data['story'])}</span>
<fieldset class="actions" aria-label="Recording and history"{(' disabled' if session else '')}><button type="button" data-history="undo"{'' if data.get('undo') else ' disabled'}>Undo</button>
<button type="button" data-history="redo"{'' if data.get('redo') else ' disabled'}>Redo</button>
<button type="button" class="{'primary' if state['action']['kind'] == 'update' else ''}" data-job="update"{'' if state['actions']['update']['enabled'] else ' disabled'} title="{e(state['actions']['update']['reason'])}">Update preview</button>
<button type="button" class="{'primary' if state['action']['kind'] == 'run' else ''}" data-job="run"{'' if state['actions']['run']['enabled'] else ' disabled'} title="{e(state['actions']['run']['reason'] or 'Record the full-size video for review')}">Make final</button>
<details class="advanced"><summary>More</summary><button type="button" data-job="recut"{'' if run else ' disabled'} title="Edit and scan this run's takes again, with the captions and edit as they are now">Re-cut</button>
<button type="button" data-job="preview" title="Start the app and record a quick preview">Record a preview</button>
</details></fieldset><nav class="section-nav" aria-label="Studio sections">{navigation}</nav></header>
{recovery}
{tools_box}
<section id="journey" class="journey" role="status" aria-live="polite" data-phase="{e(state['phase'])}"><strong id="journey-title">{e(state['title'])}</strong>
<p id="journey-detail">{e(state['detail'])}</p><p id="journey-changes" class="hint"{'' if state.get('changes') else ' hidden'}>{e(', '.join(state.get('changes', [])))}</p>
<p id="journey-plan" class="hint"{'' if state['pending'] else ' hidden'}>{e(state['update_detail'])}</p>
<button type="button" data-reset-drafts hidden>Reset unsaved edits</button><button type="button" data-reload-project hidden>Reload project</button>
<a href="#review-panel" data-jump="review-panel" id="journey-review"{'' if state['next'] == 'review' else ' hidden'}>Review this final</a>
<a href="#download-panel" data-jump="download-panel" id="journey-files"{'' if state['next'] == 'download' else ' hidden'}>Get your files</a></section>
<p id="save-error" class="error" role="alert" hidden></p>
<section id="job" hidden><p id="job-title"></p><button type="button" id="cancel">Cancel update</button><video id="job-take" controls hidden></video><audio id="audition-player" controls hidden></audio><details><summary>Progress details</summary><pre id="job-log"></pre></details></section>
<main><section class="watch" id="preview-panel" tabindex="-1">{failure_box}
<div id="selected-step" hidden><strong id="selected-step-title"></strong><p class="hint" id="selected-step-status"></p>
<button type="button" id="play-selected">Play selected step</button><a href="#story-panel" id="edit-selected">Back to this step</a></div>{top}
{f'<div class="shapes"><h2>Exports</h2><p class="hint">Measurements describe this rendered run. Update preview to measure saved changes.</p><div class="grid">{"".join(shapes)}</div></div>' if shapes else ''}
{f'<div class="docs-shots"><h2>Documentation screenshots</h2><p class="hint">From this displayed run. Update preview to render saved changes. Inspect each PNG before sharing.</p><div class="grid">{shot_images}</div></div>' if shot_images else ''}
{f'<div class="tour-previews"><h2>Clickable tour</h2><p class="hint">From this displayed run. Inspect every step, explanation and click marker before sharing.</p>{tour_previews}</div>' if tour_previews else ''}
{compare_box}
<section id="review-panel" class="review-panel" tabindex="-1"><h2>Review this recording</h2>
<p id="review-current" class="hint"{'' if state['pending'] else ' hidden'}>Saved edits are not shown in this recording. Update preview or make a final before accepting here.</p>
{f'<div class="found"><h3>What the scan found</h3><ul>{findings}</ul></div>' if findings else ''}
{evidence}
<div class="accept">{accept}</div></section>{downloads}</section>
<fieldset class="side" aria-label="Demo editing"{(' disabled' if session or data.get('needs_demonstration') else '')}><div class="beats" id="story-panel" tabindex="-1"><h2>Your story</h2><p class="hint">Choose a step to play it. Captions and timing save as you leave a field.</p><ol>{''.join(beats)}</ol></div>
{audio_box}
{screenshot_box}
{tour_box}
<div id="cut-panel" class="section-anchor" tabindex="-1">{sequence_box}</div>
<details class="styling" id="look-panel"><summary>Style and exports</summary>{styles_box}<div class="look"><h2>Caption look</h2>
<label>Place <select name="position"><option value="bottom"{' selected' if look.get('position', 'bottom') == 'bottom' else ''}>Bottom</option><option value="top"{' selected' if look.get('position') == 'top' else ''}>Top</option></select></label>
<label>Background <input name="background" value="{e(look.get('background', ''))}" placeholder="#0e0d0cc8"></label>
<label>Text <input name="foreground" value="{e(look.get('foreground', ''))}" placeholder="#ffffff"></label>
{pending.format('' if data['look_pending'] else ' hidden')}</div>
{edit_box}
</details></fieldset></main>
<p id="toast" role="status"></p>
<dialog id="export-inspector"><form method="dialog"><button>Close</button></form><h2>Inspect the rendered export</h2><p id="inspector-size"></p><div class="inspection-rail"></div></dialog>
<script>{SCRIPT}</script><script>{Path(__file__).with_name('comparison.js').read_text()}</script></body></html>'''
    if run:
        document = document.replace('run/', f'runs/{run["id"]}/')
    return document.replace('data-seen="', f'data-revision="{e(data.get("revision", ""))}" '
                            f'data-run="{e((run or {}).get("id", ""))}" '
                            f'data-binding="{e((run or {}).get("binding", ""))}" data-seen="', 1)


STYLE = '''
body[data-first] #compare-panel, body[data-first] #review-panel, body[data-first] #download-panel,
body[data-first] #look-panel, body[data-first] #cut-panel, body[data-first] #audio-panel,
body[data-first] #screenshots-panel, body[data-first] #tour-panel, body[data-first] .beat .narration,
body[data-first] .beat .redo { display:none }
:root { --bg:#f6f5f2; --panel:#fff; --ink:#1d1b18; --muted:#6b665e; --line:#e3e0da; --accent:#1d4ed8; --ok:#15803d;
  --bad:#b91c1c; --idle:#a8a29e; --seg-ink:#fff; --header-height:120px; color-scheme: light dark; }
@media (prefers-color-scheme: dark) { :root { --bg:#131211; --panel:#1c1b19; --ink:#f1efe9; --muted:#a49e94;
  --line:#2e2c29; --accent:#7aa2ff; --ok:#4ade80; --bad:#f87171; --idle:#57534e; --seg-ink:#0b0b0a; } }
* { box-sizing:border-box } body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif }
header { display:flex; flex-wrap:wrap; gap:12px; align-items:center; padding:14px 20px; border-bottom:1px solid var(--line); background:var(--panel); position:sticky; top:0; z-index:2 }
h1 { font-size:17px; margin:0 } h2 { font-size:15px; margin:0 0 8px } h3 { font-size:13px; margin:14px 0 4px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em }
.story { color:var(--muted) } .actions { margin-left:auto; display:flex; gap:8px; flex-wrap:wrap }
fieldset.actions, fieldset.side { border:0; padding:0; min-width:0 } fieldset.side { margin:0 }
.section-nav { width:100%; display:flex; flex-wrap:wrap; gap:6px; padding:2px 0 5px }
.section-nav a { color:var(--muted); font-size:13px; text-decoration:none; border:1px solid transparent; border-radius:6px; padding:5px 8px }
.section-nav a:hover, .section-nav a[aria-current] { color:var(--ink); border-color:var(--accent) }
.more-tools { flex-shrink:0; font-size:13px; padding:5px 8px }
.more-tools[open] > div { display:flex; flex-wrap:wrap; white-space:normal; padding-top:6px }
[id$="-panel"] { scroll-margin-top:calc(var(--header-height) + 16px) }
.journey { max-width:1460px; margin:14px auto 0; padding:12px 16px; border:1px solid var(--line); border-left:4px solid var(--ok); border-radius:10px; background:var(--panel) }
.journey p { margin:4px 0 } .journey[data-phase=pending], .journey[data-phase=draft], .journey[data-phase=external] { border-left-color:var(--accent) } .journey[data-phase=stopped] { border-left-color:var(--bad) }
.journey button { margin:6px 6px 0 0 } .journey a { color:var(--accent) }
#setup-panel ul { padding-left:20px } #setup-panel li { margin:8px 0 } #setup-panel .fix, #setup-panel code { overflow-wrap:anywhere }
.review-panel, .downloads { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px; margin-top:16px }
.compare-panel { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px; margin-top:16px }
.compare-panel label { margin:12px 0; display:block } .compare-panel select { max-width:100%; width:100% }
.compare-run-links { display:grid; grid-template-columns:1fr 1fr; gap:14px; overflow-wrap:anywhere }
.compare-pair { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:12px }
.compare-pair figure { margin:0; min-width:0 } .compare-pair img { width:100%; height:auto; display:block; border:1px solid var(--line); border-radius:6px }
.compare-pair figcaption { font-size:13px; margin:6px 0 } .compare-beat { border-top:1px solid var(--line); padding:12px 0 }
.compare-beat h3, #comparison-status { overflow-wrap:anywhere } .compare-beat h3 { text-transform:none; letter-spacing:normal; color:var(--ink) }
@media(max-width:600px) { .compare-pair, .compare-run-links { grid-template-columns:1fr } }
.downloads ul { padding-left:20px; overflow-wrap:anywhere } .downloads li { margin:7px 0 } .downloads a { color:var(--accent) }
.download-all { display:inline-block; font-weight:600; border:1px solid var(--accent); border-radius:8px; padding:8px 12px; margin:4px 0; text-decoration:none }
.side > .section-anchor:empty { display:none } :focus-visible { outline:2px solid var(--accent); outline-offset:3px }
@media(max-width:600px) { .journey { margin:12px 16px 0 } header { gap:8px; padding:10px 16px } .actions { gap:5px } .actions button { font-size:13px; padding:6px 8px } }
button { font:inherit; border:1px solid var(--line); background:var(--panel); color:var(--ink); border-radius:8px; padding:6px 12px; cursor:pointer }
button:hover:not(:disabled) { border-color:var(--accent) } button:disabled { opacity:.5; cursor:default }
main { display:grid; grid-template-columns:minmax(0,1.4fr) minmax(320px,1fr); gap:20px; padding:20px; max-width:1500px; margin:auto }
@media (max-width:900px) { main { grid-template-columns:1fr; padding:16px } }
@media (min-width:1100px) and (min-height:700px) {
  .watch { position:sticky; top:calc(var(--header-height) + 16px); align-self:start; max-height:calc(100dvh - var(--header-height) - 32px); overflow-y:auto; scrollbar-gutter:stable; overscroll-behavior:contain }
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
.beat { display:grid; grid-template-columns:150px 1fr; gap:12px; background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--idle); border-radius:12px; padding:12px; scroll-margin-top:calc(var(--header-height) + 16px) }
.beat.passed { border-left-color:var(--ok) } .beat.failed { border-left-color:var(--bad) } .beat.now { outline:2px solid var(--accent) }
.beat.selected { box-shadow:0 0 0 2px var(--accent) } #selected-step a { display:inline-block; margin-left:12px; color:var(--accent) }
.check-correction { margin:12px 0; padding:12px; border:1px solid var(--line); border-radius:8px }
.check-correction textarea { width:100%; box-sizing:border-box; font:inherit; color:var(--ink); background:var(--bg); border:1px solid var(--line); border-radius:7px; padding:6px 8px }
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
summary { cursor:pointer; font-weight:600 } .styling, .audio-controls, .screenshots-controls, .tour-controls { background:var(--panel); padding:14px; border:1px solid var(--line); border-radius:12px }
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
.narration textarea, .screenshot-form textarea, .tour-form textarea { width:100%; resize:vertical; min-height:72px; font:inherit; color:var(--ink); background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:8px; box-sizing:border-box }
.tour-steps { padding:0; list-style:none; display:grid; gap:12px } .tour-step { padding:12px; border:1px solid var(--line); border-radius:8px }
.tour-form { margin:12px 0 } .tour-marker { margin:10px 0 }
.tour-point { padding:0; width:100%; display:block; position:relative; cursor:crosshair; margin:8px 0 } .tour-point img { display:block; width:100%; pointer-events:none }
.tour-point span { position:absolute; transform:translate(-50%,-50%); border:2px solid white; background:#2349c5; color:white; min-width:28px; min-height:28px; border-radius:50%; pointer-events:none; display:grid; place-items:center }
.tour-previews iframe { width:100%; height:640px; border:1px solid var(--line); border-radius:8px }
.screenshot-form { padding:12px 0; border-top:1px solid var(--line); margin-top:12px }
.shot-crop { margin:10px 0 } .shot-crop-guide { position:relative; overflow:hidden; cursor:crosshair; touch-action:none; border:1px solid var(--line); margin:8px 0 }
.shot-crop .range-form { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)) }
.shot-crop-guide img { width:100%; display:block; pointer-events:none } .shot-crop-guide span { position:absolute; border:2px solid #fbbf24; box-shadow:0 0 0 400px #0006; pointer-events:none }
.docs-shots figure { margin:0 } .docs-shots img { display:block; width:100%; border:1px solid var(--line); border-radius:6px } .docs-shots figcaption { font-size:13px; margin:8px 0 }
.audio-mix { border:1px solid var(--line); border-radius:8px; padding:12px; margin:12px 0 }
#audition-player { display:block; width:min(100%, 440px); margin-top:10px } #audition-player[hidden] { display:none }
'''

SCRIPT = '''(() => {
  document.querySelectorAll('details.styling, details.advanced, details.more-tools, details.narration, details.audio-controls, details.screenshots-controls, details.tour-controls').forEach(box => {
    const key = location.pathname + ':' + box.className + ':' + (box.closest('.beat')?.dataset.beat || '');
    box.open = sessionStorage.getItem(key) === 'open';
    box.addEventListener('toggle', () => sessionStorage.setItem(key, box.open ? 'open' : 'closed'));
  });
  const video = document.getElementById('video'), head = document.getElementById('head');
  const toast = text => { const t = document.getElementById('toast'); t.textContent = text; t.classList.add('on'); clearTimeout(t.timer); t.timer = setTimeout(() => t.classList.remove('on'), 2600); };
  const error = text => { const box = document.getElementById('save-error'); box.textContent = text; box.hidden = !text; };
  let journeyState = JSON.parse(document.body.dataset.journey);
  const textFor = (id, text) => { const element = document.getElementById(id); if (element.textContent !== text) element.textContent = text; };
  const renderJourney = () => {
    const drafts = !!document.querySelector('[data-unsaved]'), external = !!journeyState.external;
    const pending = journeyState.pending || drafts || external || !!document.getElementById('session-recovery');
    document.body.dataset.studioPending = pending ? '1' : '';
    document.getElementById('journey').dataset.phase = external ? 'external' : drafts ? 'draft' : journeyState.phase;
    textFor('journey-title', external ? 'Project changed in another editor' : drafts ? 'Some edits have not been saved yet' : journeyState.title);
    textFor('journey-detail', external ? (drafts ? 'Reset the unsaved edits and reload to see the current project.' : 'Reload to see those changes before editing here.')
      : drafts ? 'Save or reset the unsaved edits before updating the recording.' : journeyState.detail);
    textFor('journey-changes', (journeyState.changes || []).join(' · '));
    document.getElementById('journey-changes').hidden = !journeyState.changes?.length || drafts || external;
    textFor('journey-plan', journeyState.update_detail || '');
    document.getElementById('journey-plan').hidden = !journeyState.pending || drafts || external;
    document.querySelector('[data-reset-drafts]').hidden = !drafts;
    const reload = document.querySelector('[data-reload-project]'); reload.hidden = !external; reload.disabled = drafts;
    document.getElementById('journey-files').hidden = journeyState.next !== 'download' || pending;
    document.getElementById('journey-review').hidden = journeyState.next !== 'review' || pending;
    document.getElementById('review-current').hidden = !pending;
    const accept = document.getElementById('accept');
    if (accept) accept.disabled = pending || !document.getElementById('watched')?.checked ||
      [...document.querySelectorAll('#to-accept fieldset')].some(field => !field.querySelector('input:checked'));
    const next = !drafts && !external ? journeyState.action : null;
    document.querySelectorAll('[data-job=update], [data-job=run], [data-job=create], [data-job=setup]').forEach(button => {
      button.classList.toggle('primary', !!next?.enabled && button.dataset.job === next.kind);
      const action = journeyState.actions[button.dataset.job];
      if (action && document.body.dataset.jobRunning !== '1') {
        button.disabled = !action.enabled || external;
        if (action.reason) button.title = action.reason;
      }
    });
  };
  const applyJourney = state => { journeyState = state; renderJourney(); };
  new MutationObserver(renderJourney).observe(document.body, {subtree:true, attributes:true, attributeFilter:['data-unsaved']});
  document.querySelectorAll('.beat input, .look input, .look select, .cut .card input, .cut [name=frame], .cut [name=background], .cut [name=foreground], .cut [name=frame_background], .cut [name=frame_background_end], .export-framing input').forEach(input =>
    input.addEventListener('input', () => input.dataset.unsaved = '1'));
  document.querySelector('[data-reset-drafts]').onclick = () => location.reload();
  document.querySelector('[data-reload-project]').onclick = () => { if (!document.querySelector('[data-unsaved]')) location.reload(); };
  const header = document.querySelector('header');
  const sizeHeader = () => document.documentElement.style.setProperty('--header-height', header.getBoundingClientRect().height + 'px');
  new ResizeObserver(sizeHeader).observe(header); sizeHeader();
  document.querySelectorAll('[data-jump]').forEach(link => link.onclick = event => {
    event.preventDefault(); const target = document.getElementById(link.dataset.jump); if (!target) return;
    if (target.tagName === 'DETAILS') target.open = true;
    if (target.id === 'review-panel') { const scan = target.querySelector('details.scan'); if (scan) scan.open = true; }
    target.scrollIntoView({block:'start'});
    const focus = target.tagName === 'DETAILS' ? target.querySelector('summary') : target;
    focus.tabIndex = -1; focus.focus({preventScroll:true});
    document.querySelectorAll('.section-nav a').forEach(item => { if (item.dataset.jump === link.dataset.jump) item.setAttribute('aria-current','location'); else item.removeAttribute('aria-current'); });
  });
  let checkingState = false;
  const refreshJourney = async () => {
    if (checkingState || document.body.dataset.jobRunning === '1') return;
    checkingState = true; const revision = document.body.dataset.revision;
    try {
      const query = new URLSearchParams({run_id:document.body.dataset.run, binding:document.body.dataset.binding, revision});
      const response = await fetch('state.json?' + query), state = await response.json();
      if (revision !== document.body.dataset.revision) return;
      if (!response.ok) { error(state.error); return; }
      if (state.session_pending && !document.getElementById('session-recovery')) {
        state.external = true;
      }
      applyJourney(state);
    } catch (_) { error('Could not check the saved project. Keep the studio running and reload when ready.'); }
    finally { checkingState = false; }
  };
  window.addEventListener('focus', refreshJourney);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshJourney(); });
  document.addEventListener('reshoot:accepted', () => location.reload());
  renderJourney();
  let queue = Promise.resolve();
  const post = (what, body, requireSaved = false) => {
    const request = () => {
      const ownForm = what === 'sequence' && body.operation === 'range' ? document.querySelector(`.sequence-part[data-part="${body.part}"] .range-form`)
        : what === 'sequence' && body.operation === 'add' ? document.getElementById('add-clip')
        : what === 'framing' && body.size != null ? document.querySelector('.recording-view')
        : what === 'framing' ? document.querySelector(`.export-framing[data-export="${body.export}"]`)
        : what === 'audio' && body.change.beat != null ? document.querySelector(`.beat[data-beat="${CSS.escape(body.change.beat)}"] .narration-form`)
        : what === 'audio' && body.change.mix ? document.querySelector('.audio-mix')
        : what === 'screenshot' && body.operation === 'add' ? document.getElementById('add-screenshot')
        : what === 'screenshot' && body.operation === 'set' ? document.querySelector(`.screenshot-form[data-name="${CSS.escape(body.name)}"]`)
        : what === 'tour' && body.change.operation === 'set' ? document.querySelector(`.tour-form[data-step="${body.change.step}"]`)
        : what === 'tour' ? document.querySelector(`.tour-form[data-operation="${CSS.escape(body.change.operation)}"]`) : null;
      const editingCheck = what === 'edit' && body.update_expect != null ? document.querySelector('.check-correction') : null;
      const savingForm = ownForm || editingCheck;
      const unsaved = [...document.querySelectorAll('[data-unsaved]')].some(input => !savingForm || !savingForm.contains(input));
      if ((requireSaved || ['job', 'undo', 'redo', 'style', 'sequence', 'framing', 'audio', 'screenshot', 'tour'].includes(what)) && unsaved) {
        const message = 'Fix the unsaved field before updating, undoing or changing the layout.';
        error(message); return {ok: false, error: message};
      }
      return fetch(what, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({run_id: document.body.dataset.run, binding: document.body.dataset.binding,
        revision: document.body.dataset.revision, ...body})}).then(r => r.json()).then(out => {
          if (out.revision) document.body.dataset.revision = out.revision;
          if (out.journey) applyJourney(out.journey);
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
  document.querySelectorAll('[data-session]').forEach(button => button.onclick = () => {
    post('session', {choice:button.dataset.session, session_token:document.getElementById('session-recovery').dataset.token})
      .then(out => { if (out.ok) location.reload(); });
  });
  document.querySelectorAll('[data-repair]').forEach(button => button.onclick = () => {
    const failure = button.closest('.failure');
    post('job', {kind: 'repair', method: button.dataset.repair, failure_run_id: failure.dataset.failure,
      failure_binding: failure.dataset.binding}).then(out => { if (out.ok) watch(); });
  });
  document.querySelectorAll('[data-remove-check]').forEach(button => button.onclick = () => {
    post('edit', {beat: button.dataset.beat, remove_expect: Number(button.dataset.index), expect: JSON.parse(button.dataset.expect)}, true)
      .then(out => { if (out.ok) location.reload(); });
  });
  document.querySelectorAll('.check-correction').forEach(form => {
    form.elements.value.addEventListener('input', () => form.elements.value.dataset.unsaved = '1');
    form.onreset = () => { delete form.elements.value.dataset.unsaved; if (!document.querySelector('[data-unsaved]')) error(''); };
    form.onsubmit = event => {
      event.preventDefault();
      const raw = form.elements.value.value;
      const value = form.dataset.kind === 'count' ? Number(raw) : form.dataset.kind === 'checked' ? raw === 'true' : raw;
      post('edit', {beat:form.dataset.beat, update_expect:Number(form.dataset.index), expect:JSON.parse(form.dataset.expect), value}, true)
        .then(out => { if (out.ok) location.reload(); });
    };
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
  let selected = null;
  const selectionKey = location.pathname + ':selected-step';
  const selectBeat = (li, seek = false) => {
    if (!li) return;
    selected = li; sessionStorage.setItem(selectionKey, li.dataset.beat);
    document.querySelectorAll('.beat').forEach(item => {
      item.classList.toggle('selected', item === li);
      if (item === li) item.setAttribute('aria-current', 'step'); else item.removeAttribute('aria-current');
    });
    document.getElementById('selected-step').hidden = false;
    textFor('selected-step-title', 'Editing step: ' + li.dataset.beat);
    const changed = !li.querySelector('.pending').hidden;
    textFor('selected-step-status', !video ? 'Finish the first preview to see this step.' : changed ? 'Saved changes are not shown yet. Update preview to see them.' :
      'Showing the recorded version. Captions and timing save as you leave a field.');
    document.getElementById('play-selected').disabled = !video || li.dataset.start === '';
    if (seek && video && li.dataset.start !== '') { stopAt = null; video.pause(); video.currentTime = +li.dataset.start; }
  };
  document.querySelectorAll('.beat').forEach(li => li.addEventListener('focusin', () => { if (selected !== li) selectBeat(li, true); }));
  selectBeat(beat(sessionStorage.getItem(selectionKey) || ''));
  document.getElementById('play-selected').onclick = () => { if (selected) play(+selected.dataset.start, +selected.dataset.end); };
  document.getElementById('edit-selected').onclick = event => {
    event.preventDefault(); if (!selected) return;
    selected.scrollIntoView({block:'start'}); selected.querySelector('input[name=caption]').focus({preventScroll:true});
  };
  document.querySelectorAll('.beat .play').forEach(b => b.onclick = () => { const li = b.closest('.beat'); selectBeat(li); play(+li.dataset.start, +li.dataset.end); });
  document.querySelectorAll('.seg').forEach(s => s.onclick = () => { const li = beat(s.dataset.beat); selectBeat(li); play(+s.dataset.start, +s.dataset.end); li.scrollIntoView({block: 'nearest', behavior: 'smooth'}); });
  document.querySelectorAll('[data-part-play]').forEach(button => button.onclick = () => play(+button.dataset.start, +button.dataset.end));
  const inspector = document.getElementById('export-inspector');
  document.querySelectorAll('[data-inspect]').forEach(button => button.onclick = () => {
    if (video) video.pause();
    const rail = inspector.querySelector('.inspection-rail'); rail.replaceChildren();
    const png = button.dataset.inspect.endsWith('.png'), gif = png || button.dataset.inspect.endsWith('.gif');
    const media = document.createElement(gif ? 'img' : 'video');
    const width = Math.max(png ? 1 : 160, Math.min(png ? 3840 : 1920, +button.dataset.view || 640));
    media.style.width = width + 'px'; media.style.height = 'auto';
    if (gif) media.alt = button.dataset.alt || 'Rendered export at viewing size';
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
    if (!document.querySelector('[data-unsaved]')) error(''); toast('Saved'); const p = where.querySelector('.pending'); if (p) p.hidden = false;
    if (where.classList.contains('beat')) selectBeat(where); };
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
  const tourChange = change => post('tour', {change}).then(out => { if (out.ok) location.reload(); });
  document.querySelectorAll('.tour-form').forEach(form => {
    const guide = form.querySelector('.tour-point');
    const draw = () => {
      if (!guide) return;
      const marker = guide.querySelector('span'); marker.hidden = !form.elements.marker.checked;
      marker.style.display = form.elements.marker.checked ? 'grid' : 'none';
      marker.style.left = form.elements.x.value + '%'; marker.style.top = form.elements.y.value + '%';
    };
    form.querySelectorAll('input, textarea, select').forEach(input => input.addEventListener('input', () => { input.dataset.unsaved = '1'; draw(); }));
    if (guide) guide.onclick = event => {
      if (form.querySelector('[type=submit]').disabled) return;
      const box = guide.getBoundingClientRect();
      form.elements.x.value = Math.max(0, Math.min(100, (event.clientX - box.left) / box.width * 100)).toFixed(2);
      form.elements.y.value = Math.max(0, Math.min(100, (event.clientY - box.top) / box.height * 100)).toFixed(2);
      form.elements.marker.checked = true;
      ['x', 'y', 'marker'].forEach(key => form.elements[key].dataset.unsaved = '1'); draw();
    };
    form.addEventListener('reset', () => {
      form.querySelectorAll('[data-unsaved]').forEach(input => delete input.dataset.unsaved);
      if (!document.querySelector('[data-unsaved]')) error(''); setTimeout(draw, 0);
    });
    draw();
    form.onsubmit = event => {
      event.preventDefault(); const operation = form.dataset.operation;
      const change = {operation};
      if (operation === 'create') Object.assign(change, {name: form.elements.name.value, title: form.elements.title.value});
      if (operation === 'title') change.title = form.elements.title.value;
      if (operation === 'add') Object.assign(change, {take: +form.dataset.take, beat: form.elements.beat.value});
      if (operation === 'set') Object.assign(change, {step: +form.dataset.step, settings: {
        title: form.elements.title.value, text: form.elements.text.value, alt: form.elements.alt.value,
        hotspot: form.elements.marker.checked ? [+form.elements.x.value / 100, +form.elements.y.value / 100] : null}});
      tourChange(change);
    };
  });
  document.querySelectorAll('[data-tour-op]').forEach(button => button.onclick = () => tourChange({operation: button.dataset.tourOp,
    step: +button.closest('.tour-step').dataset.step, ...(button.dataset.to == null ? {} : {to: +button.dataset.to})}));
  const disableTour = document.querySelector('[data-disable-tour]'); if (disableTour) disableTour.onclick = () => tourChange({operation: 'disable'});
  document.querySelectorAll('.screenshot-form').forEach(form => {
    const cropKeys = ['x', 'y', 'w', 'h'], guide = form.querySelector('.shot-crop-guide');
    const drawCrop = () => {
      if (!guide) return;
      const values = cropKeys.map(key => +form.elements['crop_' + key].value), box = guide.querySelector('span');
      ['left', 'top', 'width', 'height'].forEach((key, i) => box.style[key] = values[i] + '%');
    };
    const setCrop = values => { values = values.map(value => +value.toFixed(2)); values[2] = Math.min(values[2], 100 - values[0]); values[3] = Math.min(values[3], 100 - values[1]); cropKeys.forEach((key, i) => {
      const input = form.elements['crop_' + key]; input.value = +values[i].toFixed(2); input.dataset.unsaved = '1';
    }); drawCrop(); };
    form.querySelectorAll('[name^=crop_]').forEach(input => input.addEventListener('input', drawCrop));
    const whole = form.querySelector('[data-whole-shot]'); if (whole) whole.onclick = () => setCrop([0, 0, 100, 100]);
    if (guide) {
      let start = null;
      const point = event => { const rect = guide.getBoundingClientRect(); return [Math.max(0, Math.min(100, (event.clientX - rect.left) / rect.width * 100)), Math.max(0, Math.min(100, (event.clientY - rect.top) / rect.height * 100))]; };
      guide.onpointerdown = event => {
        if (event.button !== 0 || form.querySelector('button[type=submit]').disabled) return;
        start = point(event); guide.setPointerCapture(event.pointerId); event.preventDefault();
      };
      guide.onpointermove = event => {
        if (!start) return;
        const end = point(event), width = Math.abs(end[0] - start[0]), height = Math.abs(end[1] - start[1]);
        if (width >= .1 && height >= .1) setCrop([Math.min(start[0], end[0]), Math.min(start[1], end[1]), width, height]);
      };
      guide.onpointerup = guide.onpointercancel = () => { start = null; };
      drawCrop();
    }
    form.querySelectorAll('textarea, input, select').forEach(input => input.addEventListener('input', () => input.dataset.unsaved = '1'));
    form.addEventListener('reset', () => {
      form.querySelectorAll('[data-unsaved]').forEach(input => delete input.dataset.unsaved);
      if (!document.querySelector('[data-unsaved]')) error('');
      setTimeout(drawCrop, 0);
    });
    form.onsubmit = event => {
      event.preventDefault();
      const adding = form.dataset.operation === 'add';
      const settings = {alt: form.elements.alt.value, width: form.elements.width.value === '' ? null : +form.elements.width.value};
      if (form.elements.crop_x) settings.crop = cropKeys.map(key => +form.elements['crop_' + key].value / 100);
      if (adding) Object.assign(settings, {beat: form.elements.beat.value, take: +form.dataset.take});
      post('screenshot', {operation: form.dataset.operation, name: adding ? form.elements.name.value : form.dataset.name, settings}).then(out => { if (out.ok) location.reload(); });
    };
  });
  document.querySelectorAll('[data-remove-shot]').forEach(button => button.onclick = () => post('screenshot', {operation: 'remove', name: button.dataset.removeShot}).then(out => { if (out.ok) location.reload(); }));
  document.querySelectorAll('[data-shot-beat]').forEach(button => button.onclick = () => {
    const panel = document.querySelector('.screenshots-controls'); panel.open = true;
    const form = document.getElementById('add-screenshot'); if (!form) return;
    if (form.querySelector('[data-unsaved]')) { error('Save or reset the screenshot draft before choosing another step.'); return; }
    const existing = panel.querySelector(`.screenshot-form[data-take="${form.dataset.take}"][data-beat="${CSS.escape(button.dataset.shotBeat)}"]`);
    if (existing) { existing.scrollIntoView({block: 'center'}); existing.elements.alt.focus(); return; }
    const choice = JSON.parse(form.dataset.beats).find(beat => beat.id === button.dataset.shotBeat);
    form.elements.beat.value = choice.id; form.elements.name.value = choice.id + '-result'; form.elements.alt.value = choice.alt;
    ['beat', 'name', 'alt'].forEach(name => form.elements[name].dataset.unsaved = '1');
    form.scrollIntoView({block: 'center'}); form.elements.alt.focus();
  });
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
  const names = {recut: 'Re-cutting', preview: 'Recording a preview', run: 'Recording', from: 'Recording from a beat', repair: 'Repairing control', audition: 'Preparing narration', setup:'Checking recording tools', create:'Continuing creation'};
  const watch = () => fetch('job.json').then(r => r.json()).then(job => {
    if (!job.kind) return;
    document.body.dataset.jobRunning = job.running ? '1' : '';
    box.hidden = false; log.textContent = job.lines.join('\\n'); log.scrollTop = log.scrollHeight;
    document.getElementById('cancel').hidden = !job.running;
    document.querySelectorAll('[data-job], [data-from], [data-repair], [data-remove-check], .check-correction input, .check-correction textarea, .check-correction select, .check-correction button, .side input, .side textarea, .side select, .side button, [data-history]').forEach(button => {
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
    if (job.kind === 'setup') {
      title.textContent = job.cancelled ? 'Tool check cancelled. Your project is kept.' : job.code === 0 ? 'Tool check passed. Loading the project...' : 'Tool check needs attention. Loading the fixes...';
      if (!job.cancelled && job.n > +document.body.dataset.seen) setTimeout(() => location.reload(), 600);
      return;
    }
    title.textContent = job.cancelled ? 'Update cancelled. Your previous recording is kept.' : job.code === 0 ? what + ' worked. Loading the new run...' : what + ' failed. Loading the step that needs attention...';
    if (!job.cancelled && job.n > +document.body.dataset.seen) setTimeout(() => location.reload(), 600);
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
