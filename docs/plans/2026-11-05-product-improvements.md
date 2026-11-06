# Product improvement starting plan

Date: November 5, 2026. Branch: `docs/product-review-2026-11-05`.
Base: `5cfaec0a81c0ff4dfd439345d6724155e478fc06`.

Read the [product review](../reviews/2026-11-05-product-review.md) first for
findings R01-R08, evidence, user fit, the open source comparison and proposed
feature deferrals. This is a proposed backlog. It does not change the existing
roadmap's owner decision to defer outside-user trials. No feature has been
removed.

## Done on this branch

The owner chose to start with what sets reshoot apart: a demo that checks its
own result and says which step a change broke. That came before P01.

- [x] **Pull-request check (new).** `examples/github/check.yml` records the demo
      on each pull request and fails the job when a step stops or a check fails.
      It keeps one comment up to date with the step, the reason and a storyboard
      patch for a missing control. The Action has a `summary` output.
- [x] **P04, changes to checks.** Each run records the checks its steps declare.
      `reshoot compare`, the refresh pull request, the job summary and the
      studio comparison list checks added or removed. Runs accepted before this
      change have no saved checks, so their first comparison says "not compared".
- [x] **P07, claims.** README intro and "How it differs", the CI guide, the
      refresh review steps, two skills, and the package and plugin descriptions
      now lead with checked results and name the browser-only limit.

Tried in the private `mumit/reshoot-ci-trial` on November 6, 2026: a renamed
control failed the check with a patch that applies with `git apply` (PR #6),
and a removed check passed but was listed in the comment (PR #7). 359 fast
tests and 66 browser tests passed.

Still open in P04: explaining in the studio what each check proves. The workflow
templates must be pinned to the release commit before this branch is released.

## Direction

Concentrate on developers and documentation engineers maintaining checked
browser demos across releases. Consider limiting net-new feature expansion
for one or two releases while improving creation, editing, refresh and review.
Keep videos, GIFs and documentation screenshots as the main deliverables.

Preserve task checks, explicit repairs, reversible edits, previous recordings
and review of the exact output. Continue supporting existing projects. Reduce
prominence or investment before considering a breaking removal.

## Start here: P01, make readability feedback actionable

R03 has a concrete reproduction: the default notes final passed its checks but
reported small app text at 9.3 px at a 640 px viewing width. The measurement and
framing tools already exist. Start by improving the path from that finding to
a visible, reversible correction rather than building another renderer.

- [ ] Reproduce the current default preview and final in a fresh synthetic folder.
- [ ] Refresh the development environment's package metadata before new measures;
      the review environment imported current source with old installed metadata.
- [ ] Inspect the current hint, destination-width inspection and recording-view
      controls as a connected journey. Identify the smallest missing connection.
- [ ] Show the relevant correction beside the finding, using the studio's words.
- [ ] Show the effect on the whole task before applying a recording-size change.
- [ ] Save the choice with Undo and use the existing fresh-recording path.
- [ ] Inspect encoded MP4 and GIF output at 640 px and a narrow viewing width.

Acceptance: the author can find the issue, inspect the destination view, choose
a correction, undo it and record again without editing TOML. The task and result
checks remain intact. Inspect clipping and responsive layout changes as well as
font estimates. Use existing thresholds as hints, not an accessibility verdict
or a universal minimum-text guarantee.

Likely touchpoints: `readability.py`, `framing.py`, `layout.js`, `studio.py`,
`stills.py`, `stills.js`, `journey.py` and the existing framing/stills/browser tests.
Confirm the necessary files before editing; this is not a request to change all
of them or globally shrink every app viewport.

## Ordered backlog

| ID | Finding | Proposed work | Observable acceptance |
|---|---|---|---|
| P01 | R03 | Connect readability findings to recording-view correction | A user can inspect, correct, undo and re-record while retaining the task and checks. |
| P02 | R01 | Help configure repeatable demo data and login | Two consecutive runs begin from the intended state; reset/login failures name a next action without touching non-demo data. |
| P03 | R02 | Improve recorder coverage and unsupported-action recovery | A supported common interaction replays correctly; an unsupported one is explained immediately and retains a recoverable draft. |
| P04 | R05 | Explain intended proof and changes to checks | The author can understand what a check proves; refresh review exposes changed or removed checks. Changes to checks done; explaining proof open. |
| P05 | R04 | Reduce comparison noise | Incidental changes can be distinguished from task/result changes without hiding failed checks or material visual differences. |
| P06 | R06 | Simplify the selected-step editing journey | Common caption/hold/repair work keeps the preview and next action visible; advanced tools remain available. |
| P07 | R07, positioning | Clarify browser/native support and competitive claims | README, package/plugin descriptions and guides consistently describe the supported promise without absolute automation or uniqueness claims. Done. |
| P08 | R08 | Prepare a repeated-update effort comparison | A written protocol separates setup, active effort, machine time, waiting, repairs and review; execution respects the existing deferral of outside-user trials. |

P01 is the smallest concrete starting change, not a claim that readability is
every user's biggest problem. P02 addresses the broader repeatability risk.
Priorities can change when observed failures or user evidence justify it.

For P03, first inventory ordinary single-select, multi-select, upload, drop,
iframe and popup flows. Distinguish replay support from recorder/studio authoring
support. Choose a bounded missing interaction before promising broad coverage.

For P05, compare unchanged reruns, incidental cursor/time variation, a renamed
control, a wrong result and a real layout change. Evaluate a simple explanation
or grouping improvement before introducing perceptual algorithms or mask settings.

## Investment choices to revisit

Keep optional audio, tours, styles and advanced sequencing working, but propose
no expansion until recurring demand is clearer. Keep the VS Code extension,
microphone narration, additional platforms/simulators and a new MCP server
deferred. Do not delete existing features based on this review alone.

Independent user work could materially change these choices. It is still
deferred by the owner. Prepare a protocol if useful; do not recruit, contact
people, create external trials or represent that decision as reversed.

## Evidence for deciding whether the product helps

Compare initial setup plus several updates against manual recording of the same
task and outputs. Counterbalance method order where practical. Retain failed
attempts and unsuccessful cases in the results rather than reporting only finals.

| Measure | Record |
|---|---|
| First useful output | Completion, active author effort, documentation lookups and interventions |
| Repeated refresh | Repair effort, failed attempts, manual media edits and retained task/checks |
| Machine work | Capture, encoding and scan duration, separate from human waiting |
| Review | Active inspection time, corrections requested and output judged useful |
| Continued use | Whether users choose reshoot for the next update without prompting |
| Ongoing cost | Agent/CI costs where applicable, storage growth and maintenance work |

No improvement target or general time-saving claim is established by the current
review. Set targets before a future comparison, then report misses and limitations.
Use the [existing pilot plan](2026-10-20-user-acceptance-pilot.md) as context;
avoid creating a second conflicting study process.

## Validation and documentation for implementation

Use the notes example or newly created synthetic fixtures. Keep trial output
under ignored `takes/`; never replace accepted media as part of a test.

Run tests appropriate to the changed behavior. Use browser integration checks
when interactions or workflow transitions change, and inspect actual encoded
frames when capture, captions, zoom, framing or exports change. A clean scan
does not replace review, and automated checks do not accept media.

Follow the repository documentation map: panels in `guide/studio.md`, commands
in `guide/commands.md` and `--help`, fields in `guide/projects.md`, fixed problems
in `CHANGELOG.md`, and relevant skills when commands change. If visual rendering
changes, rebuild and inspect `examples/look/build.py` output as instructed in
`CONTRIBUTING.md`. Record new measured evidence separately from this dated review.

## Restart prompt

```text
Continue on docs/product-review-2026-11-05.
Read AGENTS.md, README.md and CONTRIBUTING.md, then:
- docs/reviews/2026-11-05-product-review.md
- docs/plans/2026-11-05-product-improvements.md

Verify the working tree and source revision; preserve any existing edits.
The pull-request check, P04's changes to checks and P07 are done; see
"Done on this branch". Next is P01: connect the existing readability hint to a visible, reversible
recording-view correction. Reproduce the notes case in a fresh synthetic folder,
inspect the current controls and make the smallest justified change.
Preserve the task, result checks and exact-recording review, and verify the
encoded MP4 and GIF at their destination viewing sizes.

Treat other backlog items as proposals. Outside-user trials remain deferred.
Do not accept media, commit, push, publish or contact anyone unless separately
instructed. Report what changed, what passed and the remaining limitations.
```
