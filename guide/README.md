# The reshoot guide

## Start here

- **[Make a demo with your agent](agent-quickstart.md):** paste one prompt into
  Claude Code or Codex.
- **[The tutorial](step-by-step.md):** make, break and repair a demo of a
  made-up notes app, or follow the [video workshop](video-workshop.md).

## Shape it

- [The studio](studio.md)
- [How the videos look](look.md)

## Keep it current

- [Keep a demo current and share it](publish.md)
- [Refresh it in CI](ci.md)

## Look something up

- [Install](install.md)
- [Project reference](projects.md): every file field and what a run writes
- [Commands](commands.md), or `reshoot COMMAND --help`
- [Troubleshooting](troubleshooting.md)
- [Skill catalog](../skills/README.md)

## Other ways to record

- [Your own web app](your-app.md)
- [A macOS window](macos-window.md)
- [Manual workflow](manual.md): Python stories, VHS terminals and Python edits

## Platforms

macOS and Linux; Windows is untested. Recording one app window and detecting
faces and people need macOS. On Linux, the scan reads text with Tesseract.

## Words

- **Project:** a `demo/` folder of the brief and TOML files
- **Storyboard:** `storyboard.toml`: a list of steps
- **Step:** actions, a caption, result checks and a hold: a `[[beat]]`
- **Result check:** a `[[beat.expect]]` that the result appeared
- **Run:** one recording, in its own folder under `takes/runs/`
- **Preview:** a smaller, quicker run to look at
- **Final:** a full-size run, the one you accept
- **Re-cut:** edit a run again without recording: `reshoot recut`
- **Cut:** which recorded steps the video shows, and in what order
- **Export:** a finished MP4 or GIF
- **Scan:** the check of every export for private details
- **Finding:** one thing the scan flagged, such as an email address
- **Accept:** say a final is right to share
- **Accepted run:** the run in `demo/accepted/`, which new runs are compared with
