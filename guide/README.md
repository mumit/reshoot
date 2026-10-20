# Making demo videos of software

I make demo videos from scripts, not by recording my screen. This guide explains how and why. The
[step-by-step](step-by-step.md) has the commands, [pitfalls](pitfalls.md) lists what goes wrong and how to avoid
it, and [reshoot in CI](ci.md) keeps a video current on its own.

## Purpose

A demo video goes stale as soon as the app changes. If I recorded it by hand, I'd have to do the whole thing again,
get every click right, and hope nothing private showed up on screen.

So each part of the video is a file I can run again:

- a **storyboard** for a web app: what to click and type, what captions to show, how long to hold;
- a **tape** for a terminal: what to type, and how long to wait;
- an **edit script** that cuts the takes into the finished video.

When the app changes, I change a line and shoot it again. That's where the name comes from.

## When to use something else

A script takes longer to write than a quick recording. A screen recorder is the better choice for a one-off video
that won't need to be made again, or for a desktop app with no web or terminal version. Use one that records a
single window, and check every frame before sharing.

## Definitions

| Term | Meaning |
|---|---|
| Take | One recording: a web page, a terminal or one app window. |
| Beat | One step of a take: an action, then a hold. Each beat has a name. |
| Storyboard | The list of beats for a web take, in a Python file. |
| Tape | A [VHS](https://github.com/charmbracelet/vhs) script for a terminal take. |
| Cut | The finished video, made from takes by the edit script. |
| Demo data | Data made for the video, with nothing private or confidential in it. |

## How it works

1. **Plan.** I decide what the video shows (three to six things for a one-minute video), and which take shows each.
2. **Set up demo data.** The app runs on its own database, folder or account, with only things anyone may see.
3. **Record the takes.**
   - **Web:** headless Chrome opens the page and plays the storyboard. A drawn cursor glides and clicks, text is
     typed at a person's pace, and captions fade in. The view can zoom in on each click. Only the page is captured.
   - **Terminal:** VHS plays a tape in its own terminal, starting from a clean shell.
   - **App window:** on macOS, `screencapture` records one window by its id. Never the whole screen.
4. **Check.** Every image a take can show, and frames from each take, go on numbered sheets. I look at each one at
   full size. Anything private fails: a person, a name, an address, a key, a customer, an internal page. I take it
   out of the demo data and record again.
5. **Cut.** A short Python script uses ffmpeg to trim at beat names, add title and end cards, speed up slow parts,
   and write a 16:9 video, a 9:16 one for phones and a GIF per section.
6. **Watch it all.** Then I post it myself.

## What I use

| Tool | For |
|---|---|
| `reshoot web` | Recording a web page from a storyboard, in headless Chrome |
| VHS | Recording a terminal from a tape |
| `reshoot window` | Recording one macOS app window |
| `reshoot check` | Contact sheets of everything a take can show, and a list of what passed |
| `reshoot.cut` and ffmpeg | Cutting the finished video and GIFs |
| Claude Code with the reshoot skills | Writing the storyboard and edit script, and running the steps |

For packaged projects, native input, release comparison, and local review, I use
the [project workflow](projects.md).

## Platforms

I've made videos with reshoot on macOS. The automated browser, check, cut, and
package tests pass on Linux and macOS. The full notes workflow, including VHS,
passes on Linux CI. Recording an app window needs macOS. External project and
live harness trials remain open; see the [delivery status](../docs/validation/2026-10-19-delivery-status.md).

| Part | macOS | Linux | Windows |
|---|---|---|---|
| Web takes | CI fixtures pass | CI fixtures pass | not tried |
| Terminal takes (VHS) | used locally | notes shoot passes in CI | not tried |
| App window takes | yes | no | no |
| Check and cut | CI passes with Tesseract | CI passes with Tesseract | not tried |

## Sound and subtitles

Most social sites start videos muted, so the captions on screen carry the main point. Sound is optional:

- **A voiceover:** a line for some beats, spoken by macOS's `say`, `espeak-ng`, or any text-to-speech command.
  Each beat waits for its line to finish, so the voice never runs into the next part.
- **Music,** looped to the video's length, quieter while the voice speaks, and faded out at the end.
- **Subtitles:** an `.srt` file with the voiceover, or the captions if there's no voice, to upload with the video.

## How long it takes

Setting up good demo data takes the longest. After that, a reshoot of a one-minute video is a few minutes of
recording, a check (often a few rounds, as failed items come out), and about a minute to cut.
