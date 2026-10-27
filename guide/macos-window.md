# Record a macOS app window

Record one window of an installed app by its ID, export an MP4 and GIF, and
keep the recipe for next time. Use only demo documents. An agent can prepare
this from the [quickstart](agent-quickstart.md), but driving the app needs app
automation or you.

## Prepare one window

Install the [CLI and ffmpeg](install.md), and give the app that runs the
capture [Screen Recording permission](manual.md#once). Open a demo document,
keep its window on screen, and check its title bar and sidebars. Then find its
ID, again after each app restart:

```bash
reshoot window --list
```

## Capture the task

Use a new folder for each take. Quote app names with spaces, such as
`"QuickTime Player"`:

```bash
mkdir -p takes/native-01
reshoot window TextEdit takes/native-01/app.mov --id WINDOW_ID -s 8
```

Do the task during the eight seconds, or run a script that drives the app,
which may need Accessibility permission. The capture adds no cursor, captions
or result checks.

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

```bash
reshoot edit takes/native-01/edit.toml takes/native-01/app.mov
```

This writes `window-final.mp4` and `window-final-readme.gif`. Trim with
numeric `start` and `end` in `[[part]]`; add captions with the
[Python edit helpers](manual.md#cut).

## Review and keep the recipe

Watch the MP4 and GIF, then make full scan sheets:

```bash
reshoot check takes/native-01/app.mov takes/native-01/window-final.mp4 takes/native-01/window-final-readme.gif --full --review takes/native-01/review
```

Look at every sheet, as in the [review checklist](studio.md#review-and-accept),
then run `reshoot check --review takes/native-01/review --fail LABEL` for a
failed item, or `--ok` once the rest pass. `reshoot accept` doesn't apply here.

Keep the brief, edit, reset steps and any script in `demo/`, and the takes out
of Git. Compare new recordings with old ones yourself. CI can't record windows.
