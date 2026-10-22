# Make a demo with your agent

Turn one useful task in your web app into a short video and a README GIF. Let
the agent handle the recording source and tool commands. Keep the project so
the next UI change can become the next recording.

## Start with one prompt

Open Codex or Claude Code in the app's repository on macOS or Linux. Use a local
session that can read the app's code, run shell commands and launch headless
Chrome. Paste this prompt; no reshoot skill needs to be installed beforehand:

```text
Make a demo of the web app in this repository using reshoot.
Read https://github.com/mumit/reshoot/blob/main/guide/agent-quickstart.md
and follow its setup and creation workflow.

Choose one useful task with a clear visible result. Use synthetic demo data.
Produce a short captioned MP4 and a README GIF. Keep the recording source in
demo/ so it can be updated later.

Inspect a preview, then record a fresh final and open both exports for review.
Ask only for permissions or missing details needed to proceed.
```

If the app is already running, add its local URL. If you know the story, add one
sentence such as “Show creating an issue, adding a label and finding it by
filtering.” Otherwise, let the agent propose the task after reading the app.

The first run may need permission to install recording tools, a way to start
the app, or an isolated demo login. Supply those when asked. The agent needs
access to the guide during setup; if GitHub access is blocked, supply a local
reshoot checkout and ask it to read this page there.

### New to coding agents?

A coding agent can read a project's files, edit them and run commands in response
to a task. Use the local app, IDE or terminal setup from the
[Codex quickstart](https://developers.openai.com/codex/quickstart) or
[Claude Code quickstart](https://code.claude.com/docs/en/quickstart), then open
the folder containing your web app. Paste the prompt into that session.
Reshoot supplies the demo workflow and recording tools; use the agent account
and permissions required by your chosen tool.

## Review what you get

Expect a short captioned MP4, an animated README GIF, their output paths and
the recording source in `demo/`. The agent should also provide a local review
page and identify any unresolved checks.

Watch both exports. Check that the intended result is visible and the captions
are readable. Give a concrete revision if needed: “Hold the search result
longer,” “Show the empty state first,” or “Use a different example task.”
The agent can revise the source and record another candidate.

Review the scan sheets and text findings before sharing. Recording acceptance
and scan-sheet approval are separate decisions. The [review instructions](step-by-step.md#4-review-the-recording-and-scan-sheets)
show how to record both. Nothing posts automatically.

## Update the demo when the app changes

Use the refresh skill with the configuration and the accepted run folder.
Replace `PREVIOUS_FINAL_ID` with the exact previous final's ID. In Codex:

```text
$reshoot-refresh
Refresh demo/reshoot.toml against demo/takes/runs/PREVIOUS_FINAL_ID.
Record the current UI performing the same task. Keep the beat IDs and result
checks, repair changed controls if needed, and retain the previous run.
Inspect a preview, make a fresh final, and open the comparison for review.
```

In Claude Code, replace the first line with `/reshoot-refresh`. With the plugin,
use `/reshoot:reshoot-refresh`. Keep the old recording until you have watched
and accepted the new one.

For a separate review, supply both run IDs:

```text
$reshoot-review
Review demo/takes/runs/CURRENT_FINAL_ID against demo/takes/runs/PREVIOUS_FINAL_ID.
Inspect the actual MP4 and GIF, result checks, scan coverage and beat evidence.
Report readability or timing problems and any human decisions still pending.
Preserve the existing recordings and review evidence.
```

In Claude Code, use `/reshoot-review`; with the plugin, use
`/reshoot:reshoot-review`. Include the task after the skill name so the agent
knows which recording to inspect.

## Install the skills yourself

Skip this section if the agent already handled setup. A skill is a reusable
set of instructions for the agent. Reshoot's three primary skills cover
creation, refresh and review; the CLI provides the recording tools.

Install the [CLI and platform dependencies](install.md), then run the command
for your agent from the app repository's root:

| Agent | Run in a terminal | Installed location |
|---|---|---|
| Codex | `reshoot skills codex --directory .` | `.agents/skills/` |
| Claude Code | `reshoot skills claude --directory .` | `.claude/skills/` |

Start with `$reshoot-demo` in Codex or `/reshoot-demo` in Claude Code, followed
by a task. Use the agent's skill selector to confirm that the skill is available.
If a newly installed skill does not appear, start a new session in the same
repository. These locations and invocation conventions follow the
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
with synthetic data. It covers the first recording and an update. To author
the story for an existing app yourself, use the [own-app walkthrough](your-app.md).

## Setup and creation workflow for the agent

When receiving the prompt above, follow this workflow:

1. Read the repository's instructions and inspect its startup commands, UI and
   existing demo fixtures. Choose a small task with an observable result. Propose
   a reasonable task when the request leaves it open; ask only when a missing
   decision prevents useful progress.
2. Read the [installation guide](install.md). Use an existing reshoot installation
   when available; otherwise install the CLI and missing platform dependencies
   within the owner's authorization. Obtain required installation permissions
   through the harness. Do not bypass permission failures.
3. Install the primary skills with `reshoot skills codex --directory .` or
   `reshoot skills claude --directory .` for the current harness. Reuse an existing
   installation or plugin instead of overwriting it. Read the installed
   `reshoot-demo/SKILL.md` and follow it. If skill discovery has not refreshed,
   read that file directly and continue within the current session.
4. Use an existing `demo/` project when appropriate, or initialize one with
   `reshoot init demo --url LOCAL_URL`. Read the [own-app walkthrough](your-app.md)
   and [project reference](projects.md) to configure startup and replace the
   placeholder with real actions, captions and explicit result checks.
5. Use isolated synthetic demo data and document its reset. Record a headless
   browser page. Keep secrets and real accounts outside the demo. If login or
   fixtures cannot be prepared from the repository, ask for the missing setup.
6. Run `reshoot doctor --config demo/reshoot.toml`, resolve required dependencies,
   then record and inspect a preview. Repair failed actions while preserving the
   intended task and expected results. Retain failed attempts.
7. Record a fresh final, read its report and inspect the actual MP4 and GIF.
   Generate its review page. Present the exact run folder, both export paths,
   checks and unresolved findings. Open the exports when the environment permits.
8. Ask the owner to watch the exports and review the scan sheets. Preserve pending
   decisions until the owner supplies a verdict. Keep source files available for
   the next refresh; commit or publish only when authorized.

The initial target is one readable task and a visible result. Add narration,
terminal segments, branding or portrait framing after that first recording
works. Use [Troubleshooting](troubleshooting.md) for setup and review failures.
