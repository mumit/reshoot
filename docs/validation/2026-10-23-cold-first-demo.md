# Cold first-demo runs

On 2026-10-23 the README's first-demo prompt ran in fresh Claude Code sessions
(`claude -p`, model `claude-opus-5-5`) against four small made-up apps reshoot
had never seen. Each session started with no reshoot install on its path, its
own uv tool folder, no reshoot skills, no project memory and no MCP servers. It
could run shell commands, edit files and fetch web pages; `git push`, `sudo`,
`brew`, `screencapture` and `reshoot window` were blocked. Sessions could not ask
questions mid-run, so a question ended the session. They installed reshoot 0.3.1
from PyPI and read the guides from GitHub.

## Results

| App | Target | Minutes | Cost | Outcome |
|---|---|---|---|---|
| Recipe Box: static page | the repository | 2.5 | $0.77 | Preview and final, 6 checks passed |
| Tiny Tracker: Flask and SQLite | the repository | 2.8 | $0.67 | Preview and final, 8 checks passed; wrote its own database reset |
| Team Standup: Vite, React, login | the repository | 7.1 | $1.58 | Preview and final, all checks passed; logged in during setup |
| Tiny Tracker, running | a URL only | 2.2 | $0.66 | Stopped and asked for a data reset |

Every session installed the CLI and skills, wrote `demo/` with a brief, a
storyboard with result checks, a configuration and an edit, inspected frames,
and handed over the `reshoot accept` command without running it. None committed,
pushed or changed the README. The three repository targets produced videos fit
to post. The URL-only session stopped correctly: its first preview failed after
creating an issue, the app had no reset, and its exact count checks could not
pass again.

## What the runs found

| Finding | Seen in | Change |
|---|---|---|
| No action for a dropdown; the agent focused it and pressed `f` | Tracker | A `select` action, and `reshoot rec` writes it |
| A storyboard error didn't say which beat or action | Tracker | Errors name the beat and the action or check |
| Text small in the 800 px GIF when the app is a narrow column | Recipes, Tracker | Skill guidance: a narrower viewport, or zoom |
| Chrome refuses port 5060; the error said `beat None` with no hint | URL only | The error names the page load and the flag that allows the port |
| Exact counts fail when data persists between takes | URL only | Skill and guide guidance for apps without a reset |
| At `960x540@2` the video showed each result a whole hold late while checks passed | Standup | Evidence comes from the video's own frames, not a screenshot |
| A higher pixel ratio only scales frames up | Standup, then a probe | Documented in the pitfalls; not fixed |

The late-result bug was the most serious: a green run with a wrong video. The
Standup app at `960x540@2` reproduced it on three of three takes, each result
appearing 2.5 seconds late, the length of the hold. Skipping the evidence
screenshot removed it on three of three; saving evidence from the screencast
instead removed it on five of five. A small synthetic page does not trigger it,
so the regression test checks the behavior rather than the race.

## Round 3: both harnesses on 0.3.2

The same four apps, from fresh clones, ran again on 0.3.2: four Claude Code
sessions, then four Codex sessions (`codex exec`, `codex-cli` 0.164.0, its
workspace-write sandbox with network on, escalations sent to automatic review).
Each URL-only run had its own tracker, on ports 5060 and 5061, which Chrome
refuses.

| App | Claude Code | Codex |
|---|---|---|
| Recipe Box | 2.2 min, preview and final, 5 checks | 5.2 min, preview and final, 10 checks |
| Tiny Tracker | 2.8 min, preview and final, 7 checks, `select` | 6.5 min, preview and final, 12 checks |
| Team Standup | 2.8 min, preview and final, 6 checks | 8.6 min, preview and final, 17 checks |
| Tracker by URL | 2.9 min, two previews; asked for a data reset before the final | 6.3 min, preview and final, 7 checks, a read-only task |

Claude Code used every round 2 fix: `select` for both dropdowns, a narrower
viewport in all four, the unsafe-port hint, and checks for the created issue
instead of counts. It stopped before the URL-only final only because each take
added a duplicate issue and it would not restart a server it had not started.

Codex finished all four, but showed new problems:

- **A stale install recorded a whole demo.** Codex runs commands in a login
  shell, which put the owner's old reshoot 0.2.0 back on the path. Three
  sessions upgraded to 0.3.2 after noticing; the URL-only session recorded
  everything with 0.2.0. The quickstart said to reuse an existing install, and
  the skills accepted 0.2.
- **Chrome is blocked by the sandbox.** Three of four first previews failed with
  Playwright's `Target page, context or browser has been closed`. Each agent
  worked out the cause and retried outside the sandbox.
- **Edits outside `demo/`.** Three of four embedded the GIF in the app's README
  without being asked; one also changed `.gitignore`.
- **Odd frame sizes,** such as 960 by 880, which shrink text in a 16:9 GIF.
- Installing skills into `.agents/` needed approval; Codex's sandbox protects it.

The fixes: `reshoot doctor` reports a newer release, the skills require 0.3.2
and say how to upgrade, the quickstart reuses only a current install, a browser
that cannot start names the sandbox as the usual cause, and agents are told to
keep changes in `demo/`.

## Limits

- One model per harness: `claude-opus-5-5` and Codex's configured default.
- The apps were small and well labelled, written for this trial.
- `claude -p` cannot answer a question, so the URL-only run's stop is the
  correct ending here, not a measure of what a person would do next.
- Rounds 1 and 2 used 0.3.1; their fixes are in 0.3.2, which round 3 used.
- Codex loaded the owner's Codex configuration, including its MCP tools, so it
  was less isolated than the Claude Code sessions.
