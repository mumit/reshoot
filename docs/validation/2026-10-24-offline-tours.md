# Offline clickable tours

On 2026-10-24 the local macOS checkout exercised the tour milestone in the
[creation and revision plan](../plans/ux-plan.md), using only synthetic notes data.
These are automated and agent-operated checks, not outside-user research or
owner acceptance of the walkthroughs.

## What changed

An optional `[tour]` with ordered `[[tour.step]]` entries produces one HTML
walkthrough from checked browser result frames. The studio and `reshoot tour`
share creation, title/explanation/alt editing, step ordering, adding/removing
steps and optional click markers. Edits preserve source tasks and checks, use
project revision guards and support Save/Reset and session Undo/Redo. Marker
placement works by clicking a preview image or entering percentages.

The exported file embeds its PNGs, CSS and navigation. It makes no external
requests and does not operate the live app. Next/Back, numbered steps, markers
and arrow/Home/End keys navigate captured screens. Navigation keeps heading
focus, titles wrap on narrow screens, and controls remain visible in the studio
frame. Without JavaScript all steps remain readable by scrolling. Plain text is
escaped; a restrictive content policy permits only the generated script and
embedded images. Review/studio previews use a sandboxed frame.

`tours.json` binds HTML, image assets, captured source frames and take metadata
by hash. Each source step requires passing result checks on a complete TOML
browser take. Re-cuts reuse this evidence, while fresh recordings refresh the
images. Tour images join configured check sources, and titles, explanations and
alt text join direct text scanning when enabled. Review, local export, run
records, Markdown and comparisons include the walkthrough. Rejected unbound
HTML exports cannot replace a run record or copy files.

## Fresh CLI trial

The ignored `takes/tours-20261024/` directory holds `trial.py`, `trial.json`,
command logs, local exports, a baseline record and comparisons. Scanning remained
enabled with the project's defaults.

| Stage | Evidence |
|---|---|
| Original notes preview | Run `5208baf71f6547ae9549abe971ad6e79`; 16.27 seconds; all 3 checks passed |
| Create two tour steps, add explanation/marker and re-cut | Run `4b28062e2b0e415b8da2e6a5fa177f31`; 4.88 seconds; original checks retained |
| Change only the app background and record again | Run `8a3ca3b6b1234115a53833547e95e099`; 16.29 seconds; same 3 checks and refreshed tour |

The re-cut retained storyboard bytes and the clean recording's SHA-256:
`06f89e050c3e8256b22306e8594ab4a282a7f35ff2d15385d0e58b8725a28720`.
The exported `demo-tour.html` was 110,955 bytes, with two result frames backed
by one and two checks respectively. The new background changed the named tour;
comparison against the local baseline record reported it as changed, and
`export --replace` updated the copied HTML and Markdown.

The final trial's scan completed using macOS Vision, with text and people
detectors available, sampled video/GIF coverage every three seconds and three
direct text files, including the tour manifest. This is not full-frame scan
coverage or a privacy verdict. The run retained pending owner review. Nothing
was accepted, posted, pushed or published.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 215 passed, 49 browser tests deselected |
| Affected tour, screenshot and studio browser suite | 4 passed |
| Final enhanced tour browser suite | 2 passed |
| Offline viewer | Actual file navigation with network disabled; embedded images load, with no HTTP requests |
| Mobile and accessibility behavior | 390 px viewport, long escaped titles, marker/Next/Back/keyboard navigation, step state and heading focus; no-JavaScript view remains readable |
| Source safety | Invalid settings, stale revisions, unbound assets/metadata and tampered HTML rejected; local export protects existing files |
| Documentation | Relative links, images and anchors checked; 25 TOML blocks parsed, including separate target alternatives |
| Static and package checks | Python compilation, viewer/studio JavaScript syntax and whitespace checks passed; wheel includes the renderer, offline script and updated skills |
| Plugin | Validation passed with existing context-file and missing-icon warnings |

The studio trial creates a tour from checked steps, protects pending fields,
uses Save/Undo/Redo, edits an explanation, places a marker and re-cuts. It checks
that the clean recording, storyboard and all three task assertions are retained,
that tour images appear among scan items, and that the sandboxed walkthrough
navigates. Reordering a step is reversible. Existing screenshot and studio flows
also passed. No page script errors were observed.

The viewer regression uses HTML-like hostile title/explanation text to confirm
that it remains text, creates no extra image nodes or external requests, and
cannot execute. It also verifies that the exact embedded PNG bytes match the
bound image assets. Text-scanner tests cover tour explanations directly.

The full notes gallery was rebuilt, and its downloadable tour and browser-rendered
image were refreshed with the final viewer. The notes images, actual local
walkthrough, studio editor, marker controls and embedded preview were visually
inspected. The final wheel was checked against the current source and skill files.

## Limits and following work

This is a walkthrough of captured result screens, not an interactive live app,
video replay or DOM reconstruction. Images retain privacy masks, possibly the
cursor/caret, and the JPEG screencast's original quality. Video captions, zoom
and framing are not added. A result check does not certify every pixel after a
hold, the explanation, marker placement or usability. Crops and markers need
inspection again after layout changes.

One tour supports up to 30 steps. The studio's default creation and Add picker
use the first TOML browser take; other takes and advanced crop/width settings
remain available through the CLI or file. Previously copied HTML is not deleted
when a tour is disabled or renamed. GitHub shows HTML source, so interactive
review requires downloading and opening it locally. No hosting or public CI
workflow was exercised. No Linux, Windows or outside-user trial was added, and
these checks are not an accessibility certification. The next milestone is a
review of the complete creation-to-review journey for remaining friction.
