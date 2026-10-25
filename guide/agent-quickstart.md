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

reshoot never calls a model and needs no API key. The agent does the writing:
it reads your app, writes the story in `demo/`, runs the reshoot commands,
looks at the frames, and fixes the story until it records cleanly. The
recording, editing and scanning are the CLI's, and the same on every agent.

### Which agent

| You have | Use |
|---|---|
| Claude Code | The prompt above. Tried with `claude-opus-5-5`: 2 to 3 minutes and under $2 a demo on small apps |
| Codex | The prompt above. Tried with codex-cli 0.164.0 and its default model: 5 to 9 minutes a demo |
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
| Start Chrome and use a local port | To record. Codex's sandbox blocks Chrome, so Codex asks to run that command outside it |
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

After [installing reshoot](install.md), run `reshoot create URL --directory demo`
with your demo server running. Show a task in the fresh browser. Use its toolbar
to add a caption, check the visible result, and choose Done. The preview opens
in the studio, where captions and holds are editable, Undo restores experiments,
Update preview chooses the work, and Make final records the full-size exports.
Inspect the video, GIF and scan sheets there before accepting. Run
`reshoot create` without a URL to try the notes example.

If tools need attention, the studio shows fixes and **Check again**. Choose
**Continue creation**, or run `reshoot create --resume --directory demo` after
fixing setup. A failed preview retains the demonstrated task for that retry.

The [tutorial](step-by-step.md) teaches the individual commands with the notes app.
Keeping a demo current in CI never needs an agent: the
[GitHub workflow](ci.md) only runs reshoot.

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
run beat by beat and saves your edits to the captions, cards, frame and exports
to the project's files. See [Shape it in the studio](customize.md#shape-it-in-the-studio).

The agent revises the source and records another run. Saying "accept" lets it
run `reshoot accept` for you; you can also run the command yourself. The
[review instructions](step-by-step.md#4-accept-the-recording) cover flagged and
rejected items. Nothing posts automatically.

You can stop here with your first clip. When ready, see [how the videos look](look.md),
then [change a caption or timing, or grow a fuller demo](customize.md).
Use [updates and publishing](publish.md) when the recording becomes part of your project.

## Update the demo when the app changes

For a browser or terminal project, use the refresh skill with the configuration
and the accepted run. `demo/accepted` names the newest run you accepted, and
`demo/latest` the newest successful one. In Codex:

```text
$reshoot-refresh
Refresh demo/reshoot.toml against demo/accepted, using its exact run ID.
Record the current UI performing the same task. Keep the beat IDs and result
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
Inspect the actual MP4 and GIF, result checks, scan coverage and beat evidence.
Report readability or timing problems and any human decisions still pending.
Preserve the existing recordings and review evidence.
```

In Claude Code, use `/reshoot-review`; with the plugin, use
`/reshoot:reshoot-review`. Include the task after the skill name so the agent
knows which recording to inspect.

For a native app, give the skill the saved capture/edit recipe and exact old
and new MP4/GIF paths instead of run IDs. Request a new one-window take and
manual comparison. See the [native workflow](macos-window.md) for its limits.

## Install the skills yourself

Skip this section if the agent already handled setup. A skill is a reusable
set of instructions for the agent. Reshoot's three primary skills cover
creation, refresh and review; the CLI provides the recording tools.

Install the [CLI and platform dependencies](install.md), then run the command
for your agent from the app repository or demo work folder:

| Agent | Run in a terminal | Installed location |
|---|---|---|
| Codex | `reshoot skills codex --directory .` | `.agents/skills/` |
| Claude Code | `reshoot skills claude --directory .` | `.claude/skills/` |

Start with `$reshoot-demo` in Codex or `/reshoot-demo` in Claude Code, followed
by a task. Use the agent's skill selector to confirm that the skill is available.
If a newly installed skill does not appear, start a new session in the same
work folder. These locations and invocation conventions follow the
[official OpenAI documentation](https://developers.openai.com/codex/skills) and
[Claude Code skill documentation](https://code.claude.com/docs/en/skills).

For the complete Claude Code plugin, run these commands inside Claude Code:

```text
/plugin marketplace add mumit/reshoot
/plugin install reshoot@reshoot
```

Follow the installation and any reload prompts. Invoke
`/reshoot:reshoot-demo` with the task. This route includes all ten skills;
the CLI's project installer copies the three primary skills. See
[Claude's plugin instructions](https://code.claude.com/docs/en/discover-plugins)
and the [skill catalog](../skills/README.md). Choose one route for the project.
The plugin still needs the CLI and recording dependencies.

## Try it without an app or an agent

Use the [bundled notes tutorial](step-by-step.md) for a complete CLI example
with synthetic data. It covers the first recording and an update. For your
target, use the [source-app walkthrough](your-app.md),
[running-URL route](your-app.md#with-only-a-url) or [native window route](macos-window.md). [Without an agent](#without-an-agent)
lists the commands in order.

## Setup and creation workflow for the agent

When receiving the prompt above, follow this workflow:

1. Identify the target: source code, running URL or native macOS window. Read
   repository instructions when present. Inspect source and fixtures when
   available, or inspect the running page/window. Choose a small task with an observable result. Propose
   a reasonable task when the request leaves it open; ask only when a missing
   decision prevents useful progress.
2. Read the [installation guide](install.md). Check `reshoot --version`: reuse an
   existing installation only if it is the latest release on
   [PyPI](https://pypi.org/project/reshoot/), which `reshoot doctor` also reports.
   Otherwise install or upgrade it with `uv tool install --upgrade 'reshoot[browser]'`,
   and install missing platform dependencies, within the owner's authorization. Obtain required installation permissions
   through the harness. Do not bypass permission failures.
3. Install the primary skills with `reshoot skills codex --directory .`
   or `reshoot skills claude --directory .` for the current harness; the CLI copies
   its own version of them. When the skills are already there, keep them if the
   CLI was not upgraded. After an upgrade, add `--replace`, first saying which
   skill folders it replaces; if `git status` shows changes to them, ask the owner
   before replacing. A plugin installation needs no project copy. Read the installed
   `reshoot-demo/SKILL.md` and follow it. If skill discovery has not refreshed,
   read that file directly and continue within the current session.
4. Choose the appropriate route. For a browser, reuse a project or initialize
   `demo/` with `reshoot init demo --url APP_URL`. Follow the
   [own-app guide](your-app.md), replace
   the placeholder with actual actions and checks, and keep the edit's endpoint
   valid. For a native app, follow the [window guide](macos-window.md): save
   capture instructions and an edit, select one window by ID and arrange
   app-specific automation or manual interaction. Do not force native capture
   into the versioned browser configuration.
5. Use isolated synthetic data and document its reset. Keep secrets and real
   accounts outside the demo. Resolve a fresh-profile login for web apps or a
   synthetic document for native apps. Ask for missing setup when needed.
6. For versioned browser projects, run `reshoot doctor --config demo/reshoot.toml --probe`
   and `reshoot preview demo/reshoot.toml`. For native apps, verify ffmpeg and
   capture permission, then make a standalone test take. Inspect the result;
   repair actions without changing the intended task. Retain failed attempts.
7. Make a fresh final and inspect the actual MP4 and GIF. For versioned runs,
   read the report and generate the review page. For standalone native takes,
   generate check sheets and compare media manually. Present exact paths,
   coverage and unresolved findings. Open the exports when the environment permits.
8. End with this handoff, in this order:
   - one sentence on the task and its visible result;
   - the MP4, the GIF and the review page as paths, opened when the
     environment permits;
   - the status line the run printed: result checks, scan items, flagged items;
   - anything the owner must look at: flagged items, reduced checks, mocked
     data, shortened waits;
   - "Reply accept, or ask for changes such as:", with two or three changes
     that fit this recording, from the table in
     [Review what you get](#review-what-you-get);
   - the `reshoot accept RUN` command the run printed, for the owner to run.

   Run `reshoot accept RUN --yes` only when the owner replies accept or
   otherwise explicitly asks; never on your own judgment. After accepting, offer
   `reshoot export demo/accepted --directory docs/demo` and the README Markdown
   it prints. Keep source files available for the next refresh; commit or
   publish only when authorized. Keep your changes in `demo/` and the skill
   folder: don't edit the app's README or other files unless the owner asks.
   `reshoot init` writes `demo/.gitignore`, which keeps recordings out.

The initial target is one readable task and a visible result. Add narration,
terminal segments, branding or portrait framing after that first recording
works. Use [Troubleshooting](troubleshooting.md) for setup and review failures.
