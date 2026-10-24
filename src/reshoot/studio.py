"""`reshoot studio`: a page on this computer for seeing a demo's latest run beat by beat and shaping it. It shows the
video with its beats on a timeline, each beat's frame, result checks and caption, and what the scan found. Caption
words and the [caption] look are edited in place and written to storyboard.toml, a re-cut shows them in seconds,
and the run can be recorded again or accepted from the page. The files stay the source of truth: an agent or an
editor can change them while the studio is open, and the page shows what is on disk when it loads.

    reshoot studio            # the project in ./demo
    reshoot studio app/demo --port 8800 --no-open

It serves on 127.0.0.1 behind a random address and takes changes only from its own page, like `review --serve`.
"""
import html, json, re, subprocess, sys, threading, tomllib
from pathlib import Path


def project(path):
    """The reshoot.toml for a project folder or the file itself, and its folder."""
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


# Edits to storyboard.toml change one line and leave the rest, comments included, as it was.
def quote(value):
    return json.dumps(value, ensure_ascii=False)  # JSON's escapes are TOML's for a basic string


def block(lines, header, match=None):
    """(start, end) of the lines under a table header, [caption] or [[beat]], up to the next header; with match,
    the [[beat]] whose keys pass it."""
    n = 0
    while n < len(lines):
        if lines[n].strip() == header:
            end = next((k for k in range(n + 1, len(lines)) if lines[k].lstrip().startswith('[')), len(lines))
            if match is None or match(tomllib.loads(''.join(lines[n + 1:end]))):
                return n + 1, end
            n = end
            continue
        n += 1
    return None


def put(lines, span, key, value, after=None):
    """Sets key = value inside span, or removes it when value is None; a new key goes after the line `after`."""
    start, end = span
    found = next((k for k in range(start, end) if re.match(rf'\s*{key}\s*=', lines[k])), None)
    if found is not None and re.match(rf'\s*{key}\s*=\s*("""|\'\'\')', lines[found]):
        raise ValueError(f'{key} is a multi-line string here; change it in the file')
    line = f'{key} = {quote(value)}\n'
    if found is not None:
        lines[found:found + 1] = [line] if value is not None else []
    elif value is not None:
        at = next((k + 1 for k in range(start, end) if after and re.match(rf'\s*{after}\s*=', lines[k])), end)
        lines.insert(at, line)


def edit(board, change):
    """Applies one change from the page to storyboard.toml and checks the result loads before writing it."""
    from reshoot import story
    lines = board.read_text().splitlines(keepends=True)
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    if change.get('beat') is not None:
        span = block(lines, '[[beat]]', lambda keys: keys.get('id') == change['beat'])
        if not span:
            raise ValueError(f'no beat {change["beat"]!r} in the storyboard')
        for key in ('caption', 'sub'):
            if key in change:
                value = change[key]
                if value is not None and not isinstance(value, str):
                    raise ValueError(f'{key} must be text')
                put(lines, span, key, ' '.join(value.split()) or None if value else None, after='id' if key == 'caption' else 'caption')
                span = block(lines, '[[beat]]', lambda keys: keys.get('id') == change['beat'])
    if 'look' in change:
        for key, value in change['look'].items():
            if key not in ('position', 'background', 'foreground'):
                raise ValueError(f'the studio does not change [caption] {key}')
            if key == 'position' and value not in ('top', 'bottom', None):
                raise ValueError('position must be top or bottom')
            if key != 'position' and value and not re.fullmatch(r'#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})', value):
                raise ValueError(f'{key} must be a colour such as #1d4ed8, or #1d4ed8e6 with its opacity')
            span = block(lines, '[caption]')
            if span is None and value:
                lines += ['\n', '[caption]\n']
                span = (len(lines), len(lines))
            if span:
                put(lines, span, key, value or None)
    temp = board.with_name('.' + board.name + '.studio')
    temp.write_text(''.join(lines))
    try:
        story.load(temp)
    except (ValueError, tomllib.TOMLDecodeError) as e:
        raise ValueError(f'not saved: {e}') from None
    finally:
        text = temp.read_text()
        temp.unlink()
    board.write_text(text)


class Job:
    """A reshoot command started from the page: a re-cut or a recording, one at a time."""
    def __init__(self):
        self.kind, self.lines, self.code, self.lock, self.n = None, [], None, threading.Lock(), 0

    def running(self):
        return self.kind is not None and self.code is None

    def start(self, kind, cmd, cwd):
        with self.lock:
            if self.running():
                raise ValueError(f'a {self.kind} is still running')
            self.kind, self.lines, self.code, self.n = kind, [], None, self.n + 1
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
        return {'n': self.n, 'kind': self.kind, 'running': self.running(), 'code': self.code, 'lines': self.lines[-400:]}


def current(folder):
    """The newest run that worked, as (root, report), or None."""
    from reshoot import review
    for root, report in review.runs(folder):
        if report.get('ok'):
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


def view(folder, take):
    """What the page shows: the storyboard's beats, joined to the latest run's where there is one."""
    from reshoot import review, story, timeline
    from reshoot.check import findings, load
    board_path = Path(folder) / take['web']
    board = story.load(board_path)
    data = {'story': board_path.name, 'look': board.get('caption', {}), 'run': None, 'beats': [], 'findings': []}
    run = current(folder)
    recorded, drawn, look_drawn = {}, {}, None
    if run:
        root, report = run
        clips = [p for p in review.exports(root, report) if p.endswith('.mp4')]
        video = clips[0] if clips else take['out']
        segments = timeline.read(root / video)['segments']
        source = (root / take['out']).resolve()
        meta = load(source.with_suffix('.take.json'), {})
        sidecar = load(source.with_suffix('.captions.json'), None)
        if sidecar:
            drawn = {row['beat']: (row.get('text'), row.get('sub')) for row in sidecar['captions']}
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
                'checks': [c.get('status') for c in beat.get('expectations', [])]}
        names = review.named(root, report)
        key, flags = load(root / 'review' / 'key.json', {}), load(root / 'review' / 'flags.json', {})
        for name, (found, labels) in findings(flags).items():
            times = []
            for label in labels:
                m = re.fullmatch(r'local source ([0-9a-f]{12})@([0-9.]+)s', str((key.get(label) or [''])[0]))
                if m and names.get(m[1]) == video:
                    times.append(float(m[2]))
            data['findings'].append({'name': name, 'found': found, 'frames': len(labels), 'times': times})
        data['run'] = {'id': report['id'], 'status': review.status(root, report), 'video': video,
                       'duration': timeline.read(root / video)['duration'], 'mode': report.get('mode', 'final'),
                       'recut_from': report.get('recut_from'), 'accepted': report.get('review_status') == 'completed',
                       'exports': [{'path': p, 'bytes': (root / p).stat().st_size} for p in review.exports(root, report)],
                       'captions_drawn': sidecar is not None}
    for beat in board['beat']:
        row = {'id': beat['id'], 'purpose': beat.get('purpose'), 'caption': beat.get('caption') or '',
               'sub': beat.get('sub') or '', **recorded.get(beat['id'], {})}
        if beat['id'] in drawn:
            row['pending'] = drawn[beat['id']] != (beat.get('caption') or None, beat.get('sub') or None)
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
                return review.reply(self, 200, page(view(folder, take), accept, seen).encode())
            if name == 'job.json':
                return review.reply(self, 200, json.dumps(job.json()).encode(), 'application/json')
            if name.startswith('run/') and (run := current(folder)):
                return review.send_file(self, run[0], name[4:])
            review.reply(self, 404, b'not found', 'text/plain')

        do_HEAD = do_GET

        def do_POST(self):
            action = self.path[len(prefix):] if self.path.startswith(prefix) else ''
            if action not in ('edit', 'job', 'accept'):
                return review.reply(self, 404, b'not found', 'text/plain')
            body = review.from_page(self, prefix + action)
            if body is None:
                return
            try:
                if action == 'edit':
                    edit(Path(folder) / take['web'], body)
                    out = {'ok': True}
                elif action == 'job':
                    run = current(folder)
                    commands = {'recut': [*cli, 'recut', str(run[0]) if run else '', '--config', str(config)],
                                'preview': [*cli, 'preview', str(config)], 'run': [*cli, 'run', str(config)]}
                    if body.get('kind') not in commands or (body['kind'] == 'recut' and not run):
                        raise ValueError('nothing to do: record a run first' if body.get('kind') == 'recut' else 'unknown job')
                    job.start(body['kind'], commands[body['kind']], folder)
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
    print(f'The studio is at {url}\nIt changes {take["web"]} as you edit; press Ctrl-C to stop.', flush=True)
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
    e = lambda v: html.escape(str(v if v is not None else ''), quote=True)
    run = data['run']
    seconds = lambda t: f'{t:.1f} s'
    beats = []
    for n, beat in enumerate(data['beats']):
        checks = beat.get('checks') or []
        passed = sum(c == 'passed' for c in checks)
        state = 'failed' if 'failed' in checks else 'passed' if checks else 'unverified'
        when = (f'{seconds(beat["start"])} to {seconds(beat["end"])}' if beat.get('start') is not None
                else 'not in this cut' if run and 'status' in beat else 'not recorded yet')
        frame = f'<img src="run/{e(beat["frame"])}" alt="The last frame of {e(beat["id"])}" loading="lazy">' if beat.get('frame') else '<div class="noframe">No frame yet</div>'
        beats.append(f'''<li class="beat {state}" data-beat="{e(beat['id'])}" data-start="{e(beat.get('start'))}" data-end="{e(beat.get('end'))}">
  <button class="play" type="button" title="Play this beat"{'' if beat.get('start') is not None else ' disabled'}>{frame}<span>&#9654;</span></button>
  <div class="body">
    <div class="head"><strong>{n + 1}. {e(beat['id'])}</strong><span class="when">{when}</span></div>
    {f'<p class="purpose">{e(beat["purpose"])}</p>' if beat.get('purpose') else ''}
    <p class="checks">{f'{passed} of {len(checks)} result checks passed' if checks else 'No result checks'}</p>
    <label>Caption <input name="caption" value="{e(beat['caption'])}" placeholder="No caption"></label>
    <label>Second line <input name="sub" value="{e(beat['sub'])}" placeholder="None"></label>
    <p class="pending"{'' if beat.get('pending') else ' hidden'}>Not in the video yet: re-cut to see it.</p>
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
    exports = ''.join(f'<li><a href="run/{e(x["path"])}" target="_blank">{e(Path(x["path"]).name)}</a> {x["bytes"] / 1e6:.1f} MB</li>'
                      for x in (run or {}).get('exports', []))
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
<div class="actions"><button type="button" data-job="recut"{'' if run else ' disabled'} title="Edit and scan this run's takes again, with the captions as they are now">Re-cut</button>
<button type="button" data-job="preview" title="Start the app and record a quick preview">Record a preview</button>
<button type="button" data-job="run" title="Start the app and record a final">Record</button></div></header>
<section id="job" hidden><p id="job-title"></p><pre id="job-log"></pre></section>
<main><section class="watch">{top}
<div class="look"><h2>Caption look</h2>
<label>Place <select name="position"><option value="bottom"{' selected' if look.get('position', 'bottom') == 'bottom' else ''}>Bottom</option><option value="top"{' selected' if look.get('position') == 'top' else ''}>Top</option></select></label>
<label>Background <input name="background" value="{e(look.get('background', ''))}" placeholder="#0e0d0cc8"></label>
<label>Text <input name="foreground" value="{e(look.get('foreground', ''))}" placeholder="white"></label>
<p class="pending"{'' if data['look_pending'] else ' hidden'}>Not in the video yet: re-cut to see it.</p></div>
{f'<div class="found"><h2>What the scan found</h2><ul>{findings}</ul></div>' if findings else ''}
{f'<div class="exports"><h2>Exports</h2><ul>{exports}</ul></div>' if exports else ''}
<div class="accept">{accept}</div></section>
<section class="beats"><h2>Beats</h2><p class="hint">Edits are saved to {e(data['story'])} as you leave a field.</p><ol>{''.join(beats)}</ol></section></main>
<p id="toast" role="status"></p>
<script>{SCRIPT}</script></body></html>'''


STYLE = '''
:root { --bg:#f6f5f2; --panel:#fff; --ink:#1d1b18; --muted:#6b665e; --line:#e3e0da; --accent:#1d4ed8; --ok:#15803d;
  --bad:#b91c1c; --idle:#a8a29e; --seg-ink:#fff; color-scheme: light dark; }
@media (prefers-color-scheme: dark) { :root { --bg:#131211; --panel:#1c1b19; --ink:#f1efe9; --muted:#a49e94;
  --line:#2e2c29; --accent:#7aa2ff; --ok:#4ade80; --bad:#f87171; --idle:#57534e; --seg-ink:#0b0b0a; } }
* { box-sizing:border-box } body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif }
header { display:flex; flex-wrap:wrap; gap:12px; align-items:center; padding:14px 20px; border-bottom:1px solid var(--line); background:var(--panel); position:sticky; top:0; z-index:2 }
h1 { font-size:17px; margin:0 } h2 { font-size:15px; margin:0 0 8px } .story { color:var(--muted) }
.actions { margin-left:auto; display:flex; gap:8px; flex-wrap:wrap }
button { font:inherit; border:1px solid var(--line); background:var(--panel); color:var(--ink); border-radius:8px; padding:6px 12px; cursor:pointer }
button:hover:not(:disabled) { border-color:var(--accent) } button:disabled { opacity:.5; cursor:default }
main { display:grid; grid-template-columns:minmax(0,1.4fr) minmax(320px,1fr); gap:20px; padding:20px; max-width:1500px; margin:auto }
@media (max-width:900px) { main { grid-template-columns:1fr; padding:16px } }
.watch > * + * { margin-top:16px } .watch > div { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px }
video { width:100%; border-radius:10px; background:#000; display:block }
.timeline { position:relative; height:34px; background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; margin-top:8px }
.seg { position:absolute; top:4px; bottom:4px; border-radius:5px; padding:0 6px; border:0; overflow:hidden; text-align:left; font-size:12px; color:var(--seg-ink); white-space:nowrap }
.seg.passed { background:var(--ok) } .seg.failed { background:var(--bad) } .seg.unverified { background:var(--idle) }
.seg + .seg { margin-left:1px } .flag { position:absolute; top:0; bottom:0; width:2px; background:var(--bad) }
#head { position:absolute; top:0; bottom:0; width:2px; background:var(--accent); left:0; pointer-events:none }
.status { margin:0; font-weight:600 } .note, .hint { color:var(--muted); margin:6px 0 }
.look label, .beat label, .accept fieldset label { display:block; margin-top:8px; font-size:13px; color:var(--muted) }
input:not([type=radio]):not([type=checkbox]), select { display:block; width:100%; margin-top:3px; font:inherit; color:var(--ink); background:var(--bg); border:1px solid var(--line); border-radius:7px; padding:6px 8px }
.beats ol { list-style:none; margin:0; padding:0; display:grid; gap:12px }
.beat { display:grid; grid-template-columns:150px 1fr; gap:12px; background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--idle); border-radius:12px; padding:12px }
.beat.passed { border-left-color:var(--ok) } .beat.failed { border-left-color:var(--bad) } .beat.now { outline:2px solid var(--accent) }
@media (max-width:520px) { .beat { grid-template-columns:1fr } }
.play { position:relative; padding:0; overflow:hidden; aspect-ratio:16/9; align-self:start; background:var(--bg) }
.play img { width:100%; height:100%; object-fit:cover; display:block } .play span { position:absolute; inset:auto 6px 6px auto; background:#000a; color:#fff; border-radius:50%; width:26px; height:26px; display:grid; place-items:center; font-size:11px }
.noframe { display:grid; place-items:center; height:100%; color:var(--muted); font-size:12px }
.head { display:flex; justify-content:space-between; gap:8px } .when, .checks, .purpose { color:var(--muted); font-size:13px; margin:2px 0 }
.pending { color:var(--accent); font-size:13px; margin:8px 0 0; font-weight:600 }
.found li, .exports li { margin:4px 0 } .seek { padding:1px 8px; font-size:12px }
#job { margin:16px 20px 0; background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 14px }
#job-log { max-height:220px; overflow:auto; font-size:12px; white-space:pre-wrap; margin:6px 0 0 }
#toast { position:fixed; bottom:16px; left:50%; transform:translateX(-50%); background:var(--ink); color:var(--bg); padding:8px 14px; border-radius:8px; opacity:0; transition:opacity .2s; pointer-events:none; max-width:calc(100% - 32px) }
#toast.on { opacity:1 }
.accept fieldset { border:1px solid var(--line); border-radius:8px; margin:10px 0 } .accept button#accept { margin-top:6px }
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
  const saved = (out, where) => { if (!out.ok) return toast(out.error); toast('Saved'); where.querySelector('.pending').hidden = false; };
  document.querySelectorAll('.beat input').forEach(input => input.addEventListener('change', () => {
    const li = input.closest('.beat');
    post('edit', {beat: li.dataset.beat, [input.name]: input.value}).then(out => saved(out, li));
  }));
  document.querySelectorAll('.look input, .look select').forEach(input => input.addEventListener('change', () => {
    post('edit', {look: {[input.name]: input.value}}).then(out => saved(out, input.closest('.look')));
  }));
  const box = document.getElementById('job'), log = document.getElementById('job-log'), title = document.getElementById('job-title');
  const names = {recut: 'Re-cutting', preview: 'Recording a preview', run: 'Recording'};
  const watch = () => fetch('job.json').then(r => r.json()).then(job => {
    if (!job.kind) return;
    box.hidden = false; log.textContent = job.lines.join('\\n'); log.scrollTop = log.scrollHeight;
    document.querySelectorAll('[data-job]').forEach(b => b.disabled = job.running);
    if (job.running) { title.textContent = names[job.kind] + '...'; return setTimeout(watch, 700); }
    title.textContent = job.code === 0 ? names[job.kind] + ' worked. Loading the new run...' : names[job.kind] + ' failed; the page still shows the last run that worked.';
    if (job.code === 0 && job.n > +document.body.dataset.seen) setTimeout(() => location.reload(), 600);
  });
  document.querySelectorAll('[data-job]').forEach(b => b.onclick = () => post('job', {kind: b.dataset.job}).then(out => out.ok ? watch() : toast(out.error)));
  watch();
})();'''
