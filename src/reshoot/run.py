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
    print("starting the demo app", flush=True)
    proc = subprocess.Popen(app["run"], shell=True, start_new_session=True)
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
        yield f"edit {edit['script']}", reshoot("edit", edit["script"], *edit.get("args", []))


def save(report, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(report, indent=2))
    temp.replace(path)
    if out := os.environ.get("GITHUB_OUTPUT"):
        with open(out, "a") as f:
            for name in ('ok', 'unchecked', 'flagged', 'scan_status', 'review_status'):
                value = report.get(name)
                if isinstance(value, bool):
                    value = str(value).lower()
                f.write(f"{name}={value if value is not None else 'unknown'}\n")
            f.write(f"report={path}\n")


def execute(cmd, timeout):
    proc = subprocess.Popen(cmd, start_new_session=True)
    try:
        return proc.wait(timeout)
    finally:
        stop_app(proc)


def main(a):
    path = Path(a.config)
    if not path.exists():
        raise SystemExit(f"no {describe(path)}: see reshoot run --help")
    shoot = tomllib.loads(path.read_text())
    plan = list(steps(shoot))
    takes = [Path(t['out']) for t in shoot.get('take', []) if 'out' in t]
    report_path = Path(shoot.get('report', takes[0].parent / 'run.json' if takes else 'takes/run.json'))
    report = {'schema_version': 1, 'config': describe(path), 'steps': [], 'ok': False,
              'unchecked': None, 'flagged': None, 'kept': [], 'scan_status': 'skipped',
              'review_status': 'pending', 'errors': []}
    app, t0 = None, time.monotonic()
    timeout = shoot.get('timeout', 600)
    try:
        if 'app' in shoot:
            app = start_app(shoot['app'])
        for name, cmd in plan:
            print('\n== ' + redact(name), flush=True)
            t = time.monotonic()
            remaining = timeout - (t - t0)
            if remaining <= 0:
                raise TimeoutError('run exceeded its timeout')
            code = execute(cmd, remaining)
            report['steps'].append({'step': redact(name), 'ok': code == 0,
                                    'seconds': round(time.monotonic() - t, 1)})
            if code:
                raise RuntimeError(f"{redact(name)} failed (exit {code})")
        if check := shoot.get('check'):
            print('\n== check', flush=True)
            review = Path(check.get('review', 'takes/review'))
            check_path = review / 'report.json'
            check_path.unlink(missing_ok=True)
            cmd = reshoot('check', *check.get('sources', []), '--review', review, '--every', check.get('every', 3),
                          *[a for w in check.get('watch_for', []) for a in ('--watch-for', w)],
                          *([] if check.get('scan', True) else ['--no-scan']))
            code = execute(cmd, max(0.01, timeout - (time.monotonic() - t0)))
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
    except (Exception, SystemExit, KeyboardInterrupt) as e:
        report['errors'].append(redact(str(e)) or type(e).__name__)
        raise SystemExit('run failed: ' + report['errors'][-1]) from None
    finally:
        stop_app(app)
        report['seconds'] = round(time.monotonic() - t0, 1)
        save(report, report_path)
    print(f"done in {report['seconds']:.0f} s. Report in {report_path}.")
    if report['review_status'] != 'completed':
        print('Human review is pending; execution success is not approval to publish.')
