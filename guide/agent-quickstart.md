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

Use a session that can run shell commands and access the app. Browser recording
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

## Review what you get

Expect a short MP4, an animated README GIF, their output paths and the recording
recipe in `demo/`. Browser stories include captions and result checks. Native
recipes use standalone capture and editing, with captions added in post when
needed. The agent should identify unresolved checks and provide a local review
page for versioned runs, or the standalone media and check sheets for native takes.

Watch both exports. Check that the intended result is visible and the captions
are readable. Give a concrete revision if needed: “Hold the search result
longer,” “Show the empty state first,” or “Use a different example task.”
The agent can revise the source and record another candidate.

Then look at the scan items on the run's review page, flagged ones first. When
both are acceptable, run the `reshoot accept` command the run printed, or tell
the agent explicitly to accept. The [review instructions](step-by-step.md#4-accept-the-recording)
cover flagged and rejected items. Nothing posts automatically.

You can stop here with your first clip. When ready, [explore the features](features.md),
[change a caption or timing](customize.md), then [build a fuller demo or tutorial](make-demo.md).
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
[running-URL route](running-web-app.md) or [native window route](macos-window.md).

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
   [source-app](your-app.md) or [running-URL](running-web-app.md) guide, replace
   the placeholder with actual actions and checks, and keep the edit's endpoint
   valid. For a native app, follow the [window guide](macos-window.md): save
   capture instructions and an edit, select one window by ID and arrange
   app-specific automation or manual interaction. Do not force native capture
   into the versioned browser configuration.
5. Use isolated synthetic data and document its reset. Keep secrets and real
   accounts outside the demo. Resolve a fresh-profile login for web apps or a
   synthetic document for native apps. Ask for missing setup when needed.
6. For versioned browser projects, run `reshoot doctor --config demo/reshoot.toml`
   and `reshoot preview demo/reshoot.toml`. For native apps, verify ffmpeg and
   capture permission, then make a standalone test take. Inspect the result;
   repair actions without changing the intended task. Retain failed attempts.
7. Make a fresh final and inspect the actual MP4 and GIF. For versioned runs,
   read the report and generate the review page. For standalone native takes,
   generate check sheets and compare media manually. Present exact paths,
   coverage and unresolved findings. Open the exports when the environment permits.
8. Ask the owner to watch the exports and look at the scan items, then give them
   the exact `reshoot accept RUN` command, with `--flagged` for each flagged item
   they must inspect. Run it only when the owner explicitly asks you to accept;
   never pass `--yes` on your own judgment. Keep source files available for
   the next refresh; commit or publish only when authorized. Keep your changes in
   `demo/` and the skill folder: don't edit the app's README, `.gitignore` or
   other files unless the owner asks. Offer the Markdown that would add the GIF
   to the README instead.

The initial target is one readable task and a visible result. Add narration,
terminal segments, branding or portrait framing after that first recording
works. Use [Troubleshooting](troubleshooting.md) for setup and review failures.
