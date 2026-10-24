# Change a demo and see the result

Use one small edit to learn how the recording source affects the output. Start
with the project from your first browser demo, or run the bundled notes example:

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
Use a hold for reading time; use an expectation for the app's readiness.
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
See [export profiles](projects.md#edit-and-export) for crops, frame rates and
size limits. Fitting a wide page into portrait dimensions does not make a
readable mobile demo.

## Keep the changes that help

Inspect each change before adding the next. Keep the task and its assertions
stable when adjusting presentation. If you alter actions, update the expected
result deliberately and explain the new story in the brief.

After choosing the result, run a fresh `reshoot run demo/reshoot.toml` and
review the actual final MP4, GIF and scan sheets. A preview is a candidate, not
an approval. The [CLI tutorial](step-by-step.md) continues with an app change,
a failed selector, repair and comparison.

Next: [build a fuller demo or tutorial](make-demo.md), or
[maintain and publish this clip](publish.md).
