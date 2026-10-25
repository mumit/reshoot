# Creation-to-review journey

On 2026-10-25 the local macOS checkout reviewed the complete creation journey
and exercised the resulting changes with synthetic notes data. This is an
agent-operated product, architecture and persona review, backed by automated
checks. It is not independent user research, a usability score, owner acceptance
or proof that making a demo feels joyful to a newcomer.

## Critical review

The feature set now supports a useful small demo and substantial polish:
checked tasks, captions, cuts, styles, destination framing, audio, screenshots
and offline tours. The weakest part of the reviewed journey was understanding
what those edits had changed and how to finish. Adding more creative controls
would have increased that uncertainty.

| Perspective | Finding | Change in this pass |
|---|---|---|
| Newcomer making a quick clip | Update preview and Make final competed without explaining whether the current video included saved edits. A long page made the next step hard to find. | One status describes the recording state, highlights the appropriate action and links directly to final review. Section navigation opens the relevant controls. |
| Repeat author refining a demo | An invalid field could block updates with no obvious way back. Returning from a file editor did not explain stale page state. | Reset unsaved edits reloads persisted source. External changes offer reload while preserving the existing revision guard. |
| Author delivering several formats | Videos, PNGs and the tour had separate links; obtaining a complete set required knowing the run's folders. | One exact-run ZIP contains exports, subtitles, image Markdown and a hash/status manifest. Individual downloads remain. |
| Careful reviewer | Saved changes could describe something different from the shown final. An explicit re-cut might adopt current words but retain older timing, narration or demo data. | Pending source changes prevent studio acceptance. Capture and render source snapshots remain separate through re-cuts. |
| Architect | Freshness cannot be represented by a single current-file hash when an update reuses capture evidence. Reset commands can also change input bytes before capture. | Separate source snapshots retain captured task/data provenance; fixture/upload bytes are bound after app reset without adopting newer script/config edits. |

The status is deliberately about saved sources. It does not claim the running
app is current. Existing exact-run media/review bindings remain the authority
for what a person watches. Earlier recordings without complete source snapshots
say so instead of claiming a complete comparison. New snapshot and download
logic live in separate modules, though the studio page/server remains a large
module and will need further separation as the interface grows.

## Fresh synthetic trial

The ignored `takes/journey-20261024/` directory contains the project, `trial.py`,
`trial.json`, CLI logs and the actual downloaded ZIPs. The directory was started
before midnight; the final trial and this record are dated October 25.

| Stage | Result |
|---|---|
| Notes creation and preview | `reshoot create --directory … --no-studio`; scanning enabled, all 3 task checks passed |
| Preview with PNG and two-step tour | Run `2d7042e5b0304738a5949c26f43705ba`; current preview state |
| Save a clearer result caption and re-cut | Run `c4d4fd09c04648689dec529154b7466e`; 5.07 seconds, current preview, original clean recording retained |
| Record final | Run `350c49f9726d4b0f85ab988559bb57a2`; 20.54 seconds, all 3 checks passed, final ready for review |
| Download previous preview after final exists | 931,099-byte ZIP still identifies the earlier preview and its exact binding |
| Download final | 1,139,381-byte ZIP identifies the final and its exact binding; every archived media/subtitle hash verified |

Both ZIPs contain MP4, GIF, PNG, offline tour HTML, video SRT, README Markdown
and `manifest.json`. Neither contains project sources, raw takes, logs or scan
sheets. The original clean capture retained by the caption re-cut has SHA-256
`cb2c780a2423a115583f6f42804edae95f0433a9b7b13a8f59ebe63cbb023df9`.

The final scan completed using macOS Vision with text and people detection
available: 9 scan items, 0 flagged and 4 directly scanned text files. Video/GIF
coverage was sampled every three seconds. This is not full-frame coverage or
a privacy verdict. Review remained pending; nothing was accepted, pushed,
posted or published.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 223 passed, 50 browser tests deselected |
| Affected journey, studio, framing, audio, screenshot and tour browser suite | 7 passed |
| Final focused journey browser run | 1 passed; reset-generated input bytes, draft recovery, caption save/re-cut, exact-run download, external reload and mobile navigation |
| Final focused journey/studio fast suite | 18 passed |
| Source and review regressions | Re-cut retains changed hold/input/upload detection; same-size music replacement requires re-cut; style-library save alone stays current; pending studio acceptance and stale bundle bindings rejected |
| External source-path replacement | Old revision rejected; reload edits the new storyboard; Undo restores it while preserving the externally changed config and original storyboard |
| Browser behavior | 390 px viewport, target clears measured sticky header, no document overflow or page script errors |
| Visual inspection | Native Chrome: current-preview status, section navigation, download panel, final-review shortcut and scan evidence; synthetic gallery rebuilt and caption/crop images inspected |
| Static/package checks | Python compilation, studio JavaScript syntax, 96 local documentation links/anchors, 32 TOML blocks, whitespace, wheel contents and plugin validation checked |

The gallery rebuild produced only capture-timing/encoding differences unrelated
to this feature, so its tracked media and generated guide were restored after
inspection. Accepted media under `docs/demo/` was untouched. Plugin validation
retains the existing root-context and missing-icon warnings.

## Remaining friction and limits

Installation still depends on browser/media/OCR tooling. A one-command notes
preview after installation does not establish a frictionless cold start.
Advanced multi-take work and custom commands still lead back to files. The
studio remains dense despite section navigation, and its usability has not
been measured with outside users. These checks establish working controls and
data integrity, not professional creative quality or enjoyment.

Source comparison covers configuration, scripts, declared inputs, uploaded files,
caption fonts, card assets and music. It cannot observe a remote service, an
external database, undeclared dependencies or arbitrary custom-command inputs.
Conservative byte comparison can request an update after a comment-only edit.
Snapshots describe the source around preparation/capture, not an immutable
filesystem transaction or a replay of concurrent live-app changes. Explicitly
record again after untracked app changes.

Reset unsaved edits discards all unsaved fields on the page; saved edits remain.
Undo history still lasts only while the studio server runs. The next planned
step is recovery across a restart with guarded persistent history. ZIPs are
local delivery artifacts; they neither replace review evidence nor publish
anything. This pass adds no Windows/Linux compatibility or outside-user trial.
