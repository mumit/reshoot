# Make a demo with your agent

## Start with one prompt

| What you have | Open Claude Code or Codex in | Set `Target:` to |
|---|---|---|
| App source code | The app repository | `the app in this repository` |
| A running web app | An empty folder | The app's URL, local or hosted |
| An installed macOS app | An empty folder on the Mac | The app's name and the window with demo data |

Paste this, with your `Target:`. No skill needs to be installed first:

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

To choose the task, add a sentence such as "Show creating an issue and finding
it by filtering." For a native app, the agent needs app automation or you to
do the task during capture.

A good first demo is one task with a visible result, in two to four steps and
10 to 30 seconds, with captions of a few words that say what happened.

The agent may ask to install tools, how to start the app, or for a demo login.
If GitHub is blocked, give it a local reshoot checkout to read this page in.

New to coding agents? Set one up with the
[Codex quickstart](https://developers.openai.com/codex/quickstart) or the
[Claude Code quickstart](https://code.claude.com/docs/en/quickstart).

## What your agent needs

reshoot needs no API key and calls no model. The skills are instructions the
agent reads; it runs the same commands you would, on your computer. The
[GitHub workflow](ci.md) needs no agent.

[Tried on small apps](../docs/validation/2026-10-23-cold-first-demo.md):
Claude Code with `claude-opus-5-5` took 2 to 5 minutes and under $2 a demo;
codex-cli 0.164.0 with its default model took 4 to 9 minutes. Other agents are
untested.

The session must be able to:

- run shell commands and edit files;
- read web pages, or a local reshoot checkout;
- show the model images;
- start Chrome and use a local port. Codex asks to run reshoot outside its
  sandbox, which blocks Chrome and Apple's Vision;
- write `.claude/skills/` or `.agents/skills/`. Codex asks first;
- record one window, for a native Mac app only.

reshoot only checks PyPI for a newer release (`RESHOOT_OFFLINE=1` stops that)
and fetches the URLs you give it. The agent sends your code and frames to its
own provider, so use demo data.

Without an agent, see [the tutorial](step-by-step.md) or
[show the task yourself](your-app.md#show-the-task).

## Review what you get

The agent hands you the MP4, the GIF and a review page. Watch both, check the
result is visible and the captions readable, and look at the scan items,
flagged ones first. Reply "accept", or ask for changes:

- "Make the captions shorter, six words at most."
- "Hold each result a second longer."
- "The GIF text is too small; use a narrower viewport."
- "Show creating a project and finding it by search instead."
- "Add a 4:5 export for LinkedIn."
- "Add a voiceover that says each caption."
- "Export the accepted demo to docs/demo and add the GIF to the README."
- "Set up the GitHub workflow that refreshes the demo when the app changes."

To change it yourself, run `reshoot studio demo` ([the studio](studio.md)).
The agent never commits, pushes or publishes. Next:
[keep a demo current](publish.md).

## Update the demo when the app changes

`demo/accepted` is the run you last accepted; `demo/latest` the newest
successful one. In Codex:

```text
$reshoot-refresh
Refresh demo/reshoot.toml against demo/accepted.
Record the current UI performing the same task. Keep the step IDs and result
checks, repair changed controls if needed, and retain the previous run.
Inspect a preview, make a fresh final, and open the comparison for review.
```

For a separate review, ask `$reshoot-review` to review `demo/latest` against
`demo/accepted`.

In Claude Code, start with `/reshoot-refresh` or `/reshoot-review`, or
`/reshoot:reshoot-refresh` with the plugin. For a native app, give the skill
the saved capture and edit recipe and the old MP4 and GIF; see
[the native workflow](macos-window.md).

To install the skills yourself, see [Install](install.md#install-the-skills).

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
