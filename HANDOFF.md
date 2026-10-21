# Reshoot handoff

Saved: 2026-10-21

Current status after the session continued into October 21 UTC: the
[ten-case update study](docs/validation/2026-10-20-ten-case-update-study.md) is
complete. Both fresh final exports are owner accepted for all ten cases, with
zero manual video edits. This meets the eight-of-ten target within the assisted
maintainer scope. Five cases needed demo repairs; two had fixture corrections.
The closing audit verified 337 manifest file hashes, 20 export hashes and bound
owner decisions, 37 passed assertions, 40 matched beat IDs, and the expected
negative-control failure. Final sampled scans have zero flags/errors; separate
scan sheets remain pending. Local `ten-case-study/results.json` and `audit.json`
contain the results. No case timers or owner export verdicts remain open.

The [reverse-order method comparison](docs/validation/2026-10-20-recording-method-comparison.md#second-pair-reverse-order)
is also complete, with evidence in
`takes/user-trial-20261020/paired-comparison-02/`. The owner accepted corrected
baselines reshoot `3d5acb2424534056adb7de507a4b18a0` (9.017 s) and director
`baseline-legacy-1ddb93b18b61` (11.317 s), and the reversed timed order. Before
timing, both isolated demo apps received the same one-line CSS correction for a
narrow generated portrait in the opening. Original recordings, protocol, feedback
and patches remain under `opening-feedback/`. `baseline-agreement.json` binds the
owner's verdict to the corrected protocol and exact baseline MP4 hashes.

Both apps then received the same six-file search-input rename. Each unchanged
story failed, and each needed only one locator repair from `#q` to
`#search-query`, with no manual video edits. The owner accepted reshoot final
`736213a6e44c462eb457b3148022eb32` (9.067 s); bound decisions are imported.
The owner then accepted director `changed-legacy-47689211ae1f` (11.233 s), replying
“Acceptable.” Exact acceptance receipts and original failed attempts are retained.
Both recordings passed their four task checks and sampled scans with zero
flags/errors; encoded opening, search and lightbox frames were inspected.
Separate scan sheets remain pending.

Elapsed to acceptance was 247.200 seconds for reshoot first and 127.632 seconds
for the director second, including review intervals of 177.572 and 74.197 seconds.
Both timers have ended. `audit-reverse-comparison.py` verified exact baseline and
update MP4 hashes, bound owner decisions, preserved failures, one locator repair
per method, identical app patches, all 48 matching source files and sequential
timing. `paired-comparison-02/results.json` records the completed results. The
first pair took 296.128 seconds for the director and 118.246 seconds for reshoot.
The elapsed ordering flipped, with review and response waiting accounting for
most of each difference. The repeated known change, agent familiarity and harness
work also limit interpretation; these pairs do not establish a general speedup.
`run-paired-comparison.py` accepts `--pair 02`; its default still targets the
intact first pair. No comparison timer or owner MP4 verdict remains open.

The next local compatibility step completed a
[five-minute continuous-animation trial](docs/validation/2026-10-20-continuous-animation.md).
Run `699111174f9341c6bf2132868e0780ec` produced a 309.333-second, 1280 by 720
final with seven passed checks and zero sampled Vision flags/errors (every ten
seconds). The encoded-motion audit passed, including a held-frame control; all
13 manifest artifact hashes match. The run captured 18,188 browser frames.
Sampled total temporary files peaked at 1.73 GiB and returned to zero; early/late
combined Python RSS medians were 101.6/102.1 MiB. Evidence and the exact video
hash are in `takes/compatibility-20261020/animation-results.json`. Its local
`animation-review/index.html` has a 12-second excerpt video, the full final,
encoded frames and links to the native review bundle and scan sheets. The owner
accepted this exact compatibility recording with “I accept”; bound video and
story-beat decisions are imported and run review is completed. Presentation,
decisions and acceptance receipts are saved beside the results. Separate scan
sheets remain pending. The earlier ten-case and method-comparison acceptances
are complete and unchanged.

[Positive face/person compatibility checks](docs/validation/2026-10-20-positive-detection.md)
also passed: the generated portrait has a face flag, the generated standing figure
has face/person flags, and the no-person control has no flags. The exact contact
sheet was inspected and seven review-file hashes and three retained originals'
pixels were verified. Evidence, both prompts and the unchanged generated images
are under `takes/compatibility-20261020/positive-detection/`; `results.json` records
the technical audit and `index.html` displays the sheet. The first sandboxed
attempt failed in Vision and is retained as `attempt-6efcf1b021ae`; the approved
outside-sandbox rerun `attempt-88cdaccf0392` passed with zero detector errors.
No demo image or human checklist approval is implied by positive detector tests.

The [native macOS window test](docs/validation/2026-10-20-native-window.md) also
passed its technical checks. A disposable AppKit notes app was recorded only by
verified window ID `23641`, owned by its fixture PID. The 10.10-second MP4 is
1864 by 1360, with 362 frames; its 1640 by 1136 window area matches the selected
820 by 568 point window at 2x. Encoded opening/middle/end frames and independent
OCR verify the original notes followed by the saved demo note. Both source MOV
and MP4 decode, all five media/frame hashes match, and one-second Vision sampling
has zero flags/errors across eleven frames. The fixture exited with code 0 and
has no windows remaining. Evidence is in
`takes/compatibility-20261020/native-window/attempt-7a7eb23cf5b2/`; `results.json`,
`presentation.json` and the local `index.html` are in its parent directory.
The owner accepted this exact recording after confirming that the instant text
update is intentional: the native handler redraws the text area, moving existing
notes down when the new note is inserted. `acceptance.json` binds that conditional
verdict and its satisfied condition to the exact MP4/MOV hashes; `results.json`
reports owner accepted. Separate scan sheets remain pending. No other desktop
app or document was used, and no whole-screen capture was performed.

The [controlled service-change trial](docs/validation/2026-10-21-changing-service.md)
has completed its six-case recording matrix. Healthy, three-second delayed,
repaired-schema and restored-format cases each passed a preview and fresh final.
HTTP 503 and an incompatible schema each failed the unchanged search assertion,
retaining failure evidence and producing no final. The fixture-only parser repair
is one line; the story, checks and holds are identical across all cases. Four
finals are owner accepted with “Accept all four”; their bound recording and
story-beat decisions are imported, and all four final runs report review completed.
The local page is `takes/compatibility-20261020/changing-service/review/index.html`.
`acceptance.json` and `acceptance-audit.json` preserve the exact verdict and
unchanged artifact hashes. The owner also approved all four presented full-frame
scan-sheet sets with “Reviewed all, approved.” All 391 sheets (1,562 distinct
images covering 2,380 decoded frames) are recorded checked; their four checklists
report review completed. `scan-acceptance.json` and `scan-acceptance-audit.json`
bind that verdict to unchanged evidence and video hashes. Older trials and other
checklists retain their previous states. All ten CLI runs
are retained in `attempt-94dc59677d9b`. This is a two-origin loopback simulation;
actual changing remote services remain untested.

Broader user/novice acceptance and compatibility evidence remain open in
ROADMAP.md, including broader detection coverage, changing remote services,
other desktop apps, platforms and longer durations. No implementation code change, commit,
push, or publication was performed for these trials. The chronology below
retains earlier states; use the opening status and linked validation records for
current status.

Resumed on 2026-10-20. See the [resume validation](docs/validation/2026-10-20-resume-validation.md)
for host checks, four fixes, all 18 corrected Claude/Codex tasks, and remaining
acceptance work. The [external trial record](docs/validation/2026-10-20-external-trials.md)
describes five synthetic app variants from four authorized GitHub repositories.

The owner accepted all five selected external candidates on 2026-10-20. Their
decisions are imported, and each selected run reports review completed. For a later
resume, start with measured user acceptance in those records. Codex authentication
and external-project selection are resolved. Do not repeat the historical setup
and trials below unless new changes require them.
The [timed pilot](docs/plans/2026-10-20-user-acceptance-pilot.md) now has a first-demo
starter, ten proposed update fixtures, a timing helper, and separate readiness
recordings. The first owner task was photosearch feature-demo creation.
A first owner trial is now complete: the revised photosearch preview and its
39.917-second final were accepted. Recorded elapsed time was 51.77 minutes to
preview acceptance and 57.39 minutes to final acceptance, including repairs and
review waiting. This experienced-maintainer feature task does not establish the
original novice or short single-task target.

The reusable demo follow-up, `feature-demo-v2`, adds a separate caption footer and
native Galaxy year playback. The owner accepted its 45.067-second preview
`1f83c0a50cb04136adb2b2037c9a1151` in the resumed session. Its 30 result checks
passed, sampled Vision scanning completed with no flags, all 72 manifest hashes
matched, and the owner's decisions were imported. Fresh final
`e011b635b6c444a0912ba02560b132ca` is 45.333 seconds at 1280 by 720. Its 30 result
checks passed and sampled scanning completed with no flags. The owner accepted
this exact final in the resumed session; its bound decisions are imported and
review is completed. Supplemental Vision scanning of every decoded final frame,
supplied images, and subtitle text completed with no flags or errors (2,770 frames
and images). Its separate scan sheets retain pending human review; the accepted
run's policy and owner verdict are unchanged. See the
[pilot](docs/plans/2026-10-20-user-acceptance-pilot.md) for current results and limits.
At that point, other apps and the ten-case study were deferred. Local fixtures live under
`/tmp/reshoot-user-trial-20261020/`, with evidence in `takes/user-trial-20261020/`.

The owner then asked to continue. A [standalone photosearch refresh](docs/validation/2026-10-20-photosearch-refresh.md)
now uses the accepted v2 final as its explicit baseline. An isolated fixture
renames the search input and its app references. The unchanged story failed at
`beach-search`; replacing four locator references with the existing accessible
textbox name preserved every beat, expectation, and hold. The repaired preview
passed all 30 checks and sampled scanning. Fresh final
`d2063aba66da4b62a4c4d1331691150a` is 45.317 seconds at 1280 by 720; all 30 checks
passed and sampled Vision scanning completed with no flags or errors. Comparison
matches all 16 beat IDs; only the two search beats change definition. The owner
accepted this exact final, bound decisions are imported, and review is completed.
Recorded elapsed time from the prepared fixture to final acceptance is 354.006
seconds (5.90 minutes), with one repair and no manual video edits. This is one
assisted refresh exercise, outside the ten-case study. Fixture preparation and
active human effort are unmeasured. The separate method comparison follows below.

The owner requested the [existing-method comparison](docs/validation/2026-10-20-recording-method-comparison.md).
Matched short browser baselines are recorded for the original photosearch director
and reshoot; the owner confirmed both baselines and browser-only scope. Both apps
received identical search-input changes before timing. The director update is
accepted, with one locator repair and an additional failed harness port probe
retained in its elapsed time. The reshoot update passed after the same locator
repair; fresh final `acacc778fa79411585c57e0d62991c42` is 9.1 seconds with four
passed assertions and zero sampled scan flags. The owner accepted it; bound
decisions are imported and review is completed. The pair is complete. Elapsed
to acceptance: director 296.128 seconds, reshoot 118.246 seconds; review intervals
215.644 and 57.795 seconds respectively. Most of the elapsed difference is review
and response waiting; this pair does not establish a general speedup. Both needed
one locator repair and zero manual video edits. Evidence and `results.json` live in
`takes/user-trial-20261020/paired-comparison-01/`; timing IDs are
`comparison-01-legacy` and `comparison-01-reshoot`. The ten-case study is unchanged.

The owner then requested the next step and explicitly agreed “Use all ten proposed
cases.” The [ten-case study](docs/validation/2026-10-20-ten-case-update-study.md)
is now agreed, with its full denominator bound to the manifest digest in
`takes/user-trial-20261020/agreement.json`. All original inputs match their saved
hashes and have been snapshotted. The four other app
variants' accepted baseline bindings were reverified. A matching photosearch
baseline, `c35fa09dd7ab466ab60d32fba8baafc0`, passes four checks and sampled Vision
scanning with zero flags or errors. The owner accepted both baseline exports;
bound decisions are imported. The current case's review page is at
`takes/user-trial-20261020/ten-case-study/review/index.html`. Its initial HTML-only
placeholder injection proved ineffective because JavaScript overwrites it; the
same declared wording change was corrected in `core.js`, with a supplemental
fixture patch/hash receipt. All original attempts and elapsed time are retained.
Final `b98e99016b8c4c0e9f0906a8f46e964b` is 8.650 seconds, passes four unchanged
checks and sampled scanning, and visibly shows the new wording. The owner accepted
U01; bound decisions are imported. Elapsed to acceptance was 429.295 seconds,
including 205.545 seconds between review markers and the fixture correction.
U02 is also accepted: final `62d7dfda53c44bcbbde1073957b4f2c8`, 8.483 seconds,
four passed checks, zero sampled scan flags/errors, two old search-target
references repaired, no other demo changes. Its failed initial preview is kept.
Elapsed to acceptance was 143.476 seconds, including 38.474 seconds between review
markers. U03 is accepted: final `0797d66fd54a4d49ae95c26bf9c455ee`, 8.550
seconds, four checks passed, zero sampled flags/errors, every demo input unchanged.
Elapsed to acceptance was 118.964 seconds, including 32.511 between review markers.
U04 is accepted. Its original fixture incorrectly delayed
all internal embedding calls; the unchanged preview timed out waiting for results.
A supplemental adapter correction restricts the same two-second delay to the
actual beach query, with all original attempts and elapsed time retained. The
story, timeouts, checks, captions, holds, configuration, and edit are unchanged.
Fresh final `a9c627a9fccf4bf09cefd48c8b3ac590` is 11.133 seconds with four checks
passed, zero sampled scan flags/errors, and the actual 2,027 ms response retained.
The owner accepted both exports; bound decisions are imported. Elapsed to
acceptance was 214.284 seconds, including 52.987 between review markers. U05 is
accepted: final `2848fce24f9d4aa6969c1a43fb962db4`, 8.800 seconds, three checks
passed, zero sampled flags/errors. Only the Save button-name locator changed to
Publish post; the failed original preview is kept. Elapsed to acceptance was
123.304 seconds, including 30.030 between review markers. U06's timer has started;
its original preview failed at the old textarea ID. Only `#body` was changed to
`#post-body`; the repaired preview and fresh full final passed on generated data.
Final `52c3aa90fa344bcd8a23014827a02d2b` is 8.750 seconds, with three saved-post
checks passed and zero sampled scan flags/errors. Four baseline beat IDs match;
only the write definition changed. Encoded middle/end frames were inspected.
The owner accepted both hash-verified exports with “Accept U06”; bound decisions
are imported. Elapsed to acceptance was 2,062.731 seconds, including 61.791 between
review markers and a long session gap before review opened. Preserve that gap;
elapsed time is not active effort. U07's unchanged-story preview and fresh full
final passed after the app's new-post route changed to `/posts/new`. Final
`14b06510a3494f15aa56ac88035e024e` is 8.767 seconds, with three saved-post
checks passed and zero sampled flags/errors. Four beat IDs and definitions match
the accepted baseline, and all prepared demo inputs are unchanged. Encoded
middle/end frames were inspected; the owner accepted both hash-verified exports
and bound decisions are imported. Elapsed to acceptance was 86.254 seconds,
including 23.951 between review markers. U08's timer has started. Its original
preview failed on the old `/demo/tasks` URL (404); failed run
`e372e86462bb4fd4a2e1b64ed7317142` and screenshot are retained. Only the two
browser URLs and terminal query's database filename were repaired to
`tasks_fixture`; the repaired preview and fresh full final passed. Final
`4af5697f21a542aeaed4d3a269a8b0f9` is 14.017 seconds, with four browser
assertions passed and zero sampled scan flags/errors. Four baseline beat IDs match;
only browse/filter definitions changed. Encoded browser and terminal result frames
both show Pick up the bikes and Buy bread. The longer terminal command wraps onto
two lines. The owner accepted both hash-verified exports with “Accept U08”; bound
decisions are imported. Elapsed to acceptance was 473.316 seconds, including
344.685 between review markers. U09's timer has started. Its original preview
failed at the renamed Completed link; failed run
`0d44b23eeab641cf913ea3a19e54a0ed` and screenshot are retained. Only the link's
accessible-name locator changed to Done. The repaired preview and fresh full final
passed; all four assertions and the other prepared inputs remain intact. Final
`83a440bd4c624a238f425ac5f9d571e0` is 8.033 seconds, with zero sampled scan
flags/errors. Four baseline beat IDs match; only the finish definition changed.
Encoded middle/end frames show the task added and checked under Done. The owner
accepted both hash-verified exports with “Accept U09”; bound decisions are
imported. Elapsed to acceptance was 134.735 seconds, including 42.499 between
review markers. U10's unchanged-story preview and fresh full final passed after
the ES5 heading changed to My tasks. Final `fb7fed99441443779bd2c32abe6c1232`
is 8.033 seconds, with four assertions passed and zero sampled scan flags/errors.
Four beat IDs and definitions match the accepted baseline; all prepared demo
inputs are unchanged. Encoded frames show My tasks and the checked task under
Completed. The owner accepted both hash-verified exports with “Accept U10”; bound
decisions are imported and review is completed. Elapsed to acceptance was 113.188
seconds, including 45.406 between review markers. The study is complete. All case
timers ended on explicit owner acceptance; U01's and U04's fixture corrections,
failed attempts, and all session/review waits remain in their records.
The separate false-count negative control failed as expected (999 versus 1), with
failed expectations and skipped scanning, outside the denominator. The earlier
method comparison remains intact. Final score: ten accepted study cases without
manual video editing. `summarize-study.py` writes the complete results;
`audit-study.py` verifies the closing evidence without changing review decisions.

The original state and instructions below remain the record of the transfer.

This file carries the working context to another Codex account and machine. The
repository contains the code, review, plan, skills, and validation record. Resuming
does not require the previous chat or its machine-local Codex memory.

## Original transfer state

Repository: `https://github.com/mumit/reshoot`

Branch: `main`

The working tree was clean before this handoff. All implementation and validation
documents were committed and pushed. No application change or test process is in
progress. The handoff itself is a later documentation commit.

| Commit | What it contains |
|---|---|
| `98e053e` | Product review, implementation plan, and truthful failure/report fixes |
| `cb7d5ad` | CLI 0.2.0 project workflow, native browser input, shared skills, review, and output improvements |
| `b08055e` | Validation record, platform guidance, and sample Action pinned to the tested implementation |
| `b8b99e2` | Documentation cleanup; last commit before this handoff |

[CI for the implementation](https://github.com/mumit/reshoot/actions/runs/39382679939)
passed on Linux and macOS. It covered browser tests, clean wheel installation and
packaged previews, plus a separate Linux browser-and-terminal notes shoot. The
following documentation-only commits used `[skip ci]`.

## Goal and instructions

The product focus is repeatable software demos that stay current as an app changes.
The main distinction is the update process: check expected results, compare stable
beats across releases, and make the new recording easy to inspect. Claude and
Codex use the same CLI, project files, and skill source. Routine runs need no LLM.

The owner's last implementation instruction was: “Now work through each, only stop
when blocked. Commit and push as appropriate.” That authorized conventional commits
and pushes for this work despite the default restriction in `AGENTS.md`. It did not
authorize public releases, posting, or publishing demo media.

Read `AGENTS.md`, `README.md`, and `CONTRIBUTING.md`. Continue to use only the notes
example or made-up demo data. Never capture the whole screen. Record a headless
browser page, a VHS terminal, or one window by its ID.

Writing should be simple, direct, and natural. Use active voice and first person
where it helps. Avoid fluff, jargon, em dashes, and repeated “I would.” Keep
implemented behaviour, measured results, proposals, and untested claims distinct.
These preferences came from the owner and their local writing guide; that local
file does not need to be present on the new machine.

## Read these next

1. [Delivery status](docs/validation/2026-10-19-delivery-status.md): evidence, limits, and open acceptance work.
2. [Implementation plan](docs/plans/2026-10-19-implementation-plan.md): intended scope and acceptance checks.
3. [Product review](docs/reviews/2026-10-19-product-review.md): the original critique, retained as a dated record.
4. [Project guide](guide/projects.md): current commands and file formats.
5. [Roadmap](ROADMAP.md): next priorities.

The core workflow is implemented. The plan is not fully accepted: live harness
trials, external projects, long-take measurements, and broader compatibility checks
remain open. Do not turn the passing fixture tests into a claim that those trials
have happened.

## Set up the new machine

Clone the repository, or pull `main` in an existing clean checkout. Do not reset or
overwrite unrelated local work. Authenticate to GitHub and Codex with the new
account's own access. Credentials and local dependencies are not in this handoff.

```bash
git clone https://github.com/mumit/reshoot.git
cd reshoot
git status --short
uv sync --extra browser
```

The project requires Python 3.11 or newer and uv. Install ffmpeg, Chrome or Chromium,
and Tesseract. On macOS, ffmpeg and Tesseract can be installed with
`brew install ffmpeg tesseract`. VHS is needed for terminal takes, not the first
browser demo. Window capture requires macOS. Windows has not been validated.

Reshoot uses the installed browser, not a Playwright browser download. Set
`RESHOOT_CHROME` if discovery cannot find it. Playwright is pinned to 1.58.0; record
the actual browser and tool versions on the new machine.

Run the existing checks before changing code:

```bash
uv run --extra browser pytest --ocr-backend=tesseract
uv run --extra browser pytest -m browser --ocr-backend=tesseract
```

The previous local results were **62 fast tests and 22 browser tests passed**. The
browser suite took about 160 seconds. Plugin validation also passed with a warning:
plugin-root `CLAUDE.md` is not loaded as context. Essential instructions are inside
each primary skill. Run `claude plugin validate .` if Claude Code is available.

A fresh synthetic preview on macOS or Linux:

```bash
reshoot_demo_dir=$(mktemp -d "${TMPDIR:-/tmp}/reshoot-resume.XXXXXX")
uv run --extra browser reshoot init "$reshoot_demo_dir"
RESHOOT_OCR=tesseract uv run --extra browser reshoot doctor --config "$reshoot_demo_dir/reshoot.toml" --json
RESHOOT_OCR=tesseract uv run --extra browser reshoot preview "$reshoot_demo_dir/reshoot.toml"
```

The generated app uses port 8765. Reshoot refuses to start if another app is already
answering there. Inspect the actual video and poster, not only browser screenshots.
The reports will still say human review is pending.

## Resume work here

### 1. Validate the installed skills in fresh sessions

The canonical source is `skills/`. The wheel bundles it; the installer copies the
three primary skills without depending on a source checkout. Do not create separate
handwritten Claude and Codex versions.

For an authorized trial project, install the desired bundle:

```bash
uv run --extra browser reshoot skills codex --directory /path/to/trial-project
uv run --extra browser reshoot skills claude --directory /path/to/trial-project
```

Codex receives `.agents/skills/`; Claude receives `.claude/skills/`. Start a fresh
session in that project. The skills are `reshoot-demo`, `reshoot-refresh`, and
`reshoot-review`. Test implicit discovery as well as explicit invocation. In Codex,
explicit invocation uses `$reshoot-demo`; in standalone Claude skills it uses
`/reshoot-demo`. The Claude plugin route remains available.

Repeat creation, refresh, and review three times per harness. Include missing tools,
unavailable capture, an ambiguous selector, and an incorrect expected result. Save
harness/model versions, prompts, interventions, failures, and artifact references.
The new Codex session is an opportunity to test discovery. Do not count merely
reading this file or installing a bundle as a passed trial. If Claude is unavailable,
record that boundary and continue work that does not require it.

### 2. Get external trial projects

The owner has not supplied the three to five project paths or repositories requested
for acceptance trials. Ask for authorized projects with synthetic data and reset
instructions. Include a static app, a backend app, and a browser-plus-terminal flow.
Do not choose unrelated working repositories or real accounts as substitutes.

Measure setup, first acceptable preview, update time, manual repairs, review time,
and successful runs. Compare updates with the maintainer's existing recording
method. The proposed 15-minute and eight-of-ten targets remain unmeasured.

### 3. Check Vision on the new host and broaden validation

Apple Vision failed on the previous macOS 27.0.1 host with
`CRImageReaderError 1`, including probes of recognition revisions. Reshoot reports
that as an error. Tesseract was installed and explicitly selected for successful
text scans. It provides no face or person detection.

Do not silently fall back from a failed explicit Vision scan or claim that
Tesseract validates Vision. Test Vision separately if the new host supports it.
`doctor` reports installed capabilities and versions; it does not probe a final
scan. Add framework-app and long-recording evidence as suitable fixtures become
available.

## Implementation map

| Area | Files |
|---|---|
| Project validation and isolation | `src/reshoot/config.py`, `project.py`, `run.py` |
| Native TOML stories and results | `src/reshoot/story.py`, `browser.py` |
| Legacy Python capture and presentation | `src/reshoot/web.py`, `overlay.js`, `zoom.py` |
| Disk-backed frames and hashes | `src/reshoot/artifacts.py` |
| Privacy checks and source redaction | `src/reshoot/check.py`, `scan.py`, `safety.py` |
| Declarative edits and source time maps | `src/reshoot/timeline.py`, `cut.py` |
| Comparison, HTML, and bound decisions | `src/reshoot/review.py` |
| Speech cache | `src/reshoot/voice.py` |
| Packaged templates and shared skills | `src/reshoot/templates/`, `src/reshoot/skills.py`, `skills/` |
| Regression evidence | `tests/test_failures.py`, `test_project.py`, `test_story.py`, `test_review.py`, `test_edit.py`, `test_distribution.py` |

New versioned projects resolve paths from their config and write separate runs
under `takes/runs/ID/`. Legacy configs retain their old path and `[keep]` behaviour.
Legacy Python actions remain unverified unless their results can be inspected.

Keep execution, expectations, scan coverage, and human review distinct. A successful
run is not approval. Comparisons require an explicit previous run; no baseline
updates itself. Imported decisions must match the run, artifacts, and scan policy.
A CLI or overlay change also needs the affected skills and guide updated.

## Local evidence and what transfers

Git contains everything needed to continue development and regenerate the synthetic
demos. It does not contain the old virtual environments, built wheels, caches, or
temporary generated recordings. Recreate those on the new machine.

An optional archive preserves the previous three-run package trial, its review
pages and media, and the historical trial script:

`takes/reshoot-handoff-2026-10-20.tar.gz` (4.1 MB)

SHA-256: `17e7cf2eddc6d0119bc4013d5ffb674dfbb18ba8695bf4e77128a3074cccf73b`

It contains only generated notes data. It is ignored by Git, so copy it separately
if you want the exact old recordings. Resuming does not depend on this archive. The
script inside records old machine paths; use it as evidence, not as an unchanged
setup script for the new machine. Trial timings and tool versions are already saved
in the delivery status.

## Prompt for the new Codex session

> Read HANDOFF.md and the linked delivery status, plan, and review. Check the current
> branch and working tree. Continue the remaining acceptance work without redoing
> completed implementation. Start with environment validation and fresh-session
> skill discovery. Ask for the missing external project paths when needed, and keep
> untested items explicit. Use synthetic data and follow AGENTS.md. Continue the
> existing authorization to commit and push appropriate work; do not publish releases
> or demo media without my instruction. Use plain, natural writing without fluff.
