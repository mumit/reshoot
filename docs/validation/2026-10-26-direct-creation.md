# Direct creation and editing

Implementation follows the [execution plan](../plans/2026-10-26-direct-creation.md)
and uses synthetic notes projects only. This record covers implementation
checks and maintainer-operated inspection, not outside-user research or an
owner's acceptance of any recording.

## Focused workspace

Commit `9200468` adds a keyboard filmstrip and one selected-step inspector.
Selection survives a page reload, normal blur-save completes before switching,
and an invalid unsaved step stays selected until corrected or reset. The
original story remains readable without JavaScript. Existing narration,
screenshots, cut, style and review controls remain available.

Verification: 42 focused fast tests and 3 browser journeys passed, including
keyboard/mobile selection, invalid-field recovery, caption re-cutting and
first creation through correction, restart and final review. Desktop and
390 px headless browser page views were inspected.

## Representative layout stills

The still renderer reads a complete recording's clean take and uses the
production caption painter, shared browser-window artwork/filter and export
geometry. Draft caption, colour, frame and crop changes do not change the
saved recording or its review. The inspector distinguishes layout feedback
from playing the recorded video; full updates still verify timing and task
changes. Missing clean takes and custom Python edits have explicit limits.

One render at a time, bounded ffmpeg calls and bounded in-memory caches keep
feedback work contained. Saved-source revisions and recorded media are checked
before and after rendering. The client ignores late responses, retains draft
fields, and releases replaced image URLs. Fonts configured in the project
are drawn by the same font loader and included in the still cache identity.

Verification: 61 focused renderer/editor fast tests passed. Eight still tests
cover comparison with encoded production output, geometry, cache reuse,
invalid requests and external edits during rendering. Four browser journeys
passed across the live-feedback trial and existing playback, framing and
history regressions. A deliberately delayed older caption response did not
replace the newer still; neither did a still replace the pinned video/run.

On the local notes fixture, the first still request took **72.1 ms** round
trip. Eight different warm captions took **8.4–9.1 ms**, median **8.75 ms**;
three framed stills took **62.8–64.3 ms**. These are local HTTP timings for this
recording, excluding the UI's 240 ms input debounce, and are not a general
performance guarantee. Source and run-file hashes remained unchanged.

The visual gallery was rebuilt and inspected after extracting the shared
window renderer. A Midnight frame was pixel-identical; sampled frame/caption
images differed by less than 0.3 per channel on average, consistent with
capture-timing differences. Encoded renderer comparisons on identical input
also passed. Generated gallery differences were preserved under ignored
`takes/direct-20261026/gallery/` and restored from the tracked gallery.

Local scripts, screenshots and latency data are under ignored
`takes/direct-20261026/`, including `layout_trial.py` and `layout.json`.
No accepted exports under `docs/demo/` were changed. Nothing was accepted on
the owner's behalf, pushed or published.

## Starting recipes

Feature highlight, Task walkthrough and Release update set pace, look and
export choices. They preserve actions, result checks, narration, current cut
ranges and existing cards. Recipes with cards add an opening and closing only
when there are none. A three-file application validates everything before
writing and rolls back its own writes if a later replacement fails. Undo/Redo
groups the studio application. Deliveries named by `[keep]` cannot silently
lose their export.

`create --recipe` remembers its choice and applies it once after demonstration.
After a failed preview, resuming preserves subsequent edits rather than
reapplying the recipe. `recipe list` and `recipe apply --dry-run` let CLI users
inspect choices. Applying a style or recipe shows its still immediately while
keeping the original recording; a new run returns to recorded-video playback.

Verification: 35 recipe/creation/setup/docs fast tests and the connected
browser journey passed. It created with Feature highlight, applied Task
walkthrough in the studio, undid/redid the grouped edit, then recorded the
same three passing task checks with the new presentation and no GIF export.
A fresh CLI Release update also produced MP4/GIF exports with all three task
checks passing. Its opening card was extracted and inspected; review remained
pending. The recipe targets are pacing guides, not guaranteed final lengths.

## Following stage

Reviewed step demonstrations are the final stage in the plan. Outside-user
testing remains deferred.
