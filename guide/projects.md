# Projects, updates, and review

This is the reference for versioned project files. For a guided first recording,
use the [agent quickstart](agent-quickstart.md) or the
[CLI tutorial](step-by-step.md). To author files for an existing app,
follow the [own-app walkthrough](your-app.md). The [command map](commands.md)
lists CLI entry points and [Troubleshooting](troubleshooting.md) covers failures.

Start with one task and a result the viewer can read. `BRIEF.md` keeps the audience,
problem, result, and next action beside the recording source.

## Install and start

Install the [platform dependencies](install.md) first, including Tesseract on
Linux. Then:

```bash
uv tool install 'reshoot[browser]'
reshoot init demo
reshoot doctor --config demo/reshoot.toml
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
```

The generated project uses made-up notes data and native Playwright input. Chrome or
Chromium and ffmpeg must be installed. The browser extra is pinned; reshoot uses the
installed Chrome and records its version. `doctor` does not install software.
It reports a missing browser when `RESHOOT_CHROME` points to a missing or
nonexecutable file. Correct or unset that path before recording.

For another app, `reshoot init demo --url http://localhost:3000/` creates a draft.
Replace the placeholder before recording. Give the app a separate demo database or
account. Configure `[app] reset = "COMMAND"` to reset that data before startup;
`reset_timeout` defaults to 30 seconds. Never use a reset that touches real data.
When `[app]` manages startup, its URL must be free before setup. Without that
table, start the app separately and leave it running. An HTTP error does not count
as ready for managed startup.

Declare demo fixture files with top-level `inputs = ["seed.json"]`. Reports hash those
files, the story, edit file, configuration, and tracked Git changes. Unlisted external
services and untracked app files are not captured by those hashes.

Versioned configurations use paths relative to their file. Each run writes to
`takes/runs/ID/` beside the configuration and prints its report path. `preview` reduces output
resolution without changing the actions. Projects with VHS takes retain the configured
browser dimensions so the preview edit can join matching takes. Python storyboards
and unversioned configurations keep their legacy behavior. Versioned projects support
web and VHS takes; arbitrary
`run` takes remain a legacy option.

## Harnesses

The overlay carries the current caption and cursor position across same-origin full
page loads. Inspect the recorded result after navigation. Zoomed and styled captions
are rendered after capture from the caption events.

```bash
reshoot skills codex --directory /path/to/project
reshoot skills claude --directory /path/to/project
```

Use the command for your harness. Each installs the three main skills and
refuses an overwrite. The Claude plugin also includes the supporting recording skills.
Codex discovers the installed project skills in `.agents/skills`, and Claude uses
`.claude/skills`. The main entry points are `reshoot-demo`, `reshoot-refresh`, and
`reshoot-review`. Installed skills require CLI 0.2 or newer and use packaged templates.
Maintainer-operated [separate-Mac trials](../docs/validation/2026-10-22-separate-mac-harnesses.md)
verified implicit refresh and explicit review invocation in both harnesses.
Independent new-user testing is deferred. Example prompts are in the
[own-app guide](your-app.md#use-an-agent).

## Storyboards

A `.toml` storyboard has `schema_version = 1`, an `id`, a `url`, and named `[[beat]]`
entries. Beats have `purpose`, `caption`, `sub`, `hold`, `action`, and `expect` fields.
`reshoot init` supplies a complete example.

Actions are `click`, `type`, `key`, `scroll`, `navigate`, `wait`, and `upload`. Targets
use exactly one of `css`, `test_id`, or `role`, with an optional role `name`, text
filter, or iframe selector `frame`. `type` uses `text` and clears first unless
`clear = false`; `key` needs a `key`; `navigate` needs `url`; `scroll` uses `dy`;
`upload` uses a fixture `file` relative to the storyboard. Unsupported operations fail.

Expectations are `text` with `contains`, `count` with `count`, `value` with `value`,
`visible`, `checked`, and `url` with `contains`. Visible-text checks also check
visibility. Each can set a millisecond `timeout`. Hidden, disabled, covered, missing,
and ambiguous targets fail rather than forcing a click. Failed beats save evidence.

Use `voice = { beat_id = "Words" }` and `voice_engine` for narration, `zoom = true`
for camera work, `blur = ["SELECTOR"]` for persistent blur, and `seed` for cursor
rhythm. An optional `[caption]` table sets `position` (`top` or `bottom`),
`margin` (fraction of frame height), `min_seconds`, `background`, `foreground`,
and a relative `font` path. Styled captions are drawn after reframing and fail if
they cannot fit inside the safe area. A `.take.json` records results, frames, resources, and the actual browser.

`reshoot rec URL story.toml` writes a draft in the new format. Passwords become a
placeholder. Recognized unsupported select, checkbox, radio, and drop interactions fail; add captions,
purposes, result checks, and setup before using the draft. Python storyboards keep
the legacy JavaScript overlay input and are labeled unverified in comparisons.

## Edit and export

Inspect each GIF's opening, ending and duration independently of the MP4.
GIF exports preserve joined sections when card and browser metadata differ.

The generated `edit.toml` lists `[[part]]` ranges from indexed takes in `[edit] args`.
`start` and `end` accept seconds or beat names. A `speed` other than 1 needs a visible
`label` and cannot cut or shorten narration. Set `trim_wait = true` and
`min_reading = SECONDS` on a result beat, then
`trim_waits = true` at the top of the edit file to shorten its verified hold. The
edit keeps at least 0.8 seconds or the declared reading time, preserves spoken
lines, and burns “Wait shortened” into affected parts. Unmarked holds stay intact.

Optional `music` is relative to the edit file. A card part uses `card` and
`duration`; `[style]` can set its `background`, `foreground`, and relative `font`
and `logo` paths. Use music you have permission to share.

`[[export]]` profiles have a safe `name`, even `width` and `height`, `format` (`mp4` or
`gif`), and `fit` (`contain` or `crop` for MP4). Optional `fps`, `max_bytes`,
`min_reading` (minimum seconds for every exported caption), and `poster_at` control
frame rate, file budget, and poster time. Portrait requires an intentional crop
or a separate responsive take; fitting landscape footage does not make its text
readable on a phone. Exports include subtitles and a poster frame. The cut helpers
write `.timeline.json` maps, which keep source cues aligned after edits. Custom
ffmpeg work without a map cannot claim accurate links to source beats.

```bash
reshoot export RUN --directory docs/demo --file takes/demo-final.mp4
```

`RUN` is the printed run folder or `run.json`. Select files recorded in that report.
The command checks their hashes and refuses overwrites. It copies locally without
changing review or publishing status. Legacy `[keep]` configurations retain their
existing copy behavior.

## Check and compare

```bash
reshoot check FINAL.mp4 --full --review REVIEW_DIR
reshoot compare PREVIOUS_RUN CURRENT_RUN --out comparison.json
reshoot review CURRENT_RUN --previous PREVIOUS_RUN
```

Runs also scan generated subtitle and narration text directly. Standalone checks can add
`--text-file FINAL.srt` or `--text-file TAKE.voice.json`. Text findings show cue times
without copying private words into the report.

The default check samples frames every three seconds. `--full` decodes every video
or GIF frame and reuses exact duplicate scans. Neither mode guarantees that OCR or
face detection finds every private detail. Missing inputs and required detectors
are errors. `--no-scan` explicitly skips detection. Sources use opaque IDs so URLs
and filenames do not enter scan logs. Sheets link labels to saved original frames.

For project runs, set `full = true` inside `[check]` to scan every frame of the
declared sources. `every = SECONDS` controls sampled checks when full mode is off.
Full scans often take most of a run; [Faster shoots](speed.md) weighs the options.

Check exits 0 for accepted supplied items, 1 for human review pending, and 2 for an
operational error. The run report separates execution, scan, and review status.
An incomplete browser take leaves expectations unverified unless an assertion failed;
earlier passed assertions do not verify the rest of the flow.
An empty findings list is not approval. New renders, changed scan settings, or watch
words need appropriate checks. A previous image decision is not approval of a video.

The local review page opens exact artifacts, source-beat evidence, full-size frames,
and previous/current comparisons, including beat durations, story definitions,
result checks, and captured environment settings. Previous and current GIFs display
as images; MP4s use video players. It exports a decisions JSON file. When the owner
has made those decisions, import it with:

```bash
reshoot review CURRENT_RUN --import-decisions decisions.json
```

The decisions cover the video, beats, and individual flagged frames. Imports must
match the run, artifact hashes, and review policy. All required decisions must be
accepted before the run reports review completed. A changed file or new
finding invalidates the decision. No run automatically replaces the chosen baseline.
Watch the complete final video before sharing it.

The scan checklist is separate: after inspecting its current sheets, original
frames and text findings, record your verdict with
`reshoot check --review RUN/review --ok`. That updates the scan checklist, not
the recording's decisions. Importing recording decisions does not fill the
scan checklist either. The [tutorial](step-by-step.md#4-review-the-recording-and-scan-sheets)
shows both, including the downloaded file and exact import command. A run report
may retain its initial scan-review snapshot; the current checklist is in
`RUN/review/report.json`.

Partial previews use `reshoot preview CONFIG --from BEAT`. Earlier actions and checks
are replayed without capture. Partial previews skip the final edit and scan because
those may refer to missing beats. They remain candidates, not final exports.
Narration is cached by text and engine command under the project's `takes/voice-cache`.
Change the engine command when changing a voice or model so the cache changes too.

Select OCR explicitly with `[check] ocr = "tesseract"` or `check --ocr tesseract`.
`auto` uses Vision on macOS and Tesseract elsewhere. `RESHOOT_OCR` sets the default
when the project or command does not select one. An explicit backend failure never
silently falls back. Tesseract provides text detection only; faces and people remain
unavailable and are reported that way. `doctor` reports installed capabilities, not
a successful scan of the final video.
