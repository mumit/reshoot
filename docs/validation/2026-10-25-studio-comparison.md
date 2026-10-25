# Compare recorded revisions in the studio

On 2026-10-25 the local macOS checkout exercised comparison of checked frames
after integrating upstream changes through `376e931` in merge `13cf46f`.
Only synthetic notes data was used. These are automated and agent-operated
checks, not independent user research, a visual-quality score or owner acceptance.

## What changed

Compare opens a deferred comparison in the studio. A picker offers up to 30
earlier complete local runs, preferring an accepted run. The selected earlier
run and the current displayed run carry explicit IDs and artifact/scan bindings.
Another command making a newer run does not change either side of the open page.

Steps match by stable story and beat ID. Added/removed steps remain visible;
labels distinguish frame-file, task-definition and recorded result-detail
changes. Images require complete browser takes, passing result checks, bound
metadata and a bound PNG at the expected evidence path. Missing, partial,
unchecked or unbound frames receive an explanation. Duplicate IDs are rejected.

Frames appear together on desktop and stack on narrow screens, with original
image-size links. Each side has its own review-evidence link, including working
relative media and scan-sheet resources. Requests verify both bindings and the
actual artifact bytes. A small in-memory cache avoids rehashing every video for
each image request while file inode/size/mtime/ctime remain unchanged. Changes
invalidate verification. Metadata and served frame/media bytes also receive
direct hash checks, including a regression for changes during a request.

The comparison is read-only. It does not write comparison files into runs,
alter sources, update a baseline or make an acceptance decision. It compares
captured result frames, retaining privacy masks, rather than rendered exports.
The UI states that later captions, zoom, framing, title cards and cuts require
inspection in the actual exports.

## Fresh synthetic trial

The ignored `takes/comparison-20261025/` contains `trial.py`, `trial.json`, CLI
logs and both complete scanned notes previews.

| Stage | Result |
|---|---|
| Original notes preview | Run `d4e7e054b06b4335a58c17c4a4cd4e4a`; 16.12 seconds; all 3 task checks passed |
| Change only the app background and capture again | Run `03913e3997f240f6b0d38f465e06db76`; 15.67 seconds; all 3 task checks passed |
| Compare checked steps | `notes/add` and `notes/search` both report changed frame files, with task definitions and result details unchanged |
| Fetch four original PNGs | Each returned byte sequence matches its advertised SHA-256 |
| Open both review pages and videos | Both review entries load; relative MP4 responses match the selected run's artifact hash |
| Verify read-only behavior | Hashes of every file in both run directories remain unchanged |

Both scans completed with the configured sampled macOS Vision workflow, and
both runs retained pending owner review. This is not full-frame coverage or
a privacy verdict. Nothing was accepted, pushed, posted or published.

Native Chrome inspection confirmed run IDs, scan/check status, review links,
matching-step labels and the visible dark-to-blue background change. The
temporary tab and local server were closed after inspection. The headless
browser trial checked the 390 px layout without horizontal document overflow
or page script errors.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 260 passed, 53 browser tests deselected |
| Affected browser suite | 4 passed: comparison, studio editing/capture, source freshness and setup continuation |
| Final focused comparison browser | 1 passed, recording two notes revisions and keeping the pair fixed after a newer run appears |
| Read-only evidence | Source hashes, run reports and both run-directory file sets remain unchanged by comparison |
| Eligibility | Unchecked, outside, unbound and partial evidence cannot supply images; duplicate stable IDs are rejected |
| Revision guards | Tampered artifacts and changed scan bindings invalidate requests; a media change during serving returns 409 |
| Selection | Earlier accepted baseline preferred; partial/future runs excluded from the picker |
| Documentation | 108 local links/anchors checked; 32 TOML blocks parsed, including separate target alternatives |
| Package | All 44 Python/browser modules and the 2 updated skills in the wheel match current source bytes |

The HTTP regression loads a chosen pair, creates another successful run and
confirms the same query still returns the original pair. It checks PNG hashes,
review-page relative resources, stale bindings and media changed after initial
verification. The browser trial also keeps the body run ID and frame URLs fixed
after a newer run is added. No automatic media acceptance is exercised.

Python compilation, both studio scripts, whitespace, documentation links and
anchors, TOML examples, wheel module/script/skill contents and plugin validation
were checked. Plugin validation retains its existing root-context and missing
icon warnings. No renderer or export geometry changed, so the gallery was not
rebuilt. Accepted media under `docs/demo/` was untouched.

## Limits and following work

This compares PNG file hashes, not perceptual image difference. A matched ID
or passing result check does not certify the entire image or task. Frames can
retain captured cursor/caret state and the original recording's image quality.
Finishing edits can change a video while leaving its captured evidence identical.

Only complete local runs with media are selectable. A committed record whose
media is absent cannot provide these images. Legacy takes without bound checked
browser evidence have no eligible frames. Matching IDs must be unique across
takes; renaming IDs appears as added/removed steps. The picker is limited to 30
earlier complete runs. Playback synchronization, visual diff heatmaps, release
clips and comparisons in pull requests remain outside this milestone.

Comparison does not continuously monitor an already displayed image. Refreshing
or loading a resource revalidates its binding; changed scans or artifacts require
a reload. No new Linux, Windows or outside-user trial was added. The next planned
step adds paired export playback with beat-aware seeking inside the studio.
