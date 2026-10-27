# Project reference

Every field of a demo project's files, and what a run writes. Paths in a file
are relative to that file. [Commands](commands.md) lists the CLI.

## The files

`BRIEF.md` says who the demo is for, the task, the visible result and how to
reset the data. `reshoot.toml`, `storyboard.toml` and `edit.toml` are below;
`styles.toml` holds saved styles. `takes/runs/ID/` holds each run and stays
out of Git; `accepted/` is the [accepted run](publish.md#the-accepted-run)'s
record to commit. `reshoot init demo` writes the notes project;
`reshoot init demo --url URL` a draft for your app.

## reshoot.toml

```toml
schema_version = 1
inputs = ["seed.json"]

[app]
run = "cd .. && npm run dev -- --port 3000"
url = "http://127.0.0.1:3000/"
reset = "cd .. && npm run demo:reset"

[[take]]
web = "storyboard.toml"
out = "takes/demo.mp4"

[edit]
file = "edit.toml"
args = ["takes/demo.mp4"]

[check]
sources = ["takes/demo-final.mp4", "takes/demo-final-readme.gif"]
review = "review"
```

| Field | Default | What it does |
|---|---|---|
| `schema_version` | required | `1`. Without it the file is a [legacy shoot](#legacy-shoot-files) |
| `inputs` | none | Demo data files inside the project; a change makes **Update preview** record again |
| `timeout` | `600` | Seconds for app startup, takes and edit together |
| `[app] run` | none | Shell command that starts the app, from this folder. Without `[app]`, a running server is used |
| `[app] url` | required with `run` | Recording waits until this answers; nothing may answer before |
| `[app] timeout` | `60` | Seconds to wait for `url` |
| `[app] reset` | none | Shell command that resets demo data before startup |
| `[app] reset_timeout` | `30` | Seconds `reset` may take |
| `[[take]] web` | | A `storyboard.toml` (or legacy `.py`) recorded in headless Chrome |
| `[[take]] out` | required with `web` | The video to write, such as `takes/demo.mp4` |
| `[[take]] tape` | | A [VHS](https://github.com/charmbracelet/vhs) tape; its `Output` line names the video |
| `[edit] file` | none | The `edit.toml`, or `script` for a Python edit |
| `[edit] args` | `[]` | The takes, numbered 0, 1, ... |
| `[check] sources` | `[]` | Files to scan. `takes/demo.assets.json` adds every image the page loaded |
| `[check] review` | | Folder for scan sheets |
| `[check] scan` | `true` | `false` skips detection but still makes sheets |
| `[check] full` | `false` | Scan every frame of a final. Previews always sample |
| `[check] every` | `3` | Seconds between sampled frames |
| `[check] watch_for` | `[]` | Words to flag, such as a real company name |
| `[check] ocr` | `"auto"` | `"vision"` (macOS) or `"tesseract"`; a chosen one never falls back. `RESHOOT_OCR` sets it too |

Each take has one of `web` or `tape`. The app is stopped at the end of a run,
even when a step fails.

### Documentation screenshots

Each `[[screenshot]]`:

| Field | Default | What it does |
|---|---|---|
| `name` | required | 1 to 80 letters, digits, `_` or `-`; writes `screenshots/NAME.png` |
| `take`, `beat` | `0`, required | The TOML browser take and a step whose result checks pass |
| `alt` | required | One line, at most 300 characters; scanned and used in Markdown |
| `width` | captured size | Maximum width, 160 to 3840 px; never enlarges |
| `crop` | whole page | `[left, top, width, height]` as fractions |

The PNG is the step's result frame, without captions, zoom or frame, and is
scanned. A preview with `--from` makes none.

### Offline tour

One optional `[tour]` with `[[tour.step]]` tables writes `tours/NAME.html`, a
single offline file.

| Field | Default | What it does |
|---|---|---|
| `name` | required | 1 to 80 letters, digits, `_` or `-` |
| `title` | required | Up to 120 characters of plain text |
| `[[tour.step]]` | required | 1 to 30 steps |
| step `take`, `beat` | `0`, required | A TOML browser take and a step whose result checks pass |
| step `title`, `alt` | required | Up to 120 and 300 characters |
| step `text` | empty | Up to 1000 characters |
| step `hotspot` | none | `[x, y]` fractions for a numbered marker that goes to the next step |
| step `width`, `crop` | 1280 px maximum, whole page | As for screenshots |

It is scanned with the video. A preview with `--from` makes none.

## storyboard.toml

[Write a checked story](your-app.md#write-a-checked-story) has a complete example.

### Top level

| Field | Default | What it does |
|---|---|---|
| `schema_version` | required | `1` |
| `id` | | The story's name in comparisons |
| `url` | required | The page to open |
| `size` | `"1280x720@1"` | Width x height @ pixel ratio; `@2` gives sharper text |
| `theme` | `"dark"` | `"dark"` or `"light"`, for `prefers-color-scheme` |
| `mobile` | `false` | Touch and a mobile viewport; use a phone `size`, such as `"390x844@3"` |
| `zoom` | `false` | `true` follows clicks and typing; a number sets the most it enlarges (1.8) |
| `blur` | `[]` | Selectors blurred on every page, such as `[".avatar"]` |
| `seed` | `1` | Fixes the cursor path and typing rhythm |
| `timeout` | `600` | Seconds the take may take |
| `voice` | none | A voiceover, `{beat_id = "Words"}`. Each step waits for its line |
| `voice_engine` | `say` or `espeak-ng` | `"kokoro --voice af_heart --speed 1"` for [Kokoro](install.md#local-neural-narration), or a command that reads stdin and writes `{out}` |
| `[[setup]]` | none | Actions before recording, such as a demo login; fields as in `[[beat.action]]` |

### Steps: `[[beat]]`

| Field | Default | What it does |
|---|---|---|
| `id` | required | Letters, digits, `_` and `-`, unique. Keep it stable so runs compare step by step |
| `purpose` | | What the step proves, for reviewers |
| `caption` | none | The caption shown from this step on |
| `sub` | none | A smaller second line |
| `hold` | `1` | Seconds on the result after the actions and checks |
| `recording_issue` | none | An interaction the recorder couldn't save; blocks recording until you add actions and remove it |
| `min_reading` | `0` | Seconds the step stays on screen, even when its wait is shortened |
| `trim_wait` | `false` | Lets the edit shorten this step's wait once its check passed; needs `trim_waits = true` |
| `[[beat.action]]` | none | Actions, in order |
| `[[beat.expect]]` | none | Result checks, after the actions |

### Actions

| `type` | Fields | Does |
|---|---|---|
| `click` | `target` | Glides the cursor there and clicks |
| `type` | `target`, `text`, `clear` (`true`) | Clicks the field, clears it and types |
| `select` | `target`, `option` | Picks a dropdown option by value or label |
| `check` | `target`, `checked` (`true`) | Sets a checkbox or radio button |
| `key` | `target`, `key` | Presses a key, such as `"Enter"` |
| `scroll` | `dy` (`300`) | Scrolls down `dy` pixels |
| `navigate` | `url` | Opens a page |
| `wait` | `target` | Waits until the target is visible |
| `upload` | `target`, `file` | Uploads a demo file |

### Result checks

| `type` | Fields | Passes when |
|---|---|---|
| `text` | `target`, `contains` | The visible target contains the text |
| `count` | `target`, `count` | Exactly that many elements match |
| `value` | `target`, `value` | A field holds the value |
| `visible` | `target` | The target is visible |
| `checked` | `target`, `checked` (`true`) | A checkbox or radio button is in that state |
| `url` | `contains` | The page's URL contains the text |

Every action and check takes `timeout` in milliseconds (`10000`). A target has
one of `css`, `test_id` or `role`, with optional `name` (accessible name, with
`role`), `text` (elements with these words) and `frame` (an iframe selector):

```toml
target = {role = "button", name = "Add note"}
target = {test_id = "note-list"}
target = {css = "#list li", text = "bikes"}
```

`fallbacks`, up to 12 alternative targets, are used only to suggest a
[repair](studio.md#repair-a-step-that-broke), never in place of `target`:

```toml
[[beat.action]]
type = "click"
target = {css = "#save"}
fallbacks = [{role = "button", name = "Save"}, {css = "button[name='save']"}]
```

A target that is missing, hidden, disabled, covered or ambiguous fails the step
and saves a failure image. Steps without result checks show as `unverified`.

### Captions and cursor

| Field | Default | What it does |
|---|---|---|
| `[caption] position` | `"bottom"` | `"top"` or `"bottom"` |
| `[caption] margin` | `0.065` | Distance from the edge, as a fraction of the height, up to 0.4 |
| `[caption] min_seconds` | `0` | Shortest time a caption stays up |
| `[caption] background`, `foreground` | translucent dark, white | Colours, such as `"#f4f1ea"` |
| `[caption] font` | system | A font file |
| `[cursor] size` | `1` | 0.5 to 3 times the arrow |
| `[cursor] typing` | `13` | Characters a second, 1 to 60 |
| `[cursor] ripple` | `true` | `false` drops the ring on each click |

Captions are plain text drawn after recording, so `reshoot recut` can change
them. [How the videos look](look.md) shows each setting.

## edit.toml

```toml
schema_version = 1
output = "demo-final.mp4"

[[part]]
card = "Save a note. Find it again."
duration = 1.5

[[part]]
take = 0
start = 0
end = "end"

[[export]]
preset = "readme"
```

| Field | Default | What it does |
|---|---|---|
| `schema_version` | required | `1` |
| `output` | `"demo-final.mp4"` | The final video |
| `music` | none | A music file you may share; ducks under the voice and fades out |
| `[audio] voice_volume` | `1` | Narration gain, 0 to 2; 0 mutes but keeps timing and subtitles |
| `[audio] music_volume` | `0.25` | Music gain, 0 to 1 |
| `[audio] duck` | `true` | Lower music while the voice speaks |
| `trim_waits` | `false` | Shorten waits of `trim_wait` steps to 0.8 s or their `min_reading`, labelled "Wait shortened" |
| `[style] background`, `foreground` | dark, white | Title card colours; `background` can be `[top, bottom]` for a frame gradient |
| `[style] font`, `logo` | none | Files for title cards |
| `[frame]` | none | Puts each take in a browser window on the `[style]` background; the page shrinks |
| `[frame] padding` | `0.06` | Space each side, as a fraction of the width, up to 0.25 |
| `[frame] radius` | `12` | Corner radius in pixels, up to 64 |
| `[frame] shadow`, `bar` | `true`, `true` | A shadow, and a title bar with three dots |
| `[frame] background`, `bar_color` | `[style] background`, `"#2b2f36"` | Colours for the frame only |
| `[[part]] take` | `0` | Which take in `[edit] args` |
| `[[part]] start`, `end` | the whole take | Seconds or step IDs; `end` stops at that step's start |
| `[[part]] through` | none | A step ID to include through its hold; not with `end` |
| `[[part]] speed` | `1` | Any other speed needs a `label`, and can't shorten a voiceover line |
| `[[part]] label` | none | Words shown on the part, such as "Sped up 2x" |
| `[[part]] card` | | A title card's words, instead of `take` |
| `[[part]] duration` | `2` | Seconds a card stays up |
| `[[export]] preset` | none | A [destination](#export-presets) that sets format, size and rate and checks limits; your fields override it |
| `[[export]] name` | `"landscape"`, or the preset | The file is `demo-final-NAME.mp4` or `.gif` |
| `[[export]] format` | `"mp4"` | `"mp4"` or `"gif"` |
| `[[export]] width`, `height` | `1280`, `720` | Even numbers |
| `[[export]] fit` | `"contain"` | `"contain"` fits the whole frame; `"crop"` fills the shape |
| `[[export]] focus` | `[0.5, 0.5]` | Crop position, 0 (left/top) to 1 (right/bottom) |
| `[[export]] display_width` | up to 640 | Viewing width, 160 to 1920 px, used only to judge text size |
| `[[export]] fps` | 60, or 15 for a GIF | 1 to 120 |
| `[[export]] max_bytes` | none | Fail if the file is larger |
| `[[export]] min_reading` | `0` | Fail if a caption shows for less than this |
| `[[export]] poster_at` | three quarters in | Seconds in for the poster frame |

Each export also gets subtitles, a poster image and a `.readability.json` of
hints: app text under 12 px, captions under 14 px, or subtitles over 18
characters a second.
`reshoot edit edit.py TAKE...` runs a Python edit instead; see the
[manual workflow](manual.md#cut).

### Export presets

| `preset` | Makes | Checked against |
|---|---|---|
| `readme` | GIF, 800x450, 15 fps | GitHub: 10 MB for an image or GIF |
| `readme-video` | MP4, 1280x720, 30 fps | GitHub: 10 MB for a video on a free plan |
| `x` | MP4, 1280x720, 30 fps | X: 0.5 s to 20 min, at most 1280x1024, shape up to 3:1, 60 fps or less |
| `x-square`, `x-portrait` | MP4, 720x720 or 720x1280 | The same |
| `linkedin` | MP4, 1920x1080, 30 fps | LinkedIn: 3 s to 15 min, 75 KB to 5 GB, 256x144 to 4096x2304, shape up to 2.4:1, 10 to 60 fps |
| `linkedin-square`, `linkedin-portrait` | MP4, 1080x1080 or 1080x1350 | The same |

An export that breaks a limit fails and says which. Limits are from
[X](https://docs.x.com/x-api/media/quickstart/best-practices) (without Premium),
[LinkedIn](https://www.linkedin.com/help/linkedin/answer/a548372) and
[GitHub](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files)
on 2026-10-24. Square and portrait presets fit; set `fit = "crop"` or record a
narrower take for readable text.

## Visual style files

`reshoot style apply STYLE` takes a key from `style list` or a style file, and
writes it into the storyboard's `[caption]` and the edit's `[style]` and
`[frame]`. A style file:

```toml
schema_version = 1
name = "Launch look"
frame_enabled = true

[caption]
position = "bottom"
margin = 0.065
background = "#172554f2"
foreground = "#ffffff"

[card]
background = "#172554"
foreground = "#ffffff"

[frame]
background = ["#253a6a", "#101726"]
padding = 0.045
radius = 12
shadow = true
bar = true
bar_color = "#1e293b"
```

`name` is 1 to 60 characters, with an optional `description` up to 200.
Omitted fields take the defaults above; cards default to `#0e0d0c` and white.
A `[frame]` turns framing on unless `frame_enabled = false`. Backgrounds are
one opaque colour or two for a gradient; caption colours may include opacity.

`style save NAME` stores it under `[styles]` in `styles.toml` with a key such
as `launch-look`.

## What a run writes

Each run gets `takes/runs/ID/`. A preview is smaller, quicker and always
sampled.

| File | What it is |
|---|---|
| `run.json` | What ran, step timings, result checks, the scan and review status |
| `review.html` | The exports, findings, scan sheets and each step's result |
| `app.log` | The app's output |
| `takes/NAME.clean.mp4` | The take without captions |
| `takes/NAME.captions.json` | When each caption showed, and its words |
| `takes/NAME.timeline.json` | Where each source step lands in the output |
| `takes/NAME.readability.json` | Text size and clipping hints |
| `takes/NAME.take.json` | Each step's actions, checks, timings and evidence frames |
| `takes/NAME.failure.png` | The page when a step failed |
| `takes/demo-final*.mp4`, `.gif`, `.srt` | The exports |
| `review/` | The scan: numbered sheets, original frames, `flags.json` and `report.json` |

`reshoot recut RUN` re-edits a run's takes into a new run.

## Scan, compare and accept

The scan reads `[check] sources`, subtitles and voiceover for email
addresses, phone numbers, keys, paths with a user name, street addresses,
`watch_for` words and, with Vision, faces and people, grouped into findings
such as `F1`.

`reshoot compare` matches steps by ID. `reshoot accept` covers the exports,
steps and scan, and writes `accepted/`; accept again if a file changes or the
scan reruns. See [commands](commands.md#review-and-accept).

## Legacy shoot files

A `reshoot.toml` without `schema_version` writes into the project, not a run
folder, and can also have:

- `[[take]] run = "COMMAND"`, such as `reshoot window MyApp takes/app.mov -s 8`;
- `[edit] script = "edit.py"`, a Python edit using `reshoot.cut`;
- `[keep]`, copies made by every run, such as `"takes/final.mp4" = "docs/demo.mp4"`.

`reshoot run --help` shows one.
