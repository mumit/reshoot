"""Writes a storyboard by watching you use the app: it opens Chrome in a window, you click and type through what the
video should show, and when you close the window it writes the beats.

    reshoot rec http://127.0.0.1:3000/ demo/draft.toml        # a storyboard.toml draft
    reshoot rec http://localhost:8000/ tools/demo/storyboard.py  # the legacy Python format

Chrome starts with a fresh, empty profile, so none of your own accounts or history are there. Use demo data and a
demo account only. Each click and each run of typing becomes a beat, found by the most stable selector it can work
out (a test id, an id, a name or label, a button's words, then its place in the page). The holds come from your own
pauses. A storyboard.toml draft also suggests result checks from what each action changed on the page: the words
typed showing up in a list, a list getting shorter, a new address, a label that changed. Keep the ones that show the
result. Captions are left for you to add. Anything typed into a password field is replaced with a placeholder. A dropdown choice becomes a select action; checkboxes, radio buttons, multiple choice and drops are not
recorded: it says so and writes no storyboard.
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


def steps_from(calls, include_tab=False):
    """[(name, js, hold, note)] from what the page reported. A run of typing in one field is one beat with the
    final text, and the click that focused the field is dropped, since __demo.type clicks it first."""
    steps = []  # dicts: start, verb, where, and value, key or dy, and the changes it made on the page
    href = None
    for t, ev in calls:
        kind, last = ev["kind"], steps[-1] if steps else None
        if kind == "changed":  # what the step before it changed
            if last:
                last.setdefault("changes", []).extend(ev["changes"])
            continue
        if kind == "page":  # a new page, which the step before it may have opened
            if last and href and ev["href"] != href:
                last.setdefault("changes", []).append({"kind": "url", "href": ev["href"]})
            href = ev["href"]
            continue
        if kind == "type":
            if last and last["verb"] == "type" and last["where"] == ev["where"]:
                last.update(value=ev["value"], secret=ev.get("secret"))
                continue
            changes = []
            if last and last["verb"] == "click" and last["where"] == ev["where"]:
                steps.pop()
                t, changes = last["start"], last.get("changes", [])
            steps.append(dict(start=t, verb="type", where=ev["where"], value=ev["value"], before=ev.get("before", ""),
                              secret=ev.get("secret"), changes=changes))
        elif kind == "click":
            steps.append(dict(start=t, verb="click", where=ev["where"]))
        elif kind == "select":
            changes = []
            if last and last["verb"] == "click" and last["where"] == ev["where"]:
                steps.pop()  # the click that opened the dropdown; select replays the whole choice
                t, changes = last["start"], last.get("changes", [])
            steps.append(dict(start=t, verb="select", where=ev["where"], option=ev["option"], changes=changes))
        elif kind == "key" and ev["key"] in (("Enter", "Escape", "Tab") if include_tab else ("Enter", "Escape")):
            steps.append(dict(start=t, verb="key", where=ev["where"], key=ev["key"]))
        elif kind == "scroll":
            steps.append(dict(start=t, verb="scroll", where=None, dy=ev["dy"]))
    return steps


def beats_from(calls):
    steps = steps_from(calls)
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
                await page.run("window.__reshootFlush && window.__reshootFlush()")  # what the last action changed
                await asyncio.sleep(0.2)
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
    if Path(a.out).suffix == '.toml':
        beats, suggested = write_toml(a.out, a.url, a.size, calls)
        print(f'wrote {a.out}: {beats} beats and {suggested} suggested result checks, from what each action changed. '
              'Keep the checks that show the result, then add captions and purposes before recording.')
        return
    if any(ev['kind'] not in ('click', 'type', 'key', 'scroll', 'changed', 'page') for _, ev in calls):
        raise ValueError('recording contains unsupported interactions; no storyboard written')
    beats = beats_from(calls)
    if not beats:
        raise SystemExit("nothing was clicked or typed, so there's no storyboard to write")
    write(a.out, a.url, a.size, beats)
    print(f"wrote {a.out}: {len(beats)} beats. Add captions and check the holds, then: reshoot web {a.out} takes/web.mp4")


def suggest(step, typed):
    """Up to two result checks from what a step changed on the page, the most telling first: what was typed showing
    up in a list, a list getting shorter, a new address, a label that changed, then any new text."""
    from urllib.parse import urlsplit
    changes = step.get("changes", [])
    def text(where, words):
        found = next((w for w in typed if w in words), None)  # the words someone typed are what to look for
        if not found:
            found = words if len(words) <= 60 else words[:60].rsplit(" ", 1)[0]
        return {"type": "text", "target": {"css": where}, "contains": found}
    added = [c for c in changes if c["kind"] == "added"]
    checks = [text(c["where"], c["text"]) for c in added if any(w in c["text"] for w in typed)][:1]
    checks += [{"type": "count", "target": {"css": c["where"]}, "count": c["count"]}
               for c in changes if c["kind"] == "fewer"][:1]
    for c in reversed(changes):
        if c["kind"] == "url":
            parts = urlsplit(c["href"])
            where = parts.path + ("?" + parts.query if parts.query else "")
            if where not in ("", "/"):
                checks.append({"type": "url", "contains": where})
            break
    checks += [text(c["where"], c["text"]) for c in changes if c["kind"] == "changed"][-1:]
    if not checks and added:
        checks.append(text(added[0]["where"], added[0]["text"]))
    return checks[:2]


def write_toml(path, url, size, calls):
    unsupported = [ev['kind'] for _, ev in calls if ev['kind'] not in ('click', 'type', 'select', 'key', 'scroll', 'changed', 'page')]
    if unsupported:
        raise ValueError('recording includes unsupported interactions: ' + ', '.join(sorted(set(unsupported))))
    lines = ['schema_version = 1', 'url = ' + json.dumps(url), 'size = ' + json.dumps(size)]
    steps = steps_from(calls, include_tab=True)
    if not steps:
        raise ValueError('no supported actions recorded')
    typed, suggested = [], 0
    for i, step in enumerate(steps):
        lines += ['', '[[beat]]', f'id = "action-{i+1}"', 'hold = 1.0', '[[beat.action]]', 'type = ' + json.dumps(step['verb'])]
        if step.get('where'):
            kind, value = step['where']
            if kind == 'css':
                spec = {'css': value}
            else:
                tag, text = value
                spec = {'css': tag, 'text': text}
            lines += ['target = {' + ', '.join(key + ' = ' + json.dumps(value) for key, value in spec.items()) + '}']
        if step['verb'] == 'type':
            value = 'demo-password' if step.get('secret') else step['value']
            lines += ['text = ' + json.dumps(value), 'clear = true']
        elif step['verb'] == 'select':
            lines += ['option = ' + json.dumps(step['option'])]
        elif step['verb'] == 'key':
            lines += ['key = ' + json.dumps(step['key'])]
        elif step['verb'] == 'scroll':
            lines += ['dy = ' + str(step['dy'])]
        if step['verb'] == 'type' and not step.get('secret') and step['value'].strip():
            typed.insert(0, step['value'].strip())
        for check in suggest(step, sorted(typed, key=len, reverse=True)):
            suggested += 1
            lines += ['[[beat.expect]]  # suggested from what this changed on the page: keep it if it is the result',
                      'type = ' + json.dumps(check['type'])]
            if 'target' in check:
                lines += ['target = {css = ' + json.dumps(check['target']['css']) + '}']
            lines += [f'{key} = ' + json.dumps(check[key]) for key in ('contains', 'count') if key in check]
    lines += ['', '[[beat]]', 'id = "end"', 'hold = 0.5']  # the generated edit ends where this starts
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('\n'.join(lines) + '\n')
    return len(steps), suggested
