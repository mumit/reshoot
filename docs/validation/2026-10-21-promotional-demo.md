# Promotional demo refresh

Status: the owner accepted all three local social MP4 and README GIF/MP4 exports
with “I approve.” The README uses the new GIF and links the social MP4. Original
notes media remain unchanged. The owner separately approved both promo scan sets
with “Reviewed both promo scan sets; approved.” Both checklists report review completed.
The owner authorized local checkpoint commits after completing both reviews.
Nothing has been pushed or published.

The previous 21.58-second video introduced the notes app, demonstrated `echo` and
`cat`, and ended with “Notes.” Its 9.34-second GIF showed the add-and-search task.
Neither showed rerunning a story after an app changed. The owner agreed to a new
story built around that benefit before setting up a different-machine trial.

## Recipe and task

The versioned recipe is `examples/promo/`. Two synthetic notes pages share the
same JavaScript, selectors and TOML storyboard. The second version changes its
heading to “Notes, refreshed.”, its button to “Save note,” and its CSS. The story
adds “Pick up the bikes” and searches for “bike.” Six assertions verify the
original count, saved note/count and final matching note/count. No locator repair
or assertion change is needed for these selected UI changes. This does not claim
that arbitrary UI changes require no storyboard repair.

Both app versions have a preview and fresh final. The updated final is generated
by the actual command typed in VHS: `reshoot run examples/promo/release-v2.toml`.
A clean terminal wrapper sends raw diagnostic output to a retained local log and
prints a short summary derived from the actual resulting run report. It does not
display host paths, personal prompts or shell history. The terminal run took
12.535 seconds. The social cut retains the command typing and actual completion,
omits the wait, and labels “Generation wait omitted.” Its duration is not a
generation-time or speedup measurement.

Only headless browser pages and a clean VHS terminal were captured. There is no
whole-screen recording, real account or private data. The promotion is authored
and edited; the app footage has no speed-change filter. The README aligns native
beat boundaries with end holds and retains its original app take files. Native
beat timestamps and encoded raw duration differ by approximately 0.62 seconds in
the updated take; exact capture-to-encode timing fidelity is not established by
this promotional trial. All task results remain visible in the encoded ending.

## Local candidates

| Export | Duration | Dimensions | Size |
|---|---:|---:|---:|
| Social MP4 | 21.23 s | 1080 by 1350, 30 fps | 347,320 bytes |
| README GIF | 9.33 s | 960 by 640, 12 fps | 477,311 bytes |
| README MP4 companion | 9.37 s | 1200 by 800, 30 fps | 136,584 bytes |

The social story opens with “Your UI changed. Update your demo,” reveals the
updated UI, shows the real command, plays the updated task, compares both results
and ends with reshoot and its repository address. The README loop plays the same
task in both app versions together. Both have text explaining the benefit without
audio. Their appeal and engagement have not been measured on social platforms.

The first composition passed technical checks, but visual inspection found a
crop across the opening search field and drift between the independent takes.
That composition remains under `initial-cut/`. The refined edit keeps the full
search fields, reveals the updated version and aligns the README beat boundaries
with holds. No app footage was rerecorded or sped up for those changes.

## Evidence

Ignored evidence is under `takes/promo/attempt-b6912829e9eb/`:

- `recording.json`, doctor/version output, commands and logs retain all four
  captures and the real VHS command run.
- `source-recipe/` and `inputs.json` retain the exact initial recipe bytes and
  hashes. `edit-recipe-*/` records each composition revision.
- `comparison.json` matches all four native beat IDs and definitions.
- `terminal-full.mp4`, `terminal-cli.log`, the generated shell/tape and
  `terminal-result.json` retain the command evidence and its actual result.
- `exports/`, edit maps, `results.json` and `review/` contain the three candidates,
  media audit, independent terminal OCR, extracted encoded frames and local page.
- `acceptance.json` binds the owner's exact verdict to all three export hashes
  and the unchanged presentation. `acceptance-audit.json` verifies those exports
  and the local README copies. `acceptance-evidence/` preserves the pre-verdict
  results and presented pages. The verdict covers the edited exports, not a
  separate approval of their raw source takes or human scan checklists.
- `full-scans/social/` and `full-scans/readme/` retain full-frame Vision scanning
  of the exact social MP4 and README GIF plus their caption text. Automatic scan
  results and separate human checklist decisions must be read independently.
- `scan-acceptance.json` and `scan-acceptance-audit.json` record the owner's
  explicit approval of both promo scan sets. All 532 checked entries match their
  scan policies; decoded-frame identities and original pixels were verified.
  All sheets, keys, originals, flags, accepted media and local copies remained
  unchanged during approval. `scan-approval-evidence/` preserves the prior reports
  and pages. No other trial's checklist was modified.

The four native run reports each passed six assertions, with unchanged storyboard
hashes and explicit baseline comparison. All 36 native manifest file hashes match;
24 assertions passed across those runs. Native sampled scans report no flags or
errors. All exports decode completely and use their intended dimensions/codecs.
Full-frame Vision scanning completed with zero flags or detector errors across
637 social MP4 frames and 112 README GIF frames. Their 532 distinct review images
occupy 133 contact sheets; the owner reviewed and approved both sets. The final audit rebuilt
the decoded-frame identities and verified their exact coverage against the scan
keys. The review page links a numbered scan-sheet viewer. The README MP4 companion
was decoded and visually checked but does not have its own full-frame scan set.
The retained original notes GIF and MP4 match the existing `docs/demo/notes.*`.
New `docs/demo/reshoot.*` are verified local copies of the accepted exports and
their captions. The legacy GitHub workflow still regenerates the separate original notes
example; the new promotion currently uses its documented local build command.

The separate-machine setup follows acceptance of this concrete demo. Its OS has
not yet been supplied. A second account/machine operated by the same maintainer
will be recorded as clean-machine reproduction, not novice-user evidence.
