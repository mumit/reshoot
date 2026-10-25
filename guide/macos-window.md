# Record a macOS app window

Use this route for an installed native app, with or without source code.
Record one window by its ID, export an MP4 and GIF, and keep the capture and
edit instructions for the next take. Use only made-up documents or demo data.

For the agent route, use the [quickstart](agent-quickstart.md) and set `Target:`
to the app name and the demo window. The agent can prepare capture and editing.
Driving the app requires app-specific automation or your interaction during
capture; browser storyboards do not operate native controls.

## Prepare one window

Install the [CLI and ffmpeg](install.md). On macOS, grant Screen Recording
permission to the terminal, editor or agent host that runs the capture. Restart
that host after changing the permission. See the [permission setup](manual.md#once).

Open a synthetic demo document and keep its window on screen, not minimized.
Choose a task that fits a short take. Arrange only that window and inspect its
title bar and sidebars for unintended content. List the available windows:

```bash
reshoot window --list
```

Match the app and window title to its ID. Look up the ID again after restarting
the app. Never use whole-screen capture.

## Capture the task

Choose an unused take directory. The commands below use `native-01`; change it
for each attempt. Replace `WINDOW_ID` with the selected numeric ID and `TextEdit`
with the exact app name from the list:

Quote an app name containing spaces, such as `"QuickTime Player"`.

```bash
mkdir -p takes
mkdir takes/native-01
reshoot window TextEdit takes/native-01/app.mov --id WINDOW_ID -s 8
```

Perform the demo interaction during those eight seconds, or coordinate a script
that drives the app while capture runs. For a first manual take, keep the task
small and leave time for the result. If an agent cannot drive the app, have it
prepare the command and explain when you should act. App automation may require
separate Accessibility or Automation permissions.

The capture command records the window; it does not generate typing, cursor
effects, captions or result checks. Record another take in a new
directory when timing or framing needs adjustment.

## Export an MP4 and GIF

Save this as `takes/native-01/edit.toml`:

```toml
schema_version = 1
output = "window-final.mp4"

[[part]]
take = 0

[[export]]
name = "readme"
format = "gif"
width = 800
height = 450
```

Run the edit from your work folder:

```bash
reshoot edit takes/native-01/edit.toml takes/native-01/app.mov
```

The outputs are `takes/native-01/window-final.mp4` and
`takes/native-01/window-final-readme.gif`. This edit keeps the entire take and
fits the GIF into 800 × 450. Use numeric `start` and `end` values in `[[part]]`
to trim it. Keep the result readable at its exported size. Use
[Python edit helpers](manual.md#cut) for caption overlays and window
cards; native captures do not contain browser beat or caption metadata.

## Review and keep the recipe

Watch the MP4 and the animated GIF. Check the result, title bar, sidebars,
readability and loop. Generate full-frame scan sheets in a new review directory:

```bash
reshoot check takes/native-01/app.mov takes/native-01/window-final.mp4 takes/native-01/window-final-readme.gif --full --review takes/native-01/review
```

Exit 1 means supplied items need human review; exit 2 means an error. Inspect
the sheets and original frames before recording a scan verdict. Follow the
[review checklist](step-by-step.md#5-review-and-accept), using
the actual media and standalone check directory. Record the verdict with
`reshoot check --review takes/native-01/review --fail LABEL` for a failed item,
then `--ok` once the rest pass. This route does not generate a versioned
run's `review.html`, and `reshoot accept` needs a versioned run.

Keep a brief, the edit, reset steps and any automation script in a source folder
such as `demo/`. Keep generated takes outside version control. Compare old and
new native recordings manually; versioned `reshoot.toml` projects and automated
beat comparison support browser and VHS takes, not standalone native capture.
Do not invent a run manifest for a window recording. Copy only accepted exports
to a new sharing folder when ready.

Next: [grow a fuller demo](customize.md#grow-it-into-a-fuller-demo). Native capture needs an interactive
macOS session; the Ubuntu browser CI template does not automate this route.
