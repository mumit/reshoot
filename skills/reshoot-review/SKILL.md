---
name: reshoot-review
description: Inspect a reshoot recording and its check report for failed actions, privacy findings, coverage gaps, and readability before sharing.
---

# Review a recording

Requires reshoot CLI 0.2 or newer. Read the project's brief and current run report. Confirm that the files belong to that run, and distinguish execution, expected results, automatic scanning, and human review.

Use `reshoot check SOURCES --review REVIEW_DIR` to generate a check report and sheets. Include final exports as well as available source images. Use `--full` for final exports when feasible. The default video scan samples every three seconds and can miss brief content. Read the reported coverage and unavailable detectors. A clean scan does not prove a recording contains no private content.

Check exits 0 for accepted supplied items, 1 for human review pending, and 2 for an error. Missing or unreadable sources must be fixed before accepting the review. `--no-scan` explicitly skips detectors; it is not a scan pass.

Inspect sheets and original frames, then watch the final video, with sound when present. Check the stated result, text size, caption wrapping, timing, audio, end card, and any mock or speed labels. Use only made-up data. Fail private names, accounts, files, tokens, or unintended people shown in the recording.

If this CLI provides `reshoot review`, use its local page to inspect timestamps and comparisons. Otherwise use the sheets and a video player. Report that limitation.
Previous and current GIFs display as images in the comparison page; inspect their
animation and loop as well as the MP4 playback.

The owner decides whether a recording is accepted. Do not run `check --ok`, import approval, or promote a baseline merely because your inspection found nothing. Carry out those actions when the owner explicitly authorizes the decision. Give the owner the files, evidence, and unresolved findings; do not publish without authorization.

`check --text-file FINAL.srt` scans exact caption text. Runs also check generated
subtitle and narration sidecars. Inspect text findings at their recorded cue times.
