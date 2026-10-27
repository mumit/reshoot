# A narrated web app workshop

Build a local video teaching one complete loop: demonstrate a useful notes
task, shape its preview, replace an action, polish the result, change the app,
repair the story, compare recordings, inspect the final and download exports.

The [written companion](../../guide/video-workshop.md) stands on its own.
`lesson.toml` holds the narration, scene titles, teaching points and chapter
order. The build produces the workshop and a short first-demo excerpt from the
same recordings. Duration follows the narration and real actions;
the build does not pad it to a target length.

## Build from scratch

From the repository root, install the browser development environment and
the [platform tools](../../guide/install.md). The narration uses optional
[local Kokoro speech](../../guide/install.md#local-neural-narration) on macOS
or Linux. First use downloads the model, selected voice and English language
data. No account or API key is needed.

```bash
uv sync --extra browser --extra kokoro
uv run python examples/tutorial/build.py record
```

For a faster workflow check while changing the recipe, add `--rehearse`.
It exercises the real controls and runs with minimal pauses. Rehearsals are
not candidate videos and cannot pass the final media audit. `--reuse-speech
takes/tutorial/attempt-ID` reuses local narration when its words and voice match.

The command prints a new `takes/tutorial/attempt-ID` folder. It prepares speech,
starts only its synthetic notes server, and records headless browser pages.
Then compose and inspect that exact attempt:

```bash
uv run python examples/tutorial/build.py compose --attempt takes/tutorial/attempt-ID
uv run python examples/tutorial/build.py audit --attempt takes/tutorial/attempt-ID
```

`audit` verifies durations, media streams, chapter and caption timing, actual
native run results and unchanged accepted repository media. It makes chapter
contact sheets, runs the privacy scan with explicitly sampled coverage, and
writes a local review player. Open `review/index.html` from the attempt folder.
It also writes `exports/transcript.md` with the complete narration, chapter
headings and scene timestamps. Both videos and their captions come from
`compose`; the transcript and review player come from `audit`.
For chapter seeking and caption tracks in the browser, use the range-aware
local server:

```bash
uv run python examples/tutorial/build.py serve --attempt takes/tutorial/attempt-ID
```

Open `http://127.0.0.1:8800/review/`. `--port` chooses another local port;
Ctrl-C stops the server. It listens only on `127.0.0.1` and does not publish.

## Change the voice on an existing recording

The workshop uses Heart (`af_heart`) at its normal speed. Audition other voices
on existing footage before rebuilding:

```bash
uv run python examples/tutorial/audition.py --attempt takes/tutorial/attempt-ID
```

It prints a new comparison page under `takes/kokoro-audition-ID/` with Heart,
Bella and Michael reading the same shorter script over original notes footage.
Repeat `--voice ID` to choose other English voices. The clips are listening
samples, not accepted workshop exports.

To replace narration without capturing the app again, change `lesson.toml`, then:

```bash
uv run python examples/tutorial/build.py renarrate --attempt takes/tutorial/attempt-ID
```

It creates a new attempt with copied original footage, native demo evidence
and downloadable demo files, then generates speech from the current lesson
and composes both edits. Scene IDs and order must match the original capture.
Audit and serve the new path printed by the command. Original recordings and
the audio in the demonstrated demo files are retained.

## Prepare a download bundle

After auditing the final attempt:

```bash
uv run python examples/tutorial/package.py --attempt takes/tutorial/attempt-ID
```

This creates a new `distribution/` directory in that attempt. `--out DIRECTORY`
chooses another new destination. It contains:

- `reshoot-workshop-heart.zip`: both MP4s, SRT/VTT captions, chapter JSON,
  transcript, a portable chapter player and viewing instructions.
- `SHA256SUMS`: a checksum for the ZIP.
- `tutorial-upload.txt` and `first-demo-upload.txt`: draft titles, descriptions,
  source links and navigation timestamps.
- `release-notes.md`: draft GitHub release notes and upload instructions.

Recipients can play the MP4s without installing reshoot or Kokoro. The included
README explains how to serve the chapter player locally with caption tracks.
The bundle leaves out internal review sheets, model files and raw footage.

Packaging checks that the MP4s match the audit. It does not accept, upload or
publish anything. Watch both final edits before sharing. Upload the matching
SRT files with the videos; use the workshop's timestamps for platform chapters.
The short introduction has only two navigation timestamps.

For a standalone GitHub video release, use a `workshop-*` tag. This repository's
`v*` tags start its Python package release workflow.

## What the recording means

- All application data is the packaged notes fixture. No real files, accounts
  or photos are used. Capture is of headless browser pages only.
- A scripted hand sends native browser input to the real recorder and Studio.
  For interactive capture, a filming hook supplies that hand in a headless
  browser. It does not mock the recorder, result checks, edits, repair or runs.
- Command graphics are instructions, not simulated terminal output. Full
  process logs remain off screen and are retained with the attempt.
- Actual page footage stays under `raw/`. The edit map records retained time
  ranges. Only recording waits may be shortened, with an on-screen label;
  clicks and typing retain their original speed. The studio page is shown at
  125% so its words can be read, and detail views crop its right column.
  The opening plays the finished demo and holds its result under the
  introduction; the hold is labeled and recorded in the edit map.
- Local synthetic narration is disclosed. Kokoro speaks connected passages;
  subtitle cues use its model word timings. Subtitles are
  available as SRT, VTT and an embedded MP4 subtitle track. Browser audio is
  not mixed over the workshop voice; the native demo exports retain their audio.
  Workshop and excerpt audio are normalized to -18 LUFS for consistent playback.
- Every native recording and the workshop remain pending owner review. The
  build never clicks acceptance controls, publishes, or overwrites `docs/demo/`.

The source snapshot, invocation logs, before-change app/project, captured
scenes, native run manifests and exports stay with the attempt. Recompose an
attempt without recording it again after an editorial change. A completed
recording can be resumed with `record --attempt`; incomplete creation may
need a new attempt. Keep failed attempts for diagnosis.

## Files to inspect

| File | Purpose |
|---|---|
| `exports/tutorial.mp4` | Narrated workshop with chapters and optional subtitles |
| `exports/first-demo.mp4` | Short first-demo excerpt |
| `exports/*.srt`, `*.vtt` | Captions for both edits |
| `exports/transcript.md` | Timestamped narration and chapter headings, generated by `audit` |
| `exports/notes-demo-exports.zip` | The final notes demo downloaded through Studio |
| `review/index.html` | Local chapter player, transcript, contact sheets and scan links |
| `timeline.json` | Exact scene timing, crops and shortened waits |
| `audit.json` | Mechanical verification and stated review status |

Installation troubleshooting, platform limitations and advanced setup belong
in the linked guides. Keep this lesson focused on useful decisions and the
second recording, and refresh its source as the studio changes.
