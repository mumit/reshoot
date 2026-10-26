# Creation, recovery and paired playback

On October 26, 2026, the local macOS checkout implemented the ordered plan
from the [upstream UX review](../reviews/2026-10-26-joyful-use-review.md).
All verification used synthetic notes projects, generated media or test
fixtures. This establishes working controls and recovery behavior, not
independent evidence of enjoyment or professional creative quality.

## Delivered behavior

| Moment | Result |
|---|---|
| Demonstrate a task | Readable step IDs stay unique when repeated and numbered control names collide. The recorded actions remain intact. |
| Finish a CLI run | Its review and acceptance instructions name that exact run, even when a newer preview or final arrives. |
| Recover a first preview | Recording controls, the status and failure guidance share one next-action decision, including creation, missing tools and saved-history recovery. |
| Retry after repeated failures | Repair selects earlier successful runs before limiting the reference list. |
| Reopen a project | Matching Undo/Redo history attaches automatically without rewriting the checkpoint. Changed files with meaningful history, unreadable checkpoints and competing changes retain their protections. An empty history adds no recovery decision. |
| Correct a bad expectation | Edit its expected count, text, address, field value or ticked state in place. The target, actions, neighboring checks and comments remain intact. Undo/Redo covers the correction. A fresh preview must verify it. |
| Refine a step | A selected-step bar names the step beside the preview, offers playback and returns to its fields. It distinguishes saved changes from the recorded version. |
| Find optional features | The main navigation keeps Preview, Story, Cut, Look, Review and Download. More tools holds comparison, audio, screenshots and tours, and closes after a section is chosen. Mobile links wrap rather than hiding the menu off screen. |
| Compare revisions | Choose a rendered MP4 or MOV on each side, start or pause both, and choose which side to hear. Step seeking follows each export's saved cut map, including trims and repeated appearances. |

Check explanations and corrections live in `expectations.py`; next-action
decisions extend `journey.py`; export selection and mapped playback live in
`playback.py` and `playback.js`. The studio remains the page/server adapter.
Existing reversible edits and checks of the displayed run remain in use.

## Connected browser journey

The new browser regression starts a notes creation with a deliberately wrong
expected count. It corrects that value through the studio, continues the
saved creation and verifies all three original task checks. It then changes
a caption, verifies that Update preview reuses the existing clean capture,
restarts the studio with Undo still available and no recovery prompt, and
records a fresh final ready for review. The original task actions and all
three checks remain; the final's review stays pending.

Existing browser journeys also cover first-preview check removal, external
edits, history recovery, setup failures, cancellation, styles, framing,
narration, documentation screenshots, offline tours and local downloads.
The wider narration trial exposed an unnecessary recovery choice after an
external edit to an empty history. That was corrected and the narration
journey passed on rerun.

## Playback verification

- Verified export media and scan state remain associated with each chosen
  run. Video requests support byte ranges and check the served bytes again.
- Trimmed steps map to their surviving interval. Repeated steps retain every
  appearance. Added or removed steps do not gain invented counterparts.
  Temporary title-card sources do not become recorded steps.
- Each side plays at its own timing and stops at its own step end. This is
  simultaneous playback, not frame synchronization or time stretching.
- The browser exercised Play both, Pause both, audio selection, step seeking,
  step-end stopping and pausing when the comparison panel closes.
- Creating a newer successful run did not switch the displayed pair, either
  player, result frames or review links.
- Changed media, changed scans, invalid cut intervals and attempts to request
  a raw take through the export route are rejected. Missing or unlisted cut
  maps leave ordinary video controls available without claiming step timing.

## Results

| Check | Result |
|---|---|
| Final complete fast suite | **300 passed, 59 browser tests deselected** |
| Focused playback/comparison fast suite | **15 passed** |
| Affected studio browser journeys | **13 passed**, split into 9 passing cases before the empty-history fix and 4 passing remaining cases after it |
| Paired playback browser journey | **1 passed**, including real encoded notes videos, audio, seeking, newer-run arrival and mobile layout |
| Final navigation/playback browser rerun | **2 passed**, after grouping playback controls and closing the optional-tools menu on selection |
| Final correction/playback browser smoke | **2 passed**, including the finished correction form and stopping playback on a middle step before either video ends |
| Final correction/history/editor fast checks | **37 passed** |
| Visual inspection | 1280 px and 390 px headless browser page views; no page script errors or horizontal document overflow; selected-step context and grouped playback controls inspected |
| Source/media preservation during visual inspection | Project source and run-file hashes unchanged for both the editing and comparison projects |
| Documentation checks | 48 local links/anchors and 2 TOML examples checked, including this record and the completed plan |
| Compatibility and packaging | Python 3.11 syntax checked; studio, comparison and playback JavaScript syntax checked; wheel built offline with the new modules and scripts included |
| Plugin validation | Passed with existing root-context and missing-icon warnings, plus marketplace-install advice |

Local artifacts are under ignored `takes/ux-plan-20261026/`: the browser
projects, a copied comparison project, `visual_trial.py`, desktop/mobile page
screenshots, `visual.json` and the wheel. Logs are under `/tmp/reshoot-plan-*`.
The earlier bug reproductions remain under ignored `takes/ux-review-20261026/`.
No owner media was accepted, accepted exports under `docs/demo/` were not
changed, and nothing was pushed or published.

## Limits

Only exported MP4 and MOV files participate in paired playback. GIFs and
other deliverables remain available through their existing inspection and
download controls. Step seeking requires a saved, listed export timeline
and identifiable recorded takes; older videos can still be compared manually.
Repeated appearances are paired by their order in each cut, which may require
choosing another appearance after a substantial reorder.

Several browser fixtures disable OCR for speed. Automated checks and rendered
page inspection are not an owner's privacy or visual verdict. The complete
browser suite was not run; the 14 distinct affected studio/comparison journeys
were exercised. Export rendering was unchanged, so the visual gallery did
not need rebuilding. No Linux/Windows run or outside-user trial was added.
Outside-user testing remains deferred under the existing plan.
