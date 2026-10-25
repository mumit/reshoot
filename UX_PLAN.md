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

## Following milestones

1. Beat trimming and sequencing, destination framing and readability feedback,
   and narration auditioning and audio balance.
2. Screenshots and tours after the creation and revision loop is established.

Outside-user testing remains deferred by the owner. Synthetic and maintainer
verification do not establish novice usability or professional creative quality.
