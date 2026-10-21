# Recording-method comparison

Date: 2026-10-20

Status: Both assisted maintainer pairs are complete, with opposite timed orders.
The owner accepted each pair's exact baselines and updated MP4s. Reshoot's bound
decisions are imported and native review is completed in both pairs. Elapsed
ordering reversed in the second pair; neither pair establishes a general speedup.
See [Second pair](#second-pair-reverse-order).

The owner asked: “Ok, do the comparison next.” This is one assisted maintainer
comparison, separate from the [completed ten-case update study](2026-10-20-ten-case-update-study.md). It compares the
existing photosearch director with reshoot on the same small browser task. It does
not measure the full launch workflow with VHS, Photos, and multiple edited scenes.

## Matched task and output

Both arms search the generated 73-item library for beach and open its first
result. Their task checks require a beach title, best-matches status, a visible
first result, and the visible lightbox. The legacy Python story performs those
checks through JavaScript waits; the reshoot TOML story uses native assertions.
Both click the search button after typing.

Both use the same three captions, two-second intro/search/open holds, a final
half-second hold, a 1280 by 720 viewport at device-pixel ratio 1, and silent H.264
MP4 at 60 fps with the slow preset and CRF 17. Neither creates a GIF or portrait
export. Both scan the output MP4 with Vision every two seconds. The legacy arm
uses the same scan CLI as reshoot so scan coverage is comparable. There are no
subtitle files in either arm and no supplemental full-frame scans in this pair.

Fresh copies come from the same isolated public-source starter, pinned to
`f73bd0f5dc1b9652f591ccbb1653ab339d45d2a3`. They retain generated thumbnails,
mocked vectors, and the adapter's source/data guards and blocked Photos/model
access. Both reset their own data before every attempt. The recording engines
are unchanged. The legacy director uses its original overlay input; reshoot uses
native Playwright input. Home-page picks, local dates, and typing/cursor behavior
differ between browser environments. Required search results and reading holds
remain the same.

## Baselines

| Method | Recording | MP4 duration | Command time including scan |
|---|---|---:|---:|
| Existing director | `baseline-legacy-0fbc9d5d467d` | 11.367 s | 21.756 s |
| Reshoot | `831e36c20c684b2d9a584aa3e3dcc2cf` | 9.150 s | 16.717 s |

Both baseline scans completed with zero flags and no detector errors. The legacy
director reported no page errors; reshoot passed all four native assertions.
Extracted frames show disclosure captions, matching beach results, and the opened
generated image in both MP4s. The review copies were verified against the original
video hashes. Their different encoded durations are retained, not corrected by
changing either recording engine. These baseline execution times exclude setup,
authoring, troubleshooting, and owner review and do not establish update savings.

## Timed update protocol

After baseline acceptance, each app receives the same search-input rename from
`q` to `search-query`, with its app JavaScript and CSS references updated. The old
story stays unchanged for the first attempt. Preserve failed attempts, diagnose
the failure, repair only the search locator, and record a fresh MP4 with the same
task checks, captions, and holds. The timer ends only after the owner accepts the
exact updated MP4.

The owner replied “Confirmed.” to the paired baseline/scope question. The separate
`baseline-agreement.json` binds that verdict to both original MP4 hashes and the
unchanged protocol digest; reshoot's baseline review decisions were also imported.
Both fixtures then received identical six-file app patches before timing started.

The existing director's unchanged story failed with `nothing matches #q`. Its
only story repair replaces that locator with `#search-query`. A subsequent attempt
failed in the comparison harness's port-availability probe: closed connections
were still in TIME_WAIT, with no live listener. The probe now uses SO_REUSEADDR
and verifies that it can listen; the recording engine remains unchanged. The
failed retry and all diagnosis/correction time remain inside the legacy arm.
The fresh recording `changed-legacy-c665421129be` completed all four JavaScript
task checks with no page errors. Its 11.317-second MP4 scan sampled six frames,
with zero flags and no detector errors. Extracted search and lightbox frames were
inspected; the owner accepted the exact hash-verified review copy. Elapsed time to
acceptance was 296.128 seconds, including 215.644 seconds between review markers.
The review interval includes the local-browser opening approval and owner response
latency; it is not a measure of active watching or human effort.

Reshoot's unchanged story failed at `search` with `action target must match exactly
one element`; the failed run `79a2b76c2b254e58ab77d6c800cc8b08` retained its
failure screenshot, unverified expectations, and skipped scan. After the same
one-locator repair, fresh final `acacc778fa79411585c57e0d62991c42` completed all
four assertions. Its 9.100-second MP4 scan sampled five frames with zero flags
and no detector errors. All four baseline beat IDs match, only the search beat's
definition changes, and expectations/captions/holds remain intact. The search
result text also differs in its transient response-time value (25 ms versus
15 ms); matching IDs do not imply identical pixels. The exact review copy
was accepted by the owner. Bound review decisions are imported and the native
run review is completed. Separate scan-sheet decisions remain pending in both
methods; the owner verdicts apply to the exact MP4s.

The declared order is existing director first, then reshoot. Run them sequentially
so capture, encoding, and scanning do not compete. Each arm includes reset,
startup, failed commands, repairs, recording, encoding, scanning, agent inspection,
and owner review. Fixture preparation and baseline preparation/review are outside
the update timers. Record both whole-arm elapsed time and individual command times.

This existing conversation has substantial knowledge of both tools. The agent
prepares the change and knows its cause, performs diagnosis and repairs, and the
owner judges the result. It is not blind discovery. Familiarity and order can
influence the second arm; one pair cannot establish a general time saving. Active
human effort is unknown and must not be inferred from command or model waiting.

## Recorded results

| Measurement | Existing director | Reshoot |
|---|---:|---:|
| Elapsed to owner acceptance | 296.128 s | 118.246 s |
| Elapsed to presentation for review | 80.256 s | 60.258 s |
| Interval between review markers | 215.644 s | 57.795 s |
| Repair interval, including reruns and scan | 58.421 s | 40.680 s |
| Sum of attempt execution times | 28.760 s | 20.952 s |
| Successful final attempt execution | 21.189 s | 16.166 s |
| Failed attempts retained | 2 (locator + harness) | 1 (locator) |
| Story locator repairs / manual video edits | 1 / 0 | 1 / 0 |

The reshoot arm reached acceptance 177.882 seconds earlier in this pair. The
difference between the review intervals alone is 157.849 seconds. This largely
reflects response latency and the legacy arm's local-browser approval, with no
measurement of active viewing. The legacy harness failure/correction, known
injected change, fixed legacy-first order, and different encoded durations further
limit interpretation. Do not infer a general speedup or subtract guessed overhead
to create an adjusted result. Both methods needed the same one-locator story
repair and delivered the required task without manual video editing.

The first pair is complete as one assisted maintainer observation. The second pair
below reverses its order. Other users, novice setup, and independent comparisons
remain open. The separate ten-case study is complete.
No eight-of-ten acceptance target has been measured by this pair.

## Local evidence

Fixtures: `/tmp/reshoot-user-trial-20261020/paired-comparison-01/`.

Protocol, baseline records, exact review copies, extracted frames, per-attempt
commands/logs, and timing receipts:
`takes/user-trial-20261020/paired-comparison-01/`.

`results.json` records both accepted arms, timing summaries, all five update
attempts, and artifact hashes. `legacy-update-acceptance.json` and
`reshoot-update-acceptance.json` bind the owner verdicts. The native baseline and
final were re-read through manifest verification, both review-copy MP4 hashes
match their originals, all 48 app source files still match between fixtures, and
both story repairs are verified as the single declared locator replacement.

The comparison has its own baseline agreement. It does not create or alter the
ten-case study's agreement. No commits, pushes, publishing, real Photos,
accounts, or whole-screen capture are part of this work.

## Second pair: reverse order

After accepting all ten update cases, the owner requested “Continue.” Fresh
isolated copies of the same pinned source and generated library are prepared at
`/tmp/reshoot-user-trial-20261020/paired-comparison-02/`. The declared timed update
order is reshoot first, then existing director. Both receive the same input-ID
rename and preserve the first pair's task, checks, captions, holds, output settings,
and two-second sampled Vision scans. Local ports are 19534 and 19533. Baseline
preparation is outside the update timers. Both update timers ended on their own
explicit owner acceptance; the director arm started after reshoot's acceptance.

| Method | Fresh baseline | MP4 duration | Command time including scan |
|---|---|---:|---:|
| Reshoot | `3d5acb2424534056adb7de507a4b18a0` | 9.017 s | 15.347 s |
| Existing director | `baseline-legacy-1ddb93b18b61` | 11.317 s | 20.277 s |

The owner reported a vertical colored box in the first reshoot baseline's opening.
Inspection identified a generated portrait image displayed with object-fit contain
in the home slideshow. Both isolated apps received the same one-line fixture CSS
correction to fill that panel using cover. Stories, task checks, holds, captions,
and recording engines are unchanged. All 48 app source files match between arms.
The original baselines, review copies, protocol, feedback, and correction patches
and hashes are preserved under `opening-feedback/`. Both methods were recorded
again; the table above identifies only the corrected candidates now presented.
The protocol discloses this baseline fixture adjustment before any agreement or
update timer. This preparation remains outside the update timers.

Reshoot passed all four native assertions. The director completed all JavaScript
task checks with no page errors. Both sampled scans completed with zero flags and
detector errors. Manifest files and exact review-copy video hashes were verified;
encoded opening/search/lightbox frames show the intended presentation and results. The original recording
engines retain their different cursor, typing, caption timing, and durations.
The owner replied “Accept” to the corrected-baseline/reversed-order question.
The agreement binds that verdict to the protocol digest and both exact MP4 hashes;
reshoot's baseline decisions are imported and review is completed. Identical
six-file app patches were then applied to both fixtures before starting reshoot's
timer, with original stories preserved.

Reshoot's unchanged first attempt failed at search; run
`46eb8980f967435e915b5d70b700ad0c` retains its inspected failure screenshot,
unverified expectations, and skipped scan. Only the `#q` story locator changed to
`#search-query`; all checks, captions, and holds remain unchanged. Fresh full final
`736213a6e44c462eb457b3148022eb32` is 9.067 seconds, passes all four assertions,
and has zero sampled Vision flags or errors. Comparison with the exact accepted
baseline matches four beat IDs; only search's definition changes. Encoded opening,
search, and lightbox frames were inspected. Its hash-verified MP4 is open above
the accepted baseline in `update-review/index.html`. The owner accepted that exact
MP4; bound decisions are imported and native review is completed. Elapsed to
acceptance was 247.200 seconds, including 177.572 between review markers. One
locator repair and zero manual video edits were recorded.

The director arm then started with its unchanged story. Attempt
`changed-legacy-94f48c0461d4` failed with nothing matches #q; the log and failed
attempt remain in its elapsed time. Only its single search-input locator changed
to `#search-query`, preserving checks, captions, and holds. Fresh recording
`changed-legacy-47689211ae1f` is 11.233 seconds. All four JavaScript task checks
completed, with no page errors, and its two-second sampled Vision scan completed
with zero flags and errors. Encoded opening/search/lightbox frames were inspected.
The owner accepted the exact hash-verified director MP4 with “Acceptable.” Its
elapsed time to acceptance was 127.632 seconds, including 74.197 between review
markers. Its acceptance receipt binds the verdict to the original and copied
video hash. No manual video edit was needed in either arm.

| Second pair measurement | Reshoot first | Director second |
|---|---:|---:|
| Elapsed to owner acceptance | 247.200 s | 127.632 s |
| Elapsed to presentation for review | 69.441 s | 53.246 s |
| Interval between review markers | 177.572 s | 74.197 s |
| Repair interval, including rerun and scan | 42.912 s | 30.400 s |
| Sum of attempt execution times | 19.656 s | 30.466 s |
| Successful final attempt execution | 15.168 s | 23.219 s |
| Failed attempts retained | 1 | 1 |
| Story locator repairs / manual video edits | 1 / 0 | 1 / 0 |

The closing audit reverified both baseline agreements and exact update copies,
the native manifests and review binding, four native result assertions and four
matched beat IDs, each minimal story repair, both failed attempts, identical app
patches, all 48 matching app source files, and sequential timing. Both final
sampled scans have zero flags or errors; their separate scan sheets remain
pending. The local update page now identifies the director recording as accepted.

| Pair and timed order | Reshoot elapsed | Director elapsed | Reshoot review interval | Director review interval |
|---|---:|---:|---:|---:|
| 01: director, then reshoot | 118.246 s | 296.128 s | 57.795 s | 215.644 s |
| 02: reshoot, then director | 247.200 s | 127.632 s | 177.572 s | 74.197 s |

The elapsed ordering flips: reshoot reached acceptance 177.882 seconds earlier
in pair 01; the director reached acceptance 119.568 seconds earlier in pair 02.
The review-interval differences are 157.849 and 103.375 seconds respectively.
These intervals include response waiting and, where needed, permission to open
the local review page. They do not measure active viewing. Pair 01 also includes
a director harness failure; pair 02 includes the already known repeated task and
baseline fixture styling correction before timing. Do not subtract estimated
overhead, pool these two observations into a causal saving, or infer human effort
from command times. Both methods delivered the required task after one locator
repair per arm and without manual video editing.

The agent and owner already know this change from earlier trials. Reversing order
does not remove repeated-task learning or turn these observations into novice or
independent-user evidence. Keep all failures and owner response waiting in each
arm's elapsed time; do not infer active human effort or a general speedup.

Protocol, attempts, hashes, extracted frames, and baseline copies are under
`takes/user-trial-20261020/paired-comparison-02/`. The review page is
`baseline-review/index.html` there. `results.json` retains second-pair timing,
attempts, hashes, owner verdicts, and limitations; `audit-reverse-comparison.py`
reverifies its evidence without changing decisions. The completed first pair and
ten-case result are preserved unchanged.
