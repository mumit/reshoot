# Docs simplification plan

Make the docs as easy to follow as the studio now is to use. Give each fact one
home, write it in plain words, and keep feature work from piling up on top of
the pages again.

## Where the docs are now

The docs come to about 56,000 words: 19 guide pages, 10 skills, the README and
the root files. Another 37,000 words sit in 35 validation records. The last
two days of feature work added most of the growth, and it shows in five ways.

1. **Features are stacked, not placed.** Each new studio feature added a
   section at the top of `guide/customize.md`: tours, screenshots, audio,
   styles, cut, framing, comparison, sessions and repair. That page is now
   5,600 words, and its original walk-through starts below them. `look.md`
   and `projects.md` grew the same way, with new sections at the top or in
   the middle.
2. **The same thing is explained many times.** The tour and screenshots are
   each described in 6 files, `reshoot create` in 9, Update preview in 11 and
   Undo in 8. The README's "Try it in a minute" lists nearly every studio
   panel.
3. **Pitfalls became a change log.** `guide/pitfalls.md` has 67 "Fixed in
   reshoot" entries. Seventeen of them, all about the studio, come before the
   first heading. A reader who wants to know what to watch for has to skip
   past what reshoot already handles.
4. **The words are internal.** The newer text uses the implementer's terms:
   "binding", "revision guard", "stale-evidence checks", "pending-range
   protection", "checkpointed", "interprocess lock", "hashed measurements".
   They're accurate, but they describe how the code works, not what the
   person should do.
5. **There are many front doors.** A newcomer can start from the README, the
   guide index, the agent quickstart's "Without an agent" section,
   `your-app.md` or the tutorial. Each of them describes `reshoot create`
   and the studio a little differently.

The skills have the same problem: about 10,500 words, with long paragraphs
that repeat the guide (`record-web` 2,300 words, `cut-video` 1,600,
`reshoot-demo` 1,400).

## Principles

- **One home per fact.** Explain a feature once, on the page whose job it is.
  Elsewhere, write one line and a link to it.
- **Pages by purpose.** A tutorial teaches, a how-to page does one job, a
  reference page lists every field and command, and an explanation page says
  why. A page does one of these.
- **Write what to do, then why.** Start with the reader's goal, use the
  studio's own button names, and leave out how the code keeps things safe
  unless the reader has to act on it.
- **Plain words.** Prefer "the run shown on the page" to "the displayed run's
  binding", and "the file changed since you loaded it" to "a stale revision".
- **The CLI is a short appendix to the studio.** Each studio how-to ends with
  the matching commands. Their full flags live in `commands.md` and `--help`.

## Target structure

| Page | Job | Change |
|---|---|---|
| `README.md` | What reshoot is, one command to try it, the agent prompt, where next | Cut "Try it in a minute" back to the commands and one paragraph. Move the panel list to the studio page. Aim for under 1,000 words |
| `guide/README.md` | Index and glossary | Add glossary entries for the studio's terms: Update preview, Make final, Your cut, tour, docs screenshot |
| `guide/install.md` | Install and check the tools | Make `reshoot doctor --probe` the check, in one place |
| `guide/step-by-step.md` | The one tutorial | Rewrite to start with `reshoot create`: shape it in the studio, break the app, repair the beat, compare, accept. Put each command in an aside |
| `guide/agent-quickstart.md` | Make a demo with an agent | Keep the prompt, "What your agent needs" and review. Replace "Without an agent" with a link to the tutorial |
| `guide/your-app.md` | Record your own web app | Keep: show the task, choose a result, demo data and login |
| `guide/studio.md` (new) | Every studio panel, in the order a person meets them | Move the studio sections out of `customize.md` and the README into it. Under each heading: what it's for, the steps, what to check, the CLI commands |
| `guide/customize.md` | Change a demo by its files | Keep the file-based changes: words, holds, cursor, frame, destination, growing a fuller demo. Link to the studio for pointing |
| `guide/look.md` | Pictures of each setting | Pictures and settings only. Move the how-to text to the studio page |
| `guide/publish.md`, `team.md`, `ci.md` | Share it, run it as a team, refresh it in CI | Explain "review a refresh pull request" once, in `team.md`, and link to it from the other two |
| `guide/projects.md` | Every field | Order it file by file: reshoot.toml, storyboard.toml, edit.toml, styles.toml, then tours and screenshots under reshoot.toml |
| `guide/commands.md` | Every command | Group the rows by job: create, record, shape, review, share |
| `guide/troubleshooting.md` | Errors and what to do | Keep it organized by error message. Move entries that only explain into pitfalls |
| `guide/pitfalls.md` | What to watch for | Keep the lessons a person still has to act on, grouped by topic. Move the history of what reshoot fixed to the CHANGELOG (decision 1) |
| `guide/manual.md`, `macos-window.md`, `speed.md` | Unchanged jobs | Light edit for plain words |
| `skills/*/SKILL.md` | The workflow and its guardrails, for an agent | Cut repeated reference text. Point to `reshoot COMMAND --help` and `projects.md` for fields. Keep the rules an agent must follow, such as not starting interactive commands, never weakening a result check, and leaving acceptance to the owner |
| Root files | Contributor and project status | Move `UX_PLAN.md` to `docs/plans/` and link to it from ROADMAP. Keep CHANGELOG entries to one or two lines each |

## Steps

Each step is a separate commit. The tests, `claude plugin validate .` and the
link checker must pass after each one.

1. **Agree the structure.** The decisions below are settled. Pause feature
   work that edits docs, or have it follow the new structure, so the two
   don't collide.
2. **Add `guide/studio.md`.** Move the studio sections from `customize.md`,
   the README and `look.md` into it, in the order a person meets them:
   create, the status line, beats and holds, Update preview and Make final,
   Undo and sessions, style and exports, your cut, framing, audio, docs
   screenshots, tour, compare, repair, scan and accept, download. Rewrite each
   section in plain words, about half its current length.
3. **Rewrite the tutorial** around `reshoot create` and the studio, with the
   commands beside each step.
4. **Cut the README and the guide index** to point at the tutorial, the
   studio page and the agent quickstart.
5. **Reorder the reference pages**, `projects.md` and `commands.md`, by file
   and by job. Check that every field and command is still there.
6. **Split pitfalls from history.** Keep the open pitfalls and move the
   "Fixed in reshoot" entries to the CHANGELOG. Update the AGENTS.md rule to
   match.
7. **Slim the skills.** Keep each skill's workflow and guardrails, move
   reference text to the guide, and run the skill evals or a cold run to show
   the agents still make a demo.
8. **A plain-words pass** over everything else, plus a check in the tests:
   a list of banned terms, no em dashes, and a word limit for the README and
   each skill.

## Done when

- A newcomer can make the notes demo, change a caption, update the preview
  and accept it, reading only the tutorial.
- Each studio feature is explained on one page, and other pages link to it.
- The README is under 1,000 words, and no skill is over 1,200.
- The tests fail if a banned term or an em dash appears in the guide or the
  skills.
- A cold agent run, like the [first-demo trial](../validation/2026-10-23-cold-first-demo.md),
  still makes a demo in about the same time.

## Decisions

The owner accepted each recommendation below on 2026-10-25.

1. **Where "Fixed in reshoot" history lives.** AGENTS.md says a fixed pitfall
   gets "Fixed in reshoot" in `pitfalls.md`. Recommendation: keep pitfalls to
   what a person must still watch for, and record fixes in the CHANGELOG.
2. **One tutorial, studio first.** Recommendation: yes, with each step's
   command shown beside it, so the CLI is still taught.
3. **Where plans live.** Recommendation: `docs/plans/`, including
   `UX_PLAN.md`, linked from ROADMAP.
4. **Word limits.** Recommendation: under 1,000 words for the README and under
   1,200 for each skill, checked by a test.
5. **Validation records.** Recommendation: leave them as they are. They're
   evidence, not guidance, and `docs/validation/README.md` already summarizes
   them. Guide pages link to them only for a claim about what was tested.
