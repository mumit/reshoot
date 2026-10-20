# Timed user acceptance pilot

Date: 2026-10-20

Status: The owner will perform the first trial, scoped to photosearch and its main
features. A fresh interactive Codex session is prepared as the default workflow.
The timer starts when the owner launches it. The ten-case update study is deferred;
no timed user trial or eight-of-ten result has been recorded.

The owner accepted the five earlier external candidates. This pilot measures the
effort of creating and updating a demo, including repairs and review. It extends
the [external trials](../validation/2026-10-20-external-trials.md).

## Current first task

The owner said: "I'll perform the trial, let's start with just photosearch, showing
the top features." This replaces the earlier narrow beach-search task for the
first participant session. Other apps and update cases are deferred.

The prepared brief asks for a 45–75 second landscape demo connecting search,
look-alikes, Time Machine, Galaxy, and saving a local smart album. It keeps the
photosearch name and labels the generated images and mocked model. The task
ends at a preview for the owner to judge, followed by a fresh final run after
preview acceptance. New artifacts need their own decisions.

Feature APIs were checked on the separate smoke fixture: search and look-alikes
returned results, Time Machine covered 2018–2025, Galaxy mapped 73 generated
items, and a local album saved and loaded. This was an agent readiness check,
with a sandbox-blocked startup followed by an authorized retry. It was not a user
trial or visual review of those new scenes. The participant starter has no warmed
Galaxy layout and no authored storyboard or edit.

The starter reset now clears its generated albums and Galaxy layout as well as
rebuilding its index. Numba's cache stays in its own generated data directory.
This prevents a saved album from an earlier preview contaminating a fresh run.

The local launcher is `takes/user-trial-20261020/start-photosearch`. It starts the
owner's timer, opens a fresh Codex session with the brief and installed skill,
and saves launch metadata and events locally. Its dry run does not start a timer.
The owner can provide verdicts directly in that session; no downloaded decisions
file is required. The participant task, runtime, and measurement instructions
are in the starter's `TASK.md`, `TRIAL.md`, and `AGENTS.md`.

Report this as an experienced maintainer's multi-feature creation task. Its scope
differs from the originally proposed short single-task preview; retain that
distinction when discussing the 15-minute target. The historical protocol below
still describes the proposed broader study.

## Participant and scope

Start with a photosearch maintainer trial. Record whether the participant uses
Codex, Claude, or only the CLI, their prior reshoot experience, and which tasks an
agent performs. The owner has already seen the previous recordings, so an owner
trial is an experienced maintainer pilot. It cannot establish a new user's time
to learn the workflow. Another participant is needed for that claim.

Record the actual harness/model version and conversation context. Using this
existing conversation includes extensive prior knowledge of the app and reshoot.
Use a fresh session for the first-demo task when possible. Record help and
interventions rather than excluding them from the time.

All fixtures are isolated copies of the pinned public sources from the external
trials. Photosearch retains its actual name, generated thumbnails, mocked search
model, blocked Photos/model imports, and disabled Photos operations. The required
CSS repair from the previous trial is retained. Other apps use generated rows,
tasks, and a local demo account. Capture a headless browser page or VHS terminal.

## First demo

The original proposed task below is retained as the protocol history. The current
participant task is the feature demo described above.

The starter contains the app adapter, generated data, startup/reset instructions,
and installed Codex skills. It contains no reshoot configuration, storyboard, edit,
or recording. A separate smoke project checks that the prepared environment works.

The participant's task is:

> Make a short README demo of photosearch. Search the generated library for beach,
> show the search results, and open the first result. Keep the name photosearch.
> Clearly label the generated images and mocked model. Use the local adapter and
> runtime documented in TRIAL.md. Make a preview I can watch, with explicit result
> checks. Keep each new recording pending review until I decide it is acceptable.

Start the first-demo clock when the participant receives this task in the prepared
environment. Stop it only when that participant watches and accepts a specific
preview. Include planning, story authoring, model thinking, commands, troubleshooting,
and playback. Also record final-render and final-review times separately.

Dependencies and fixture preparation are a separate setup measurement. The agent
prepared this pilot's dependencies and fixture; their preparation time does not
measure user setup. Do not substitute CLI execution time for first acceptable
preview time. The proposed first-preview target is 15 minutes with dependencies
and demo data ready. A maintainer result does not establish the novice target.

## Ten proposed update cases

Agree this set before recording any case. Each case starts from its own isolated
copy of the unchanged story and corresponding baseline app state. Changes are
independent. Preserve the task and expected result. The fixture prepares the app
change; the participant or their assistant diagnoses and repairs the demo.

| Case | App | Change | Expected demo repair |
|---|---|---|---|
| U01 | photosearch | Search placeholder wording changes | None expected |
| U02 | photosearch | Search input ID becomes `search-query` | Update the locator |
| U03 | photosearch | Result grid spacing and corners change | None expected; inspect readability |
| U04 | photosearch | Mocked search response gains a two-second delay | Adjust waits only if necessary; retain the real delay |
| U05 | Flaskr | Save button becomes Publish post | Update the button locator |
| U06 | Flaskr | Body textarea ID becomes `post-body`; submitted field stays `body` | Update the locator |
| U07 | Flaskr | New-post route moves to `/posts/new` | Semantic link should follow the new route |
| U08 | Datasette | Database becomes `tasks_fixture.db`, changing browser routes and the terminal command | Repair URLs and the VHS tape |
| U09 | TodoMVC React | Completed filter becomes Done | Update the link locator |
| U10 | TodoMVC ES5 | Task-list heading becomes My tasks | None expected |

Photosearch's new baseline uses the original branding. It needs its own acceptance;
the earlier accepted recording used the temporary photo finder label. The other
apps can use their previously accepted selected candidates as explicit baselines.
Record fixture ports and infrastructure differences in comparisons. Do not promote
any candidate automatically.

Count a case as complete without manual video editing only when a full fresh run
passes its required task checks and scans, has an explicit baseline comparison,
and the participant watches and accepts its final exports. Editing a storyboard,
selector, wait, configuration, tape, or declarative edit file is allowed but must
be counted separately. Record direct editing of rendered footage as manual video
editing. Keep failed attempts and their time. A final failure, abandoned case,
pending review, or required detector error cannot count as complete.

Report successes out of all ten agreed cases. The proposed target is at least
eight complete without manual video editing. Do not remove difficult cases from
the denominator. An interrupted or incomplete study remains incomplete. Run a
deliberately incorrect expectation as a separate negative control; it is not one
of the ten legitimate updates and must remain failed until its meaning is resolved.

## Existing-method comparison

Photosearch's existing method is documented in its `tools/launch/README.md`.
The full launch process contains browser, Claude/VHS, Photos, and multiple edits.
This pilot compares only the same short browser task through the existing
`tools/director/director.py` and reshoot. Use the same fixture, changed input ID
(U02), viewport, result, caption reading holds, and MP4 deliverable in both arms.
The participant must confirm that this browser-only adaptation represents how
they would update that part of their existing demo.

Prepare and accept a baseline for each method before timing the update. Begin
each arm when the participant receives the changed app and existing story. End
only after the participant accepts the updated MP4. Count startup, source repairs,
recording, encoding, errors, inspection, and review in both arms. Leave out GIFs
and supplemental full scans from this specific comparison unless both arms do
them; record those costs separately. Save each arm's command and output times too.

Record arm order and familiarity. One paired maintainer trial is a descriptive
result, not proof of general time savings. Repeat with reversed order and other
users before generalizing. Running the full Photos launch against personal data
is outside this pilot.

## Recording measurements

Save participant role, workflow, fixture/source versions, protocol agreement,
task start, preview rendered, preview accepted, final rendered, review start/end,
final accepted, repair intervals, help requests, video edits, failed attempts,
interruptions, run IDs, artifact bindings, and baseline IDs.

Measure total elapsed task time first. Also report deliberate interruption time
and recorded repair/review intervals. Do not label unmarked time as active human
effort: it includes waiting, model work, and tool execution. Missing timings stay
unmeasured. Historical acceptance has no reconstructed stopwatch measurement.

The local timing helper writes the events directly to disk; it needs no downloads
or renamed decision files. The assistant can record explicit owner decisions and
import them into the exact candidate, as it did for the previous review.

From the reshoot checkout, the helper is
`.venv/bin/python takes/user-trial-20261020/timing.py`.
Use `start TASK --actor owner --workflow codex`,
then `mark TASK EVENT --run /path/to/run.json` at each relevant step. Use `summary
TASK` to read the measurements. The helper binds rendered/accepted events to the
referenced run and rejects human acceptance for an agent-only task. Legacy events
use `--artifact /path/to/demo.mp4` instead. Do not start an owner timer until the
owner begins the task. Preserve separate attempt IDs and record interruptions.

Before update timing, save the participant's explicit case-set agreement and the
SHA-256 of the prepared case list in the local `agreement.json`. The timing helper
checks that the case list still matches. Agreement and outcome are separate records.

## Prepared local material

- Fixture root: `/tmp/reshoot-user-trial-20261020/`.
- First-demo starter: `starter/reshoot_trial/`, with `TRIAL.md` and installed skills.
- Separate readiness smoke project: `smoke/reshoot_trial/reshoot.toml`.
- Update projects: `cases/U01/` through `cases/U10/`, using separate ports.
- Local preparation script, manifest, app patches, and dependency checks:
  `takes/user-trial-20261020/` in this checkout.
- Legacy comparison fixtures: `legacy-baseline/` and `legacy-changed/`, with a
  storyboard for the same task. The local `run-legacy.py` wrapper resets the fixture,
  starts its server, invokes the pinned director, and stops its own server.
- Each update configuration passes doctor. Doctor checks configuration and tool
  availability; it does not establish a successful capture, result, or scan.

Preparation initially stopped on U09 because its React change targeted `base.js`
instead of `app.bundle.js`. The correction and resumed preparation completed all
ten configurations. This was a fixture-authoring repair before participant timing.
No update acceptance case was executed during preparation.

The separate reshoot smoke preview completed in a reported 24 seconds. Its four
browser checks passed and its sampled Vision scan completed. I inspected search
and lightbox frames extracted from the encoded MP4; the task, captions, and original
branding are visible. This is an agent readiness check. Full playback and human
acceptance of this new baseline remain pending. Its local review page is
`takes/user-trial-20261020/smoke-review/review.html`.

The legacy baseline readiness recording also completed, with no reported page
errors. Its wrapper measured 18.577 seconds for reset, startup, capture, encoding,
and cleanup. A sampled Vision check completed with human review pending. I
inspected encoded search/lightbox frames. The first attempt was blocked from
binding local ports by the outer sandbox; an authorized retry completed outside
it. These readiness times have different scopes and output settings. They do not
measure a user update or establish a time saving. The saved legacy MP4 is
`takes/user-trial-20261020/legacy-review/demo.mp4`.

The local material reuses existing installed Python environments and the public
TodoMVC npm dependencies. It is specific to this host. Recreate the pinned sources
and dependencies on another host before repeating the pilot. Generated fixture
sources, media, and raw measurements remain ignored by Git.
