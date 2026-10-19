---
name: record-web
description: Record a web page or web app acting out a storyboard in headless Chrome, with a moving cursor, typing and captions, using `reshoot web`. Use for the browser part of a demo video, including phone-sized layouts.
---

# Record a web take

`reshoot web STORYBOARD.py OUT.mp4` opens the page in headless Chrome, plays the beats, and writes:

- `OUT.mp4`: 60 fps, at the page size times the pixel ratio (1280x720@1.5 gives 1920x1080);
- `OUT.beats.json`: when each beat starts, for cutting;
- `OUT.assets.json`: every image and media URL the page loaded, for check-privacy;
- `OUT.events.json`: each action and caption, with where and when.

Only the page is captured, so nothing else on the screen can show.

## The storyboard

A Python file. `../../examples/notes/storyboard.py` from this skill's folder is a full one.

```python
URL = "http://localhost:8000/"
SIZE = "1280x720@1.5"          # CSS width x height @ pixel ratio
THEME = "dark"                 # prefers-color-scheme
SETUP = [                      # run before recording: log in, clear what the last take left
    ("login", "await __demo.type('#email', 'demo@example.com'); await __demo.type('#password', 'demo'); __demo.key('Enter')", 1),
]
WARM = ["#map"]                # views to open before recording, so their data is loaded
ASSETS = ["/uploads/"]         # optional: only list URLs containing these
ZOOM = True                    # zoom in on clicks and typing; or {"scale": 1.8, "quiet": 4.0, ...} (see below)
BEATS = [
    ("home",   "__demo.caption('Find any note', 'works offline')", 2.0),
    ("type",   "__demo.caption(null); await __demo.type('#q', 'bikes')", 0.4),
    ("search", "await __demo.click('#go'); await __demo.waitFor('#results li')", 2.5),
    ("end",    "__demo.caption('Notes', 'open source'); __demo.hide()", 2.5),
]
```

Each beat is (name, JavaScript, seconds to hold after it). The JavaScript runs in the page inside an async function.
`__demo` has:

| Call | Does |
|---|---|
| `await __demo.click(sel)` | glides the cursor there and clicks, with a ripple |
| `await __demo.type(sel, text, {clear: true})` | clicks the field and types at a person's pace |
| `__demo.key("Enter")` | presses a key; Enter submits the form |
| `await __demo.waitFor(sel or fn, ms)` | waits until something appears |
| `await __demo.scroll(dy, {sel})` | scrolls smoothly |
| `await __demo.to(sel)` / `moveTo(x, y)` | moves the cursor without clicking |
| `__demo.caption(text, small)` / `caption(null)` | shows or hides a caption |
| `__demo.hide()` / `show()` | hides or shows the cursor |
| `__demo.byText(tag, text)` | the element whose words are text, such as `byText("button", "Save")`; pass it to `click` |
| `__demo.zoom(sel, {scale})` / `zoomOut()` | with `ZOOM` on: zooms in on sel until `zoomOut()`, over the automatic zoom |

A beat may also call the app's own functions, or set `location.hash`, when that's simpler than clicking.

## Zoom on clicks

With `ZOOM = True` (or `--zoom`), the view moves in on what's being clicked or typed. It's worked out after
recording, from where each action happened and from the frames, so it starts just before a click and lands as the
click happens. The view moves only when it has to, since zooming out and back in for nothing is distracting:

| Next thing | What the view does |
|---|---|
| An action already in view, after any pause (up to `quiet`) | stays |
| An action just out of view, if a wider view still enlarges 1.2x or more | widens to take it in |
| An action far away | moves out, then in on the new place |
| Nothing for `quiet` seconds, or a new caption | moves out |
| Something sizeable changes outside the view (a new list item, a new page) | moves out once the action under way is done (just before, for a new page) and stays out for `show` seconds |

Small changes, like the text caret, the cursor and a click's ripple, don't count as changes. A target already as
wide as the page isn't zoomed, so phone layouts mostly stay as they are.

- Settings: `scale` (1.8) is the most it enlarges, `lead` (0.7 s) how early it starts, `hold` (1.0 s) how long it
  stays after the last action, `quiet` (4 s) how long a pause ends a zoom, `show` (1 s) how long it stays out to
  show a change, and `watch` (on) whether it looks at the frames for changes.
- The page is recorded at up to twice its pixel ratio, so zoomed text stays sharp.
- Captions are drawn after the zoom, so they stay put. They're plain text there: tags such as `<i>` are dropped.
- It takes longer: about 2.5 times the length of the take, against about 1.5 without zoom.

A beat can follow a link to a new page. The overlay is added to every page, the cursor keeps its place, and the hold
starts once the new page has loaded. Code after the click in the same beat doesn't run, since its page is gone, so
put it in the next beat.

## Steps

1. Start the app on demo data, on its own port.
2. Get a first storyboard, one of two ways:
   - **The person clicks through it:** `reshoot rec http://localhost:8000/ tools/demo/storyboard.py` opens Chrome
     with a fresh profile. They click and type through what the video should show and close the window, and it
     writes the beats. Ask them to do this when the flow is long or the selectors are hard to find.
   - **You write it:** read the app's HTML for the selectors. Prefer test ids, ids and names.
3. Finish the storyboard: add captions, check the holds, and give the beats names the cut can use. Try a beat at a
   time: put the beats so far in the file and record a short take.
4. Record: `reshoot web tools/demo/storyboard.py takes/web.mp4`. Each beat prints how long it took. A beat that
   fails stops the take and names the beat.
5. Look at frames, not only the log: `ffmpeg -ss 5 -i takes/web.mp4 -frames:v 1 frame.png`, at several times.
6. For phones: `--size 390x844@3 --mobile`, or `SIZE` and `MOBILE = True` in a second storyboard.

## Pitfalls

- **Waiting for results.** A fixed hold that's fine on one run is too short on the next. After a click that loads
  something, `await __demo.waitFor(...)` before the hold.
- **Blank maps and images when first shown.** Each take starts with a fresh browser profile, so nothing is cached.
  List those views in `WARM`.
- **Logged out.** The fresh profile has no cookies. Log in with a demo account in `SETUP`. Never point reshoot at
  someone's own browser profile.
- **Phone sizes.** Headless Chrome won't make a window under 500 px. reshoot sets the size with device metrics
  instead, and prints a note if the page's `innerWidth` isn't the width asked for.
- **Frameworks ignore typed text.** React and others watch the field's value setter. `__demo.type` uses it; setting
  `el.value` yourself in a beat may not update the app.
- **Random content.** A view that picks items at random shows different things in each take. Every take needs its own
  check, not just the first.
- **The last frame.** Chrome sends no frames while the page is still. reshoot holds each frame until the next, and
  the last until recording stops, so the end card gets its full time.
- **Zooming hides a result.** A result that appears outside the view is normally caught by watching the frames.
  One that's small (a short line of text, a little icon) may not count as a change. Call `__demo.zoomOut()` in the
  beat that shows it.
- **Zooming in and out too often.** Usually a long hold in a recorded storyboard: a pause spent finding the next
  button. If the next action is far away, shorten that hold. Or raise `quiet`.
- **A recorded storyboard is a draft.** `reshoot rec` turns a password into a placeholder, skips ids that look made
  up by a framework, and finds a button by its words when it can. Read the selectors anyway: one that matches only
  by its place in the page breaks first when the page changes.
- **Page errors** are printed at the end. Fix them: they often mean a beat ran before the page was ready.
