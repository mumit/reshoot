# Make a demo, then update it

This tutorial makes a demo of the bundled notes app, changes it in the studio,
breaks the app on purpose, and repairs the demo. It shows each step in the
studio, and then the same step from the terminal, so you learn both.

The notes app saves a made-up note, searches for a word, and checks that the
matching note appears. You'll finish with an MP4, a README GIF and an accepted
record of them.

Install [reshoot and its tools](install.md) first. Then work in one terminal,
in a folder where a new `demo/` folder can be made. You don't need a
repository, an AI account or any real data. To have an agent make a demo
instead, use the [agent quickstart](agent-quickstart.md).

## 1. Create the demo

```bash
reshoot create
```

It makes the notes project in `demo/`, checks that the recording tools work,
records a preview, and opens it in [the studio](studio.md). The preview takes
about 15 seconds. If a tool is missing, the studio's **Recording tools** says
what to install; choose **Check again**, then **Continue creation**.

The project holds:

```text
demo/
  BRIEF.md         Who the demo is for and what it shows
  index.html       The made-up notes app
  storyboard.toml  The steps: actions, captions and result checks
  edit.toml        Which parts to keep, and the formats to write
  reshoot.toml     How to start the app, record, edit and scan
  .gitignore       Keeps the recordings in takes/ out of Git
```

**From the terminal:** `reshoot init demo` makes the project,
`reshoot doctor --config demo/reshoot.toml --probe` checks the tools, and
`reshoot preview demo/reshoot.toml` records the preview. reshoot starts its
own notes server for each recording and stops it afterwards. It records only
the browser page, never your desktop.

## 2. Look at the preview

The studio shows the video with its steps on a timeline under it. Click a
step to play it. The note "Pick up the bikes" is saved, then found as the only
result for "bike".

The save and search steps are green because their result checks passed. The
`intro` and `end` steps are grey: they have no result checks, so nothing
confirms what they show.

**From the terminal:** the preview prints the paths of what it made:

```text
Done in 13 s: 3 of 3 result checks passed · scan: 6 items, 0 flagged · not accepted yet.
  video  demo/takes/runs/RUN_ID/takes/demo-final.mp4
  GIF    demo/takes/runs/RUN_ID/takes/demo-final-readme.gif
  review demo/takes/runs/RUN_ID/review.html
```

Open them with `open PATH` on macOS or `xdg-open PATH` on Linux. Each run has
its own folder, and `reshoot runs demo` lists them.

## 3. Change a caption and a hold

In the studio, under **Your story**, change the `intro` caption to "Find the
note you need" and leave the field. Then raise the `search` step's **Hold
result (seconds)** from 2 to 3, so the result stays on screen a second longer.

Each change is saved to `demo/storyboard.toml`. Choose **Update preview**. A
caption alone would only need the recording edited again, in seconds; the
longer hold needs a new recording, so the studio records the task again. Watch
the new preview. If you don't like a change, **Undo** takes it back.

**From the terminal:** edit the files, then make a new preview:

```toml
caption = "Find the note you need"   # the intro beat
hold = 3.0                           # the search beat
```

```bash
reshoot recut demo/latest           # after a caption or edit.toml change: no recording
reshoot preview demo/reshoot.toml   # after a change to actions, checks or holds
```

## 4. Make the final

A preview is smaller and quicker, for looking at. When it looks right, choose
**Make final** to record the full-size run.

The scan samples a frame every three seconds, so it can miss something brief.
To scan every frame of each final, add `full = true` to the `[check]` table
in `demo/reshoot.toml`. It takes longer, and it still needs your review.

**From the terminal:**

```bash
reshoot run demo/reshoot.toml --full
```

The run's folder holds the finished `takes/demo-final.mp4`, its
`demo-final.srt` subtitles and `demo-final-readme.gif`, plus `review.html`
and the scan's evidence in `review/`.

## 5. Review and accept

Accepting says two things: the video shows the task clearly, and nothing in it
should stay private. A clean scan decides neither; you do.

In the studio, open **Review this recording**:

1. Watch the MP4 and the GIF to the end.
2. Open **Inspect scan sheets**. Each sheet holds up to four labelled images,
   such as `1-1` and `1-2`. Look for names, accounts, keys, file paths or
   people that shouldn't be there. Anything the scan flagged comes first.
3. Choose whether each finding may be shared, tick that you watched
   everything, and accept.

This writes `demo/accepted/`, a small record of the run to commit with the
project. Later runs are compared with it. A change to the run's files undoes
the acceptance.

If something must not be shared, reject the run instead. Then fix the demo data
or the story and record again: the rejected video still shows the problem.

**From the terminal:**

```bash
reshoot accept demo/latest              # accept the newest final
reshoot accept demo/latest --flagged F1 # accept a finding the scan flagged
reshoot accept demo/latest --reject F1  # reject the run because of a finding
```

`demo/latest` means the newest successful run. `accept` refuses a preview, and
lists each finding once, such as `F1  email sam.•••: 318 frames, 1-1 to 80-2`.
`reshoot review demo/latest --serve` opens the review page with the same
choices.

To give a verdict on each step separately, use **Your decisions** at the end
of the review page, choose **Download decisions**, and import the file with
`reshoot review RUN_FOLDER --import-decisions FILE`. Most reviews don't need
this.

![The review page's Your decisions controls, with each notes step and the video still pending](../docs/guide/review-decisions.png)

## 6. Change the app and repair the demo

This renames the app's search box from `q` to `note-search`, as a real app
change might. It edits only the made-up notes app:

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
```

In the studio, choose **Update preview**. The recording stops on the search
step, because the storyboard still looks for `#q`. This is the failure you
want: the demo stops where the app changed, instead of recording the wrong
thing. The studio keeps your last good video and says what happened:

```text
Step 'search' stopped: it couldn't find the control matching #q. It's probably
"Search notes" now: that one is where it was.
```

Choose **Use "Search notes"**. The studio checks the box on the current app,
then changes only how the step finds it. The search word and the expected
result stay the same. Choose **Update preview**, and all three result checks
pass again. If the suggestion is wrong, choose **Choose replacement in app**
instead: a browser opens at the search step, and clicking the box there
doesn't type into it.

**From the terminal:** the failed preview prints the suggestion and the
commands:

```bash
reshoot repair demo/takes/runs/RUN_ID --apply  # use the suggested control
reshoot repair demo/takes/runs/RUN_ID --pick   # or choose the box in a browser
```

Or change the step yourself in `demo/storyboard.toml`, leaving the rest of it
as it was:

```toml
target = {css = "#note-search"}
```

Then record a preview with `reshoot preview demo/reshoot.toml`.

## 7. Compare, accept and copy the update

Choose **Make final**. Open **More tools**, then **Compare**. **Play both**
shows the accepted export beside the new one; the checked frames below show
the task's results. The caption and the search step changed; the task and its
result didn't. [Comparison controls](studio.md#compare-with-an-earlier-recording)
let you inspect a step or choose another export.

Review and accept the new final as in step 5. The earlier acceptance covers
only the earlier run; `demo/accepted` now records the update. Choose
**Download all exports** for a ZIP of the video, GIF and subtitles.

**From the terminal:**

```bash
reshoot run demo/reshoot.toml --full
reshoot compare demo/accepted demo/latest --out demo/comparison.json
reshoot review demo/latest --previous demo/accepted
reshoot accept demo/latest --export docs/demo
```

`compare` lists which steps matched and which changed:

```text
Compared run NEW_ID with ACCEPTED_ID. Beats: 4 matched.
  notes/intro: matched, changed steps
  notes/search: matched, changed steps
Result checks passed before, passed now. Wrote demo/comparison.json.
```

Four matched beats means the same steps were found, not the same pixels.
`export` copies the MP4, GIF and subtitles, checks them against the run, and
prints the Markdown that shows the GIF in a README. It never overwrites a file
unless you add `--replace`, and it doesn't publish anything.

## Keep it in Git

Commit the brief, the app's demo data, the TOML files and `demo/accepted/`.
`demo/.gitignore` keeps the recordings in `demo/takes/` out. With the accepted
record committed, [CI](ci.md) can record the demo again and compare it.

## Next

- Follow the [video workshop companion](video-workshop.md) for URL-based
  demonstration, Studio editing and updating a changed app. Its linked recipe
  builds the narrated video locally.
- Record your own app: [a web app](your-app.md), or [a macOS window](macos-window.md).
- Every studio panel: [the studio](studio.md).
- Change a demo by its files: [change and grow a demo](customize.md).
- Every field and command: [the project reference](projects.md) and
  [commands](commands.md).
