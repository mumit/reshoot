# Destination framing and readability

On 2026-10-24, the local macOS checkout was exercised with synthetic notes data
to verify the destination framing milestone in the [creation and revision
plan](../../UX_PLAN.md). These are automated and agent-operated checks, not
independent-user research or owner acceptance of media.

## What changed

Each export has Fit/Crop, horizontal and vertical crop position, and an
intended browser viewing width. The studio's crop guide uses the rendered
master's poster. Saved settings are rendered by Update preview; the viewing-size
inspector retains its requested width with scrolling when needed. CLI
`reshoot frame` uses the same validated operations. Pending choices must be
saved or reset, and each operation supports studio Undo/Redo.

MP4 and GIF share even-pixel geometry and crop offsets. Spatial transforms
survive browser framing, trimming, sequencing and export resizing. Recordings
collect bounded main-page font-size and rectangle samples at result holds,
without adding sampled page text or field values. Caption rendering records
its box and font sizes, and title cards record text geometry.

The resulting `.readability.json` reports estimate small app-text samples,
caption and title sizes, subtitle reading pace and crop clipping at the chosen
viewing width. Reports are hashed alongside media and surfaced in the studio,
CLI and review page. They do not change run success or acceptance. A Recording
view control changes the first browser take's viewport and triggers a fresh
capture with the existing task and checks.

## Fresh CLI trial

Evidence is under the ignored `takes/framing-20261024-final/` directory. Its
`trial.py`, `trial.json`, command logs and Fit/Crop frames retain the exact
steps and timings.

| Stage | Evidence |
|---|---|
| Fit preview at 960x540 | Run `9b1034375e8f416d9aba8d8489ae1217`; 16.9 seconds; all 3 checks passed |
| Set crop focus and re-cut | Run `8789c85ed6564dc1b63a0fb61aacde6d`; 6.3 seconds; all 3 original checks retained |
| Change recording view to 640x480 and preview | Run `f294344cdbed4d68a0021d429bae45be`; 17.3 seconds; all 3 checks passed |

The original storyboard bytes were unchanged through all operations. The crop
re-cut retained the clean recording hash
`765b4896bdb06229242a6f06aff71071786f8d8c21b8da35a1cc2aea9c2e9f4b`.
The portrait MP4 and GIF had identical geometry and measurement reports.
Their Fit version measured small app-text samples at about 5.2 px and caption
text at 8.5 px at 360 px viewing width. The deliberate crop removed sampled app
text and cut through the caption and result-check bounds. The report retained
unknown app-font sizing rather than inventing a readable value.

The narrower capture used the requested 640 px CSS viewport and produced fresh
measurements. This does not establish that narrowing alone improves every
destination: fitting and cropping have different consequences. Both exports,
the crop guide, viewing-size playback and recording-view controls were inspected.
No sample was accepted or published.

Visual inspection found a noisy source-clipping hint for a text check against
an entire long list. Text checks now use the matched words' bounds when possible,
falling back to element bounds for split or unsupported text. A focused browser
regression verifies that the notes baseline has no such source-clipping hint
while the deliberate crop still reports clipping. Other result-check bounds
may include more content than the expected words, which the report states.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 164 passed, 45 browser tests deselected |
| Affected framing, sequencing, style and studio browser suite | 4 passed |
| Final enhanced framing browser trial with matched-text bounds and a new recording view | 1 passed |
| Gallery | Rebuilt from notes with crop focus comparisons and measured font sizes |
| Documentation | 125 relative links, images and anchors checked; 21 TOML blocks parsed, with target alternatives parsed individually |
| Packaging and static checks | Wheel built with the new Python modules and layout sampler; studio and sampler JavaScript syntax and whitespace checks passed |

The regressions verify encoded red/blue crop regions in both MP4 and GIF,
shared offsets, font scaling through a browser frame and trim, source clipping
versus export clipping, explicit limits under camera zoom, invalid settings,
stale edits and preservation of source content, budgets and scan sources.

The browser journey verifies optional geometry-only samples, crop-guide input,
blocked updates with pending fields, Save/Undo/Redo, a 390 px inspector, a re-cut
using the existing clean recording, and a new 640 px recording with all three
checks. It also verifies that changing a measurement sidecar invalidates the
run's artifact hashes. The gallery and new notes exports were visually inspected.

## Limits and following work

These are editing hints, not an accessibility or readability certification.
The current thresholds are 12 px for small app-text samples, 14 px for caption
and title text, and 18 subtitle characters per second. App samples are bounded
and cover main-page result holds, not every frame. Camera zoom, scaled/rotated
app text, canvas/iframe text and custom placement have explicit limitations.
At most 30 individual hints are listed. Colour contrast, every animation frame
and the clarity of the story remain visual-review responsibilities.

Recording view changes the first TOML browser take's layout dimensions, not
its device identity. A responsive layout can require locator repair. Old
recordings need a fresh capture for app-font samples, while a re-cut can redraw
caption measurements. Undo lasts for the studio session; CLI edits remain
ordinary project-file changes. No Linux, Windows or independent-user trial was
added. Narration auditioning and audio balance remain the next milestone.
