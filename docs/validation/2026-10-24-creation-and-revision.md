# Creation and revision workflow

On 2026-10-24, the local macOS checkout was exercised with synthetic notes data
to verify the [creation and revision plan](../../UX_PLAN.md). Existing Chrome,
ffmpeg and Vision installations were used. These are automated and agent-operated
checks, not independent-user usability research or owner acceptance of media.

## What changed

- `reshoot create [URL] --directory demo` checks dependencies, records a task
  or tries notes, makes a preview and opens the studio. The default 960x540
  viewport gives the app more of the export; its pixel ratio is 1.5.
- The TOML recorder has Done, Pause, Caption here, Check result, Hide and
  Remove last step controls. Result selection does not activate the selected
  control. Checkbox and radio states replay as native `check` actions.
- Unsupported interactions preserve the other steps and leave a blocking
  `recording_issue`. They cannot silently produce a completed recording.
- The studio puts story beats before styling, edits holds, supports Undo/Redo,
  chooses between recording and re-cutting, cancels jobs and shows scan sheets.
  Failed fields remain visible and block updates until fixed.
- Media URLs name the exact run shown. Decisions include that run's artifact
  and scan binding. Project writes require the page's revision; stale tabs
  cannot overwrite a newer edit, and undo preserves external changes.

## Verification

| Check | Result |
|---|---|
| `uv run pytest -q` | 116 passed, 37 browser tests deselected |
| `uv run pytest -m browser -q` | 37 passed |
| Final focused creation, studio and served-review browser trials | 4 passed |
| Final creation regression module | 8 passed, 2 browser tests deselected |
| `claude plugin validate .` | Passed; warnings about root CLAUDE.md context and a missing plugin icon |
| Changed-document relative links and TOML snippets | Links exist; 21 snippets or alternative assignments parse |
| `uv run python examples/look/build.py` | Gallery rebuilt; frame, caption and export examples inspected |
| Python compilation, JavaScript syntax and `git diff --check` | Passed |

The complete browser suite and final focused trials ran separately as the
implementation was refined. The focused trial verified the final save guards,
hold changes, cancellation, source composition and recorded posters. The final
fast suite includes the notes viewport regression added afterwards.

The synthetic URL-only trial demonstrated pinning a checkbox, saving a note,
adding a caption, selecting its result check, hiding a link without navigating,
pausing, searching and finishing. Its generated story replayed successfully,
produced an MP4 and GIF, and opened on a nonblank app frame.

The studio trial changed a caption, undid and redid it, refused an invalid
colour and an update with that unsaved value, added a card and frame, and
automatically re-cut. Changing a hold caused a new recording. A partial replay
worked, and cancelling another update retained the previous recording. Server
regressions verified that an old tab's media and decision still name its old
run when a newer run exists, and that a changed scan rejects a stale decision.

## Fresh packaged-project smoke run

```bash
uv run reshoot create --directory takes/ux-implementation-20261024/final-smoke --no-studio
uv run reshoot run takes/ux-implementation-20261024/final-smoke/reshoot.toml --full
```

- Preview: 15 seconds, all 3 result checks passed, 6 scan items, 0 flags.
- Final: 75.8 seconds including the explicit full scan, all 3 result checks
  passed, 548 scan items on 137 sheets, 0 flags.
- MP4: 1440x810, 8.55 seconds. GIF: 800x450, 8.54 seconds.
- The opening and held-result frames were inspected. The notes task and its
  caption are legible; the opening frame contains the app.
- Final run: `dd2e99abee3e46c8a046601cac65990f`. Its media, report and review
  page are under the ignored smoke project's `takes/runs/` folder.

The full scan is opt-in and dominates this final's time. Neither its zero flags
nor frame inspection is an owner's approval. The sample remains unaccepted.
The already accepted media in `docs/demo/` was left unchanged.

## Limits and following work

Setup time on an unprepared machine was not measured. The URL-only flow was
driven with synthetic native input events, not a newcomer. No Windows or Linux
trial was added. Independent-user testing remains deferred by the owner.

Undo history lasts for the studio server's lifetime. Revision checks cover the
editable project files; they do not snapshot an external app or database.
Automatic re-cutting is conservative for multiple takes and older metadata.
After a remote app or untracked external data changes, explicitly record a new
preview even when also changing captions.

Visual locator repair, richer sequencing and framing, reusable styles and
convenient narration/audio controls remain following milestones. This work
establishes the core creation and revision loop; it does not establish that
reshoot has reached professional editing quality or the best possible UX.
