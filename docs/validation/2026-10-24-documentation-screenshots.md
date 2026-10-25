# Documentation screenshots that stay current

On 2026-10-24 the local macOS checkout exercised the screenshot milestone in
the [creation and revision plan](../../UX_PLAN.md). Automated tests and
agent-operated trials used the bundled synthetic notes app. This is not
outside-user research or owner acceptance of media.

## What changed

`[[screenshot]]` entries in `reshoot.toml` select a stable PNG name, browser take,
checked beat, alt text and optional crop/maximum width. CLI `reshoot screenshot`
and studio operations share validation, project revision guards and reversible
edits. Use for docs opens a prefilled selection from a checked story step.
Existing selections offer a drag crop guide and keyboard percentage fields,
with Save/Reset and Undo/Redo. The gallery retains the displayed run's PNGs until
an update, with local downloads and an inspector at the image's encoded width.

PNGs use the existing captured result frame at the end of a beat's hold. They
retain page privacy masks and can include the recorded cursor, without adding
video captions, decorative framing or camera zoom. Resizing never enlarges the
source. A complete TOML browser take and passing checks on the selected beat
are required; missing, partial and unchecked source evidence fails explicitly.
The crop does not change the original result assertions.

Every PNG and `screenshots.json` manifest is included in the run's file hashes.
The manifest binds output pixels to the original result frame and take metadata.
PNGs join configured check sources, and enabled detection scans alt text directly.
Review pages, local export, Markdown, run records and comparison reports include
the named images. The refresh template stages all final exports by default.
No GitHub workflow was run or published in this trial.

## Fresh CLI trial

The ignored `takes/screenshots-20261024/` directory retains `trial.py`,
`trial.json`, command logs, local documentation exports and comparisons.

| Stage | Evidence |
|---|---|
| Original notes preview | Run `ccbfb51e806c4046b0b335927fbf6e77`; 15.17 seconds; all 3 checks passed |
| Select search-result PNG and re-cut | Run `0c71f3bc80764a7081773f8ca4148828`; 4.60 seconds; all 3 original checks retained |
| Change only the app background and record again | Run `b1ba053f8fa24b47b89017b20f063048`; 15.28 seconds; same 3 checks, refreshed PNG |
| Crop the refreshed result frame | Re-cut `756222ed59234d1193cc38e59bc39417`; PNG is 460 x 203 pixels |

Adding the screenshot retained storyboard bytes and the clean take's SHA-256:
`912ee81e07ae8548f684dddc88b1277d7f38740a5cd04fa933a92c9632f3ebb7`.
The selected PNG had the same 720 x 405 captured viewport because its configured
960 px maximum does not upscale. Changing the synthetic app background produced
a different PNG with the same stable name and task. A comparison against the
local baseline record reported the image as changed; `export --replace` updated
the local file and Markdown. A subsequent CLI crop retained the checked source.

Privacy detection was disabled for the timing/visual trial; the PNG was included
on the run's contact sheets. This is not a privacy scan pass. Tests separately
verify that exact alt text is sent to the text scanner. No media was accepted or
published, and accepted examples in `docs/demo/` were not replaced.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 199 passed, 47 browser tests deselected |
| Affected screenshot, audio and studio browser journeys | 3 passed |
| Final enhanced screenshot browser journey | 1 passed, including rectangle crop and PNG image-size inspection |
| Source and output pixels | Cropped colour regions and dimensions verified, downsizing never upscales |
| Provenance and file safety | Unbound pixels/metadata rejected; invalid and stale edits preserve project files; overwritten exports require explicit replacement |
| Documentation | Relative links, images and anchors checked; 24 TOML blocks parsed, including separate target alternatives |
| Static and package checks | Python compilation, studio JavaScript syntax and whitespace checks passed; wheel built with screenshot operations and updated skills |
| Plugin | Validation passed with existing context-file and missing-icon warnings |

The browser journey selects a checked step, verifies pending-field protection,
Save/Undo/Redo, re-cuts without changing the clean recording or three checks,
finds the PNG among scan items, and opens it at image size with its alt text.
Dragging a crop updates the same percentage settings, renders a smaller PNG and
retains the clean take. Invalid alt text remains unsaved; removing a selection
retains the displayed run's image until the next update. No page script errors
were observed. Existing audio and studio flows also passed.

The gallery was rebuilt with an actual checked notes PNG. The generated image,
the blue-background refresh and the cropped PNG were visually inspected. The
local studio gallery, settings, drag crop guide and image-size inspector were
also inspected.

## Limits and following work

These are viewport result frames from the existing recording, not full-page
stitches, clean DOM re-captures or lossless browser screenshots: the original
screencast is JPEG, saved as PNG for evidence. The cursor and caret can remain.
Checks confirm the specified result before the hold; they do not certify every
pixel in a later animation, crop, alt description or privacy mask. A video cut
can omit a beat whose checked screenshot is still exported.

Pixel changes include cursor position and rendering noise; comparison does not
infer semantic changes. Crops need review after responsive layouts change.
Other TOML browser takes can be selected through the CLI; the studio's new-step
picker follows the first browser take. Partial previews export no screenshots.
Existing copied PNGs and Markdown are not deleted when a selection is removed.
Undo lasts for the studio session. Linux, native windows, terminal screenshots
and outside-user testing were not added. Clickable tours are the next milestone.
