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
- **Odd frame sizes,** such as 960 by 880. Round 4 showed these are viewports
  the agents chose for narrow apps, not a capture fault.
- Installing skills into `.agents/` needed approval; Codex's sandbox protects it.

The fixes: `reshoot doctor` reports a newer release, the skills require 0.3.2
and say how to upgrade, the quickstart reuses only a current install, a browser
that cannot start names the sandbox as the usual cause, and agents are told to
keep changes in `demo/`.

## Round 4: Codex on the fixes

Four fresh Codex sessions ran the same apps after commit `3315fa2`. They read
the new quickstart from GitHub but installed 0.3.2 from PyPI, so the new
`doctor` notice and Chrome error were not yet in the CLI they used. The old
0.2.0 was still on the login shell's path.

| App | Minutes | Outcome |
|---|---|---|
| Recipe Box | 6.8 | Preview and final, 12 checks, `960x720` |
| Tiny Tracker | 5.9 | Preview and final, 11 checks |
| Team Standup | 6.5 | Preview and final, 15 checks, `960x840` |
| Tracker by URL | 4.9 | Preview and final, 11 checks; the final kept the preview's issue, and said so |

- **Stale install: fixed.** All four compared the installed version with PyPI
  and upgraded before writing anything. None recorded with 0.2.0. Because the
  upgrade went into each session's own tool folder, the login shell still found
  0.2.0 first, and each agent then called the new CLI by its path or with
  `uv tool run`. A normal install upgrades in place.
- **README: fixed.** No session changed a file outside `demo/` and `.agents/`.
- **Chrome in the sandbox: still the first failure** in all four, with
  Playwright's message, since the clearer error is not released yet. Each
  agent retried outside the sandbox.
- **Opening exports:** the sandbox also blocks `open`. Two agents served
  `demo/` over local HTTP and opened it in Chrome, one asked for access.
- Every scan found nothing to flag.

## Round 5: Codex on 0.3.3

Two fresh Codex sessions, Recipe Box and Team Standup, ran on the released
0.3.3. Both finished with a preview and a final, 9 and 14 checks, no flags, and
no changes outside `demo/` and `.agents/`, in 5.4 and 8.2 minutes.

- **Chrome in the sandbox: fixed.** Both first previews still failed inside
  the sandbox, now with `Chrome could not start` and the note naming Codex's
  sandbox. Both reran outside it and went on.
- The upgrade notice could not be tested: 0.3.3 was the latest release, and
  the owner's own install had been upgraded to it.
- The Standup agent saw a caption overlap a heading in the preview and moved it
  before the final.

## Round 6: the upgrade notice, on 0.3.5

On 2026-10-24, one fresh Codex session ran Recipe Box with an older reshoot
installed: 0.3.4 in the session's own tool folder, and the owner's 0.3.3 on
the login shell's path. `doctor` from 0.3.4 printed "0.3.5 is out". The
session finished in 5.1 minutes with a preview and a final, 8 checks, no
flags, and no changes outside `demo/` and `.agents/`.

- **Upgrade: done, before anything was written.** Following the quickstart, it
  compared `reshoot --version` with PyPI and ran
  `uv tool install --upgrade 'reshoot[browser]'` as its fifth and sixth
  commands. The login shell still found 0.3.3 first, so it called the new CLI
  by its path, as in round 4. Its `doctor` then reported 0.3.5 with no
  notice. The PyPI check came first, so this shows the quickstart leads to an
  upgrade; it does not show the `doctor` notice alone would.
- **Errors that name the field:** its first story used `exact` in a target.
  The new message, `unknown target option exact; use css, test_id or role,
  with name, text or frame`, led to a fix in one edit.
- **Chrome in the sandbox:** the first preview failed with the sandbox hint
  and was rerun outside it, as in round 5.
- **Opening exports:** still blocked by the sandbox; it said so and gave the
  paths.
- Its closing `reshoot accept` command names `reshoot`, which on the owner's
  path is still 0.3.3; the owner's own upgrade is theirs to run.

## Limits

- One model per harness: `claude-opus-5-5` and Codex's configured default.
- The apps were small and well labelled, written for this trial.
- `claude -p` cannot answer a question, so the URL-only run's stop is the
  correct ending here, not a measure of what a person would do next.
- Rounds 1 and 2 used 0.3.1; their fixes are in 0.3.2, which rounds 3 and 4
  used. Round 4 read the guides from `main`; round 5 used 0.3.3.
- Codex loaded the owner's Codex configuration, including its MCP tools, so it
  was less isolated than the Claude Code sessions.
