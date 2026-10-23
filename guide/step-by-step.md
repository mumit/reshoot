# Make a demo, then update it

To have Codex or Claude Code make a demo of your app, use the
[agent quickstart](agent-quickstart.md). This tutorial teaches the CLI workflow
directly with a bundled example.

Start with the bundled notes app. It saves a made-up note, searches for a word,
and checks that the matching note appears. This tutorial produces an MP4 and a
README GIF, then repairs the recording after a small app change.

Install the [CLI and dependencies](install.md), then run the commands in
one terminal, from a writable folder where a new `demo/` directory can be created.
No repository checkout, VHS, AI account or real user data is needed.

## 1. Create a project

```bash
reshoot init demo
reshoot doctor --config demo/reshoot.toml
```

The first command creates:

```text
demo/
  BRIEF.md          Who the demo is for and what it proves
  index.html       The made-up notes app
  about.html       A second example page
  storyboard.toml  Actions, captions and result checks
  edit.toml        Which parts to keep and which formats to write
  reshoot.toml     App startup, recording, edit and scan settings
```

Keep this terminal in the folder containing `demo`, rather than changing into
it. All commands below use that same working directory. If the directory already
exists, `init` refuses to overwrite its files; choose another name or continue
with the existing project.

`doctor` should report ffmpeg, ffprobe, Chrome and Playwright available, and a
text detector installed. Resolve missing dependencies before recording. On Linux,
Tesseract reads text; faces and people need visual inspection.

## 2. Record a preview

```bash
reshoot preview demo/reshoot.toml
```

Reshoot starts its own local notes server on port 8765, or on the free port
`reshoot init` chose if 8765 was in use. It records a browser page,
cuts the video, writes a GIF, checks the outputs, and stops its server. It never
captures the desktop. The notes reset on each new page load.

The last lines include a report path like:

```text
Report in /.../demo/takes/runs/UNIQUE_ID/run.json.
Human review is pending; execution success is not approval to publish.
/.../demo/takes/runs/UNIQUE_ID/review.html
Watch the exports and look at the scan items on that page, then run:
  reshoot accept /.../demo/takes/runs/UNIQUE_ID
```

Save that run folder in a shell variable, replacing the example ID with the
one printed by the command. `reshoot runs demo` lists every run with its ID:

```bash
PREVIEW=demo/takes/runs/PASTE_PREVIEW_ID_HERE
```

The run wrote `$PREVIEW/review.html`; it prints the path but does not open a
browser. Open that file using the browser's File > Open command or a file
manager. On macOS, run `open "$PREVIEW/review.html"`; on a Linux desktop,
run `xdg-open "$PREVIEW/review.html"`. In a headless environment, copy the complete
run folder to a machine with a browser, preserving its subdirectories.

Watch `takes/demo-final.mp4` and `takes/demo-final-readme.gif`. The note
“Pick up the bikes” should be saved, then remain as the single result for “bike”.
The report should show successful execution and three passed expectations.
The `intro` and `end` beats have no assertions and may be labeled `unverified`;
the save and search beats have the actual result checks.

The preview is smaller than the final. Use it to catch wrong actions or unreadable
captions before making the final recording. If a command fails, keep its run
folder and see [Troubleshooting](troubleshooting.md).

You have the first clip. Stop here to [explore features](features.md) or
[change captions, timing and export size](customize.md). Continue below when
ready to learn final review, updates and comparison. To record your own target,
choose [source code](your-app.md), a [running URL](running-web-app.md) or a
[macOS window](macos-window.md).

## 3. Make a final recording

Add `full = true` inside the existing `[check]` table in `demo/reshoot.toml`:

```toml
[check]
sources = ["takes/demo-final.mp4", "takes/demo-final-readme.gif"]
review = "review"
scan = true
full = true
```

This checks every decoded frame of both final exports, reusing exact duplicates.
The default preview checked samples every three seconds; those samples could
miss brief content. Full checks take longer and still need a person's review.

```bash
reshoot run demo/reshoot.toml
```

Save this new run folder separately:

```bash
BASELINE=demo/takes/runs/PASTE_FINAL_ID_HERE
```

The final folder contains these files, plus source evidence and other sidecars:

```text
run.json
review.html
review/
  report.json
  key.json
  flags.json
  01.jpg, 02.jpg, ...
  originals/
takes/
  demo.mp4                 Original browser take
  demo.take.json           Beat results and captured environment
  demo-final.mp4           Finished 1280×720 video
  demo-final.srt           Subtitles
  demo-final-readme.gif    800×450 loop
```

Open the new `review.html` and watch both finished exports. Check the note,
search result, caption timing and loop. The bundled edit stops at the start of
the `end` beat; that beat's extra half-second hold is not in the finished cut.

## 4. Accept the recording

Accepting says two things: the recording shows the task clearly, and nothing
in its frames or captions should stay private. A clean automatic scan decides
neither.

In `$BASELINE/review.html`, watch both final exports to the end. Then look at
the scan items below them. Each numbered `.jpg` in `$BASELINE/review/` holds up
to four labeled images, such as `1-1` and `1-2`; the page links each label to
its full-size original. Flagged items come first, boxed in red. Look for
unintended names, accounts, tokens, paths or people. In this tutorial all app
data is made up.

When everything is acceptable, run:

```bash
reshoot accept "$BASELINE"
```

It lists the exports, beats and scan items it covers and asks you to confirm.
It then records the verdict for all of them, bound to the run's exact files and
scan policy. `run.json` reports `review_status` as `completed`. A later change
to a file or the scan policy invalidates the verdict.

If the scan flagged something, `accept` stops and lists it. Inspect each flagged
item at full size, then name the ones you accept:

```bash
reshoot accept "$BASELINE" --flagged 1-2
```

If an item must not be shared, reject it instead:

```bash
reshoot accept "$BASELINE" --reject 1-2
```

That marks the run failed. Fix the demo data or story and make a new recording;
a rejected take still contains the problem.

To give separate verdicts per beat, use the **Your decisions** controls at the
end of the review page, click **Download decisions**, and import the file with
`reshoot review "$BASELINE" --import-decisions FILE`. Most reviews do not need this.

![The local review page's Your decisions controls, with all notes beats and video still pending](../docs/guide/review-decisions.png)

## 5. Change a caption

In `demo/storyboard.toml`, change the intro caption:

```toml
caption = "Find the note you need"
```

Leave the beat ID `intro` and the result checks intact, then record a preview:

```bash
reshoot preview demo/reshoot.toml
```

Open this new preview as in step 2. It should show the new words while performing
the same task. The earlier final in `$BASELINE` remains unchanged.

## 6. Change the app and repair the story

Run this once to change both the search input's HTML ID and its JavaScript
lookup. It edits only the tutorial's made-up app:

```bash
python3 - <<'PY'
from pathlib import Path
app = Path("demo/index.html")
text = app.read_text()
assert 'id="q"' in text and 'querySelector("#q")' in text, "App already changed?"
text = text.replace('id="q"', 'id="note-search"')
text = text.replace('querySelector("#q")', 'querySelector("#note-search")')
app.write_text(text)
PY
reshoot preview demo/reshoot.toml
```

The preview should fail on `#q`: the app now calls that input `note-search`.
This is an expected failure. Keep its run folder; earlier passed assertions do
not prove the interrupted search worked. The final edit may not exist for that
failed run. Its `takes/demo.take.json` and failure image help diagnose it.

In `demo/storyboard.toml`, change only the search target:

```toml
target = {css = "#note-search"}
```

Keep the search beat ID, note text, search word and expected count and text.
Then record a repaired preview and a fresh final:

```bash
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
```

Both should complete with all three expectations passing. Save the final
folder printed by the second command:

```bash
UPDATED=demo/takes/runs/PASTE_UPDATED_FINAL_ID_HERE
reshoot compare "$BASELINE" "$UPDATED" --out demo/comparison.json
reshoot review "$UPDATED" --previous "$BASELINE"
```

Open `$UPDATED/review.html`. The old and new videos and GIFs appear together,
with matching beat evidence below. Four matched IDs mean the same beats were
found; they do not mean identical pixels. The intro caption and search target
definitions changed; the expected task and result remain the same.

## 7. Review and export the update

Repeat step 4 for `$UPDATED`, including its fresh scan sheets, and accept it
with `reshoot accept "$UPDATED"`. The earlier verdict covers `$BASELINE` only.

After accepting the update, copy its chosen files to a new local directory:

```bash
reshoot export "$UPDATED" --directory demo/exports-v2 \
  --file takes/demo-final.mp4 \
  --file takes/demo-final-readme.gif \
  --file takes/demo-final.srt
```

The output directory contains `demo-final.mp4`, `demo-final-readme.gif` and
`demo-final.srt`. Export verifies source hashes and refuses to overwrite files.
It copies locally; it does not publish or select a new baseline automatically.
Retain both run folders and explicitly choose which final to use next time.

If using Git, keep the brief, app fixtures, TOML files and their dependencies
under version control, with `demo/accepted/`. Accepting a run writes that small
record of it, so a fresh checkout or [CI](ci.md) can compare later runs with it.
Ignore `demo/takes/`, local export directories and downloaded review files
unless deliberately including them in the repository.

For another app, continue with [Record your own app](your-app.md). For settings
and less common actions, see the [project reference](projects.md) and
[command map](commands.md). The [manual workflow](manual.md) covers Python
storyboards, VHS terminal takes and native app windows.
