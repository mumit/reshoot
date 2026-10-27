# The reshoot guide

Make a demo of one task in your app, keep its story beside the code, and record
it again when the app changes.

## Start here

Pick one:

- **[Make a demo with your agent](agent-quickstart.md).** Paste one prompt into
  Claude Code or Codex, then reply "accept". This is the quickest way to a demo
  of your own app.
- **[The tutorial](step-by-step.md).** Learn reshoot by hand on a made-up notes
  app: create a demo, change it in the studio, break the app and repair the
  story. The [video workshop](video-workshop.md) follows the same path on video.

## Shape it

- [The studio](studio.md): change the story, timing, look, cut and sound by
  pointing, then review and accept the final.
- [How the videos look](look.md): the cursor, zoom, captions, frames and export
  shapes, in pictures.

## Keep it current

- [Keep a demo current and share it](publish.md): record again after a change,
  compare, accept, copy the files into your repository, and run it on a team.
- [Refresh it in CI](ci.md): a GitHub workflow that records the demo when the
  app changes and opens a pull request.

## Look something up

- [Install](install.md): the tools, upgrading and the skills.
- [Project reference](projects.md): every field of `reshoot.toml`,
  `storyboard.toml` and `edit.toml`, and what a run writes.
- [Commands](commands.md), or `reshoot COMMAND --help`.
- [Troubleshooting](troubleshooting.md): error messages, slow runs and what to
  watch for.
- [Skill catalog](../skills/README.md).

## Other ways to record

- [Record your own web app](your-app.md) by showing the task or writing the
  story yourself.
- [Record a macOS window](macos-window.md) for an installed Mac app.
- [Manual workflow](manual.md): Python stories, VHS terminal recordings and
  Python edits.

## Platforms

reshoot runs on macOS and Linux; Windows is untested. Recording one app window
and detecting faces and people work only on macOS. On Linux, the scan reads
text with Tesseract.

## When reshoot fits

Use reshoot for software demos that need updating: README loops, release
walkthroughs and feature clips. Writing the first story takes longer than
recording once by hand; every later recording is one command. For a one-off
video, a screen recorder is quicker.

## Words

| Word | Means |
|---|---|
| Project | A `demo/` folder: the brief, `reshoot.toml`, the storyboard and the edit |
| Storyboard | The script, `storyboard.toml`: a list of steps |
| Step | One part of the task: actions, a caption, result checks and a hold. Each is a `[[beat]]` in the storyboard |
| Result check | A `[[beat.expect]]` that the result appeared, such as a saved note in the list |
| Run | One `reshoot run` or `reshoot preview`, in its own folder under `takes/runs/` |
| Preview | A smaller, quicker run to look at |
| Final | A full-size run, the one you accept |
| Re-cut | Edit a run again with the captions and edit as they are now, without recording: `reshoot recut` |
| Cut | Which recorded steps the video shows, and in what order |
| Export | A finished MP4 or GIF |
| Scan | The check of every export for private details, shown as numbered sheets |
| Finding | One thing the scan flagged, such as an email address |
| Accept | Say a final is right to share: `reshoot accept`, or **Review this recording** in the studio |
| Accepted run | The run you last accepted, recorded in `demo/accepted/`. New runs are compared with it |
