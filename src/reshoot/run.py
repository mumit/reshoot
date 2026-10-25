"""Records a whole demo from a reshoot.toml: starts the app, records each take, edits, scans the exports, and
writes a review page. Each run gets its own folder, takes/runs/ID beside the reshoot.toml, so a failed run never
replaces an earlier one.

    reshoot run demo/reshoot.toml          # a final
    reshoot run demo/reshoot.toml --full   # a final that scans every frame
    reshoot preview demo/reshoot.toml      # the same actions, smaller and quicker

`reshoot init demo` writes a complete project. Its reshoot.toml (paths are relative to this file):

    schema_version = 1
    inputs = ["seed.json"]                 # optional: demo data files, hashed into the report

    [app]                                  # optional: started first, stopped at the end
    run = "npm run dev -- --port 3000"     # runs in this file's folder
    url = "http://127.0.0.1:3000/"         # recording waits until this answers
    timeout = 60                           # seconds to wait
    reset = "npm run demo:reset"           # optional: resets demo data before startup

    [[take]]
    web = "storyboard.toml"                # a browser take, or tape = "cli.tape" for a VHS terminal take
    out = "takes/demo.mp4"

    [edit]
    file = "edit.toml"                     # cuts, cards and exports
    args = ["takes/demo.mp4"]

    [check]                                # the privacy scan of the exports
    sources = ["takes/demo-final.mp4", "takes/demo-final-readme.gif"]
    review = "review"
    watch_for = ["Acme"]                   # optional: words to flag wherever they appear
    full = false                           # true scans every frame, as --full does

guide/projects.md has a table of every field. A run ends with its result checks, what the scan found, the paths of
the video, GIF and review page, and the `reshoot accept` command. It exits 0 when the run worked, even though it
still needs accepting, and nonzero with the failed step, run folder and failure image when it didn't.

Legacy shoot files, without schema_version, write into the project instead of a run folder. They can also have
`run = "COMMAND"` takes, `[edit] script = "edit.py"` and `[keep] "takes/final.mp4" = "docs/demo.mp4"` copies. In
GitHub Actions a run sets the step outputs ok, unchecked, flagged and report.
"""
import json, os, re, shlex, shutil, signal, subprocess, sys, time, tomllib, urllib.error, urllib.request
from pathlib import Path
from reshoot.safety import describe, redact


def answers(url, ready=False):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return not ready or 200 <= response.status < 400
    except urllib.error.HTTPError:
        return not ready
    except OSError:
        return False


def tail(log, lines=15):
    """The end of the app's log, to show beside an error."""
    try:
        text = Path(log).read_text(errors='replace').splitlines()[-lines:]
    except (OSError, TypeError):
        return ''
    return ('\nThe app\'s last output, from ' + str(log) + ':\n  ' + '\n  '.join(text)) if text else ''


def start_app(app, log=None):
    url = app.get("url")
    if url and answers(url):
        from urllib.parse import urlsplit
        parts = urlsplit(url)
        # A loopback address is safe to print; anything else stays redacted.
        where = (f"port {parts.port} on {parts.hostname}" if parts.hostname in ('127.0.0.1', 'localhost', '::1')
                 and parts.port else url)
        raise SystemExit(f"something is already answering at {where}: stop it, or change the port in [app] and the "
                         "storyboard's url, so the takes show the app this shoot starts")
    if app.get('reset'):
        code = execute(['sh', '-c', app['reset']], app.get('reset_timeout', 30), app.get('cwd'))
        if code:
            raise RuntimeError('demo data reset failed')
    print("starting the demo app", flush=True)
    # The app's own output, such as a server's request log, goes to a file in the run folder, not between reshoot's.
    out = open(log, 'ab') if log else None
    try:
        proc = subprocess.Popen(app["run"], shell=True, start_new_session=True, cwd=app.get("cwd"),
                                stdout=out, stderr=subprocess.STDOUT if out else None)
    finally:
        if out:
            out.close()
    if url:
        deadline = time.time() + app.get("timeout", 60)
        while not answers(url, ready=True):
            if proc.poll() is not None:
                raise SystemExit(f"the app stopped before it answered at {url} (exit {proc.returncode})" + tail(log))
            if time.time() > deadline:
                stop_app(proc)
                raise SystemExit(f"the app didn't answer at {url} within {app.get('timeout', 60)} s" + tail(log))
            time.sleep(0.5)
    return proc


def stop_app(proc):
    if proc and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(10)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(10)
            except ProcessLookupError:
                pass


def reshoot(*args):
    """The same reshoot this is running in, as a command."""
    return [sys.executable, "-m", "reshoot.cli", *map(str, args)]


def steps(shoot):
    """(name, command) for each step of the shoot, in order."""
    for i, take in enumerate(shoot.get("take", []), 1):
        if "web" in take:
            if "out" not in take:
                raise SystemExit(f"take {i} ({take['web']}) needs an out, such as out = \"takes/web.mp4\"")
            extra = [a for k in ("url", "size", "theme") if k in take for a in (f"--{k}", take[k])]
            yield f"web {take['web']}", reshoot("web", take["web"], take["out"], *extra, *(["--mobile"] if take.get("mobile") else []))
        elif "tape" in take:
            yield f"tape {take['tape']}", ["vhs", take["tape"]]
        elif "run" in take:
            yield f"run {take['run']}", shlex.split(take["run"])
        else:
            raise SystemExit(f"take {i} needs one of web, tape or run")
    if edit := shoot.get("edit"):
        script = edit.get("file", edit.get("script"))
        if not script:
            raise ValueError("edit needs file or script")
        yield f"edit {script}", reshoot("edit", script, *edit.get("args", []))


def save(report, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(report, indent=2))
    temp.replace(path)
    if out := os.environ.get("GITHUB_OUTPUT"):
        with open(out, "a") as f:
            for name in ('ok', 'unchecked', 'flagged', 'scan_status', 'review_status', 'expectations_status'):
                value = report.get(name)
                if isinstance(value, bool):
                    value = str(value).lower()
                f.write(f"{name}={value if value is not None else 'unknown'}\n")
            f.write(f"report={path}\n")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        # The job's summary page, so a failed beat is visible without reading the log.
        lines = [f"### reshoot: {'recorded' if report.get('ok') else 'failed'}", '',
                 f"- Result checks: {report.get('expectations_status', 'unverified')} ({report.get('expectations_count', 0)})",
                 f"- Scan: {report.get('scan_status')}, {report.get('unchecked') or 0} items to look at, "
                 f"{report.get('flagged') or 0} flagged",
                 f"- Review: {report.get('review_status')}"]
        lines += [f"- Error: {error}" for error in report.get('errors', [])]
        for failure in report.get('repairs', []):
            for target in failure.get('candidates', []):
                lines.append(f'- Suggested control for {failure["beat"]}: `' + redact(json.dumps(target)) + '`; apply explicitly and record again.')
        with open(summary, "a") as f:
            f.write('\n'.join(lines) + '\n\n')


def execute(cmd, timeout, cwd=None):
    env = {**os.environ, 'RESHOOT_IN_RUN': '1'}
    if cwd:
        env['RESHOOT_VOICE_CACHE'] = str(Path(cwd) / 'takes' / 'voice-cache')
    proc = subprocess.Popen(cmd, start_new_session=True, cwd=cwd, env=env)
    try:
        return proc.wait(timeout)
    finally:
        stop_app(proc)


def main(a):
    path = Path(a.config)
    if not path.exists():
        raise SystemExit(f"no {describe(path)}: see reshoot run --help")
    from reshoot.config import prepare
    shoot = prepare(path)
    if getattr(a, 'full', False):
        if 'check' not in shoot:
            raise SystemExit(f'--full scans the exports, but {describe(path)} has no [check]')
        shoot['check']['full'] = True
    if os.environ.get('RESHOOT_FROM_BEAT'):
        shoot.pop('edit', None)
        shoot.pop('check', None)
        shoot.pop('keep', None)
        shoot.pop('screenshot', None)
        shoot.pop('tour', None)
    source = getattr(a, 'source', None)  # a re-cut: the takes of that run, edited and scanned again
    if source:
        source_root, source_report = source
        for take in shoot.get('take', []):
            out = take.get('out') or (re.search(r'(?m)^Output\s+"([^"\n]+)"', Path(take['tape']).read_text()) or [None, None])[1]
            if not out:
                raise ValueError('a take without an out cannot be re-cut')
            relative = Path(out).relative_to(shoot['_run_dir'])
            found = [f for f in (source_root / relative.parent).glob(relative.stem + '.*')]
            if not (source_root / relative).is_file():
                raise ValueError(f'{relative} is not in run {source_report["id"]}: record a new run')
            for f in found:
                target = Path(shoot['_run_dir']) / relative.parent / f.name
                target.parent.mkdir(parents=True, exist_ok=True)
                (shutil.copytree if f.is_dir() else shutil.copyfile)(f, target)
            redraw(take)
        shoot.pop('app', None)
        shoot['take'] = []
        if source_report.get('mode', 'final') != 'final':
            os.environ['RESHOOT_PREVIEW'] = '1'  # a preview's takes stay a preview, scanned the quick way
    plan = list(steps(shoot))
    takes = [Path(t['out']) for t in shoot.get('take', []) if 'out' in t]
    report_path = Path(shoot.get('report', takes[0].parent / 'run.json' if takes else 'takes/run.json'))
    report = {'schema_version': 1, 'config': describe(path), 'steps': [], 'ok': False,
              'unchecked': None, 'flagged': None, 'kept': [], 'scan_status': 'skipped',
              'review_status': 'pending', 'errors': []}
    from reshoot.artifacts import digest
    from importlib.metadata import version
    report['inputs'] = {'config_sha256': digest(path), 'reshoot': version('reshoot'), 'stories': [],
                        'fixtures': [{'source': describe(f), 'sha256': digest(f)} for f in shoot.get('inputs', [])]}
    raw_config = tomllib.loads(path.read_text())
    report['inputs']['recording_config_sha256'] = __import__('hashlib').sha256(json.dumps(
        {k: v for k, v in raw_config.items() if k in ('app', 'take', 'inputs')}, sort_keys=True).encode()).hexdigest()
    for take in shoot.get('take', []):
        story = take.get('web') or take.get('tape')
        if story and Path(story).is_file():
            report['inputs']['stories'].append({'sha256': digest(story), 'kind': 'web' if 'web' in take else 'tape'})
    if source:  # what was recorded is the earlier run's, so its stories and demo data are too
        report['inputs'].update(stories=source_report.get('inputs', {}).get('stories', []),
                                fixtures=source_report.get('inputs', {}).get('fixtures', []))
        report['inputs']['recording_config_sha256'] = source_report.get('inputs', {}).get('recording_config_sha256')
        report['recut_from'] = source_report['id']
    if edit := shoot.get('edit'):
        edit_path = edit.get('file', edit.get('script'))
        if edit_path and Path(edit_path).is_file():
            report['inputs']['edit_sha256'] = digest(edit_path)
    root = shoot.get('_root', str(Path.cwd()))
    revision = subprocess.run(['git', '-C', root, 'rev-parse', 'HEAD'], capture_output=True, text=True)
    if revision.returncode == 0:
        dirty = subprocess.run(['git', '-C', root, 'status', '--porcelain'], capture_output=True).stdout
        tracked_diff = subprocess.run(['git', '-C', root, 'diff', 'HEAD', '--binary'], capture_output=True).stdout
        report['inputs']['tracked_diff_sha256'] = __import__('hashlib').sha256(tracked_diff).hexdigest()
        report['inputs'].update(commit=revision.stdout.strip(), dirty=bool(dirty), dirty_index_sha256=__import__('hashlib').sha256(dirty).hexdigest())
    app, t0, failure = None, time.monotonic(), None
    timeout = shoot.get('timeout', 600)
    report.update(id=shoot.get('_run_id') or __import__('uuid').uuid4().hex, exports=shoot.get('_exports', {}),
                  mode='partial-preview' if os.environ.get('RESHOOT_FROM_BEAT') else 'preview' if os.environ.get('RESHOOT_PREVIEW') else 'final')
    if source:
        report['mode'] = source_report.get('mode', 'final')
    try:
        event_path = report_path.parent / 'events.jsonl'
        event_path.parent.mkdir(parents=True, exist_ok=True)
        def event(kind, **fields):
            with event_path.open('a') as f:
                f.write(json.dumps({'run': report['id'], 'kind': kind, 'at': time.monotonic()-t0, **fields})+'\n')
        event('start')
        if 'app' in shoot:
            app = start_app({**shoot['app'], 'timeout': min(shoot['app'].get('timeout',60), timeout)},
                            report_path.parent / 'app.log')
        for name, cmd in plan:
            print('\n== ' + redact(name).replace(str(Path.cwd().resolve()) + os.sep, ''), flush=True)
            t = time.monotonic()
            event('step_start', index=len(report['steps']))
            remaining = timeout - (t - t0)
            if remaining <= 0:
                raise TimeoutError('run exceeded its timeout')
            code = execute(cmd, remaining, shoot.get('_root'))
            report['steps'].append({'step': redact(name), 'ok': code == 0,
                                    'seconds': round(time.monotonic() - t, 1)})
            event('step_end', index=len(report['steps'])-1, exit=code)
            if code:
                raise RuntimeError(f"{redact(name)} failed (exit {code})")
        if specs := shoot.get('screenshot'):
            from reshoot.screenshots import render
            rows = render(shoot['_run_dir'], specs, raw_config.get('take', []))
            event('screenshots', count=len(rows))
            if 'check' in shoot:
                shoot['check']['sources'] += [str(Path(shoot['_run_dir']) / row['path']) for row in rows
                                             if str(Path(shoot['_run_dir']) / row['path']) not in shoot['check']['sources']]
        if spec := shoot.get('tour'):
            from reshoot.tours import render
            tour = render(shoot['_run_dir'], spec, raw_config.get('take', []))
            event('tour', steps=len(tour['steps']))
            if 'check' in shoot:
                shoot['check']['sources'] += [str(Path(shoot['_run_dir']) / step['image']) for step in tour['steps']]
        if check := shoot.get('check'):
            print('\n== check', flush=True)
            review = Path(check.get('review', 'takes/review'))
            check_path = review / 'report.json'
            check_path.unlink(missing_ok=True)
            cmd = reshoot('check', *check.get('sources', []), *(['--ocr', check['ocr']] if 'ocr' in check else []), *(['--full'] if check.get('full') and not os.environ.get('RESHOOT_PREVIEW') else []), '--review', review, '--every', check.get('every', 3),
                          *[a for w in check.get('watch_for', []) for a in ('--watch-for', w)],
                          *([] if check.get('scan', True) else ['--no-scan']))
            text_paths = sorted({str(p) for p in report_path.parent.rglob('*') if p.suffix == '.srt' or p.name.endswith('.voice.json')})
            if (report_path.parent / 'screenshots.json').is_file():
                text_paths.append(str(report_path.parent / 'screenshots.json'))
            if (report_path.parent / 'tours.json').is_file():
                text_paths.append(str(report_path.parent / 'tours.json'))
            cmd += [arg for p in text_paths for arg in ('--text-file', p)]
            code = execute(cmd, max(0.01, timeout - (time.monotonic() - t0)), shoot.get('_root'))
            result = json.loads(check_path.read_text()) if check_path.exists() else {}
            report.update(review=str(review), scan_status=result.get('scan', {}).get('status', 'failed'),
                          review_status=result.get('review', 'pending'), unchecked=result.get('unchecked'),
                          flagged=result.get('flagged'))
            if code not in (0, 1) or result.get('status') != 'completed':
                raise RuntimeError(f'check failed (exit {code}); see its report')
        for src, dst in shoot.get('keep', {}).items():
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            report['kept'].append(describe(dst))
        report['ok'] = True
        event('completed')
    except (Exception, SystemExit, KeyboardInterrupt) as e:
        report['errors'].append(redact(str(e)) or type(e).__name__)
        failure = 'run failed: ' + report['errors'][-1]
    finally:
        stop_app(app)
        report['seconds'] = round(time.monotonic() - t0, 1)
        from datetime import datetime, timezone
        report['finished_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        from reshoot.artifacts import digest
        report['files'] = [{'path': str(f.relative_to(report_path.parent)), 'sha256': digest(f)}
                           for f in report_path.parent.rglob('*')
                           if f.is_file() and f.resolve().is_relative_to(report_path.parent.resolve())
                           and (f.suffix in ('.mp4', '.mov', '.gif', '.srt') or f.name.endswith(('.take.json', '.timeline.json', '.beats.json', '.events.json', '.voice.json', '.assets.json', '.captions.json', '.readability.json'))
                                or f.parent.name.endswith(('.evidence', '.resources')) or f.name.endswith(('.poster.png', '.failure.png'))
                                or f == report_path.parent / 'screenshots.json' or (f.parent == report_path.parent / 'screenshots' and f.suffix == '.png')
                                or f == report_path.parent / 'tours.json' or (f.is_relative_to(report_path.parent / 'tours') and f.suffix in ('.html', '.png')))]
        checks = []
        metadata_files = list(report_path.parent.rglob('*.take.json'))
        native_takes = sum(str(take.get('web', '')).endswith('.toml') for take in shoot.get('take', []))
        incomplete = len(metadata_files) < native_takes or any(
            not step['ok'] and step['step'].startswith('web ') for step in report['steps'])
        for metadata in metadata_files:
            try:
                result = json.loads(metadata.read_text())
                if result.get('failure'):
                    report.setdefault('repairs', []).append(result['failure'])
                incomplete = incomplete or result.get('status') != 'completed'
                if result.get('error') and result['error'] not in report['errors']:
                    report['errors'].append(result['error'])  # which beat failed, and why
                for beat in result.get('beats', []):
                    checks.extend(beat.get('expectations', []))
            except (OSError, ValueError, TypeError):
                report['errors'].append('unreadable take result metadata')
                report['ok'] = False
                checks.append({'status': 'failed'})
        report['expectations_status'] = 'failed' if any(x.get('status') == 'failed' for x in checks) else 'passed' if checks and not incomplete else 'unverified'
        report['expectations_count'] = len(checks)
        save(report, report_path)
    root = report_path.parent
    if failure or not report["ok"]:
        lines = [(failure or 'run failed').replace(str(Path.cwd().resolve()) + os.sep, ''), '  run folder     ' + shown(root)]
        lines += ['  failure image  ' + shown(p) for p in sorted(root.rglob('*.failure.png'))]
        for item in report.get('repairs', []):
            if item.get('candidates'):
                lines.append('  suggested control ' + redact(json.dumps(item['candidates'][0])))
                lines.append('  apply repair   reshoot repair ' + shlex.quote(shown(root)) + ' --apply')
            lines.append('  choose control reshoot repair ' + shlex.quote(shown(root)) + ' --pick')
        if app is not None and (root / 'app.log').exists():
            lines.append('  app output     ' + shown(root / 'app.log'))
        raise SystemExit('\n'.join(lines))
    from types import SimpleNamespace
    from reshoot import review
    preview = report.get('mode', 'final') != 'final'
    print(f"\nDone in {report['seconds']:.0f} s: {review.status(root, report)}.")
    for path in review.exports(root, report):
        print(f"  {'tour' if path.endswith('.html') else 'PNG' if path.endswith('.png') else 'GIF' if path.endswith('.gif') else 'video':6} " + shown(root / path))
    if report['review_status'] == 'completed':
        return
    try:
        review.main(SimpleNamespace(run_path=str(root), previous=None, import_decisions=None, quiet=True))
    except Exception as e:  # the run has succeeded; a missing page must not fail it
        print('review page not written: ' + (redact(str(e)) or type(e).__name__))
        page = None
    else:
        page = root / 'review.html'
        print('  review ' + shown(page))
    if any(file['path'].endswith('.readability.json') for file in report['files']):
        print('  framing/readability: reshoot frame check ' + shlex.quote(shown(root)))
    if preview:
        print(f'\nThis is a preview, smaller and quicker than a final. When it looks right, record the final:\n'
              f'  reshoot run {shlex.quote(str(a.config))}')
        return
    from reshoot.check import load
    from reshoot.check import findings
    groups = findings(load(root / 'review' / 'flags.json', {}))
    print('\nNothing is accepted or shared yet. Watch the exports' + (' and look at the scan items, findings first,'
          if page else '') + ' then accept the run:')
    print('  reshoot accept ' + shlex.quote(shown(root)) + (' --flagged ' + ' '.join(groups) if groups else ''))
    if page:
        print('or on its review page, with a button for each finding:\n  reshoot review ' + shlex.quote(shown(root)) + ' --serve')


def redraw(take):
    """Draws a re-cut web take's captions again from its storyboard as it is now, and says which changed. A take
    recorded before reshoot drew captions afterwards keeps the ones it has."""
    from reshoot import captions, story
    if not str(take.get('web', '')).endswith('.toml'):
        return
    if not Path(take['out']).with_suffix('.captions.json').is_file():
        print(f'{Path(take["out"]).name} was recorded with its captions in the page, so they stay as they were; '
              'record a new run to change them.', flush=True)
        return
    changed = captions.draw(take['out'], story.load(take['web']), take['web'], quiet=True)
    print(f'Captions from the storyboard as it is now: {", ".join(changed)} changed.' if changed else
          'Captions from the storyboard as it is now; none changed.', flush=True)


def recut(a):
    """Edit and scan an earlier run's takes again, into a new run, without starting the app or recording: for a
    change to edit.toml, such as cards, music, a frame or the exports, or to a storyboard's caption words and
    [caption] look. The new run keeps that recording's result checks."""
    from reshoot.review import read
    source_root, source_report = read(a.run_path)
    if source_report.get('record'):
        raise ValueError('this is a run record without its media; re-cut the run itself, under takes/runs/')
    if not source_report.get('ok'):
        raise ValueError(f'run {source_report["id"]} failed, so there is nothing to re-cut: record a new run')
    config = Path(a.config) if a.config else source_root.parent.parent.parent / 'reshoot.toml'
    if not config.is_file():
        raise ValueError(f'no {describe(config)}: name the project with --config')
    from reshoot.artifacts import digest
    stories = {s['sha256'] for s in source_report.get('inputs', {}).get('stories', [])}
    from reshoot.config import read as read_config
    shoot, folder = read_config(config)
    now = {digest(folder / t[k]) for t in shoot.get('take', []) for k in ('web', 'tape') if k in t and (folder / t[k]).is_file()}
    if stories and now != stories:
        print(f'The storyboard changed since run {source_report["id"]} was recorded. This re-cut uses that recording, '
              'with its actions, waits and holds as they were, and draws its captions again; record a new run to '
              'see any other change.', flush=True)
    print(f'Re-cutting the takes of run {source_report["id"]}; nothing is recorded.', flush=True)
    previous = os.environ.get('RESHOOT_PREVIEW')
    try:
        return main(type('Args', (), {'config': str(config), 'full': a.full, 'source': (source_root, source_report)})())
    finally:
        if previous is None:
            os.environ.pop('RESHOOT_PREVIEW', None)
        else:
            os.environ['RESHOOT_PREVIEW'] = previous


def shown(path):
    """A path as short as it can be from here."""
    path = Path(path)
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def preview(a):
    previous = os.environ.get('RESHOOT_PREVIEW')
    before = os.environ.get('RESHOOT_FROM_BEAT')
    if getattr(a, 'from_beat', None):
        os.environ['RESHOOT_FROM_BEAT'] = a.from_beat
    try:
        from reshoot.config import read
        shoot, _ = read(a.config)
        # VHS keeps its configured dimensions. Preserve matching web dimensions
        # for mixed takes while retaining the preview encoder and report mode.
        os.environ['RESHOOT_PREVIEW'] = 'native-size' if any('tape' in take for take in shoot.get('take', [])) else '1'
        return main(a)
    finally:
        if before is None:
            os.environ.pop('RESHOOT_FROM_BEAT', None)
        else:
            os.environ['RESHOOT_FROM_BEAT'] = before
        if previous is None:
            os.environ.pop('RESHOOT_PREVIEW', None)
        else:
            os.environ['RESHOOT_PREVIEW'] = previous
