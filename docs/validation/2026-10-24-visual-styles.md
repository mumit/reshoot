# Reusable visual styles

On 2026-10-24, the local macOS checkout was exercised with synthetic notes data
to verify the reusable styles milestone in the [creation and revision
plan](../plans/ux-plan.md). These are automated and agent-operated checks, not
independent-user research or owner acceptance of media.

## What changed

The studio offers Focus, Midnight and Paper looks with illustrative sketches.
Users can save the current look by name in the project's `styles.toml`, download
a portable style, and import one into another project. `reshoot style list`,
`apply` and `save` use the same validation and transformations as the studio.
The [gallery](../../guide/look.md#visual-styles) shows actual notes exports.

A style sets caption placement, margin and colours, title-card colours and
browser framing across every TOML browser take. It preserves the task, holds,
result checks, fonts, logos, audio, exports and scan settings. Applied values
are ordinary storyboard and edit settings, with no run-time style dependency.

Applying a style and saving a named style each take one Undo step. All affected
files validate before any replacement. Stale source or library edits reject
the operation. A later write failure rolls back only the operation's own
writes, preserving concurrent edits. This is a checked group of file
replacements, not a crash-safe filesystem transaction.

Frame and title-card backgrounds are independently editable, including a
two-colour frame gradient. The main preview uses a poster from the finished
export, so its paused image includes the applied style. On large displays,
the preview stays beside the style controls while scrolling; narrow screens
retain the stacked layout.

## Fresh CLI trial

Evidence is under the ignored `takes/styles-20261024/` directory. Its
`trial.py`, `trial.json` and command logs retain the exact steps and timings.

| Stage | Evidence |
|---|---|
| Baseline notes preview with opening card | Run `28d9f3bb4eb44cc382f74d339b73e2bd`; 15.6 seconds; all 3 checks passed |
| Apply Midnight and re-cut | Run `e31e8288358b443a9d3033cdac1ee4fb`; 6.1 seconds; all 3 original checks retained |
| Save, export, import into a fresh notes project | Run `dd7c9c8ef81c4ac1a43c149a688512f0`; 15.6 seconds; all 3 checks passed |
| Final re-cut with rendered poster | Run `b5ecd95852a940e69b102c1f220339f0`; about 5 seconds; all 3 checks retained, 8 scan items, 0 flags |

The first styled run retained the baseline's clean recording hash
`4b9ecfe37500520c699ec0de1447c7349a449b789cbaa6e4d3766c6db729ee18`.
The original expectation arrays were compared directly and remained unchanged.
The imported project's resolved visual settings matched the original project.
The MP4, GIF, gallery frames and studio layout were inspected using demo data.
No recording was accepted or published.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 138 passed, 43 browser tests deselected |
| Final affected studio/style browser suite | 2 passed |
| Final focused fast style/studio checks | 25 passed |
| `uv run python examples/look/build.py` | Rebuilt the gallery, including Midnight and Paper exports; inspected the rendered frames |
| Changed-document links, anchors, images and TOML examples | 140 references and 24 snippets or alternatives checked |
| Python compilation, JavaScript syntax and whitespace checks | Passed |
| Wheel build and plugin validation | Passed; plugin validation retains existing root context and missing icon warnings |

The complete fast suite passed 138 tests. Focused style tests cover portability,
all browser takes, retained fonts and recording settings, invalid or out-of-scope
styles, duplicate names, export overwrite protection, failed validation, later
write failure, and external edits before and during replacement.

The browser journey covers selection, import, saving, duplicate names,
Undo/Redo, stale tabs, unsaved fields, independent frame colours, reuse of the
verified recording, finished-export posters, visible desktop playback and the
narrow-screen layout. It also checks for JavaScript errors and the rendered
Paper poster's background colour.

An intermediate browser run found that the edit helper saved a frame colour
but did not return the response to its caller, leaving the current-style label
stale. Returning that response fixed the regression. Visual inspection also
found that a raw-take poster hid the applied style; finished edits now produce
their own poster and the studio uses it.

## Limits and next work

Styles do not choose fonts, copy logos, alter app themes, or measure caption
contrast and overlap. Saving a mixed-look project uses its first browser
take's caption settings; applying the saved style sets all TOML browser takes.
The library remains optional and independently editable.

Studio undo history lasts for that server session. CLI applies have no
persistent undo stack; project files remain reviewable in version control.
Always inspect actual export sizes, especially after framing shrinks the app.
No Linux or Windows trial was added. Beat sequencing, destination readability
feedback and convenient narration/audio controls remain following milestones.
