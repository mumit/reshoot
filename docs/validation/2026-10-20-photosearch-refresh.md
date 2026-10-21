# Standalone photosearch refresh

Date: 2026-10-20

Status: The owner accepted the fresh final. Bound decisions are imported and the
run reports review completed. The original accepted baseline is unchanged.

After accepting the reusable photosearch feature demo, the owner asked to continue.
This exercise refreshes that demo after a search-input rename. It is separate from
the deferred ten-case study and contributes no eight-of-ten result.

## Baseline and fixture

The explicit baseline is accepted final `e011b635b6c444a0912ba02560b132ca` from
`starter/reshoot_trial/feature-demo-v2/takes/runs/`. Its bound owner decisions and
all 74 artifact hashes were verified before preparing the new fixture.

The new fixture is `/tmp/reshoot-user-trial-20261020/refresh-search-id-01/`, copied
from the existing isolated public-source starter. Its source pin is
`f73bd0f5dc1b9652f591ccbb1653ab339d45d2a3`. Source/data assertions, blocked Photos
and model imports, generated thumbnails/vectors, and disabled Photos operations
remain in the local adapter. Every attempt resets its own generated index, smart
albums, and Galaxy layout. The app uses loopback port 19521; the baseline used
19475. The original fixture and accepted recordings remain intact.

All six current demo input files were checked against the accepted final's saved
input hashes before copying. Infrastructure changes are the fixture directory and
port. The local brief also names the explicit baseline and exercise scope.
Caption text, footer composition, native input speed, holds, and intended task
remain unchanged.

The injected app change renames the search input from `q` to `search-query` and
updates its JavaScript and CSS references. Six app files change. This keeps the
app working while exposing the old storyboard's `#q` locator.

## Attempts and repair

| Attempt | Result |
|---|---|
| `adb34df502664e1899e1446ec08a2b6e` | Unchanged preview failed at `beach-search` in 16.3 s: its action target matched no element. The opening assertion passed, aggregate expectations remain unverified, scanning was skipped, and no successful export exists. Failure image, metadata, and report are retained. |
| `335ba43af35a463a8c9a0d63e8efbc98` | Repaired preview completed in 63.3 s. All 30 expectations passed. Sampled Vision scanning and exact subtitle scanning completed with no flags or detector errors. Human review remains pending. |
| `d2063aba66da4b62a4c4d1331691150a` | Fresh final completed in 84.7 s. Silent MP4: 45.317 s, 1280 by 720. All 30 expectations passed; sampled Vision scanning and exact subtitle scanning completed with zero flags and no detector errors. The owner selected “Accept this final”; bound decisions were imported and review is completed. |

The repair changes four action-target references in two beats from CSS `#q` to
the existing accessible textbox name, `search`. Structured comparison verifies
that every expectation, stable beat ID, action, hold, and other story setting is
preserved. The caption cues, compositor, and pacing policy remain unchanged.
Extracted preview frames show beach results, Galaxy progression, and the saved
Beach discoveries album. Eight extracted final frames also show readable footer
captions, look-alikes, Time Machine, and the saved album. All 73 final artifact
hashes were verified.

The saved comparison matches all 16 beat IDs, with none added or removed. Only
`beach-search` and `return-to-beach` change definition because their search targets
changed. Four beats have different recorded result values: the isolated app uses
a different local URL, and search status shows 4 ms rather than the baseline's
7 ms. Their original expectations still pass. The fresh Galaxy layout also changes
its visual arrangement; no pixel-equivalence claim follows from matching IDs.

The final's Vision check covers supplied images, video sampled every two seconds,
and exact subtitle text. Its 72 supplied items retain pending sheet review. This
is not a full-frame scan of the new final; the earlier baseline's supplemental
scan does not transfer coverage or acceptance. The owner watched the opened final
and accepted it. Agent inspection used extracted frames. The separate image-sheet
review retains its existing state; final acceptance is recorded through the run's
normal bound-decision import.

## Measurement limits and evidence

The owner uses this existing Codex conversation; the agent prepared the fixture,
knew the injected change, diagnosed it, and repaired it. This is an assisted
maintainer exercise, not blind discovery or novice setup. The exact serving model
and reasoning setting are unknown; the owner's configuration was retained.
Reshoot is 0.2.0. Capture uses the installed headless Chrome and explicit sandbox
escalation. No whole-screen capture, real Photos data, or accounts are involved.

The local timer `photosearch-refresh-search-id-01` starts after fixture preparation
and doctor checks. Preparation time is unmeasured. One preparation attempt stopped
because it assumed final runs contained source copies; the incomplete fixture is
preserved separately. The corrected preparation verifies saved input hashes before
copying current source inputs. This was resolved before refresh timing.

The timer records repair and render intervals and the explicit final verdict.
Recorded elapsed time to final acceptance is 354.006 seconds (5.90 minutes),
including 92.699 seconds in the repair interval and 63.699 seconds in final review.
The final-rendered mark is at 240.729 seconds. There is one repair episode and no
manual video editing. No separate owner preview acceptance was requested or
recorded; first-acceptable-preview time remains unmeasured. Command/model waits
are part of elapsed time; active human effort is unknown. These measurements
exclude fixture preparation and do not establish a comparison with the existing
recording method. The known semaphore-cleanup warning appeared after capture;
the repaired preview and final run reports have no errors.

Recipes, app and storyboard patches, saved repaired inputs, fixture metadata, and
extracted frames are in `takes/user-trial-20261020/refresh-search-id-01/`. Run
directories live under the fixture's `reshoot_trial/feature-demo/takes/runs/`.
The original ten-case manifest and its proposed agreement status are unchanged.
