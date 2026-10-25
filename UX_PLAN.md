# Creation and revision plan

Make a useful first demo without reference reading, then make changes in the
studio with confidence. Keep the project files editable and the existing CLI
available for automation. Use synthetic data for all verification.

## Implementation

- [x] Bind studio media, review and acceptance to the displayed run and its
  artifact binding. Show scan sheets beside the decision.
- [x] Add `reshoot create [URL] --directory demo`: check dependencies, create a
  project, record a task, make a preview and open the studio. Without a URL,
  make the bundled notes preview.
- [x] Add recording controls for Done, Pause, Caption, Check result and Hide.
  Record checkbox and radio state. Preserve unsupported steps as explicit,
  blocking repair notes instead of losing the recording.
- [x] Make Update preview choose between re-cutting and recording. Expose
  holds in the studio and put beats before global styling.
- [x] Add revision checks, undo/redo, persistent save errors and cancellation.
  Preserve external edits and prevent editing while a job uses the files.
- [x] Verify the browser journey, stale-page rejection, interruption recovery
  and the notes exports. Update commands, skills, pitfalls and onboarding.

Verification is recorded in
[the creation and revision trial](docs/validation/2026-10-24-creation-and-revision.md).
That trial passed 116 fast tests, 37 browser tests, and the final
focused browser trial four. A fresh notes preview took 15 seconds; the final
with an explicit full-frame scan took 76 seconds. Nothing was published or
accepted on the owner's behalf.

## Acceptance criteria

A newcomer can try the notes example with one command after installation, or
demonstrate a task at a demo URL and reach a preview without moving files.
They can add a caption and result check while recording, change its hold in
the studio, undo that edit, update the preview and inspect scan evidence.
Media and acceptance always refer to the run shown. Unsupported interactions
remain visible and cannot silently produce an apparently complete final.

## Visual repair implementation

- [x] Save stable alternative locators while recording.
- [x] Diagnose missing controls without silently changing a recording.
- [x] Offer a revalidated suggested repair through the CLI and studio.
- [x] Let the owner select and confirm a replacement in the app.
- [x] Preserve checks, source revisions and studio undo; verify with a fresh preview.
- [x] Test renamed, ambiguous and stale controls, result mismatches and cancellation;
  update commands, skills and validation evidence.

See [the locator repair trial](docs/validation/2026-10-24-locator-repair.md).

## Reusable visual styles

- [x] Offer Focus, Midnight and Paper starting looks with illustrative sketches.
- [x] Share validated style operations between the CLI and studio.
- [x] Save a project style library and import/export portable TOML styles.
- [x] Apply to all TOML browser takes in one undoable change, preserving story,
  timing, fonts, audio, exports and scan coverage.
- [x] Validate every affected file before replacing any, reject stale edits and
  roll back the style's own writes if a later replacement fails.
- [x] Keep frame and card backgrounds independently editable; show a finished
  export's poster and retain the preview beside desktop style controls.
- [x] Verify reuse across synthetic projects, re-cutting and undo; rebuild and
  inspect the gallery and document the workflow.

See [the visual styles trial](docs/validation/2026-10-24-visual-styles.md).

## Beat trimming and sequencing

- [x] Share inclusive named ranges and move, duplicate, remove and add operations
  between the CLI and studio, preserving the full capture task and result checks.
- [x] Retain comments and advanced settings; keep numeric custom ranges until
  explicitly replaced and leave nested custom tables to file editing.
- [x] Protect complete narration lines, source revisions and recording hashes;
  keep concurrent edits outside undo history and reject partial runs as sources.
- [x] Support one-step undo, range Save/Reset and protection against updates
  with unsaved range choices.
- [x] Map every beat appearance and ordered output part, including title cards,
  and enable playback after rendering the saved cut.
- [x] Verify notes in the CLI and browser, repeated subtitles and export maps;
  rebuild and inspect the gallery and document the workflow.

See [the beat sequencing trial](docs/validation/2026-10-24-beat-sequencing.md).

## Destination framing and readability

- [x] Share validated per-export Fit/Crop, focus and viewing-width settings
  between the CLI and studio, with one-step undo and pending-field protection.
- [x] Use one geometry calculation for MP4 and GIF and retain spatial transforms
  through browser frames, cuts and exports.
- [x] Capture bounded geometry-only app-font samples and checked-result bounds;
  measure caption boxes, title text and subtitle reading time.
- [x] State coverage limits for missing data, camera zoom, transformed app text,
  custom placement, iframe/canvas text and unsampled frames; keep hints advisory.
- [x] Show rendered exports at viewing size with scrollable inspection and a
  crop guide. Include hashed measurements in CLI output and the review page.
- [x] Offer a recording-view control that makes a fresh first-browser capture
  with the same task and checks, preserving source files and undo.
- [x] Verify encoded crop colours, MP4/GIF parity, stale edits, source clipping,
  undo and new captures; inspect notes exports and rebuild the gallery.

See [the destination framing trial](docs/validation/2026-10-24-destination-framing.md).

## Narration auditioning and audio balance

- [x] Share guarded per-beat narration and voice edits between CLI and studio;
  preserve actions, result checks, scan sources, comments and undo history.
- [x] Audition a saved line without launching the app, using the same voice
  cache and project-relative speech command as the recording.
- [x] Offer local voice choices, explicit Save/Reset, pending-field protection,
  cancellable auditions and playback without replacing the displayed run.
- [x] Share validated voice/music gains and optional music ducking; keep muted
  narration's timing/subtitles and limit mix peaks before encoding.
- [x] Verify fresh capture after narration changes, re-cut after balance edits,
  encoded timing/gain/ducking/mute/limiting and retention of all task checks.
- [x] Complete the fresh local-speech trial, broader regressions, visual
  inspection, gallery rebuild and documentation/package verification.

See [the narration and audio trial](docs/validation/2026-10-24-narration-and-audio.md).

## Documentation screenshots

- [x] Select named PNGs from complete TOML browser takes with passing result
  checks; preserve their captured privacy masks and original source frames.
- [x] Share guarded CLI/studio selections, alt text, maximum width and crop
  settings without changing the captured task or result checks.
- [x] Offer Use for docs, Save/Reset, Undo/Redo, drag/keyboard crops, local
  downloads and image-size inspection beside the displayed run.
- [x] Generate screenshots on fresh runs and re-cuts; bind pixels, source frames
  and take metadata, and add PNGs and alt text to the configured scan/review.
- [x] Include PNGs in local exports, refresh records, Markdown and screenshot
  comparisons; extend the refresh template to stage all configured exports.
- [x] Complete the final crop browser trial, regressions, fresh CLI refresh,
  gallery/UI inspection and documentation/package verification.

See [the documentation screenshots trial](docs/validation/2026-10-24-documentation-screenshots.md).

## Offline clickable tours

- [x] Build one offline HTML walkthrough from complete browser result frames
  with passing checks; retain privacy masks and source evidence.
- [x] Share guarded CLI/studio creation, words, step ordering and marker edits,
  with Save/Reset, pending-field protection and Undo/Redo.
- [x] Embed images, styles and navigation; support step numbers, markers,
  Next/Back, arrow/Home/End keys, heading focus and a readable no-JavaScript view.
- [x] Bind HTML, image assets and original evidence; include tour images and
  words in configured scanning, review, export, records and comparison.
- [x] Verify offline mobile viewing, escaped text and no external requests,
  plus studio revision flow and re-cutting without changing task checks.
- [x] Finish the fresh scanned CLI refresh, visual/gallery inspection and
  documentation/package verification.

See [the offline tour trial](docs/validation/2026-10-24-offline-tours.md).

## Creation-to-review coherence

- [x] Review the complete journey as a newcomer, repeat author and careful
  reviewer; record critical findings and the limits of persona-based review.
- [x] Distinguish unsaved fields, saved changes, current previews, final review
  and accepted files, with a visible next action and pending-review protection.
- [x] Bind rendered and captured source fingerprints separately, retaining
  task/data changes across re-cuts and binding fixture bytes after app reset.
- [x] Add section navigation, measured sticky-header layout, explicit draft
  reset and external-change reload without silently adopting revisions.
- [x] Bundle the displayed run's exports and video subtitles for local download,
  with image Markdown, review status and hashes; exclude sources and logs.
- [x] Exercise preview, caption revision, re-cut, final review and exact-run
  downloads; verify mobile navigation, stale edits and source-path replacement.

See [the creation journey review](docs/validation/2026-10-25-creation-journey.md).

## Studio session recovery

- [x] Persist up to 50 grouped Undo/Redo steps with deduplicated source bytes,
  atomic checkpoints, file syncing and private local storage.
- [x] Offer explicit Resume history or Start with current files after a restart;
  keep changed sources and archive previous checkpoints on a fresh start.
- [x] Offer a saved source ZIP for comparison without restoring or executing it.
  Reject stale recovery/download requests and unsafe archive paths.
- [x] Guard competing studios with an OS lock and checkpoint generation checks;
  retain source revision guards and block edits/jobs/decisions during recovery.
- [x] Verify restarts, grouped Undo/Redo, external changes, bad checkpoints,
  failed checkpoint writes, source-path checks and bounded storage.
- [x] Exercise the fresh scanned notes capture, recovery, source download and
  re-cut, desktop/mobile UI and affected browser regressions; update the guide,
  skills, package checks and validation record.

See [the session recovery trial](docs/validation/2026-10-25-session-recovery.md).

## First-run setup and continuation

- [x] Share structured tool checks and actionable fixes between doctor, creation
  and the studio, while retaining existing doctor JSON fields.
- [x] Add explicit synthetic probes for H.264/ffprobe, TOML browser input/capture
  and configured OCR; keep app state, scan choices and media verdicts separate.
- [x] Preserve creation stages and offer `create --resume`, retaining URL,
  viewport and the saved task after setup or preview failures.
- [x] Record demonstrations into new drafts and guard installation against
  source changes; keep both sources when another editor changes the project.
- [x] Offer focused Recording tools fixes, Check again and Continue creation,
  with successful checks collapsed and terminal/environment recovery explained.
- [x] Verify missing and corrected tools, probe failures, source preservation,
  cached-check invalidation, fresh notes creation, mobile UI, regressions and
  documentation/package checks.

See [the first-run setup trial](docs/validation/2026-10-25-first-run-setup.md).

## Compare recorded revisions

- [x] Offer earlier complete local runs, preferring an accepted baseline, while
  keeping the current displayed run and chosen baseline explicit.
- [x] Match stable story/beat IDs, retain added/removed steps and show frame,
  definition and result-detail changes with eligibility explanations.
- [x] Require bound metadata and PNGs from complete checked browser takes;
  reject duplicate IDs, partial captures, unbound/outside frames and stale scans.
- [x] Bind image-size views and both review pages/media to the selected runs;
  verify bytes and preserve source, run files and acceptance.
- [x] Support deferred loading, stale-request protection and stacked mobile
  frames, with clear limits for captured evidence versus finished exports.
- [x] Verify fresh scanned notes revisions, HTTP/media bindings, unchanged run
  files, a newer run arriving during comparison, desktop/mobile UI, regressions
  and documentation/package checks.

See [the studio comparison trial](docs/validation/2026-10-25-studio-comparison.md).

## Following milestones

1. Compare the paired exports through video playback in the studio, including
   beat-aware seeking while retaining the selected run and review bindings.

Outside-user testing remains deferred by the owner. Synthetic and maintainer
verification do not establish novice usability or professional creative quality.
