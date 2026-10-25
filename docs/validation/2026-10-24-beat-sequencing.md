# Beat trimming and sequencing

On 2026-10-24, the local macOS checkout was exercised with synthetic notes data
to verify the beat trimming and sequencing milestone in the [creation and
revision plan](../../UX_PLAN.md). These are automated and agent-operated checks,
not independent-user research or owner acceptance of media.

## What changed

Your cut in the studio selects From and Through beats, moves parts earlier or
later, duplicates or removes them, and adds another recorded clip. CLI
`reshoot sequence` uses the same operations. Each studio operation is one undo
step. Unsaved ranges must be saved or reset before other edits or updates.

The edit's `through = "search"` includes that beat's end and result hold;
`end = "search"` remains exclusive. Named boundaries follow the timing of a
fresh recording. Numeric custom boundaries stay intact until explicitly
replaced. Nested custom part tables remain available through file editing.

The storyboard still executes the complete task in its original order and
verifies its result checks. Only the video sequence changes. Cuts cannot split
spoken lines. Repeated captions, subtitles and complete narration map to the
new output times. The studio maps every appearance, identifies omitted beats
and plays each cut part, including title cards, after an updated preview.

Source revisions and recording evidence are rechecked before replacement.
Concurrent storyboard or style edits cannot become part of a sequence undo.
The default CLI source is the latest complete successful run; partial previews
are skipped. Explicit partial runs and changed evidence are rejected.

## Fresh notes CLI trial

Evidence is under the ignored `takes/sequence-20261024/` directory. Its
`trial.py`, `trial.json`, command logs and sampled part frames retain the exact
steps and timings. The documented CLI commands produced this order:

1. Search through search, showing the result.
2. Intro through add, showing how the note was created.
3. Search through search, showing the result again.

| Stage | Evidence |
|---|---|
| Baseline preview | Run `9eda5b25e9514e698e50e55bad79481b`; 16.5 seconds; all 3 checks passed |
| Range, add, duplicate and move | Each command took less than 0.4 seconds |
| Re-cut | Run `1b51686e202a45398ba11d658e69a125`; 5.8 seconds; all 3 original checks retained, 8 scan items, 0 flags |
| MP4 | 720x404, 11.55 seconds |
| GIF | 800x450, 11.54 seconds, 173 frames |

The storyboard bytes and clean recording hash
`fba857d87f501f36bcc813a83f530b57f1cbd308aa1381670c38c4560245e065`
were unchanged. The three output-part intervals were retained in the final
map. Frames from each part confirmed result, creation, result. The studio
layout and part playback were inspected. The [gallery](../../guide/look.md#beat-cuts-and-sequence)
includes a rebuilt example of this sequence. No sample was accepted or published.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 150 passed, 44 browser tests deselected |
| Affected sequencing, style and studio browser suite | 3 passed |
| Final focused sequencing browser trial after project revision refinements | 1 passed |
| Gallery build | Rebuilt from notes, including an outcome-first sequence |
| Changed-document links, anchors, images and TOML examples | 119 references and 22 snippets or alternatives checked |
| Python compilation, JavaScript syntax and whitespace checks | Passed |
| Wheel build and plugin validation | Passed; plugin validation retains existing root context and missing icon warnings |

The regressions cover inclusive result holds, exclusive end compatibility,
invalid or reversed ranges, unknown takes and positions, preserving at least
one part, comments, exports and task files, stale source edits, changed
recording evidence, default selection after partial previews and narration
boundaries. A rendered synthetic colour sequence verifies ordered part maps,
cards and repeated subtitles in both the main movie and an export.

The browser trial verifies Save/Reset, blocked updates with unsaved choices,
stale tabs, undo/redo, moving and duplicating clips, re-cutting a verified
recording, playback of the second occurrence, repeated timeline markers,
omitted beats and absence of JavaScript errors.

## Limits and following work

Studio ranges snap to complete recorded beats; frame-level trims and nested
custom tables remain file operations. Undo history lasts for the server
session. CLI edits have no persistent undo stack. Other takes can be added to
the cut, while the story editor continues to shape its first browser take.

The checks describe the full recorded task, including omitted beats; they do
not independently judge whether a shortened or reordered video tells a clear
story. Inspect the actual MP4 and GIF before keeping the cut. No Linux or
Windows trial or independent-user study was added. Destination readability
feedback and convenient narration/audio controls remain following milestones.
