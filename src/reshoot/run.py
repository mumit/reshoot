"""Runs a whole shoot from a reshoot.toml: starts the app, records each take, cuts, makes the review sheets, and
copies the finished files to where they're kept. Each step runs in its own process, so one failure is reported
clearly and the app is always stopped.

    reshoot run                    # reshoot.toml in this folder
    reshoot run tools/demo/reshoot.toml

A reshoot.toml looks like this (paths are relative to the folder it's run from):

    [app]                                  # optional: the app to record, started first and stopped at the end
    run = "npm run dev -- --port 8000"     # a shell command
    url = "http://localhost:8000/"         # recording waits until this answers
    timeout = 60                           # seconds to wait

    [[take]]
    web = "tools/demo/storyboard.py"       # reshoot web STORYBOARD OUT
    out = "takes/web.mp4"

    [[take]]
    tape = "tools/demo/cli.tape"           # vhs TAPE; the tape's Output names the file

    [[take]]
    run = "reshoot window MyApp takes/app.mov -s 8"   # any other command

    [edit]
    script = "tools/demo/edit.py"          # reshoot edit SCRIPT ARGS
    args = ["takes/web.mp4", "takes/cli.mp4"]

    [check]                                # reshoot check, for the review by eye
    sources = ["takes/web.assets.json", "takes/final.mp4"]
    review = "takes/review"
    watch_for = ["Acme", "Jane Roe"]       # optional: words to flag wherever they appear
    scan = true                            # scan for likely problems (the default)

    [keep]                                 # copies of the finished files, such as into the docs
    "takes/final.mp4" = "docs/demo.mp4"
    "takes/web.gif" = "docs/demo.gif"

It writes run.json next to the first take (or at `report = "..."`) with what happened. In GitHub Actions it also
sets the step's outputs: ok, unchecked, flagged and report.
"""
import json, os, shlex, shutil, signal, subprocess, sys, time, tomllib, urllib.error, urllib.request
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


def start_app(app):
    url = app.get("url")
    if url and answers(url):
        raise SystemExit(f"something is already answering at {url}: stop it first, so the takes show the app this "
                         "shoot starts")
    if app.get('reset'):
        code = execute(['sh', '-c', app['reset']], app.get('reset_timeout', 30), app.get('cwd'))
        if code:
            raise RuntimeError('demo data reset failed')
    print("starting the demo app", flush=True)
    proc = subprocess.Popen(app["run"], shell=True, start_new_session=True, cwd=app.get("cwd"))
    if url:
        deadline = time.time() + app.get("timeout", 60)
        while not answers(url, ready=True):
            if proc.poll() is not None:
                raise SystemExit(f"the app stopped before it answered at {url} (exit {proc.returncode})")
            if time.time() > deadline:
                stop_app(proc)
                raise SystemExit(f"the app didn't answer at {url} within {app.get('timeout', 60)} s")
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


def execute(cmd, timeout, cwd=None):
    env = dict(os.environ)
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
    if os.environ.get('RESHOOT_FROM_BEAT'):
        shoot.pop('edit', None)
        shoot.pop('check', None)
        shoot.pop('keep', None)
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
    for take in shoot.get('take', []):
        source = take.get('web') or take.get('tape')
        if source and Path(source).is_file():
            report['inputs']['stories'].append({'sha256': digest(source), 'kind': 'web' if 'web' in take else 'tape'})
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
    app, t0 = None, time.monotonic()
    timeout = shoot.get('timeout', 600)
    report.update(id=shoot.get('_run_id') or __import__('uuid').uuid4().hex, exports=shoot.get('_exports', {}),
                  mode='partial-preview' if os.environ.get('RESHOOT_FROM_BEAT') else 'preview' if os.environ.get('RESHOOT_PREVIEW') else 'final')
    try:
        event_path = report_path.parent / 'events.jsonl'
        event_path.parent.mkdir(parents=True, exist_ok=True)
        def event(kind, **fields):
            with event_path.open('a') as f:
                f.write(json.dumps({'run': report['id'], 'kind': kind, 'at': time.monotonic()-t0, **fields})+'\n')
        event('start')
        if 'app' in shoot:
            app = start_app({**shoot['app'], 'timeout': min(shoot['app'].get('timeout',60), timeout)})
        for name, cmd in plan:
            print('\n== ' + redact(name), flush=True)
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
        if check := shoot.get('check'):
            print('\n== check', flush=True)
            review = Path(check.get('review', 'takes/review'))
            check_path = review / 'report.json'
            check_path.unlink(missing_ok=True)
            cmd = reshoot('check', *check.get('sources', []), *(['--ocr', check['ocr']] if 'ocr' in check else []), *(['--full'] if check.get('full') else []), '--review', review, '--every', check.get('every', 3),
                          *[a for w in check.get('watch_for', []) for a in ('--watch-for', w)],
                          *([] if check.get('scan', True) else ['--no-scan']))
            text_paths = sorted({str(p) for p in report_path.parent.rglob('*') if p.suffix == '.srt' or p.name.endswith('.voice.json')})
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
        raise SystemExit('run failed: ' + report['errors'][-1]) from None
    finally:
        stop_app(app)
        report['seconds'] = round(time.monotonic() - t0, 1)
        from reshoot.artifacts import digest
        report['files'] = [{'path': str(f.relative_to(report_path.parent)), 'sha256': digest(f)}
                           for f in report_path.parent.rglob('*')
                           if f.is_file() and f.resolve().is_relative_to(report_path.parent.resolve())
                           and (f.suffix in ('.mp4', '.mov', '.gif', '.srt') or f.name.endswith(('.take.json', '.timeline.json', '.beats.json', '.events.json', '.voice.json', '.assets.json'))
                                or f.parent.name.endswith(('.evidence', '.resources')) or f.name.endswith(('.poster.png', '.failure.png')))]
        checks = []
        metadata_files = list(report_path.parent.rglob('*.take.json'))
        native_takes = sum(str(take.get('web', '')).endswith('.toml') for take in shoot.get('take', []))
        incomplete = len(metadata_files) < native_takes or any(
            not step['ok'] and step['step'].startswith('web ') for step in report['steps'])
        for metadata in metadata_files:
            try:
                result = json.loads(metadata.read_text())
                incomplete = incomplete or result.get('status') != 'completed'
                for beat in result.get('beats', []):
                    checks.extend(beat.get('expectations', []))
            except (OSError, ValueError, TypeError):
                report['errors'].append('unreadable take result metadata')
                report['ok'] = False
                checks.append({'status': 'failed'})
        report['expectations_status'] = 'failed' if any(x.get('status') == 'failed' for x in checks) else 'passed' if checks and not incomplete else 'unverified'
        report['expectations_count'] = len(checks)
        save(report, report_path)
    if not report["ok"]:
        raise SystemExit(2)
    print(f"done in {report['seconds']:.0f} s. Report in {report_path}.")
    if report['review_status'] != 'completed':
        print('Human review is pending; execution success is not approval to publish.')
        from types import SimpleNamespace
        from reshoot import review
        try:
            review.main(SimpleNamespace(run_path=str(report_path.parent), previous=None, import_decisions=None))
        except Exception as e:  # the run has succeeded; a missing page must not fail it
            print('review page not written: ' + (redact(str(e)) or type(e).__name__))
        else:
            print('Watch the exports and look at the scan items on that page, then run:')
            print('  reshoot accept ' + shlex.quote(str(report_path.parent)))


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
