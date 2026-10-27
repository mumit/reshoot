# Command map

`reshoot COMMAND --help` describes each command. File fields are in the
[project reference](projects.md).

`RUN` is a run folder such as `demo/takes/runs/ID`, its `run.json`,
`demo/latest` (the newest successful run) or `demo/accepted`. `CONFIG` is a
`reshoot.toml`. Numbers for parts, takes, exports and steps start at 1.
Commands that edit a project take `--project demo`.

## Project workflow

### Create and set up

| Command | What it does |
|---|---|
| `reshoot --version` | Prints the version |
| `reshoot create` | Makes the notes project, checks tools, makes a preview and opens the studio; again, it opens the existing project |
| `reshoot create URL --directory demo` | Records the task you show, then previews it. `--no-studio` stops after the preview; `--no-open` prints the studio address |
| `reshoot create --recipe feature --directory demo` | Starts with a recipe: `feature`, `walkthrough` or `release`; `--title` names new cards |
| `reshoot create --resume --directory demo` | Continues a paused creation or retries its preview |
| `reshoot init demo` | Writes the notes project; never overwrites |
| `reshoot init demo --url URL` | Writes a draft for your app |
| `reshoot doctor --config CONFIG` | Checks tools and detectors |
| `reshoot doctor --config CONFIG --probe` | Also tries encoding, browser capture and OCR on made-up input; `--json` for structured output |
| `reshoot recipe list` | Lists [starting recipes](studio.md#choose-a-starting-recipe) |
| `reshoot recipe apply feature` | Applies one; `--title 'Words'` names new cards, `--dry-run` only describes it |

### Record

| Command | What it does |
|---|---|
| `reshoot preview CONFIG` | Records a quicker, smaller run |
| `reshoot preview CONFIG --from BEAT` | Replays earlier steps unrecorded; no edit or scan |
| `reshoot run CONFIG` | Starts the app, records, edits and scans a final; `--full` scans every frame |
| `reshoot runs PROJECT` | Lists runs, newest first, marking `latest` and `accepted` |

### Shape

| Command | What it does |
|---|---|
| `reshoot studio PROJECT` | Opens [the studio](studio.md) until Ctrl-C; `--no-open`, `--port` |
| `reshoot recut RUN` | Edits and scans that run's takes again with the current captions and edit |
| `reshoot step record BEAT` | Records replacement actions for a step into a draft; `--mode before` or `--mode after` adds a step |
| `reshoot step list`, `show DRAFT`, `apply DRAFT`, `discard DRAFT` | Lists the newest draft, shows it, saves it or drops it |
| `reshoot style list` | Lists the built-in and saved styles |
| `reshoot style apply STYLE` | Applies a style key or file |
| `reshoot style save NAME` | Saves the look in `styles.toml`; `--out FILE` writes a style file, `--replace` overwrites |
| `reshoot sequence list` | Lists video parts and step names from the latest run |
| `reshoot sequence range PART --from BEAT --through BEAT` | Sets a part's steps, inclusive |
| `reshoot sequence move PART --to POSITION`, `duplicate PART`, `remove PART` | Moves, repeats or removes a part |
| `reshoot sequence add --take TAKE --from BEAT --through BEAT` | Appends a clip. `--run RUN` on any `sequence` command uses an older run |
| `reshoot frame set EXPORT --fit crop --x 50 --y 50 --view-width 390` | Sets Fit or Crop, crop position and viewing width |
| `reshoot frame record --size 640x480@2` | Sets the browser take's viewport |
| `reshoot frame check RUN` | Prints the run's text-size, clipping and subtitle-pace hints |
| `reshoot tour create --title 'Save and find a note'` | Makes a tour from the checked steps |
| `reshoot tour set STEP --text '...' --x 50 --y 44` | Edits a step and its marker in percent; also `--title`, `--alt`, `--take`, `--beat`, `--width`, `--crop`, `--no-marker` |
| `reshoot tour move STEP --to POSITION`, `add --beat search --take 1`, `remove STEP` | Reorders, appends or removes a step |
| `reshoot tour title --title 'Find a note'` | Renames the tour; `--name` renames the file |
| `reshoot tour disable` | Stops making the tour |
| `reshoot screenshot set NAME --beat search --alt '...'` | Makes a PNG of a step's result; also `--width 960`, `--crop 0.1 0.05 0.8 0.7`, `--native` (no width limit), `--full-frame` (no crop), `--take 2` |
| `reshoot screenshot list`, `remove NAME` | Lists screenshots, or stops making one |
| `reshoot audio set --beat search --text '...'` | Saves a narration line; `--text ''` removes it |
| `reshoot audio set --voice-volume 1 --music-volume 0.15 --duck` | Sets the balance; `--no-duck` turns ducking off |
| `reshoot audio set --engine 'kokoro --voice af_heart --speed 1'` | Chooses the voice, such as [Kokoro](install.md#local-neural-narration) or `say -v Samantha`; `--engine ''` returns to the default |
| `reshoot audio audition search` | Speaks a saved line and prints its WAV path |

### Repair

| Command | What it does |
|---|---|
| `reshoot repair RUN` | Prints a failed run's suggested control and the repair commands |
| `reshoot repair RUN --apply` | Checks the suggestion on the app, then changes only the target |
| `reshoot repair RUN --pick` | Opens a browser at the broken step to choose the control; `--config FILE` for a moved project |

### Review and accept

| Command | What it does |
|---|---|
| `reshoot compare OLD_RUN NEW_RUN --out comparison.json` | Compares steps by ID; `--markdown FILE` writes a pull request summary |
| `reshoot review RUN` | Writes the review page; `--previous OLD_RUN` compares |
| `reshoot review RUN --serve` | Serves it locally to accept or reject |
| `reshoot review RUN --import-decisions FILE` | Imports per-step decisions from the review page |
| `reshoot accept RUN` | Accepts the run; name each finding with `--flagged F1` or `--reject F1`. `--export docs/demo` also copies the exports, replacing them. `--preview` accepts a preview; `--yes` skips the prompt |

### Share

| Command | What it does |
|---|---|
| `reshoot export RUN --directory DEST` | Copies videos, GIFs, subtitles, screenshots and tours, and prints Markdown; `--file NAME` (repeatable) picks files, `--replace` overwrites |
| `reshoot export RUN --record demo/accepted` | Writes the run's record for comparisons |
| `reshoot export RUN --directory DEST --record DIR --markdown FILE --link URL` | Also writes pull request Markdown with each finding's frame in `DIR/findings/` |

### Skills

| Command | What it does |
|---|---|
| `reshoot skills codex --directory PROJECT` | Installs the three primary Codex skills; `--replace` after an upgrade |
| `reshoot skills claude --directory PROJECT` | The same for Claude Code |

## Individual takes and edits

| Command | What it does |
|---|---|
| `reshoot rec URL story.toml` | Drafts a storyboard from what you do in a browser |
| `reshoot web story.toml takes/web.mp4` | Records a TOML or Python browser story |
| `reshoot window --list` | Lists macOS windows |
| `reshoot window APP takes/app.mov --id ID -s 8` | Records one window for 8 seconds |
| `reshoot last-change takes/cli.mp4` | Finds a take's last visible change |
| `reshoot edit edit.toml takes/web.mp4` | Applies an edit file, TOML or Python |
| `reshoot gif takes/web.mp4 takes/loop.gif START END` | Makes a GIF between two times or steps |

Terminals record with `vhs FILE.tape`; see the [manual workflow](manual.md) and
[a macOS window](macos-window.md).

## Check supplied files

```bash
reshoot check FINAL.mp4 FINAL.gif --full --text-file FINAL.srt --review REVIEW_DIR
```

`--full` checks every frame; otherwise `--every SECONDS` (3). `--ocr tesseract`
reads text only; `--watch-for "WORD1,WORD2"` adds words to flag. After looking
at the sheets, `reshoot check --review REVIEW_DIR --fail LABEL` fails an item
and `--ok` accepts the rest. It exits 0 when all are accepted, 1 when some need
a person, and 2 on an error.
