# Command map

Use this page to find a command. For a complete first recording and update,
follow the [tutorial](step-by-step.md); for file settings, see the
[project reference](projects.md). `reshoot COMMAND --help` describes each
command with examples; `reshoot run --help` shows a complete `reshoot.toml`.

## Project workflow

`RUN` is a run folder such as `demo/takes/runs/ID`. End it with `latest` for the
newest successful run or `accepted` for the newest accepted run, such as
`demo/latest` or `demo/takes/runs/accepted`. The command prints which run it chose.

| Command | What it does |
|---|---|
| `reshoot --version` | Prints the installed package version |
| `reshoot init demo` | Creates the bundled notes demo; refuses to overwrite files |
| `reshoot init demo --url URL` | Creates a draft for the supplied app URL |
| `reshoot doctor --config CONFIG` | Checks tools and installed detectors without recording |
| `reshoot preview CONFIG` | Makes an isolated preview with the same actions |
| `reshoot preview CONFIG --from BEAT` | Replays earlier actions without capturing them; skips the final edit and scan |
| `reshoot run CONFIG` | Starts the configured app, records, edits and scans a new run |
| `reshoot runs PROJECT` | Lists a project's runs, newest first, with result, review status and which are `latest` and `accepted` |
| `reshoot compare OLD_RUN NEW_RUN --out comparison.json` | Compares stable beat IDs, definitions, evidence and results; `--markdown FILE` adds a summary for a pull request |
| `reshoot review RUN --previous OLD_RUN` | Writes a local comparison page; omitting `--previous` reviews one run |
| `reshoot review RUN --serve` | Serves the review page on this computer only, to accept or reject the run with its buttons; stops once you decide |
| `reshoot accept RUN` | Accepts the exports, beats and scan items in one verdict; name each finding with `--flagged F1` or `--reject F1`, or a single frame by its label. Refuses a preview unless given `--preview` |
| `reshoot review RUN --import-decisions FILE` | Imports the owner's decisions bound to that run and its policy |
| `reshoot export RUN --directory DEST` | Copies the run's videos, GIFs and subtitles locally and prints README Markdown for the GIF; `--file` picks single files; refuses to overwrite unless given `--replace` |
| `reshoot export RUN --record demo/accepted` | Writes the run's small record (report, beat results, evidence frames) for later comparisons |
| `reshoot export RUN --directory DEST --record DIR --markdown FILE --link URL` | Also writes Markdown showing the GIF, the MP4 and each scan finding with its frame, such as for a pull request; finding frames go in `DIR/findings/` |
| `reshoot skills codex --directory PROJECT` | Installs three project-local Codex skills; `--replace` installs over them after an upgrade |
| `reshoot skills claude --directory PROJECT` | Installs the same primary skills for Claude Code |

`RUN` can be the printed run folder or its `run.json`. Artifact names supplied to
`export --file` are relative to that folder. Repeat `--file` to select more
files. `CONFIG` is a `reshoot.toml` path. Versioned runs write under the configuration's
`takes/runs/ID/`, even when invoked from another directory.

## Individual takes and edits

| Command | What it does |
|---|---|
| `reshoot rec URL story.toml` | Opens a fresh browser and drafts a storyboard from recorded actions, with suggested result checks |
| `reshoot web story.toml takes/web.mp4` | Records a declarative TOML browser story |
| `reshoot web story.py takes/web.mp4` | Records a supported Python browser story |
| `reshoot window --list` | Lists macOS windows available to capture |
| `reshoot window APP takes/app.mov --id ID -s 8` | Records one macOS window for eight seconds |
| `reshoot last-change takes/cli.mp4` | Finds the last visible change in a take |
| `reshoot edit edit.toml takes/web.mp4` | Applies a declarative edit; Python edit files also work |
| `reshoot gif takes/web.mp4 takes/loop.gif START END` | Exports the interval between times or named beats |

Terminal recording uses `vhs FILE.tape`. Install VHS separately. See
the [manual workflow](manual.md) for terminal takes, Python helpers and windows.
For a first standalone native recording, use the [macOS window walkthrough](macos-window.md).

## Check and review supplied content

```bash
reshoot check FINAL.mp4 FINAL.gif --full --text-file FINAL.srt --review REVIEW_DIR
```

This decodes every frame and checks exact subtitle text. Without `--full`, video
and GIF checks sample every three seconds by default. `--every SECONDS` changes
that sampling interval. `--ocr tesseract` selects text-only scanning explicitly;
`--watch-for "WORD1,WORD2"` adds words to flag. The scanner's backend and available
detectors are recorded in its report.

After inspecting the current sheets, original frames and text findings, record
your verdict with `reshoot check --review REVIEW_DIR --fail LABEL` for a
failure, or `reshoot check --review REVIEW_DIR --ok` after accepting all remaining
supplied items. Neither command watches or accepts the recording. For a run,
`reshoot accept RUN` records the scan checklist and the recording verdict together.

Standalone check returns 0 for accepted supplied items, 1 for human review pending,
and 2 for an error. Other commands do not use this three-way status convention.
Read `run.json`, `review/report.json` and the actual output before deciding
what happened. [Troubleshooting](troubleshooting.md) explains common failures.
