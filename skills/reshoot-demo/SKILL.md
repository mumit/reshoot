---
name: reshoot-demo
description: Create a repeatable software demo with reshoot from an app and demo data. Use for product demos, release videos, README clips, and launch recordings.
---

# Create a demo

Requires reshoot CLI 0.2 or newer. Run `reshoot --version` and `reshoot doctor --config CONFIG` for an existing project. If the CLI is missing, use the repository's documented installation; do not invent commands for a different version.

Resolve missing required tools before recording. If `RESHOOT_CHROME` is set, it must name an executable browser; correct or unset a stale path. A successful doctor check does not probe capture or the final scan.

Choose one useful task and a visible result. Use the app's code and existing demo setup to identify the audience, problem, task, expected result, destination, length, and next action. Ask only for missing details that materially affect the story.

For a new project, use `reshoot init DIR --url DEMO_URL`; omit `--url` to try the packaged notes example. Fill in `BRIEF.md`. Replace the placeholder with actual actions and result checks before recording. The generated files are in the project, not in this skill folder. Read `reshoot web --help` for storyboard settings and `reshoot run --help` for configuration.

Use made-up data in a separate account, folder, or database. Document and run its reset before each take. Record only a headless browser page, VHS terminal, or one macOS window by ID. Never capture the whole screen or reuse a person's browser profile.

Run `reshoot preview CONFIG`, inspect frames and expected results, then `reshoot run CONFIG`. Read the printed run report. Execution success does not mean a scan passed or a person reviewed the video. Fix failed inputs and actions rather than suppressing checks. Inspect the actual final recording and give the owner its files and pending review items.

For combined web and VHS edits, configure matching take dimensions. Mixed previews retain the browser's configured dimensions because VHS keeps its tape dimensions.

Keep captions short and explain the result, not the click. Leave time to read. Identify mocked responses or shortened waits. Do not change the product claim merely to make a recording finish.

Inspect captions after page navigation. The overlay restores the current caption on same-origin page loads; zoomed or styled captions are drawn after recording.

Commit, push, or publish only within the owner's existing authorization. Creating local files is not publishing.
