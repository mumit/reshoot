# The reshoot guide

Make a demo of one task in your app, keep its story beside the code, and record
it again when the app changes.

## Start here

| You are | Start with |
|---|---|
| Showing a task yourself | `reshoot create URL --directory demo`, or `reshoot create` to try notes; [your app](your-app.md#show-the-task) covers the toolbar |
| Asking Codex or Claude Code to make a demo | [Make a demo with your agent](agent-quickstart.md): one prompt, then reply "accept" |
| Using the CLI yourself | [The tutorial](step-by-step.md): record the bundled notes app, break it, repair it, compare |
| Adopting reshoot for a team | [Reshoot on a team](team.md): ownership, CI, alerts and cost |
| Reviewing a demo refresh pull request | [Review a refresh pull request](team.md#review-a-refresh-pull-request) |

Then record your own app: [a web app, from source or a URL](your-app.md), or
[a macOS window](macos-window.md).

## What you can add

Start with one task and a visible result, then add one thing at a time and
watch whether it helps. [How the videos look](look.md) shows each in pictures.

| Goal | Use | Read |
|---|---|---|
| See and shape it by pointing | The studio: beats on a timeline, captions, cards, the frame, music and exports | [Shape it in the studio](customize.md#shape-it-in-the-studio) |
| Explain a task without sound | Short captions and readable holds on the result | [Change and grow a demo](customize.md) |
| Draw the eye to a control | The cursor, auto-zoom and caption placement | [How the videos look](look.md) |
| Explain a longer process | Sections, title cards, a voiceover and subtitles | [Grow it into a fuller demo](customize.md#grow-it-into-a-fuller-demo) |
| A README loop or a social clip | GIF and MP4 exports, crops and size limits | [edit.toml](projects.md#edittoml) |
| Show a CLI beside the UI | A VHS terminal take, joined with the browser take | [Manual workflow](manual.md) |
| Show an installed Mac app | One window, by its ID | [Record a macOS window](macos-window.md) |
| Keep it current | The accepted run, a new run, a comparison | [Keep a demo current](publish.md) |
| Refresh it on every change | A GitHub workflow that opens a pull request | [CI](ci.md) |

## Look something up

| For | Read |
|---|---|
| Installing, upgrading or pinning a version | [Install](install.md) |
| Every field of reshoot.toml, storyboard.toml and edit.toml | [Project reference](projects.md) |
| Every command | [Commands](commands.md), or `reshoot COMMAND --help` |
| An error message, or a review that still says pending | [Troubleshooting](troubleshooting.md) |
| A run that takes too long | [Faster shoots](speed.md) |
| Python storyboards, VHS tapes and Python edits | [Manual workflow](manual.md) |
| What went wrong before, and how reshoot fixed it | [Pitfalls](pitfalls.md) |
| The skills | [Skill catalog](../skills/README.md) |

## Words

| Word | Means |
|---|---|
| Project | A `demo/` folder: the brief, `reshoot.toml`, the storyboard and the edit |
| Storyboard | The script: `storyboard.toml`, a list of beats |
| Beat | One step, like a shot: actions, a caption, result checks and a hold |
| Result check | A `[[beat.expect]]` that the result appeared, such as a saved note in the list |
| Take | One recording of a browser page, a terminal or an app window |
| Run | One `reshoot run` or `reshoot preview`: its takes, edit, scan and report, in `takes/runs/ID/` |
| Preview | A run at a smaller size, to look at before recording a final |
| Final | A full-size run, the one you accept |
| Re-cut | Edit and scan a run's takes again, with the captions and edit as they are now, without recording: `reshoot recut` |
| Studio | A page on your computer for shaping a demo: `reshoot studio` |
| Export | A finished MP4 or GIF |
| Scan | The check of every export for private details, shown as numbered sheets |
| Finding | One thing the scan flagged, such as an email address, in every frame it is in |
| Accept | Say a final is right to share: `reshoot accept` |
| Accepted run | The run you last accepted, recorded in `demo/accepted/`. New runs are compared with it |

## When reshoot fits

Use reshoot for software demos that need updating: README loops, release
walkthroughs and feature clips. Writing the first story and its demo data takes
longer than recording once by hand; every later recording is one command. For
a one-off video, a screen recorder is quicker. Native Mac apps need their own
way to drive the window: reshoot records it but cannot click arbitrary desktop
controls.

## Platforms

| Part | macOS | Linux | Windows |
|---|---|---|---|
| Browser stories and exports | CI, local and separate-Mac maintainer trials | CI and Debian 12 ARM64 Podman maintainer trials | Not validated |
| VHS terminal takes | Local promotional and notes workflows | Notes CI and full Podman promo build | Not validated |
| Native app window capture | One window by ID; local AppKit trial | Not supported | Not supported |
| Text scanning | Vision by default; Tesseract selectable | Tesseract | Not validated |
| Face and person detection | Vision; generated positive controls tested | Unavailable | Not validated |

The [Linux record](../docs/validation/2026-10-21-podman-linux.md),
[separate-Mac record](../docs/validation/2026-10-21-separate-mac.md) and
[Codex/Claude refresh and review record](../docs/validation/2026-10-22-separate-mac-harnesses.md)
describe the tested environments. These were run by the maintainer; testing by
new users is still to come. They show how reshoot behaves there, not that it
works with every app.
