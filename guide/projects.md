# Project reference

Every field of the three files in a demo project, and what a run writes. For a
guided first recording, use the [agent quickstart](agent-quickstart.md) or the
[CLI tutorial](step-by-step.md); for your own app, [Record your own web app](your-app.md).
[Commands](commands.md) lists the CLI, and `reshoot COMMAND --help` describes
each command.

## The files

| File | What it holds |
|---|---|
| `BRIEF.md` | The audience, the task, the visible result, the destination, and how to reset the demo data |
| `reshoot.toml` | How to start the app, which takes to record, the edit and the scan |
| `storyboard.toml` | The beats: actions, captions, result checks and holds |
| `edit.toml` | Which parts of the takes to keep, title cards, music and the exports |
| `takes/runs/ID/` | One run: its report, recordings, scan sheets and review page. Ignored by git |
| `accepted/` | The accepted run's report, beat results and evidence frames, without media. Commit it |

`reshoot init demo` writes a complete project with a made-up notes app, and
`reshoot init demo --url URL` a draft for your app. Paths in each file are
relative to that file.

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
| `schema_version` | required | `1`. Without it the file is a legacy shoot, below |
| `inputs` | none | Demo data files inside the project, such as `["seed.json"]`. The report hashes them, so a comparison shows when they changed. It cannot hash an external database |
| `timeout` | `600` | Seconds the app startup, takes and edit may take together |
| `[app] run` | none | The shell command that starts the app, run in this file's folder. Leave `[app]` out to record a server that is already running |
| `[app] url` | required with `run` | Recording waits until this answers without an HTTP error. Nothing may answer there before the run starts |
| `[app] timeout` | `60` | Seconds to wait for `url` |
| `[app] reset` | none | A shell command that resets the demo data before startup. Never point it at real data |
| `[app] reset_timeout` | `30` | Seconds `reset` may take |
| `[[take]] web` | | A `storyboard.toml` (or a legacy `.py` storyboard) recorded in headless Chrome |
| `[[take]] out` | required with `web` | The video to write, inside the run, such as `takes/demo.mp4` |
| `[[take]] tape` | | A [VHS](https://github.com/charmbracelet/vhs) tape for a terminal take. Its `Output "..."` line names the video |
| `[edit] file` | none | The `edit.toml`, or `script` for a Python edit |
| `[edit] args` | `[]` | The takes the edit numbers 0, 1, ... |
| `[check] sources` | `[]` | The files to scan, usually the final MP4 and GIF. `takes/demo.assets.json` adds every image the page loaded |
| `[check] review` | | The folder for scan sheets, inside the run |
| `[check] scan` | `true` | `false` skips detection; the sheets are still made for your eyes |
| `[check] full` | `false` | Scan every frame of a final, as `reshoot run --full` does. Previews always sample |
| `[check] every` | `3` | Seconds between sampled frames |
| `[check] watch_for` | `[]` | Words to flag wherever they appear, such as a real company name |
| `[check] ocr` | `"auto"` | `"vision"` (macOS), `"tesseract"`, or `auto` for Vision on macOS and Tesseract elsewhere. A chosen engine that fails never falls back |

Each take has exactly one of `web` or `tape`. A run with `[app]` stops the app
at the end, even when a step fails. `RESHOOT_OCR` sets the scan engine when the
file doesn't.

## storyboard.toml

```toml
schema_version = 1
id = "notes"
url = "http://127.0.0.1:8765/"
size = "1280x720@1"
seed = 1

[[beat]]
id = "search"
purpose = "Show only the matching note"
caption = "Find the matching note"
hold = 2.0
[[beat.action]]
type = "type"
target = {css = "#q"}
text = "bike"
[[beat.expect]]
type = "count"
target = {css = "#list li"}
count = 1
```

### Top level

| Field | Default | What it does |
|---|---|---|
| `schema_version` | required | `1` |
| `id` | | A name for the story, shown in comparisons |
| `url` | required | The page to open |
| `size` | `"1280x720@1"` | CSS width x height @ pixel ratio. `@2` records twice the pixels for sharper text |
| `theme` | `"dark"` | `"dark"` or `"light"`, for `prefers-color-scheme` |
| `mobile` | `false` | A phone: touch and a mobile viewport. Use a phone `size`, such as `"390x844@3"` |
| `zoom` | `false` | `true` follows clicks and typing with the camera; a number sets the most it enlarges (1.8) |
| `blur` | `[]` | Selectors blurred on every page for the whole take, such as `[".avatar"]` |
| `seed` | `1` | Sets the cursor's path and typing rhythm, so takes match |
| `timeout` | `600` | Seconds the whole take may take |
| `voice` | none | A voiceover: `{beat_id = "Words"}`. Each line is spoken before recording, and its beat waits for it |
| `voice_engine` | `say` or `espeak-ng` | A text-to-speech command; `{out}` is the sound file and the text comes on stdin. Lines are cached by their words and this command, in `takes/voice-cache`, so change the command to change the voice |
| `[[setup]]` | none | Actions run before recording, such as a demo login. Same fields as `[[beat.action]]` |
| `[caption]` | | How captions look, below |
| `[cursor]` | | How the cursor looks, below |

### Beats

Each `[[beat]]` is one step. Its ID stays the same across releases, so runs can
be compared beat by beat.

| Field | Default | What it does |
|---|---|---|
| `id` | required | Letters, digits, `_` and `-`, unique in the story. Edits cut at beat IDs |
| `purpose` | | What the beat proves, for reviewers |
| `caption` | none | The caption shown from this beat on |
| `sub` | none | A smaller second line under the caption |
| `hold` | `1` | Seconds to stay on the result after the actions and result checks |
| `min_reading` | `0` | Seconds the beat must stay on screen, even when its wait is shortened |
| `trim_wait` | `false` | Lets the edit shorten this beat's wait, once its result check passed. Needs `trim_waits = true` in the edit |
| `[[beat.action]]` | none | Actions, in order |
| `[[beat.expect]]` | none | Result checks, after the actions |

### Actions

| `type` | Fields | Does |
|---|---|---|
| `click` | `target` | Glides the cursor there and clicks |
| `type` | `target`, `text`, `clear` (`true`) | Clicks the field, clears it, and types at a person's pace |
| `select` | `target`, `option` | Picks a dropdown option by its value or label |
| `key` | `target`, `key` | Presses a key in the target, such as `"Enter"` in a search field |
| `scroll` | `dy` (`300`) | Scrolls the page down by `dy` pixels |
| `navigate` | `url` | Opens a page |
| `wait` | `target` | Waits until the target is visible |
| `upload` | `target`, `file` | Uploads a demo file, relative to the storyboard |

### Result checks

| `type` | Fields | Passes when |
|---|---|---|
| `text` | `target`, `contains` | The visible target contains the text |
| `count` | `target`, `count` | Exactly that many elements match |
| `value` | `target`, `value` | A field holds the value |
| `visible` | `target` | The target is visible |
| `checked` | `target`, `checked` (`true`) | A checkbox or radio button is checked, or with `checked = false`, not |
| `url` | `contains` | The page's URL contains the text |

Every action and result check can set `timeout` in milliseconds (default
`10000`). A target has exactly one of `css`, `test_id` or `role`, with an
optional `name` (the accessible name, with `role`), `text` (only elements with
these words) and `frame` (an iframe's selector):

```toml
target = {role = "button", name = "Add note"}
target = {test_id = "note-list"}
target = {css = "#list li", text = "bikes"}
```

Actions use real input. A target that is missing, hidden, disabled, covered or
matches more than one element fails the beat, and the run saves a failure
image, rather than forcing the click. Beats without result checks are labeled
`unverified` on the review page.

### Captions and cursor

| Field | Default | What it does |
|---|---|---|
| `[caption] position` | `"bottom"` | `"top"` or `"bottom"` |
| `[caption] margin` | `0.065` | Distance from the edge, as a fraction of the frame's height, up to 0.4 |
| `[caption] min_seconds` | `0` | The shortest time a caption stays up |
| `[caption] background`, `foreground` | translucent dark, white | Colors, such as `"#f4f1ea"` |
| `[caption] font` | system | A font file, relative to the storyboard |
| `[cursor] size` | `1` | 0.5 to 3 times the default arrow |
| `[cursor] typing` | `13` | Characters a second, 1 to 60 |
| `[cursor] ripple` | `true` | `false` leaves out the ring that spreads on each click |

Styled and zoomed captions are drawn after recording, and a run fails if one
cannot fit inside the margins. [How the videos look](look.md) shows each.
Python storyboards, the legacy format, are in the [manual workflow](manual.md).

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
name = "readme"
format = "gif"
width = 800
height = 450
```

| Field | Default | What it does |
|---|---|---|
| `schema_version` | required | `1` |
| `output` | `"demo-final.mp4"` | The final video, beside the first take |
| `music` | none | A music file, relative to this file. It ducks under the voiceover and fades out. Use music you may share |
| `trim_waits` | `false` | Shorten the waits of beats marked `trim_wait`, keeping at least 0.8 s or their `min_reading`, and label them "Wait shortened" |
| `[style] background`, `foreground` | dark, white | Title card colors |
| `[style] font`, `logo` | none | Files for title cards, relative to this file |
| `[[part]] take` | `0` | Which take in `[edit] args` |
| `[[part]] start`, `end` | the whole take | Seconds or beat IDs |
| `[[part]] speed` | `1` | Any other speed needs a `label` shown on screen, and cannot shorten a voiceover line |
| `[[part]] label` | none | Words burned into the part, such as "Sped up 2x" |
| `[[part]] card` | | A title card's words, instead of `take` |
| `[[part]] duration` | `2` | Seconds a card stays up |
| `[[export]] name` | `"landscape"` | Letters, digits, `_` and `-`; the file is `demo-final-NAME.mp4` or `.gif` |
| `[[export]] format` | `"mp4"` | `"mp4"` or `"gif"` |
| `[[export]] width`, `height` | `1280`, `720` | Even numbers |
| `[[export]] fit` | `"contain"` | `"contain"` fits the whole frame in; `"crop"` fills the shape from the middle |
| `[[export]] fps` | 60, or 15 for a GIF | Frames a second, 1 to 120 |
| `[[export]] max_bytes` | none | Fail the export if the file comes out larger |
| `[[export]] min_reading` | `0` | Fail the export if any caption is on screen for less than this |
| `[[export]] poster_at` | three quarters in | Seconds into the export for its poster frame |

Each export also gets subtitles and a poster image. A portrait export of a wide
page shrinks its text: crop on purpose, or record a narrower take. Every cut
writes a `.timeline.json`, which keeps the review page's links from the final
video back to the source beats. `reshoot edit edit.py TAKE...` runs a Python
edit instead; see the [manual workflow](manual.md#cut).

## What a run writes

Each run gets its own folder, `takes/runs/ID/`, beside `reshoot.toml`, so a
failed run never replaces an earlier one. `reshoot runs demo` lists them.
Commands that take a run also accept `demo/latest`, the newest successful run,
and `demo/accepted`, the accepted run. A preview records the same actions at a
smaller size with faster encoding and a sampled scan, and `accept` refuses it.

| File | What it is |
|---|---|
| `run.json` | What ran, how long each step took, the result checks, the scan and the review status |
| `review.html` | The exports, findings, scan sheets and each beat's result, for looking at |
| `app.log` | The app's own output |
| `takes/NAME.take.json` | Each beat's actions, result checks, timings and evidence frames, and the browser used |
| `takes/NAME.failure.png` | The page when a beat failed |
| `takes/demo-final*.mp4`, `.gif`, `.srt` | The exports |
| `review/` | The scan: numbered sheets, original frames, `flags.json` and `report.json` |

The report hashes the story, the edit, `reshoot.toml`, the declared inputs and
uncommitted git changes. Services the app calls and untracked files are not
covered.

## Scan, compare and accept

A run scans the files in `[check] sources`, plus subtitles and voiceover text,
for email addresses, phone numbers, keys, paths with a user name, street
addresses, the `watch_for` words and, with Vision on macOS, faces and people.
It points at likely problems; it never proves a frame is safe. Flagged items
are grouped into findings by what was found, so an address on screen for the
whole video is one finding, `F1`, not hundreds. Tesseract reads text only;
faces and people then need your eyes. A detector that fails is an error, not an
empty list.

```bash
reshoot compare demo/accepted demo/latest --out demo/comparison.json
reshoot review demo/latest --previous demo/accepted
reshoot accept demo/latest --flagged F1
```

`compare` matches beats by ID and reports whether each one's definition,
duration, evidence frame and result checks changed; `--markdown FILE` adds a
summary for a pull request. A matched beat does not mean equal pixels.
`review --previous` writes the review page with both runs side by side.

`accept` covers the exports, every beat and every scan item at once, binds the
decision to the run's exact files and scan settings, and writes `accepted/`.
Each finding must be named with `--flagged` or `--reject`; it stops and lists
them otherwise. It asks for confirmation, and without a terminal needs `--yes`.
A changed file or a new scan undoes the decision. The
[tutorial](step-by-step.md#4-accept-the-recording) walks through it.

For a decision per beat, the review page's **Your decisions** controls download
a file for `reshoot review RUN --import-decisions FILE`; that covers the
recording only, and `reshoot check --review RUN/review --ok` the scan only.
`reshoot check` on its own exits 0 when every item is accepted, 1 when some
still need a person, and 2 on an error.

## Legacy shoot files

A `reshoot.toml` without `schema_version` is a legacy shoot. It writes into
the project rather than a run folder, and can also have:

- `[[take]] run = "COMMAND"`: any command, such as `reshoot window MyApp takes/app.mov -s 8`;
- `[edit] script = "edit.py"`: a Python edit using `reshoot.cut`;
- `[keep]`: copies of finished files, such as `"takes/final.mp4" = "docs/demo.mp4"`, made by every run.

`reshoot run --help` shows one. New projects should use `schema_version = 1`.
