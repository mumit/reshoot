# Make a demo, then update it

Make a demo of the bundled notes app, change it in the studio, break the app
and repair the demo. Each step shows the studio, then the same thing from the
terminal. You need [reshoot and its tools](install.md) and an empty folder; no
repository, AI account or real data.

## 1. Create the demo

```bash
reshoot create
```

It makes the notes project in `demo/`, records a preview in about 25 seconds,
and opens it in [the studio](studio.md). If a tool is missing, **Recording
tools** says what to install.

```text
demo/
  BRIEF.md         Who the demo is for and what it shows
  index.html       The made-up notes app
  storyboard.toml  The steps: actions, captions and result checks
  edit.toml        Which parts to keep, and the formats to write
  reshoot.toml     How to start the app, record, edit and scan
  .gitignore       Keeps the recordings in takes/ out of Git
```

**From the terminal:** `reshoot init demo`, then
`reshoot doctor --config demo/reshoot.toml --probe` and
`reshoot preview demo/reshoot.toml`.

## 2. Look at the preview

Click a step on the timeline to play it. The note "Pick up the bikes" is
saved, then found as the only result for "bike". Green steps passed their
result checks; grey ones, `intro` and `end`, have none.

**From the terminal:** the preview prints its paths:

```text
Done in 13 s: 3 of 3 result checks passed · scan: 6 items, 0 flagged · not accepted yet.
  video  demo/takes/runs/RUN_ID/takes/demo-final.mp4
  GIF    demo/takes/runs/RUN_ID/takes/demo-final-readme.gif
  review demo/takes/runs/RUN_ID/review.html
```

Open them with `open PATH` on macOS or `xdg-open PATH` on Linux.
`reshoot runs demo` lists the runs.

## 3. Change a caption and a hold

Under **Your story**, change the `intro` caption to "Find the note you need"
and leave the field. Raise the `search` step's **Hold result (seconds)** from
2 to 3. Choose **Update preview**; the hold makes it record again
([which changes need which](studio.md#update-the-preview-then-make-the-final)).
**Undo** takes a change back.

**From the terminal:** edit `demo/storyboard.toml`:

```toml
caption = "Find the note you need"   # the intro beat
hold = 3.0                           # the search beat
```

```bash
reshoot recut demo/latest           # after a caption or edit.toml change: no recording
reshoot preview demo/reshoot.toml   # after a change to actions, checks or holds
```

## 4. Make the final

Choose **Make final** for the full-size run. The scan samples a frame every
three seconds; to scan every frame, add `full = true` under `[check]` in
`demo/reshoot.toml`.

**From the terminal:** `reshoot run demo/reshoot.toml --full`. The run's
folder holds `takes/demo-final.mp4`, `demo-final.srt`,
`demo-final-readme.gif`, `review.html` and the scan's evidence in `review/`.

## 5. Review and accept

Open **Review this recording** and follow
[its three steps](studio.md#review-and-accept). Accepting writes
[`demo/accepted/`](publish.md#the-accepted-run), a small record to commit.

**From the terminal:**

```bash
reshoot accept demo/latest              # accept the newest final
reshoot accept demo/latest --flagged F1 # accept a finding the scan flagged
reshoot accept demo/latest --reject F1  # reject the run because of a finding
```

`accept` refuses a preview and lists each finding, such as
`F1  email sam.•••: 318 frames, 1-1 to 80-2`. `reshoot review demo/latest
--serve` opens the review page.

To judge each step separately, use **Your decisions** at the end of the review
page, choose **Download decisions**, and run
`reshoot review RUN_FOLDER --import-decisions FILE`.

![The review page's Your decisions controls, with each notes step and the video still pending](../docs/guide/review-decisions.png)

## 6. Change the app and repair the demo

Choose **Change the notes app and record again**, or rename the search box
yourself:

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

Choose **Update preview**. The recording stops on the search step, keeps your
last good video, and says:

```text
Step 'search' stopped: it couldn't find the control matching #q. It's probably
"Search notes" now: that one is where it was.
```

Choose **Use "Search notes"**, then **Update preview**; all three result checks
pass. If the suggestion is wrong, choose **Choose replacement in app** and
click the box in the browser that opens.

**From the terminal:**

```bash
reshoot repair demo/takes/runs/RUN_ID --apply  # use the suggested control
reshoot repair demo/takes/runs/RUN_ID --pick   # or choose the box in a browser
```

Or set `target = {css = "#note-search"}` in the step and run
`reshoot preview demo/reshoot.toml`.

## 7. Compare, accept and copy the update

Choose **Make final**. Open **More tools**, then **Compare**, and choose
**Play both** to see the accepted export beside the new one
([comparison controls](studio.md#compare-with-an-earlier-recording)). Review
and accept the new final as in step 5. **Download all exports** gives a ZIP.

**From the terminal:**

```bash
reshoot run demo/reshoot.toml --full
reshoot compare demo/accepted demo/latest --out demo/comparison.json
reshoot review demo/latest --previous demo/accepted
reshoot accept demo/latest
reshoot export demo/accepted --directory docs/demo
```

```text
Compared run NEW_ID with ACCEPTED_ID. Steps: 4 kept.
  Intro: kept, changed its story
  Search: kept, changed its story
Result checks passed before, passed now. Wrote demo/comparison.json.
```

Kept means the step is still in the story, not that it looks the same. `export` copies
the MP4, GIF and subtitles, prints the README Markdown, and overwrites only
with `--replace`.

## Keep it in Git

Commit [these files](publish.md#the-accepted-run), including `demo/accepted/`,
so [CI](ci.md) can record and compare the demo.

## Next

- [The video workshop](video-workshop.md)
- Your own app: [a web app](your-app.md) or [a macOS window](macos-window.md)
- [A fuller demo](studio.md#grow-it-into-a-fuller-demo)
