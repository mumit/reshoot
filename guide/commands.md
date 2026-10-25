# Command map

Use this page to find a command. For a complete first recording and update,
follow the [tutorial](step-by-step.md); for file settings, see the
[project reference](projects.md). `reshoot COMMAND --help` describes each
command with examples; `reshoot run --help` shows a complete `reshoot.toml`.

## Project workflow

`RUN` is a run folder such as `demo/takes/runs/ID`. End it with `latest` for the
newest successful run or `accepted` for the newest accepted run, such as
`demo/latest` or `demo/takes/runs/accepted`. The command prints which run it chose.

### Create and set up

| Command | What it does |
|---|---|
| `reshoot --version` | Prints the installed package version |
| `reshoot create` | Creates the notes project, checks dependencies, makes a preview and opens the studio. Run it again and it opens the existing project, making a preview only when it has no run yet |
| `reshoot create URL --directory demo` | Records your task in a fresh browser with a toolbar, then makes a preview and opens the studio; `--no-studio` stops after the preview, `--no-open` prints the studio address |
| `reshoot create --resume --directory demo` | Continues setup or retries a failed preview from the saved creation, preserving its story, URL and viewport; a completed creation opens the studio |
| `reshoot init demo` | Creates the bundled notes demo; refuses to overwrite files |
| `reshoot init demo --url URL` | Creates a draft for the supplied app URL |
| `reshoot doctor --config CONFIG` | Checks tools and installed detectors without recording |
| `reshoot doctor --config CONFIG --probe` | Tests temporary synthetic H.264 encoding/inspection, TOML browser capture and configured OCR; `--json` includes structured checks and fixes |

### Record

| Command | What it does |
|---|---|
| `reshoot preview CONFIG` | Makes an isolated preview with the same actions |
| `reshoot preview CONFIG --from BEAT` | Replays earlier actions without capturing them; skips the final edit and scan |
| `reshoot run CONFIG` | Starts the configured app, records, edits and scans a new run |
| `reshoot runs PROJECT` | Lists a project's runs, newest first, with result, review status and which are `latest` and `accepted` |

### Shape

| Command | What it does |
|---|---|
| `reshoot studio PROJECT` | Opens the latest recording to edit captions and holds, undo/redo, update the preview, compare checked revision frames, make a final, inspect scan sheets and accept the displayed run; saved history offers explicit recovery after restart; runs until Ctrl-C |
| `reshoot recut RUN` | Edits and scans that run's takes again into a new run, after a change to `edit.toml` or the captions; nothing is recorded |
| `reshoot style list --project demo` | Lists Focus, Midnight, Paper and the project's saved visual styles |
| `reshoot style apply STYLE --project demo` | Applies a listed style key or portable TOML file to captions, title-card colours and framing; update the preview afterwards |
| `reshoot style save NAME --project demo` | Saves the current look in `demo/styles.toml`; `--out FILE` exports a portable style, `--replace` permits overwriting |
| `reshoot sequence list --project demo` | Lists the video parts and recorded beat names from the latest complete successful run |
| `reshoot sequence range PART --from BEAT --through BEAT --project demo` | Saves an inclusive beat range; the task and checks stay unchanged |
| `reshoot sequence move PART --to POSITION --project demo` | Moves a video part; part and position numbers start at 1 |
| `reshoot sequence duplicate PART --project demo` | Repeats a video part immediately after itself |
| `reshoot sequence remove PART --project demo` | Removes a video part, keeping at least one |
| `reshoot sequence add --take TAKE --from BEAT --through BEAT --project demo` | Appends a clip; take numbers start at 1. `--run RUN` on any sequence command selects an older complete run from the project |
| `reshoot frame set EXPORT --fit crop --x 50 --y 50 --view-width 390 --project demo` | Sets Fit/Crop, crop position and viewing width without changing the task; export numbers start at 1, update the preview afterwards |
| `reshoot frame record --size 640x480@2 --project demo` | Sets the first TOML browser take's viewport; Update preview records again with the existing actions and checks |
| `reshoot frame check RUN` | Reads measured font-size, clipping and subtitle-reading hints bound to that run's artifacts; this is not an automatic readability verdict |
| `reshoot tour create --title 'Save and find a note' --project demo` | Creates one offline tour from the first browser take's checked beats; update the preview to build it |
| `reshoot tour set STEP --text 'The note was saved.' --x 50 --y 44 --project demo` | Edits step words and marker position in percentages; `--no-marker` removes the marker. `--title`, `--alt`, `--take`, `--beat`, `--width` and `--crop` also edit a step |
| `reshoot tour move STEP --to POSITION --project demo` | Reorders a tour step; numbers start at 1 |
| `reshoot tour add --beat search --take 1 --project demo` | Appends a checked step; words can be given or edited afterwards |
| `reshoot tour remove STEP --project demo` | Removes a step, keeping at least one |
| `reshoot tour title --title 'Find a note' --project demo` | Changes the tour title; `--name` changes the HTML file name |
| `reshoot tour disable --project demo` | Stops exporting the tour in future runs; previous local files remain |
| `reshoot screenshot set NAME --beat search --alt 'Search shows the matching note' --project demo` | Selects a checked browser result frame for a stable PNG; Update preview renders it and includes it in scan/review |
| `reshoot screenshot set NAME --width 960 --crop 0.1 0.05 0.8 0.7 --project demo` | Changes maximum width and crop fractions; `--native` removes the width limit, `--full-frame` removes cropping, `--take 2` selects another browser take |
| `reshoot screenshot list --project demo` | Lists named documentation screenshot settings |
| `reshoot screenshot remove NAME --project demo` | Stops exporting a screenshot in future runs; previously copied files remain |
| `reshoot audio set --beat search --text "Find the matching note." --project demo` | Saves a narration line on the first TOML browser take; empty `--text ''` removes it. Update preview records again so beats wait for their lines |
| `reshoot audio audition search --project demo` | Speaks one saved line into the recording's voice cache and prints its WAV path and duration; no app capture |
| `reshoot audio set --voice-volume 1 --music-volume 0.15 --duck --project demo` | Saves linear gains and music ducking in `edit.toml`; `--no-duck` disables ducking, and Update preview re-cuts the current recording |
| `reshoot audio set --engine 'say -v Samantha' --project demo` | Changes the narration command; `--engine ''` returns to the system default. Custom commands need `{out}` and read text on stdin |

### Repair

| Command | What it does |
|---|---|
| `reshoot repair RUN` | Inspects a failed browser run and prints any suggested control and the repair commands |
| `reshoot repair RUN --apply` | Starts the configured demo app, replays to the failure and revalidates the suggestion before changing only the target |
| `reshoot repair RUN --pick` | Opens a fresh browser at the broken step; select and confirm the replacement without activating it. `--config FILE` names a relocated project |

### Review and accept

| Command | What it does |
|---|---|
| `reshoot compare OLD_RUN NEW_RUN --out comparison.json` | Compares stable beat IDs, definitions, evidence and results; `--markdown FILE` adds a summary for a pull request |
| `reshoot review RUN --previous OLD_RUN` | Writes a local comparison page; omitting `--previous` reviews one run |
| `reshoot review RUN --serve` | Serves the review page on this computer only, to accept or reject the run with its buttons; stops once you decide |
| `reshoot accept RUN` | Accepts the exports, beats and scan items in one verdict; name each finding with `--flagged F1` or `--reject F1`, or a single frame by its label. Refuses a preview unless given `--preview` |
| `reshoot review RUN --import-decisions FILE` | Imports the owner's decisions bound to that run and its policy |

### Share

| Command | What it does |
|---|---|
| `reshoot export RUN --directory DEST` | Copies videos, GIFs, subtitles, documentation PNGs and offline tour HTML locally, and prints Markdown; `--file` picks single files; refuses to overwrite unless given `--replace` |
| `reshoot export RUN --record demo/accepted` | Writes the run's small record (report, beat results, evidence frames) for later comparisons |
| `reshoot export RUN --directory DEST --record DIR --markdown FILE --link URL` | Also writes Markdown showing the GIF, the MP4 and each scan finding with its frame, such as for a pull request; finding frames go in `DIR/findings/` |

### Skills

| Command | What it does |
|---|---|
| `reshoot skills codex --directory PROJECT` | Installs three project-local Codex skills; `--replace` installs over them after an upgrade |
| `reshoot skills claude --directory PROJECT` | Installs the same primary skills for Claude Code |

`RUN` can be the printed run folder or its `run.json`. Artifact names supplied to
`export --file` are relative to that folder. Repeat `--file` to select more
files. `CONFIG` is a `reshoot.toml` path. Versioned runs write under the configuration's
`takes/runs/ID/`, even when invoked from another directory.

## Individual takes and edits

| Command | What it does |
|---|---|
| `reshoot rec URL story.toml` | Opens a fresh browser with recording controls and drafts a storyboard, explicit and suggested result checks; Done finishes, or close the window |
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
