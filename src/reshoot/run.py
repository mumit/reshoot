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


def answers(url):
    try:
        urllib.request.urlopen(url, timeout=2)
        return True
    except urllib.error.HTTPError:  # it answered, even if with an error page
        return True
    except OSError:
        return False


def start_app(app):
    url = app.get("url")
    if url and answers(url):
        raise SystemExit(f"something is already answering at {url}: stop it first, so the takes show the app this "
                         "shoot starts")
    print(f"starting the app: {app['run']}", flush=True)
    proc = subprocess.Popen(app["run"], shell=True, start_new_session=True)
    if url:
        deadline = time.time() + app.get("timeout", 60)
        while not answers(url):
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
            os.killpg(proc.pid, signal.SIGKILL)


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
    path.write_text(json.dumps(report, indent=1))
    if out := os.environ.get("GITHUB_OUTPUT"):
        with open(out, "a") as f:
            f.write(f"ok={str(report['ok']).lower()}\nunchecked={report['unchecked'] or 0}\n"
                    f"flagged={report.get('flagged') or 0}\nreport={path}\n")


def main(a):
    path = Path(a.config)
    if not path.exists():
        raise SystemExit(f"no {path}: see `reshoot run --help` for what goes in it")
    shoot = tomllib.loads(path.read_text())
    plan = list(steps(shoot))
    takes = [Path(t["out"]) for t in shoot.get("take", []) if "out" in t]
    report_path = Path(shoot.get("report", takes[0].parent / "run.json" if takes else "takes/run.json"))
    report = {"config": str(path), "steps": [], "ok": False, "unchecked": None, "kept": []}
    app, t0 = None, time.time()
    try:
        if "app" in shoot:
            app = start_app(shoot["app"])
        for name, cmd in plan:
            print(f"\n== {name}", flush=True)
            t = time.time()
            if cmd[0] == "vhs" and not shutil.which("vhs"):
                raise SystemExit("vhs isn't installed: see https://github.com/charmbracelet/vhs#installation")
            code = subprocess.run(cmd).returncode
            report["steps"].append({"step": name, "ok": code == 0, "seconds": round(time.time() - t, 1)})
            if code:
                raise SystemExit(f"{name} failed (exit {code})")
    finally:
        stop_app(app)
        report["seconds"] = round(time.time() - t0, 1)
        if not all(s["ok"] for s in report["steps"]) or len(report["steps"]) < len(plan):
            save(report, report_path)  # the run failed: say so before stopping

    if check := shoot.get("check"):
        print("\n== check", flush=True)
        review = check.get("review", "takes/review")
        cmd = reshoot("check", *check.get("sources", []), "--review", review, "--every", check.get("every", 3),
                      *[a for w in check.get("watch_for", []) for a in ("--watch-for", w)],
                      *([] if check.get("scan", True) else ["--no-scan"]))
        code = subprocess.run(cmd).returncode
        key, flags = Path(review) / "key.json", Path(review) / "flags.json"
        report["unchecked"] = len(json.loads(key.read_text())) if code == 1 and key.exists() else 0
        report["flagged"] = len(json.loads(flags.read_text())) if code == 1 and flags.exists() else 0
        report["review"] = review
    for src, dst in shoot.get("keep", {}).items():
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        report["kept"].append(dst)
    report["ok"] = True
    save(report, report_path)

    print(f"\ndone in {report['seconds']:.0f} s: {len(plan)} steps", end="")
    if report["kept"]:
        print(f", kept {', '.join(report['kept'])}", end="")
    print(f". Report in {report_path}.")
    if report["unchecked"]:
        print(f"{report['unchecked']} images haven't been checked by eye yet"
              + (f", and the scan flagged {report['flagged']}" if report.get("flagged") else "")
              + f": look at the sheets in {report['review']}/ before sharing anything.")
