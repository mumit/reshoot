# Change and grow a demo

Make one small change at a time and record a preview to see it: a caption, a
hold, the cursor, an export size. Then, once the short clip works, grow it into
a fuller product demo or tutorial. [How the videos look](look.md) shows each
setting in pictures. Start with the project from your first browser demo, or
the bundled notes example:

```bash
reshoot init demo
reshoot preview demo/reshoot.toml
```

Keep the printed run folder as your original. Open its
`takes/demo-final.mp4` and `takes/demo-final-readme.gif`. Each preview below
creates another run, so the original stays available for comparison.

For the agent route, ask:

```text
Use the existing demo/ project. Show me where its captions, result holds and
export settings live. Change one caption and hold the result one second longer.
Keep the task and result checks. Record a preview and show both versions.
```

## Shape it in the studio

To see the whole demo and change it by pointing, open the studio:

```bash
reshoot studio demo
```

It opens a page on this computer with the latest run's video and its beats on
a timeline under it, green where the result checks passed. Each beat shows its
last frame, its result checks, and its caption and second line, ready to edit.
Click a beat to play just that part.

- **Change a caption** and leave the field: it is saved to
  `demo/storyboard.toml`, and the beat says it is not in the video yet.
- **Change the caption look**, its place and colours, the same way.
- **Change the edit**: add, reword, time or remove an opening or closing title
  card, turn the browser frame on and set its background, choose a music file
  from the project folder, and change, add or remove exports by preset. These
  are saved to `demo/edit.toml`, and `[check] sources` in `reshoot.toml` follows
  the exports, so each one is still scanned.
- **Re-cut** draws the captions again on the same recording, edits and scans it,
  in seconds, and loads the new run.
- **Record from here**, on a beat, starts the app, replays the beats before it
  off camera and records from that beat on, then shows that take. A beat whose
  actions, checks or hold changed since the recording is marked in red. When
  the take looks right, **Record** records the whole run.
- **Exports** shows each export in its own shape, with its size, length and
  file size, and the limits of the place its preset is for.
- **What the scan found** marks each finding on the timeline, and the accept
  panel accepts the run, as `reshoot accept` does.

The files stay the source of truth: edit them by hand or ask an agent while the
studio is open, and reload the page to see the change. Actions, result checks
and holds are changed in the storyboard itself. The studio serves on
`127.0.0.1` behind a random address, takes changes only from its own page, and
runs until you press Ctrl-C.

## Find the files

| File | Change it to |
|---|---|
| `demo/BRIEF.md` | Describe the audience, task and visible result |
| `demo/storyboard.toml` | Change actions, captions, result checks or holds |
| `demo/edit.toml` | Change cuts, title cards or export dimensions |
| `demo/reshoot.toml` | Change startup, take paths or check coverage |

These are the files generated for browser projects. For native recordings,
edit the [standalone capture recipe](macos-window.md) and its numeric cuts;
there is no browser storyboard to replay.

## Change the words

In the notes project's `storyboard.toml`, change the `intro` beat's caption to:

```toml
caption = "Find the note you need"
```

Save the file and record another preview:

```bash
reshoot preview demo/reshoot.toml
```

Watch the first seconds of the new MP4. The caption changes; adding the note
and finding it still perform the same task. In your own project, choose one
caption that explains the result rather than naming the click.

## Give the result time

In the same file, find the `search` beat. Change its `hold` from `2.0` to `3.0`:

```toml
hold = 3.0
```

Record another preview and compare the matching-note result. The browser waits
for its explicit checks, then holds the successful result for an extra second.
Use a hold for reading time and a result check to wait for the app.
Do not hide a real service delay by speeding it up without a visible label.

## Change the cursor

The cursor glides to each control, presses down with a ring on each click, and
types at an uneven pace. To make it larger in a small GIF, or type faster, add
this to the top of `demo/storyboard.toml`, above the first `[[beat]]`:

```toml
[cursor]
size = 1.5     # times the default arrow
typing = 20    # characters a second; the default is 13
```

`ripple = false` leaves out the ring. Record another preview to see it.

## Change only the edit, quickly

Title cards, music, the frame, the cuts and the exports are all in
`demo/edit.toml`, which works on what was already recorded. After changing only
that file, skip the recording:

```bash
reshoot recut demo/latest
```

It edits and scans the latest run's takes again, into a new run, in seconds.
It also draws the captions again, so a re-cut picks up new caption words and
a new `[caption]` look in `storyboard.toml`. A caption still shows for as long
as its beat did in the recording: to give a longer caption more time, raise
the beat's `hold` and record again.

## Frame it like a browser window

Add this to `demo/edit.toml`, above the first `[[part]]`:

```toml
[style]
background = ["#2a3f5f", "#101826"]   # a gradient, top to bottom; or one colour

[frame]
```

Each take then sits in a window with a title bar, rounded corners and a soft
shadow, on that background. The page shrinks to fit, so check that its text is
still easy to read. [How the videos look](look.md#a-browser-frame) shows it
and its settings.

## Change a destination

In `demo/edit.toml`, make the README GIF smaller. The `readme` preset makes an
800x450 GIF and checks it against GitHub's 10 MB limit; a field you give
overrides the preset's:

```toml
[[export]]
preset = "readme"
width = 640
height = 360
```

Replace that existing export table; do not append a second export with the same
name. To add a clip for X or LinkedIn, add another export with
`preset = "x"` or `preset = "linkedin"`; the
[presets](projects.md#export-presets) check each platform's limits. Record another preview. Compare the GIF at its actual size: smaller text
may need a tighter task or different framing. Keep the MP4 as the fuller version.
See [export profiles](projects.md#edittoml) for crops, frame rates and
size limits. Fitting a wide page into portrait dimensions does not make a
readable mobile demo.

## Keep the changes that help

Look at each change before adding the next. Keep the task and its result checks
the same while adjusting how it looks. If you change the actions, change the
result checks on purpose and explain the new story in the brief.

Once you choose, record a fresh `reshoot run demo/reshoot.toml` and look at the
final MP4, GIF and scan sheets. A preview is for looking at, not for accepting.

## Grow it into a fuller demo

Expand a working clip only when each extra section helps the viewer. Write the
audience, starting state and visible result in `BRIEF.md`, and decide whether
the video shows why a feature matters or how to use it. A product demo leads
with the result and keeps setup short. A tutorial includes the steps a viewer
must repeat and holds menus and result text long enough to read.

| Section | Show | Result check |
|---|---|---|
| Start | A list with several demo notes | The target is hard to spot |
| Create | Add "Prepare the release notes" | The saved note appears |
| Find | Search for "release" | Only the matching note remains |
| Finish | Hold the result and say what to do next | The result stays readable |

Keep each section small enough to record again on its own, with a stable beat
ID. For native apps, save the starting document and the steps, and check the
visible result yourself: there are no automatic result checks there.

To have the agent do it:

```text
Expand the existing demo/ into a short tutorial of creating an item and finding
it by search. Read its brief and current recording first. Use synthetic data.
Keep the working task and result checks; add only the context needed to follow
it. Use clear captions, readable result holds and a short closing instruction.
Inspect previews, record a fresh final, and show the MP4 and README GIF.
```

Add the audience, destination and length when you know them. Ask for narration
only when it explains something; the video should still make sense muted.

### Add a title card

`demo/edit.toml` picks beat ranges from the takes, joins them and adds cards.
This version opens the notes demo with a title:

```toml
schema_version = 1
output = "demo-final.mp4"

[[part]]
card = "Save a note. Find it again."
duration = 1.5

[[part]]
take = 0
start = 0
end = "end"

[[export]]
preset = "readme"
```

Replace the notes project's edit with it and record another preview. For your
own story, use its beat names. Every edit field, music and card styling is in
the [project reference](projects.md#edittoml). The [manual workflow](manual.md)
covers Python edits, narration and VHS terminal takes; match terminal and
browser take sizes when joining them. The [promo recipe](../examples/promo/README.md)
is a before-and-after video built this way.

### Finish for the viewer

Watch the full MP4 and every shorter GIF or crop. Check that captions name the
outcome, text fits, typing is legible and the result stays on screen. Say so
when a response is mocked or a wait was shortened. Check narration against the
picture, and read the subtitles when there are any.

Next: [keep the demo current and share it](publish.md).
