"""Writes a storyboard by watching you use the app: it opens Chrome in a window, you click and type through what the
video should show, and Done in the toolbar (or closing the window) writes the beats.

    reshoot rec http://127.0.0.1:3000/ demo/draft.toml        # a storyboard.toml draft
    reshoot rec http://localhost:8000/ tools/demo/storyboard.py  # the legacy Python format

Chrome starts with a fresh, empty profile, so none of your own accounts or history are there. Use demo data and a
demo account only. Each click and each run of typing becomes a beat, found by the most stable selector it can work
out (a test id, an id, a name or label, a button's words, then its place in the page). The holds come from your own
pauses. A storyboard.toml draft also suggests result checks from what each action changed on the page: the words
typed showing up in a list, a list getting shorter, a new address, a label that changed. Keep the ones that show the
result. The TOML toolbar adds captions and explicit result checks, hides selected elements, pauses and removes the
last recorded step. Toolbar controls are not app actions. Passwords become placeholders. Dropdowns, checkboxes
and radio buttons replay their chosen state. Multiple choice, file selection and drops remain as blocking
recording_issue notes for repair, keeping the other steps.
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
        alternatives = ev.get('fallbacks', [])
        if kind == 'undo':
            if steps:
                steps.pop()
            continue
        if kind in ('caption', 'expect'):
            if last is None:
                last = dict(start=t, verb='note', where=None)
                steps.append(last)
            if kind == 'caption':
                last['caption'] = ev['text']
            else:
                last.setdefault('checks', []).append(ev['check'])
            continue
        if kind.startswith('unsupported-'):
            steps.append(dict(start=t, verb='issue', where=None,
                              issue=ev.get('message', 'This interaction needs a manual storyboard action: ' + kind)))
            continue
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
            steps.append(dict(start=t, verb="type", where=ev["where"], value=ev["value"], before=ev.get("before", ""), label=ev.get('label'),
                              secret=ev.get("secret"), changes=changes, fallbacks=alternatives))
        elif kind == "click":
            steps.append(dict(start=t, verb="click", where=ev["where"], label=ev.get('label'), fallbacks=alternatives))
        elif kind in ("select", "check"):
            changes = []
            if last and last["verb"] == "click" and last["where"] == ev["where"]:
                steps.pop()  # the click that opened the dropdown; select replays the whole choice
                t, changes = last["start"], last.get("changes", [])
            value = {'option': ev['option']} if kind == 'select' else {'checked': ev['checked']}
            steps.append(dict(start=t, verb=kind, where=ev['where'], changes=changes, fallbacks=alternatives, **value))
        elif kind == "key" and ev["key"] in (("Enter", "Escape", "Tab") if include_tab else ("Enter", "Escape")):
            steps.append(dict(start=t, verb="key", where=ev["where"], key=ev["key"], fallbacks=alternatives))
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


async def session(url, w, h, calls, headless=False, drive=None, toolbar=False):
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
            await page.cmd("Page.addScriptToEvaluateOnNewDocument", source='window.__reshootToolbar = ' + json.dumps(toolbar) + ';' +
                           (HERE / 'targets.js').read_text() + (HERE / "rec.js").read_text())
            await page.cmd("Page.navigate", url=url)
            if drive:
                await drive(page)
                await asyncio.sleep(0.5)  # the last reports, such as a scroll settling
                await page.run("window.__reshootFlush && window.__reshootFlush()")  # what the last action changed
                await asyncio.sleep(0.2)
            else:
                print("Chrome is open. Use demo data. Show the task, then choose Done in the recording toolbar or close the window.",
                      flush=True)
                while not reader.done() and not any(ev.get('kind') == 'finish' for _, ev in calls):
                    await asyncio.sleep(.15)
    except (websockets.ConnectionClosed, asyncio.CancelledError):
        pass
    finally:
        web.stop_chrome(chrome, profile)
        if 'reader' in locals():
            reader.cancel()
            await asyncio.gather(reader, return_exceptions=True)


def main(a):
    w, h, dpr = web.parse_size(a.size)
    calls = []
    try:
        asyncio.run(session(a.url, w, h, calls, headless=a.headless, toolbar=Path(a.out).suffix == '.toml'))
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


def step_id(step):
    """A beat ID that says what the step did, such as click-albums or type-search-notes: the control's words when the
    recorder saved them, otherwise the last plain word of its selector. """
    verb = step['verb']
    if verb == 'key':
        return 'press-' + re.sub(r'[^a-z0-9]+', '-', str(step.get('key', 'key')).lower()).strip('-')
    if not step.get('where'):
        return {'note': 'note', 'issue': 'needs-repair'}.get(verb, verb)
    from reshoot.repair import words as own_words
    kind, value = step['where']
    words = step.get('label') or own_words(step.get('fallbacks'))
    if kind == 'text':
        words = value[1]
    if not words:  # #tabs > a:nth-of-type(2) says only "tabs"
        plain = [w for w in re.sub(r'[#\[\]=\"\'>:().,-]+', ' ', value).split() if not w.isdigit() and w not in ('nth', 'of', 'type', 'child')]
        words = next((w for w in reversed(plain) if len(w) > 1), plain[-1] if plain else 'it')
    slug = '-'.join(re.findall(r'[a-z0-9]+', words.lower())[:3])[:24].strip('-') or 'it'
    return f'{verb}-{slug}'


def write_toml(path, url, size, calls):
    lines = ['schema_version = 1', 'url = ' + json.dumps(url), 'size = ' + json.dumps(size)]
    hidden = list(dict.fromkeys(ev['selector'] for _, ev in calls if ev['kind'] == 'blur'))
    if hidden:
        lines.append('blur = ' + json.dumps(hidden))
    steps = steps_from(calls, include_tab=True)
    if not steps:
        raise ValueError('no supported actions recorded')
    typed, suggested, used = [], 0, {'end'}
    for i, step in enumerate(steps):
        name = step_id(step)
        ident, number = name, 2
        while ident in used:
            ident = f'{name}-{number}'
            number += 1
        used.add(ident)
        lines += ['', '[[beat]]', 'id = ' + json.dumps(ident), 'hold = 1.0']
        caption = step.get('caption') or step.get('label')
        if caption:
            lines.append('caption = ' + json.dumps(caption))
        if step['verb'] == 'issue':
            lines.append('recording_issue = ' + json.dumps(step['issue']))
            continue
        if step['verb'] != 'note':
            lines += ['[[beat.action]]', 'type = ' + json.dumps(step['verb'])]
        if step.get('where'):
            kind, value = step['where']
            if kind == 'css':
                spec = {'css': value}
            else:
                tag, text = value
                spec = {'css': tag, 'text': text}
            lines += ['target = {' + ', '.join(key + ' = ' + json.dumps(value) for key, value in spec.items()) + '}']
            alternatives = [value for value in step.get('fallbacks', []) if value != spec]
            if alternatives:
                from reshoot.workspace import quote
                lines.append('fallbacks = ' + quote(alternatives))
        if step['verb'] == 'type':
            value = 'demo-password' if step.get('secret') else step['value']
            lines += ['text = ' + json.dumps(value), 'clear = true']
        elif step['verb'] == 'select':
            lines += ['option = ' + json.dumps(step['option'])]
        elif step['verb'] == 'key':
            lines += ['key = ' + json.dumps(step['key'])]
        elif step['verb'] == 'scroll':
            lines += ['dy = ' + str(step['dy'])]
        elif step['verb'] == 'check':
            lines += ['checked = ' + json.dumps(step['checked'])]
        if step['verb'] == 'type' and not step.get('secret') and step['value'].strip():
            typed.insert(0, step['value'].strip())
        manual = step.get('checks', [])
        inferred = suggest(step, sorted(typed, key=len, reverse=True)) if not manual else []
        suggested += len(inferred)
        for check in manual + inferred:
            lines += ['[[beat.expect]]' + ('  # suggested from what this changed on the page: keep it if it is the result' if check in inferred else ''),
                      'type = ' + json.dumps(check['type'])]
            if 'target' in check:
                lines += ['target = {' + ', '.join(k + ' = ' + json.dumps(v) for k, v in check['target'].items()) + '}']
            lines += [f'{key} = ' + json.dumps(check[key]) for key in ('contains', 'count', 'value', 'checked') if key in check]
            if check.get('fallbacks'):
                from reshoot.workspace import quote
                lines.append('fallbacks = ' + quote(check['fallbacks']))
    lines += ['', '[[beat]]', 'id = "end"', 'hold = 0.5']  # the generated edit ends where this starts
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('\n'.join(lines) + '\n')
    return len(steps), suggested
