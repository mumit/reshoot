# Studio session recovery

On 2026-10-25 the local macOS checkout exercised persistent studio editing
history with synthetic notes data. These are automated and agent-operated
checks, not outside-user research or owner acceptance of the media.

## What changed

The studio checkpoints grouped Undo/Redo steps under the project's ignored
`takes/studio/` folder. Restarting offers Resume history when tracked file names
and bytes match the checkpoint, or Start with current files. Recovery itself
does not replace source files. A fresh start archives the old checkpoint.

If sources changed elsewhere, the studio keeps them, lists changed file names
and offers a ZIP of the saved source copy for comparison. Resume is unavailable.
The same recovery choice appears after reloading external changes during an
active session with history. Editing, recording and acceptance wait for recovery
to be resolved; media inspection and exact-run downloads remain available.
The server enforces this rule independently of the disabled UI controls.

Checkpoints contain up to 50 grouped steps, deduplicate source bytes by SHA-256
and preserve missing files, comments and exact original bytes. Writes use a
private temporary file, file syncing, atomic replacement and directory syncing.
An OS file lock plus checkpoint generation checks serialize competing studios
and reject stale writes. Recovery and source downloads carry the checkpoint's
hash. Stored path names must match the currently configured sources before
resuming; archive names cannot escape their numbered source folders.

Invalid or oversized checkpoints require an explicit fresh start and remain in
an archive. A failed checkpoint write reports when the source edit has already
saved, retains the previous checkpoint and blocks further editing until recovery.
Recovery after an interruption compares actual source bytes with the last
complete checkpoint instead of assuming the interrupted operation finished.

## Fresh synthetic trial

The ignored `takes/sessions-20261025/` contains `trial.py`, `trial.json`, CLI
logs, the notes project, archived checkpoints and `saved-sources.zip`.

| Stage | Result |
|---|---|
| Initialize and record notes preview | Run `4587eb67e73f4f31adb9a667fbfd09d6`; preview in 15.46 seconds; all 3 task checks passed |
| Save a caption, restart, resume and undo | Original storyboard bytes restored by the explicit Undo action |
| Restart again, resume and redo | Edited caption bytes restored by the explicit Redo action |
| Edit source externally while stopped | Conflict shown; Resume unavailable; external bytes retained |
| Download saved source copy | ZIP contains the checkpoint's config, storyboard and edit script plus a README; original caption bytes verified |
| Start with current files | Old checkpoint archived; external source bytes unchanged |
| Re-cut the current story | Run `d688e1f1e3e647e1baaf08282c3c6a86`; 4.95 seconds; all 3 checks retained and original clean capture unchanged |

The retained clean recording has SHA-256
`242b263f7e5a03bf01b66a8d015a1fca9d1fc906fa33527025ba4b6626539444`.
Scanning remained enabled with sampled macOS Vision coverage. Both successful
runs retained pending owner review. No recording was accepted, pushed, posted
or published.

The native Chrome inspection confirmed the matched-session prompt, disabled
editing/recording controls, source-copy link and external-conflict message with
the changed storyboard name. It used only the synthetic project. A headless
390 px trial verified the recovery controls without document overflow or page
script errors. The actual MP4/GIF preview remained present during recovery.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 235 passed, 51 browser tests deselected |
| Focused session fast suite | 12 passed |
| Affected browser workflows | 11 passed across verified groups of 7 and 4 |
| Final focused recovery browser | 1 passed |
| Documentation | 103 local links/anchors checked; 32 TOML blocks parsed, including separate target alternatives |
| Static/package checks | Python compilation, studio JavaScript syntax, whitespace, exact wheel module/skill bytes and plugin validation passed |

The focused recovery suite covers grouped files and absent style libraries,
Undo and Redo across separate restarts, external edits, archive retention,
unknown/truncated checkpoints, source-path mismatch, unsafe ZIP names, competing
studios, a source change during resume, checkpoint replacement failure and the
50-step bound. HTTP tests reject edits, cut changes, Undo/Redo, jobs and decisions
before recovery, plus stale recovery and source-copy requests. A valid Resume
then permits editing.

The browser recovery test saves a caption, restarts the HTTP server, resumes,
undoes, restarts again, resumes and redoes. It then creates an external edit,
downloads the saved source ZIP, switches to a narrow viewport and starts fresh,
checking the external bytes remain intact. The existing recording browser test
now explicitly starts with current files after an external hold edit, then
verifies recording from that beat and cancellation.
The audio regression also chooses current files after an external voice-engine
change, then verifies failed and cancelled auditions keep the displayed video.

Python compilation, studio JavaScript syntax, whitespace, documentation links
and anchors, TOML examples, wheel source/skill contents and plugin validation
were checked. Plugin validation retains the existing root-context and missing
icon warnings. No media renderer, cursor, captions, cards or export geometry
changed, so the visual gallery was not rebuilt for this milestone. Accepted
media under `docs/demo/` was untouched.

## Limits and following work

Only saved source edits are checkpointed. Unsaved input fields, browser panel
state, running jobs and recordings in progress are not resumed. The checkpoint
is not a crash-safe transaction across several source files; recovery preserves
whatever bytes actually reached disk and offers the last complete source copy.
It cannot prevent arbitrary simultaneous writes by other editors or commands.
The guards protect tracked file revisions and competing studio checkpoints.

Storage is capped at 32 MB per checkpoint and 50 steps. A project whose history
exceeds that cap must start fresh; already saved source edits remain intact.
Archives stay local until deliberately removed. The saved source ZIP is
unreviewed project source, not a deliverable or media acceptance. Sessions have
no effect on existing exact-run review, accepted baselines or publication.

The locking implementation targets the documented macOS/Linux platforms; this
pass adds no Windows or independent Linux recovery trial. Outside-user testing
remains deferred. The next planned step addresses missing-tool setup and
actionable recovery before a first capture.
