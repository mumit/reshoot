"""Records one app window on macOS, never the whole screen.

    reshoot window --list                 # the windows on screen: id, app, title
    reshoot window TextEdit OUT.mov -s 8  # 8 seconds of TextEdit's front window

It finds the window's id with Quartz and records it with `screencapture -v -l<id>`. The terminal running this needs
Screen Recording permission (System Settings, Privacy & Security, Screen Recording). The window must be on screen,
not minimized. The recording includes the window's shadow; cut.window_box() finds the window inside it.
"""
import platform, subprocess
from pathlib import Path


def windows():
    """[(id, app, title)] of the ordinary windows on screen, front to back."""
    if platform.system() != "Darwin":
        raise SystemExit("reshoot window works on macOS only")
    import Quartz
    out = []
    for w in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
                                               Quartz.kCGNullWindowID):
        if w.get("kCGWindowLayer") == 0:
            out.append((int(w["kCGWindowNumber"]), w.get("kCGWindowOwnerName", ""), w.get("kCGWindowName") or ""))
    return out


def find(app, title=None):
    """The id of app's frontmost window (whose title contains title, if given)."""
    for wid, owner, name in windows():
        if owner == app and (title is None or title in name):
            return wid
    raise SystemExit(f"no window of {app!r} on screen" + (f" titled like {title!r}" if title else "") +
                     ": is it open and not minimized? `reshoot window --list` shows what's there")


def record(wid, out, seconds):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)  # screencapture won't overwrite
    r = subprocess.run(["screencapture", "-x", "-v", f"-V{seconds}", f"-l{wid}", str(out)])
    if r.returncode or not out.exists() or out.stat().st_size == 0:
        raise SystemExit("screencapture couldn't record the window. Give the app running this (Terminal, iTerm, your "
                         "editor) Screen Recording permission in System Settings, Privacy & Security, then restart it.")
    return out


def main(a):
    if a.list:
        for wid, owner, name in windows():
            print(f"{wid:8}  {owner:24}  {name}")
        return
    if not a.app or not a.out:
        raise SystemExit("give an app name and an output file, or --list")
    wid = a.id or find(a.app, a.title)
    print(f"recording window {wid} of {a.app} for {a.seconds} s")
    record(wid, a.out, a.seconds)
    print("wrote", a.out)
