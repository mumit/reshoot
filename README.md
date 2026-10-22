# reshoot

**Give your agent a task. Get a demo you can run again.**

An agent-first toolkit for software demos: open source skills and recording
tools for Codex and Claude Code. Turn a task in your app into a captioned MP4,
a README GIF, and source files that keep the demo repeatable as the app changes.

![The same notes task recorded before and after a UI update, using one reshoot storyboard](docs/demo/reshoot.gif)

The UI changed. The same story still saves and finds the same note.
[Watch the 21-second demo](docs/demo/reshoot.mp4) ·
[Make a demo of your app](guide/agent-quickstart.md) ·
[Explore the skills](skills/README.md) · [Use the CLI](guide/step-by-step.md)

## Make a demo of your app

Open **Codex or Claude Code** in your app's repository, or an empty demo folder
if you only have a running app. Paste this prompt. Change `Target:` to your
web app's URL or the name of a macOS app and its demo window when needed.

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

Add a task if you have one: “Show creating a project and finding it by search.”
Otherwise, let the agent inspect the app and propose a useful task. Source code
is optional. Browser recording runs on macOS or Linux; native window capture
requires macOS and app-specific automation or your interaction during capture.
The agent needs a local session with a shell and access to the target.

The agent handles setup, reads the app's controls, writes the story, records a
preview and prepares the final exports. You watch the result, request changes
and decide whether to share it. Initial setup may need installation permissions
or an isolated demo login.

**You get a video, a GIF, and their source.** Keep the `demo/` recipe beside the
app's code or in its own folder. Browser projects retain each attempt in a
versioned run folder. Native recipes retain standalone takes and edit scripts.

Already installed the skills? Start with `$reshoot-demo` in Codex or
`/reshoot-demo` in Claude Code, followed by the task.

## Three skills, one workflow

A skill gives the coding agent a reusable workflow: how to choose the task,
record it, check the result and present it for review. Reshoot's CLI performs
the recording and editing. The agent uses available source code or the running
app's controls to adapt that workflow to the product.

| When | Skill | What to ask for |
|---|---|---|
| Make the first demo | [reshoot-demo](skills/reshoot-demo/SKILL.md) | “Show a customer saving a search and seeing its results.” |
| The app changed | [reshoot-refresh](skills/reshoot-refresh/SKILL.md) | “Record that task again with the updated UI. Keep the old take for comparison.” |
| Check before sharing | [reshoot-review](skills/reshoot-review/SKILL.md) | “Inspect the final video and GIF, compare the previous run, and report anything that needs attention.” |

For a refresh or review, include the demo's configuration and the exact previous
run, or the native capture recipe and previous media. See the
[copyable follow-up prompts](guide/agent-quickstart.md#update-the-demo-when-the-app-changes).

Browser projects keep actions, captions and expected results in editable files.
Result checks can verify that a saved item appears or that a search returns one
match. When a control moves or a label changes, the agent can repair the story
and record a new candidate. Watch and approve the new exports before sharing.

## Install the skills

Use the first-demo prompt above to let the agent handle setup, or install the
tools and skills yourself. The skills need the reshoot CLI, Python 3.11+, Git,
ffmpeg and, for browser recording, Chrome or Chromium. Linux text scanning also
needs Tesseract. Follow the [platform setup](guide/install.md), then choose one
installation route.

### Codex

Run this in the app repository or demo work folder:

```bash
reshoot skills codex --directory .
```

This installs `reshoot-demo`, `reshoot-refresh` and `reshoot-review` into
`.agents/skills/`. In Codex, invoke a skill and describe the task:

```text
$reshoot-demo
Create a short demo of saving a task and finding it by search.
Produce an MP4 and a README GIF using synthetic data.
```

### Claude Code

Run this in the app repository or demo work folder:

```bash
reshoot skills claude --directory .
```

This installs the same three skills into `.claude/skills/`. In Claude Code:

```text
/reshoot-demo
Create a short demo of saving a task and finding it by search.
Produce an MP4 and a README GIF using synthetic data.
```

### Claude Code plugin

To install all ten skills through Claude Code's plugin system, run these
commands inside Claude Code and follow its installation prompts:

```text
/plugin marketplace add mumit/reshoot
/plugin install reshoot@reshoot
```

Use `/reshoot:reshoot-demo`, `/reshoot:reshoot-refresh` or
`/reshoot:reshoot-review`, followed by the task. The plugin includes seven
supporting skills for planning, individual recordings, editing, privacy checks
and CI. Install the CLI and recording dependencies as well.

The [agent quickstart](guide/agent-quickstart.md#install-the-skills-yourself)
covers skill discovery and the differences between these routes. The CLI
installer preserves existing skill folders; compare updates before replacing
local changes.

## Keep the demo with the code

Reshoot records real interactions with the app. The demo project describes
what to do, what should happen, how long the result should remain visible and
which formats to export.

| Keep in a browser project | Purpose |
|---|---|
| `BRIEF.md` | Audience, task, visible result and destination |
| `storyboard.toml` | Actions, captions and expected results |
| `edit.toml` | Cuts, result holds and output formats |
| `reshoot.toml` | App startup, recording and check settings |

Each versioned browser or terminal candidate retains its report, video, GIF and
review evidence under `takes/runs/ID/`. Keep the recording source in version control and generated
takes outside it. Select an explicit baseline when comparing updates.

Native demos keep their capture instructions and edit script separately; see
the [macOS window workflow](guide/macos-window.md).
Use the [CI workflow](guide/ci.md) to record browser and terminal candidates after
app changes. Review the outputs before updating published demo media.

## Choose the recording for the task

| Show | Tools |
|---|---|
| A web app | Headless Chrome, native browser actions, cursor, typing and captions |
| A CLI or an agent at work | [VHS](https://github.com/charmbracelet/vhs) terminal recordings |
| A native app on macOS | One window captured by its ID; app-specific automation or manual interaction |
| The result in different formats | MP4 and GIF exports, custom edits and intentional portrait crops |
| A narrated explanation | Optional voiceover, music and subtitles |

Use synthetic demo data. Capture a browser page, a terminal or one app window.
Watch the finished exports and inspect the scan sheets. Automatic checks flag
potential problems; you make the final review decisions. Reshoot keeps
publication manual.

Browser workflows are tested on macOS and Linux. Native window capture and
Vision face/person detection require macOS; Linux uses Tesseract for text.
See [platforms and tested limits](guide/README.md#platforms).

## Use the CLI directly

Start with the bundled notes app to try the tools without a coding agent:

```bash
reshoot init demo
reshoot doctor --config demo/reshoot.toml
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
```

The [CLI tutorial](guide/step-by-step.md) covers the complete first recording,
an app change, a deliberate failure, repair, comparison, review and export.
For your own app, `reshoot init demo --url http://localhost:3000/` creates a
project draft. Replace its placeholder story with actions and result checks
using the [own-app walkthrough](guide/your-app.md).

## Grow the demo at your own pace

| Stage | Start here |
|---|---|
| 1. Get a first recording | [One agent prompt](guide/agent-quickstart.md), or the [CLI notes tutorial](guide/step-by-step.md) |
| 2. See what else is possible | [Explore features and examples](guide/features.md) |
| 3. Change something small | [Edit a caption, timing and GIF size](guide/customize.md) |
| 4. Make a fuller demo or tutorial | [Build the story and edit](guide/make-demo.md) |
| 5. Keep it current and share it | [Updates and publishing](guide/publish.md), then [GitHub Actions](guide/ci.md) |

Start from [source code](guide/your-app.md), a [running web URL](guide/running-web-app.md)
or a [macOS app window](guide/macos-window.md). Skip directly to the stage you need.

## Find the right guide

| Task | Start here |
|---|---|
| Get a first demo with an agent | [Agent quickstart](guide/agent-quickstart.md) |
| Browse the skill package | [Skill catalog](skills/README.md) |
| Install or upgrade the tools | [Installation](guide/install.md) |
| Learn the CLI workflow from scratch | [Notes tutorial](guide/step-by-step.md) |
| Write a story for an existing app | [Own-app walkthrough](guide/your-app.md) |
| Look up actions, captions, edits and exports | [Project reference](guide/projects.md) |
| Find a command or fix a failed step | [Command map](guide/commands.md) · [Troubleshooting](guide/troubleshooting.md) |
| Record a terminal or native window | [Manual workflow](guide/manual.md) |
| Reproduce the README demo | [Before-and-after recipe](examples/promo/README.md) |

## Why reshoot exists

I made the launch video for [photosearch](https://github.com/mumit/photosearch)
this way, and pulled the tools and what I learned into reshoot. A demo takes
work to make. Keeping its story beside the app makes that work useful again
when the product changes.

The [original notes recording](docs/demo/notes.mp4) and its
[source files](examples/notes/) remain available.

## Contributing

New pitfalls, skills and fixes are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md)
for contribution instructions and [ROADMAP.md](ROADMAP.md) for planned work.

## License

MIT. See [LICENSE](LICENSE).
