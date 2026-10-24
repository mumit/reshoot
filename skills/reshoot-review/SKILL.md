---
name: reshoot-review
description: Inspect a reshoot recording and its check report for failed actions, privacy findings, coverage gaps, and readability before sharing.
---

# Review a recording

Requires reshoot CLI 0.3.4 or newer. Run `reshoot --version`; if it is older, or `reshoot doctor` says a newer release is out, upgrade with `uv tool install --upgrade 'reshoot[browser]'` before going on. Read the project's brief and, for a versioned project, its current run report. Confirm which attempt produced the files, and distinguish execution, expected results, automatic scanning and human review.

For standalone native media, read its capture/edit recipe and exact source/export paths instead of requiring or inventing a run report. Compare old and new recordings manually and identify the result visually; do not claim browser assertions or automated beat comparison. Use a video player and check sheets rather than `reshoot review RUN`, which requires a versioned run manifest. Preserve existing reviews; generate any new scan in a separate directory.

Use `reshoot check SOURCES --review REVIEW_DIR` to generate a check report and sheets. Include final exports as well as available source images. Use `--full` for final exports when feasible. The default video scan samples every three seconds and can miss brief content. Read the reported coverage and unavailable detectors. A clean scan does not prove a recording contains no private content.

Check exits 0 for accepted supplied items, 1 for human review pending, and 2 for an error. Missing or unreadable sources must be fixed before accepting the review. `--no-scan` explicitly skips detectors; it is not a scan pass.

Inspect sheets and original frames, then watch the final video, with sound when present. Check the stated result, text size, caption wrapping, timing, audio, end card, and any mock or speed labels. Use only made-up data. Fail private names, accounts, files, tokens, or unintended people shown in the recording.

For a versioned run, use the local page from `reshoot review RUN` to inspect timestamps and comparisons. For a native capture, which has no run, use the sheets and a video player, and say so.
Previous and current GIFs display as images in the comparison page; inspect their
animation and loop as well as the MP4 playback.

The owner decides whether a recording is accepted. For a versioned run, give the owner the exact command: `reshoot accept RUN`, plus `--flagged LABEL` for each flagged item they must inspect, or `--reject LABEL` for one that fails. Do not run `accept`, `check --ok` or an import, pass `--yes`, or promote a baseline merely because your inspection found nothing. Carry out those actions only when the owner explicitly authorizes the decision. Give the owner the files, evidence, and unresolved findings; do not publish without authorization.

`check --text-file FINAL.srt` scans exact caption text. Runs also check generated
subtitle and narration sidecars. Inspect text findings at their recorded cue times.
