# A narrated web app workshop

Build a local video teaching one complete loop: demonstrate a useful notes
task, shape its preview, replace an action, polish the result, change the app,
repair the story, compare recordings, inspect the final and download exports.

The [written companion](../../guide/video-workshop.md) stands on its own.
`lesson.toml` holds the narration, scene titles, teaching points and chapter
order. The build produces a long workshop and a short first-demo excerpt from
the same actual recordings. Duration follows the narration and real actions;
the build does not pad it to a target length.

## Build

From the repository root, install the browser development environment and
the [platform tools](../../guide/install.md). The default narration uses an
installed macOS Samantha voice. On Linux, change `voice` in `lesson.toml` to
an installed `espeak-ng` voice before recording.

```bash
uv sync --extra browser
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
If the browser restricts local caption tracks, serve the attempt with
`python3 -m http.server 8800 --directory takes/tutorial/attempt-ID` and open
`http://127.0.0.1:8800/review/`.

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
  clicks and typing retain their original speed. Detail views crop the page.
  The opening plays the finished demo and holds its result under the
  introduction; the hold is labeled and recorded in the edit map.
- Local synthetic narration is disclosed. Sentence-timed subtitles are
  available as SRT, VTT and an embedded MP4 subtitle track. Browser audio is
  not mixed over the workshop voice; the native demo exports retain their audio.
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
| `exports/notes-demo-exports.zip` | The final notes demo downloaded through Studio |
| `review/index.html` | Local chapter player, transcript, contact sheets and scan links |
| `timeline.json` | Exact scene timing, crops and shortened waits |
| `audit.json` | Mechanical verification and stated review status |

Installation troubleshooting, platform limitations and advanced setup belong
in the linked guides. Keep this lesson focused on useful decisions and the
second recording, and refresh its source as Studio changes.
