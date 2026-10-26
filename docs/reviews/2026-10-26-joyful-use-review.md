# Upstream review: making reshoot joyful to use

Reviewed on October 26, 2026, at `62f387f`, covering the 29 upstream commits
after `7621431`. This is a product, architecture and persona review supported
by source inspection, synthetic reproductions and browser checks. It is not
an independent usability study or an owner's acceptance of any recording.

## Assessment

The upstream work improves the experience substantially. The shorter entry
points, a dedicated studio guide, useful failure explanations, suggested
replacement controls and fewer unavailable panels all reduce the effort of
getting started. Waiting for the first captured frame and naming stalled
Chrome operations also address failures that otherwise feel arbitrary.

The product now has enough features to make a useful quick demo and to refine
one considerably. Its weakest point remains the effort of understanding what
to do next when creation fails, a session reopens or a recording is ready to
keep. More creative controls should follow a more dependable core journey.

## Findings to fix first

### P1: recording ordinary button names can produce an invalid story

In [rec.py](../../src/reshoot/rec.py), lines 260–264, the new readable beat IDs
count each base name independently without reserving the IDs already emitted.
Recording clicks on `Save`, `Save`, then `Save 2` writes `click-save`,
`click-save-2`, `click-save-2`. Loading the generated storyboard fails with
`beat IDs must be unique letters, digits, underscores, or hyphens`.

This stops the demonstrate-and-preview path after the user has done the work.
Keep the readable names, but allocate each against a set of all emitted IDs,
including the reserved ending ID. Check both ordering directions of a
numbered name and a repeated name.

### P2: the final handoff can point to a different recording

In [run.py](../../src/reshoot/run.py), lines 408–421, the new closing instructions
use `PROJECT/latest` for review and acceptance rather than the completed run's
folder. That alias resolves to the newest successful recording, including a
preview, as implemented in [review.py](../../src/reshoot/review.py), lines 14–16
and 45–60.

If someone watches final A, makes preview B, then follows A's printed command,
acceptance targets B and refuses it as a preview. If B is another final, the
command instead asks about that different final. Human confirmation still
exists; the problem is that the instruction has lost its association with
the video just watched. Synthetic run reports reproduced the alias changing
from the watched final to the later preview.

Print the exact run folder in a completed run's review and acceptance commands.
Keep `latest` for commands whose explicit purpose is to select the newest run.

### P2: fixing the first preview recommends a disabled action

In [studio.py](../../src/reshoot/studio.py), lines 1016–1028, the failed-check
message correctly says **Continue creation** when creation is pending. After
**Remove this check**, the failure becomes stale and the message changes to
**Update preview**. That button remains disabled during creation at lines
1407–1408. The enabled action is still **Continue creation** in the tools panel.
The repaired-control branch has the same unconditional wording.

This was reproduced in the browser with a pending creation and a deliberately
wrong notes count. The current first-preview browser test starts with `init`
and `preview`, so it does not exercise the saved `create` state. The alternate
continuation did produce a working preview; the user is given conflicting
guidance rather than being completely blocked.

Derive the recovery instruction and the enabled button from the same next
action. Cover removal, repair and other edits while first creation is pending.

### P2: repeated failures hide the last working repair reference

In [run.py](../../src/reshoot/run.py), lines 168–176, `earlier()` slices the five
newest runs before filtering for successful runs. Five recent failures
therefore hide the last successful capture. Without an accepted baseline,
the new fingerprint-based repair loses the reference it needs to recognize a
renamed control, just when repeated attempts make assistance most useful.

A synthetic history of five failures followed by one successful final
reproduced an empty earlier-run list. Filter eligible successful runs first,
then limit their number. Test a history containing several failures and no
accepted baseline.

## Product and persona review

These are design judgments and remaining limitations, separate from the
reproduced defects above.

| Person and goal | What is better | What still costs effort |
|---|---|---|
| First-time maker: get one useful clip | The notes path is short; unavailable panels disappear; tool checks collapse when ready. | Recovery still changes its vocabulary and next action. A user can complete the recording and receive a file-validation error they cannot fix by pointing. |
| App developer with an agent: demonstrate a real task | The README now describes an honest agent-led route; URL briefs describe the target app correctly. | The first useful result still depends on the agent establishing good demo data and meaningful checks. A successful bundled example alone does not establish success on the user's app. |
| Returning author: refine and resume | Captions, holds, Undo, reusable looks, framing and narration provide substantial control. | Matching saved history still requires a blocking Resume history / Start with current files decision. The recovered preview exposes ten navigation destinations even for a small clip. |
| Author seeking professional polish | Several formats, framing, readability feedback, audio and comparison are valuable foundations. | The creative loop still requires saving, rendering and inspecting. Feature count does not establish pacing, readability or professional creative quality. |
| Maintainer or reviewer: trust what is kept | Checked results, scan evidence and studio decisions associated with the displayed run remain strong foundations. | The CLI handoff's moving alias weakens that association. A failed check is easier to remove than to correct in the studio. |

The next design work should concentrate on three moments:

1. **Recover without losing the task.** Show what happened and one working
   next action beside it. Let the author correct a check's expected result
   before making removal the easiest in-studio edit. Explain what the check
   proves; retain removal and Undo for genuinely wrong suggestions.
2. **Make small edits feel immediate.** Keep the preview, selected step and
   relevant controls together. Show the saved change and whether a render is
   needed. Use the existing re-cut path when possible, retain advanced tools
   behind deliberate entry points, and preserve the last working preview
   during an update. Do not make captions, timing, audio and optional tours
   compete equally for a first-time maker's attention.
3. **Make finishing unmistakable.** Keep review and local delivery attached
   to the exact final. Show the few remaining decisions in place. Automatically
   resume history when its files match; show recovery choices when there is
   an actual mismatch or unreadable history.

## Architecture and execution order

The contradictory recovery instruction is a symptom of state being interpreted
in several places. `creation_pending`, repaired/stale failure state, session
recovery, source freshness and the current job independently affect messages
and controls. `journey.py` already centralizes part of this; the studio then
adds its own state-specific decisions.

Extend that shared model to return the next action, its label, its availability
and the reason for any block. Have the header, status card and failure panel
consume that result. Keep existing exact-run artifact checks and reversible
edit operations. This can be a small extraction rather than a studio rewrite.

Recommended order:

1. Fix the four reproduced defects with focused regressions.
2. Consolidate the next-action logic and remove the routine matching-history
   interruption. Exercise first creation, failure, repair, restart, saved edits
   and final review as connected journeys.
3. Improve check correction and the selected-step editing loop. Keep optional
   deliverables and deeper polish available without making them prerequisites.
4. Resume paired video comparison after these transitions are dependable.
   Build on the existing selection of exact runs and checked frames.

Judge each stage by observable outcomes: reach a useful preview without
reference reading, recover from a bad check without editing TOML, reopen an
unchanged project directly, see which saved edits need rendering, and keep
the same final that was reviewed. Record completion time, failed attempts and
documentation lookups as future measures; no new novice baseline was measured
in this review. Outside-user testing remains deferred under the existing plan.

## Verification and limits

- Complete fast suite: **270 passed, 57 deselected**.
- Four affected browser tests: **4 passed**. They cover first-preview failed
  checks, renamed-control suggestions, result-hold video evidence and hidden
  tab counts. The complete browser suite was not rerun.
- Separate synthetic reproductions confirmed all four findings. No acceptance
  command was executed for the alias reproduction.
- The first-create fixture recovered through `create --resume --no-studio`:
  a preview completed in 15 seconds, with 2 of 2 remaining result checks
  passing and 6 scan items, none flagged. Those results are automated evidence,
  not an owner's visual or privacy verdict.
- Desktop and 390 px browser pages were inspected. Matching history required
  an explicit decision; the mobile document had no horizontal overflow.
- Local scripts, reports and page screenshots are under ignored
  `takes/ux-review-20261026/`; test and reproduction logs are under `/tmp/`.
  All data was synthetic. No recording was accepted, published or pushed.

No production source was changed during this review. The findings describe
the merged checkout; the recommendations have not been implemented.

Follow-up: [implementation and validation](../validation/2026-10-26-joyful-creation.md)
records the subsequent work on this plan.
