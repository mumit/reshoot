# Command map

Use this page to find a command. For a complete first recording and update,
follow the [tutorial](step-by-step.md); for file settings, see the
[project reference](projects.md). `reshoot COMMAND --help` gives its CLI arguments.
`reshoot run --help` also describes the legacy shoot format; versioned TOML
settings are documented in the project reference.

## Project workflow

| Command | What it does |
|---|---|
| `reshoot --version` | Prints the installed package version |
| `reshoot init demo` | Creates the bundled notes demo; refuses to overwrite files |
| `reshoot init demo --url URL` | Creates a draft for the supplied app URL |
| `reshoot doctor --config CONFIG` | Checks tools and installed detectors without recording |
| `reshoot preview CONFIG` | Makes an isolated preview with the same actions |
| `reshoot preview CONFIG --from BEAT` | Replays earlier actions without capturing them; skips the final edit and scan |
| `reshoot run CONFIG` | Starts the configured app, records, edits and checks a new candidate |
| `reshoot compare OLD_RUN NEW_RUN --out comparison.json` | Compares stable beat IDs, definitions, evidence and results |
| `reshoot review RUN --previous OLD_RUN` | Writes a local comparison page; omitting `--previous` reviews one run |
| `reshoot review RUN --import-decisions FILE` | Imports the owner's decisions bound to that run and its policy |
| `reshoot export RUN --directory DEST --file takes/demo-final.mp4` | Copies explicitly selected artifacts locally without overwriting |
| `reshoot skills codex --directory PROJECT` | Installs three project-local Codex skills |
| `reshoot skills claude --directory PROJECT` | Installs the same primary skills for Claude Code |

`RUN` can be the printed run folder or its `run.json`. Artifact names supplied to
`export --file` are relative to that folder. Repeat `--file` to select more
files. `CONFIG` is a `reshoot.toml` path. Versioned runs write under the configuration's
`takes/runs/ID/`, even when invoked from another directory.

## Individual takes and edits

| Command | What it does |
|---|---|
| `reshoot rec URL story.toml` | Opens a fresh browser and drafts a storyboard from recorded actions |
| `reshoot web story.toml takes/web.mp4` | Records a native TOML browser story |
| `reshoot web story.py takes/web.mp4` | Records a supported Python browser story |
| `reshoot window --list` | Lists macOS windows available to capture |
| `reshoot window APP takes/app.mov --id ID -s 8` | Records one macOS window for eight seconds |
| `reshoot last-change takes/cli.mp4` | Finds the last visible change in a take |
| `reshoot edit edit.toml takes/web.mp4` | Applies a declarative edit; Python edit files also work |
| `reshoot gif takes/web.mp4 takes/loop.gif START END` | Exports the interval between times or named beats |

Terminal recording uses `vhs FILE.tape`. Install VHS separately. See
the [manual workflow](manual.md) for terminal takes, Python helpers and windows.

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
failure, or `reshoot check --review REVIEW_DIR --ok` after approving all remaining
supplied items. Neither command watches or accepts the recording.

Standalone check returns 0 for accepted supplied items, 1 for human review pending,
and 2 for an error. Other commands do not use this three-way status convention.
Read `run.json`, `review/report.json` and the actual output before deciding
what happened. [Troubleshooting](troubleshooting.md) explains common failures.
