---
name: reshoot-refresh
description: Update an existing reshoot demo after an app or release changes. Use when a saved storyboard, video, or README clip needs recording again.
---

# Refresh a demo

Requires reshoot CLI 0.2 or newer. Read the project's brief, config, storyboard, and previous run before changing anything. Run `reshoot --version` and `reshoot doctor --config CONFIG`.

Reset the made-up demo data and record the current app using `reshoot preview CONFIG`. Retain stable beat names. Diagnose failures using the beat, screenshot, and expected result. A selector repair should still perform the same task; it must not delete a failed assertion or replace the intended result with whatever the app happens to show.

When authorized to make local fixes, update the smallest necessary part, then rerun the affected flow. Use a full fresh `reshoot run CONFIG` for the final take. Keep the previous run. Read the report for execution errors, scan coverage, and pending human review.

If this CLI version provides `reshoot compare`, compare the previous and new runs by beat and inspect the actual frames. Otherwise, show the old and new recordings and disclose that comparison is manual. A successful run must not silently replace the chosen comparison baseline or inherit approval from it.

Use only made-up data and page, terminal, or single-window capture. Call out changes to the story's claim, fixture meaning, speed, or narration. Present the new files and unresolved items. Publishing and repository changes follow the owner's existing authorization.
