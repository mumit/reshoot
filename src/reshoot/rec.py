"""Writes a storyboard by watching you use the app: it opens Chrome in a window, you click and type through what the
video should show, and when you close the window it writes the beats.

    reshoot rec http://localhost:8000/ tools/demo/storyboard.py

Chrome starts with a fresh, empty profile, so none of your own accounts or history are there. Use demo data and a
demo account only. Each click and each run of typing becomes a beat, found by the most stable selector it can work
out (a test id, an id, a name or label, a button's words, then its place in the page). The holds come from your own
pauses. Captions are left for you to add. Anything typed into a password field is replaced with a placeholder.
"""
import asyncio, json, re
from datetime import date
from pathlib import Path

from reshoot import web

HERE = Path(__file__).resolve().parent
CLICK, TYPE_EXTRA, CPS = 0.9, 0.9, 13  # about how long __demo.click and __demo.type take: for working out holds


def find(where):
    """JavaScript that finds the element again."""
    kind, value = where
    if kind == "text":
        return f"__demo.byText({json.dumps(value[0])}, {json.dumps(value[1])})"
    return json.dumps(value)


def name_for(where, verb):
    kind, value = where
    words = value[1] if kind == "text" else re.sub(r"[#\[\]=\"'>:().-]+", " ", value).split()[-1:]
    words = words if isinstance(words, str) else " ".join(words)
    slug = re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-")[:24] or "it"
    return f"{verb}-{slug}"


def beats_from(calls):
    """[(name, js, hold, note)] from what the page reported. A run of typing in one field is one beat with the
    final text, and the click that focused the field is dropped, since __demo.type clicks it first."""
    steps = []  # dicts: start, verb, where, and value, key or dy
    for t, ev in calls:
        kind, last = ev["kind"], steps[-1] if steps else None
        if kind == "type":
            if last and last["verb"] == "type" and last["where"] == ev["where"]:
                last.update(value=ev["value"], secret=ev.get("secret"))
                continue
            if last and last["verb"] == "click" and last["where"] == ev["where"]:
                steps.pop()
                t = last["start"]
            steps.append(dict(start=t, verb="type", where=ev["where"], value=ev["value"], before=ev.get("before", ""),
                              secret=ev.get("secret")))
        elif kind == "click":
            steps.append(dict(start=t, verb="click", where=ev["where"]))
        elif kind == "key" and ev["key"] in ("Enter", "Escape"):
            steps.append(dict(start=t, verb="key", where=ev["where"], key=ev["key"]))
        elif kind == "scroll":
            steps.append(dict(start=t, verb="scroll", where=None, dy=ev["dy"]))
    out, used = [], {}
    for i, st in enumerate(steps):
        note = None
        if st["verb"] == "type":
            # Text added to what was there is typed as it is; anything else (cleared, changed) clears the field first.
            before, value = st.get("before") or "", st["value"]
            added = value.startswith(before)
            text = value[len(before):] if added else value
            if st.get("secret"):
                text, note = "demo-password", "a password field: put the demo account's password here"
            if added and not text:
                continue  # focused and left as it was
            clear = "" if added else ", { clear: true }"
            js, took = f"await __demo.type({find(st['where'])}, {json.dumps(text)}{clear})", len(text) / CPS + TYPE_EXTRA
        elif st["verb"] == "click":
            js, took = f"await __demo.click({find(st['where'])})", CLICK
        elif st["verb"] == "key":
            js, took = f"__demo.key({json.dumps(st['key'])})", 0.1
        else:
            js, took = f"await __demo.scroll({st['dy']})", 0.9
        nxt = steps[i + 1]["start"] if i + 1 < len(steps) else None
        hold = 2.5 if nxt is None else max(0.4, min(3.0, round(nxt - st["start"] - took, 1)))
        name = f"press-{st['key'].lower()}" if st["verb"] == "key" else name_for(st["where"], st["verb"]) if st["where"] else st["verb"]
        used[name] = used.get(name, 0) + 1
        out.append((name if used[name] == 1 else f"{name}-{used[name]}", js, hold, note))
    return out


def write(path, url, size, beats):
    lines = [f'"""Recorded with `reshoot rec` on {date.today().isoformat()}. Before recording:',
             "", "- add captions where they help, such as (\"intro\", \"__demo.caption('What this shows')\", 2.0);",
             "- check each hold (seconds after the action), and the selectors, which should still match next time;",
             "- give the beats better names: the cut uses them.", "",
             f"    reshoot web {path} takes/web.mp4", '"""', "", f"URL = {json.dumps(url)}", f"SIZE = {json.dumps(size)}",
             "", "BEATS = ["]
    for name, js, hold, note in beats:
        if note:
            lines.append(f"    # {note}")
        lines.append(f"    ({json.dumps(name)}, {js!r}, {hold}),")
    lines += ['    ("end", "__demo.hide()", 2.5),', "]", ""]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines))


async def session(url, w, h, calls, headless=False, drive=None):
    """Opens the page and collects what's done into calls, until the window is closed (or drive(page) returns, for
    tests)."""
    import websockets
    chrome, profile, ws_url = web.start_chrome(w, h, headless=headless)
    try:
        async with websockets.connect(ws_url, max_size=200_000_000) as ws:
            page = web.Page(ws, [])
            page.calls = calls
            reader = asyncio.create_task(page.read())
            await page.cmd("Page.enable"); await page.cmd("Runtime.enable")
            await page.cmd("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=0, mobile=False)
            await page.cmd("Runtime.addBinding", name="__reshootRec")
            await page.cmd("Page.addScriptToEvaluateOnNewDocument", source=(HERE / "rec.js").read_text())
            await page.cmd("Page.navigate", url=url)
            if drive:
                await drive(page)
                await asyncio.sleep(0.5)  # the last reports, such as a scroll settling
            else:
                print("Chrome is open. Click and type through what the video should show, then close the window.",
                      flush=True)
                await reader  # ends when the window (its tab) is closed
    except (websockets.ConnectionClosed, asyncio.CancelledError):
        pass
    finally:
        web.stop_chrome(chrome, profile)


def main(a):
    w, h, dpr = web.parse_size(a.size)
    calls = []
    try:
        asyncio.run(session(a.url, w, h, calls, headless=a.headless))
    except KeyboardInterrupt:  # stopped from the terminal: keep what was done so far
        pass
    beats = beats_from(calls)
    if not beats:
        raise SystemExit("nothing was clicked or typed, so there's no storyboard to write")
    write(a.out, a.url, a.size, beats)
    print(f"wrote {a.out}: {len(beats)} beats. Add captions and check the holds, then: reshoot web {a.out} takes/web.mp4")
