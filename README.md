# reshoot

**Demos that stay current.**

Script a task in your app once. reshoot records it as a captioned MP4 and a
README GIF, checks that the result appeared, and keeps the script beside your
code. When the UI changes, run it again.

![The same notes task recorded before and after a UI update, from one reshoot storyboard](docs/demo/reshoot.gif)

Before and after a UI change, from one storyboard.
[Watch the 21-second social cut](docs/demo/reshoot.mp4).

Each run confirms the result appeared, stops on the step whose control no
longer matches, and scans the frames for email addresses, keys and faces.
[Skills](skills/README.md) for Claude Code and Codex write the story from your
app, and a GitHub workflow records it again when the app changes.

## Make a demo of your app

Open **Claude Code or Codex** in your app's repository, or in an empty folder
if you only have a running app, and paste:

```text
Make a short demo with reshoot.
Read https://github.com/mumit/reshoot/blob/main/guide/agent-quickstart.md
and follow its setup and creation workflow.

Target: the app in this repository.
Choose one useful task with a clear visible result. Use synthetic demo data.
Produce a short captioned MP4 and a README GIF. Keep the recording source in
demo/ so it can be updated later.

Inspect a preview, then record a fresh final and open both exports for review.
Ask only for permissions or missing details needed to proceed.
```

Change `Target:` to a URL, or a macOS app and its window, if there's no source.
In [trials on new apps](docs/validation/2026-10-23-cold-first-demo.md) this took
2 to 5 minutes in Claude Code and 4 to 9 in Codex. Reply "accept" or ask for
changes. reshoot needs no API key: see
[what your agent needs](guide/agent-quickstart.md#what-your-agent-needs).

## Or try it on a made-up app

```bash
uv tool install 'reshoot[browser]'
reshoot create        # make the notes demo and open it in the studio
```

It needs [uv](https://docs.astral.sh/uv/), ffmpeg and Chrome or Chromium on
macOS or Linux; see [installation](guide/install.md). It records a preview in
about 25 seconds and opens it in [the studio](guide/studio.md), a local page
where you change captions, timing, the look and the cut by pointing.
[The tutorial](guide/step-by-step.md) walks through it.

To show a task in your own simple web app, start it with demo data and run
`reshoot create http://127.0.0.1:3000/ --directory demo`. See
[show the task](guide/your-app.md#show-the-task).

## The story is a file

```toml
[[beat]]
id = "search"
caption = "Find the matching note"
hold = 2.0
[[beat.action]]
type = "type"
target = {css = "#q"}
text = "bike"
[[beat.expect]]
type = "text"
target = {css = "#list li"}
contains = "Pick up the bikes"
```

reshoot types into the real page with a visible cursor, shows the caption, and
holds on the result. When the app renames `#q`, the run stops on that step, and
the studio offers the new control.

## Keep it current

Accept a final once; that writes `demo/accepted/` to commit. After the app
changes:

```bash
reshoot run demo/reshoot.toml
reshoot compare demo/accepted demo/latest --out demo/comparison.json
reshoot accept demo/latest
reshoot export demo/accepted --directory docs/demo --replace
```

Or let [the GitHub workflow](guide/ci.md) record the demo when `main` changes
and open a pull request with the new video, GIF and comparison.

## How it differs

Unlike Screen Studio or Loom, you never record the same flow by hand again.
Unlike Playwright video, it adds a cursor, typing, captions, zoom, cuts, a GIF,
result checks and a privacy scan. Unlike Arcade or Supademo, it makes ordinary
MP4 and GIF files locally that CI can refresh. It is
[VHS](https://github.com/charmbracelet/vhs) for web apps and macOS windows, and
uses VHS for terminals.

## What it records

A web app in headless Chrome (the page only, never your desktop), a terminal
with VHS, or one macOS window, with optional voiceover, music and subtitles.
See [platforms](guide/README.md#platforms).

## Where next

[The guide](guide/README.md) covers [your own web app](guide/your-app.md),
[a macOS window](guide/macos-window.md), [how the videos look](guide/look.md),
[teams](guide/publish.md#on-a-team), [CI](guide/ci.md), the
[project reference](guide/projects.md), [commands](guide/commands.md) and
[troubleshooting](guide/troubleshooting.md). The
[before-and-after recipe](examples/promo/README.md) rebuilds the video above.

## Why reshoot exists

I made the launch video for [photosearch](https://github.com/mumit/photosearch)
this way and pulled the tools into reshoot. The
[original notes recording](docs/demo/notes.mp4) and its
[source files](examples/notes/) are still here.

[Contributing](CONTRIBUTING.md) · [Roadmap](ROADMAP.md) · MIT [license](LICENSE)
