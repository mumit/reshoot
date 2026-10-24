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

## Change a destination

In `demo/edit.toml`, change the existing README export's dimensions:

```toml
[[export]]
name = "readme"
format = "gif"
width = 640
height = 360
```

Replace that existing export table; do not append a second export with the same
name. Record another preview. Compare the GIF at its actual size: smaller text
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
name = "readme"
format = "gif"
width = 800
height = 450
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
