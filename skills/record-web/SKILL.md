---
name: record-web
description: Record a web page or web app acting out a storyboard in headless Chrome, with a moving cursor, typing and captions, using `reshoot web`. Use for the browser part of a demo video, including phone-sized layouts.
---

# Record a web take

The overlay keeps the current caption and cursor position across full page loads on the same origin. Inspect the saved result frames after navigation as well as the action frames.

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
BLUR = [".avatar"]             # blurred on every page for the whole take
VOICE = {"home": "Notes keeps your lists in one place."}  # a voiceover: a line as each named beat starts
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
| `__demo.blur(sel, {px})` / `unblur(sel)` | blurs everything matching sel (12 px), including what the page adds later |
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

## Voiceover

For documentation PNGs, select a checked TOML beat with
`reshoot screenshot set search-result --beat search --alt 'Search shows the matching note' --project demo`.
Update preview to reuse its result frame; record again after the app changes.
The PNG retains page privacy masks and can retain the recorded cursor. It is
the captured viewport, without video captions, zoom or framing. It joins scanning,
review and local export; its alt text is scanned directly when enabled. Never
replace a missing result check with an unverified standalone screenshot.

For a versioned TOML project, use the studio's per-step **Narration** or
`reshoot audio set --beat search --text 'Find the matching note.' --project demo`.
`reshoot audio audition search --project demo` writes one saved line to the
recording's voice cache and prints its WAV path and duration, without launching
the app. In the studio, **Audition saved line** plays it. Audio lists local voices;
`--engine 'say -v Samantha'` sets a command from the CLI and `--engine ''` restores
the default. Custom commands execute with project permissions. Changing words
or voice requires a fresh preview so beats wait for their lines. Empty text
removes a line. Keep every action, expected result and scan source intact.

`VOICE = {beat name: words}` adds a voiceover. Each line is spoken before recording, so reshoot knows how long it
takes, and its beat waits until the line is done: a voiceover never runs into the next beat. The clips go in
`OUT.voice/`, and `OUT.voice.json` says when each starts in the take. The cut adds them (cut-video).

- The voice is macOS's `say` by default, or `espeak-ng` on Linux. `VOICE_ENGINE = "say -v Samantha"` picks a macOS
  voice. Any other text-to-speech is a command with `{out}` for the sound file and the text on stdin, such as
  `VOICE_ENGINE = "python3 tools/demo/tts.py {out}"`; that command handles any service key itself.
- Lines are spoken again only when their words or the engine change.
- Keep lines short and plain, one per beat that needs it. The captions still say the main point on screen, since
  most people watch muted.
- `../../examples/notes/voiced.py` is the notes example with a voiceover.

A beat can follow a link to a new page. The overlay is added to every page, the cursor keeps its place, and the hold
starts once the new page has loaded. Code after the click in the same beat doesn't run, since its page is gone, so
put it in the next beat.

## Steps

1. Start the app on demo data, on its own port.
2. Get a first storyboard, one of two ways:
   - **The person clicks through it:** `reshoot rec http://localhost:8000/ demo/draft.toml` opens Chrome with a
     fresh profile. They click and type through what the video should show and close the window, and it writes the
     beats, with result checks suggested from what each action changed on the page. Keep the suggestions that show
     the result. Ask them to do this when the flow is long or the selectors are hard to find. A `.py` path writes the
     legacy format, without suggestions.
     For a complete owner-driven project, offer `reshoot create URL --directory demo` instead. The TOML recorder
     toolbar adds captions and explicit checks, hides an element, pauses and finishes. Checkbox and radio choices
     replay their state. Unsupported interactions are saved as blocking `recording_issue` steps for repair.
     TOML operations also save `fallbacks` with stable alternative targets. They only suggest a later repair;
     replay never silently substitutes them. Inspect a missing-control failure with `reshoot repair RUN`, apply
     a revalidated suggestion with `--apply`, or let the owner choose with `--pick`, then record a fresh preview.
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
- **Something private on every page,** like the account name in a header: put it in `BLUR`, rather than hoping
  each take avoids it.
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

Browser commands, navigation, beats, and the recording have timeouts. Unexpected page errors fail the take. A new take without `VOICE` removes the old narration metadata.

For a quick whole-project take use `reshoot preview reshoot.toml`; it uses a smaller output and faster encoding. Captured JPEGs are spooled to temporary disk files. Versioned projects keep each run separate, including its narration metadata.

## Native input and TOML stories

For new takes, use a schema-version-1 TOML storyboard with named `[[beat]]` entries, `[[beat.action]]` operations and `[[beat.expect]]` result checks. `reshoot init DIR` supplies a complete notes example. Install the `browser` extra. TOML targets use `css`, `test_id`, or `role` with an optional `name`, `text` and `frame`; guide/projects.md lists every field. Actions use native input and fail on covered, disabled, missing, or ambiguous controls. Never force a click to bypass a broken demo. A `.take.json` records each result check and its screenshot. Python storyboards still use the legacy overlay input and cannot claim the same native-input checks.

`reshoot preview CONFIG --from BEAT` replays earlier actions without capture, then records the selected part. Partial previews skip editing and checking and never replace a final run. Captions wrap to fit the frame; keep copy short enough to read. Narration cache files are keyed by text and engine command and can be reused across isolated runs.

TOML stories can set `[caption]` position, safe margin, minimum seconds, font,
background, and foreground, and `[cursor]` `size` (0.5 to 3), `typing` (characters a second, default 13) and
`ripple` (default true). Clicks, typing and choices show the same glide, press, ripple and uneven typing as
Python storyboards. Inspect a recorded frame near the bottom as well as a
browser screenshot; they use different capture paths.
