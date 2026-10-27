# Make a demo with your agent

Turn one useful task in your app into a short video and a README GIF. Let
the agent handle the recording source and tool commands. Keep the project so
the next UI change can become the next recording.

## Start with one prompt

Open Codex or Claude Code in a local work folder. Choose the folder and target
from this table; source code is optional:

| What you have | Open | Set `Target:` to |
|---|---|---|
| App source code | The app repository | `the app in this repository` |
| A running web app | An empty demo work folder | The actual app URL, local or hosted |
| An installed macOS app | An empty demo work folder on the Mac | App name and the window containing demo data |

Use a session that can run shell commands and access the app;
[What your agent needs](#what-your-agent-needs) has the full list, and the
route without an agent. Browser recording
works on macOS or Linux. Native capture needs macOS and permission to record
one window. Paste this prompt and adjust `Target:`; no reshoot skill needs to
be installed beforehand:

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

If you know the story, add one sentence such as “Show creating an issue, adding
a label and finding it by filtering.” Otherwise, let the agent propose the task
after inspecting the app. A URL-only session can inspect page controls without
source code. For a native app, the agent needs app-specific automation or your
interaction during capture; reshoot does not operate arbitrary desktop controls.

> **A good first demo**
>
> - One task with a visible result, such as a saved item appearing in a list.
> - Two to four steps.
> - Captions of a few words that say what happened, not what was clicked.
> - About 10 to 30 seconds long. The Feature highlight recipe aims for 15 seconds.
> - A preview of a small app takes under a minute to record.

The first run may need permission to install recording tools, a way to start
the app, or an isolated demo login. Supply those when asked. The agent needs
access to the guide during setup; if GitHub access is blocked, supply a local
reshoot checkout and ask it to read this page there.

### New to coding agents?

A coding agent can read a project's files, edit them and run commands in response
to a task. Use the local app, IDE or terminal setup from the
[Codex quickstart](https://developers.openai.com/codex/quickstart) or
[Claude Code quickstart](https://code.claude.com/docs/en/quickstart), then open
the folder chosen above. Paste the prompt into that session.
Reshoot supplies the demo workflow and recording tools; use the agent account
and permissions required by your chosen tool.

## What your agent needs

There are two ways to use reshoot, and only one needs a model:

| Use | Needs a coding model | Who decides the story |
|---|---|---|
| The CLI on its own | No | You: show the task with `reshoot create`, or write the storyboard, then shape it in the studio |
| The skills | Yes: a coding agent, which is a harness such as Claude Code or Codex plus its model | The agent: it reads your app, writes the story in `demo/`, runs the reshoot commands, looks at the frames and fixes the story until it records cleanly |

The skills call no model themselves. They are Markdown instructions that the
agent reads, and the agent runs the same reshoot commands you would. You can
also read a skill as a checklist and follow it by hand.

Either way, reshoot needs no API key. The recording,
editing and scanning run on your computer, and are the same on every agent:
headless Chrome, VHS or one macOS window to record, ffmpeg to edit, and Apple
Vision or Tesseract, which recognize text and faces on the device, to scan.
Narration uses system speech, optional [local Kokoro speech](install.md#local-neural-narration),
or the command you set. Keeping a demo current in CI needs no coding agent:
the [GitHub workflow](ci.md) only runs reshoot.

### Which agent

| You have | Use |
|---|---|
| Claude Code | The prompt above. Tried with `claude-opus-5-5`: 2 to 5 minutes and under $2 a demo on small apps |
| Codex | The prompt above. Tried with codex-cli 0.164.0 and its default model: 4 to 9 minutes a demo |
| Both | Either; you need only one. The demo files are the same, so another agent can refresh it later |
| Another coding agent | Untested. It may work if it has everything in the next table; paste the same prompt |
| No agent | The CLI on its own, below |

The trials are in the [cold-run record](../docs/validation/2026-10-23-cold-first-demo.md):
one model for each agent, on small apps made for the trial. Other models have
not been tried. A smaller model may write weaker stories and need more of your
corrections. reshoot's result checks still stop a story that shows the wrong
result.

### What the session must allow

| It must | Because |
|---|---|
| Run shell commands | To install reshoot, start your app and run `reshoot` |
| Edit files | To write `demo/` |
| Read web pages, or a local reshoot checkout | To read this guide when no reshoot skill is installed |
| Show the model images | To look at frames and scan sheets; without that, it can only go by the result checks |
| Start Chrome and use a local port | To record. Codex's sandbox blocks Chrome and Apple's Vision, so Codex asks to run reshoot outside it |
| Write `.claude/skills/` or `.agents/skills/` | To install the skills. Codex protects `.agents/`, so it asks first |
| Record one window (macOS only) | Only for a native Mac app, which needs screen-recording permission |

Expect it to ask to install reshoot, ffmpeg and Chrome if it is missing, to start your
app, and for a demo login if the app has one. It should not commit, push,
publish or accept the demo for you; accepting waits for your "accept".

### What leaves your computer

reshoot sends nothing to a model. It checks PyPI for a newer release
(`RESHOOT_OFFLINE=1` stops that) and fetches only the URLs you give it. The
agent, though, sends what it reads to its own provider, as it does for any
task: your app's code and the recorded frames. Use demo data, which the prompt
asks for, and the provider's usual terms apply.

### Without an agent

Run `reshoot create` to try the notes example; [the tutorial](step-by-step.md)
walks through it. To record your own app, [show the task yourself](your-app.md#show-the-task)
with `reshoot create URL --directory demo`. [The studio](studio.md) covers
shaping and accepting the result.

## Review what you get

Expect a short MP4, an animated README GIF, their output paths and the recording
recipe in `demo/`. Browser stories include captions and result checks. Native
recipes use standalone capture and editing, with captions added in post when
needed. The agent should identify unresolved checks and provide a local review
page for versioned runs, or the standalone media and check sheets for native takes.

The agent ends with the same handoff each time: what the demo shows, the MP4,
the GIF and the review page, the result checks and scan items, anything you
need to look at, and the command that accepts it.

Watch both exports. Check that the intended result is visible and the captions
are readable. Then look at the scan items on the review page, flagged ones
first. Reply in plain words:

| You want | Say |
|---|---|
| To keep it | "accept" |
| Shorter captions | "Make the captions shorter, six words at most." |
| More time on the result | "Hold each result a second longer." |
| Larger text in the GIF | "The GIF text is too small; use a narrower viewport." |
| A different task | "Show creating a project and finding it by search instead." |
| A portrait cut | "Add a 4:5 export for LinkedIn." |
| A voiceover | "Add a voiceover that says each caption." |
| It in your README | "Export the accepted demo to docs/demo and add the GIF to the README." |
| It kept current | "Set up the GitHub workflow that refreshes the demo when the app changes." |

To make changes yourself by pointing, run `reshoot studio demo`: it shows the
run step by step and saves your edits to the project's files. See
[the studio](studio.md).

The agent revises the source and records another run. Saying "accept" lets it
run `reshoot accept` for you; you can also accept in the studio's
[Review this recording](studio.md#review-and-accept). Nothing posts
automatically.

You can stop here with your first clip. When ready, see [how the videos look](look.md)
and [grow a fuller demo](studio.md#grow-it-into-a-fuller-demo). Use
[Keep a demo current](publish.md) when the recording becomes part of your project.

## Update the demo when the app changes

For a browser or terminal project, use the refresh skill with the configuration
and the accepted run. `demo/accepted` names the newest run you accepted, and
`demo/latest` the newest successful one. In Codex:

```text
$reshoot-refresh
Refresh demo/reshoot.toml against demo/accepted.
Record the current UI performing the same task. Keep the step IDs and result
checks, repair changed controls if needed, and retain the previous run.
Inspect a preview, make a fresh final, and open the comparison for review.
```

In Claude Code, replace the first line with `/reshoot-refresh`. With the plugin,
use `/reshoot:reshoot-refresh`. Keep the old recording until you have watched
and accepted the new one.

For a separate review, compare the newest run with the accepted one:

```text
$reshoot-review
Review demo/latest against demo/accepted.
Inspect the actual MP4 and GIF, result checks, scan coverage and step evidence.
Report readability or timing problems and any human decisions still pending.
Preserve the existing recordings and review evidence.
```

In Claude Code, use `/reshoot-review`; with the plugin, use
`/reshoot:reshoot-review`. Include the task after the skill name so the agent
knows which recording to inspect.

For a native app, give the skill the saved capture and edit recipe and the
old and new MP4 and GIF paths. Request a new one-window recording and
manual comparison. See the [native workflow](macos-window.md) for its limits.

## Install the skills yourself

Skip this if the agent already set itself up. [Install](install.md#install-the-skills)
covers the project skills and the Claude Code plugin.

## For the agent: setup and creation workflow

When you receive the prompt above:

1. Read the [installation guide](install.md). Check `reshoot --version`, and
   reuse an installation only if it is the latest release, which
   `reshoot doctor` reports. Otherwise run
   `uv tool install --upgrade 'reshoot[browser]'` and install missing tools,
   within the owner's authorization and the harness's permissions. Do not
   bypass permission failures.
2. Install the primary skills with `reshoot skills codex --directory .` or
   `reshoot skills claude --directory .`. If they are already there and the CLI
   was upgraded, add `--replace`, first saying which skill folders it
   replaces; if `git status` shows changes to them, ask the owner first. A
   plugin installation needs no project copy.
3. Read the installed `reshoot-demo/SKILL.md` and follow it, including its
   handoff. If skill discovery has not refreshed, read that file directly and
   continue in the current session. Offer two or three changes from
   [Review what you get](#review-what-you-get) in the handoff.
