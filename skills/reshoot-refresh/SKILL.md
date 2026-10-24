---
name: reshoot-refresh
description: Update an existing reshoot demo after an app or release changes. Use when a saved storyboard, video, or README clip needs recording again.
---

# Refresh a demo

For combined web and VHS edits, keep take dimensions matched. Mixed previews retain the configured browser dimensions to match the unchanged VHS output size.

Requires reshoot CLI 0.3.4 or newer. Run `reshoot --version`; if it is older, or `reshoot doctor` says a newer release is out, upgrade with `uv tool install --upgrade 'reshoot[browser]'` before going on. For a versioned browser/VHS project, read its brief, config, storyboard and previous run before changing anything, then run `reshoot doctor --config CONFIG`. Use `reshoot runs PROJECT` to list runs; a run path ending in `accepted` or `latest` resolves to the newest accepted or successful run. Record the exact ID of the baseline you compare against, since aliases move as new runs finish. When there is no `demo/accepted`, compare against the newest final run in `reshoot runs`, and tell the owner it was never accepted.

For a standalone native recording, read the brief, capture/edit scripts and exact previous media instead of expecting a versioned config or run report. Look up the current demo window ID, reset synthetic data, and use `reshoot window APP NEW_TAKE.mov --id ID -s SECONDS` with app-specific automation or coordinated manual interaction. Keep test and fresh final takes in new folders; edit and scan final exports. Compare the old/new MP4s and animated GIFs manually. Disclose that browser assertions, versioned `preview`/`run`, and automated beat comparison do not apply. Follow the versioned flow below only for browser/VHS projects.

Reset the made-up demo data and record the current app using `reshoot preview CONFIG`. Retain stable beat names. Diagnose failures using the beat, screenshot, and expected result. A selector repair should still perform the same task; it must not delete a failed assertion or replace the intended result with whatever the app happens to show.

When authorized to make local fixes, update the smallest necessary part, then rerun the affected flow. Use a full fresh `reshoot run CONFIG` for the final take. Keep the previous run. Read the report for execution errors, scan coverage, and pending human review.

A failed or missing browser take leaves the overall expectations unverified unless an assertion explicitly failed. Earlier passed assertions do not establish the result of an incomplete flow.

Compare the previous and new runs by beat with `reshoot compare` and inspect the actual frames. For a native capture, which has no run, show the old and new recordings and say that comparison is manual. A successful run must not silently replace the chosen comparison baseline or inherit approval from it.

Use only made-up data and page, terminal, or single-window capture. Call out changes to the story's claim, fixture meaning, speed, or narration. Present the new files and unresolved items. The new run needs its own verdict: give the owner its `reshoot accept RUN` command, and do not run it without their explicit instruction. Publishing and repository changes follow the owner's existing authorization.
