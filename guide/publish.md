# Maintain and publish a demo

Keep the recording source with the app when you develop it, or in a separate
demo repository when you only have a URL or installed app. Save a working local
recording before moving to automation.

## Keep an explicit baseline

Commit the brief, story, edit, configuration and synthetic reset scripts when
ready. Keep credentials out of them. Ignore generated `takes/` directories;
archive the accepted run separately and note its exact ID and app revision.
Keep that folder and its evidence available for comparison, even if it is not
in Git. Do not select a baseline just because it is the most recent attempt.

When the app changes, use the
[refresh prompt](agent-quickstart.md#update-the-demo-when-the-app-changes) or
record through the CLI:

```bash
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
reshoot review demo/takes/runs/NEW_ID --previous demo/takes/runs/ACCEPTED_ID
```

Replace both IDs with the printed run folders. Inspect the preview before the
final. Preserve stable beat IDs and the task's expected result. If a changed
label breaks a target, repair the selector rather than deleting its check.
Compare the finished exports and review the new scan evidence. Approval of the
old recording does not accept the new one.

For native windows, record to a new folder using the saved
[capture recipe](macos-window.md), look up the current window ID, and compare
old and new exports manually. Native captures do not use versioned beat
comparison or `reshoot export`.

## Prepare files for sharing

After recording and scan-sheet approval, select the versioned run's exports:

```bash
reshoot export demo/takes/runs/NEW_ID --directory demo/exports-v2 --file takes/demo-final.mp4 --file takes/demo-final-readme.gif --file takes/demo-final.srt
```

Use the actual run ID and artifact names from its report. Choose an unused
destination directory. The command copies selected files locally and refuses
to overwrite; it does not upload them. For standalone native media, copy the
approved MP4 and GIF into a new sharing folder yourself.

| Destination | Prepare |
|---|---|
| GitHub README | A short, readable GIF; add alt text and a link to the full MP4 |
| X or LinkedIn | An MP4 that explains the result without sound; review any crop at actual size |
| Product guide or tutorial | The fuller MP4, subtitles when available, and written prerequisites |

For a repository, copy approved files to `docs/demo/` and link them from the
README. Check the rendered page and playback before publishing. The exported
subtitle file is useful for players and upload flows that accept SRT; confirm
the destination's current requirements. Keep the source project out of the
viewer's way, but available to maintainers.

Ask the agent to prepare these files and draft copy, then authorize any commit,
push or public post explicitly. Recording success does not publish anything.

## Automate candidate recordings

Start with a local script that calls `reshoot run demo/reshoot.toml` and retains
its exit status and run folder. Resolve startup, fixtures and secrets locally.
Then use the [GitHub Actions guide](ci.md) to record on demand, after relevant
commits or on releases, and retain review artifacts even on failure.

CI replays the configured task. It does not author a story, repair broken
selectors or approve media. Repair failures locally, then record another
candidate. Keep publication separate from candidate generation until you have
an explicit review and promotion process. The browser/VHS template does not
automate native windows on a hosted Ubuntu runner.
