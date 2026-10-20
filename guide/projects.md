# Projects, updates, and review

I start with one task and a result the viewer can read. `BRIEF.md` keeps the audience,
problem, result, and next action beside the recording source.

## Install and start

```bash
uv tool install 'reshoot[browser] @ git+https://github.com/mumit/reshoot'
reshoot init demo
reshoot doctor --config demo/reshoot.toml
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
```

The generated project uses made-up notes data and native Playwright input. Chrome or
Chromium and ffmpeg must be installed. The browser extra is pinned; reshoot uses the
installed Chrome and records its version. `doctor` does not install software.

For another app, `reshoot init demo --url http://localhost:3000/` creates a draft.
Replace the placeholder before recording. Give the app a separate demo database or
account. Configure `[app] reset = "COMMAND"` to reset that data before startup;
`reset_timeout` defaults to 30 seconds. Never use a reset that touches real data.
The app URL must be free before setup. An HTTP error does not count as ready.

Declare demo fixture files with top-level `inputs = ["seed.json"]`. Reports hash those
files, the story, edit file, configuration, and tracked Git changes. Unlisted external
services and untracked app files are not captured by those hashes.

Versioned configs use paths relative to their file. Each run writes to
`takes/runs/ID/` beside the config and prints its report path. `preview` reduces output
resolution without changing the actions. Python storyboards and unversioned configs
keep their legacy behaviour. Versioned projects support web and VHS takes; arbitrary
`run` takes remain a legacy option.

## Harnesses

```bash
reshoot skills codex --directory /path/to/project
reshoot skills claude --directory /path/to/project
```

I use the command for the harness I need. Each installs the three main skills and
refuses an overwrite. The Claude plugin also includes the supporting recording skills.
Codex discovers the installed project skills in `.agents/skills`, and Claude uses
`.claude/skills`. The main entry points are `reshoot-demo`, `reshoot-refresh`, and
`reshoot-review`. Installed skills require CLI 0.2 or newer and use packaged templates.
Live harness trials are separate from package and CLI tests; see the [delivery status](../docs/validation/2026-10-19-delivery-status.md).

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
the legacy JavaScript overlay input and are labelled unverified in comparisons.

## Edit and export

The generated `edit.toml` lists `[[part]]` ranges from indexed takes in `[edit] args`.
`start` and `end` accept seconds or beat names. A `speed` other than 1 needs a visible
`label` and cannot cut or shorten narration. Set `trim_wait = true` and `min_reading = SECONDS` on a result beat, then
`trim_waits = true` at the top of the edit file to shorten its verified hold. The
edit keeps at least 0.8 seconds or the declared reading time, preserves spoken
lines, and burns “Wait shortened” into affected parts. Unmarked holds stay intact.

Optional `music` is relative to the edit
file. A card part uses `card` and `duration`; `[style]` can set its `background`, `foreground`, and relative `font` and `logo` paths. Use music you have permission to share.

`[[export]]` profiles have a safe `name`, even `width` and `height`, `format` (`mp4` or
`gif`), and `fit` (`contain` or `crop` for MP4). Optional `fps`, `max_bytes`, `min_reading` (minimum seconds for every exported caption), and `poster_at` control frame rate, file budget, and poster time. Portrait requires an intentional crop
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
existing copy behaviour.

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

Check exits 0 for accepted supplied items, 1 for human review pending, and 2 for an
operational error. The run report separates execution, scan, and review status.
An empty findings list is not approval. New renders, changed scan settings, or watch
words need appropriate checks. A previous image decision is not approval of a video.

The local review page opens exact artifacts, source-beat evidence, full-size frames,
and previous/current comparisons, including beat durations, story definitions, result checks, and captured environment settings. It exports a decisions JSON file. When the owner
has made those decisions, import it with:

```bash
reshoot review CURRENT_RUN --import-decisions decisions.json
```

The decisions cover the video, beats, and individual flagged frames. Imports must match the run, artifact hashes, and review policy. All required decisions must be accepted before the run reports review completed. A changed file or new
finding invalidates the decision. No run automatically replaces the chosen baseline.
I still watch the complete final video before sharing it.

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
