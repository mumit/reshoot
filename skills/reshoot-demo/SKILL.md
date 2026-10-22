---
name: reshoot-demo
description: Create a repeatable software demo with reshoot from an app and demo data. Use for product demos, release videos, README clips, and launch recordings.
---

# Create a demo

Requires reshoot CLI 0.2 or newer. Run `reshoot --version` and `reshoot doctor --config CONFIG` for an existing project. If the CLI is missing, use the repository's documented installation; do not invent commands for a different version.

Resolve missing required tools before recording. If `RESHOOT_CHROME` is set, it must name an executable browser; correct or unset a stale path. A successful doctor check does not probe capture or the final scan.

Identify the target: app source, a running web URL, or an installed native macOS app. Source code is optional. Inspect code and demo fixtures when available; otherwise inspect the actual page or window. Choose one useful task with a visible result, audience and destination. Ask only for missing details that materially affect the story.

For a new browser project, use `reshoot init DIR --url DEMO_URL`; omit `--url` to try the packaged notes example. Fill in `BRIEF.md`. Replace the placeholder with actual actions and result checks, keeping an `end` beat if the edit uses it. Inspect the page's DOM or use `reshoot rec URL DRAFT.toml` when no source is available. Recorder drafts still need captions and assertions. An external URL project has no managed server unless `[app]` is added. Resolve login with an isolated demo account in a fresh profile. The generated files are in the project, not in this skill folder. Read `reshoot web --help` for storyboard settings and `reshoot run --help` for configuration.

For a native macOS app, save a brief, capture recipe and edit script in a demo folder. Use `reshoot window --list` to select the exact demo window, then `reshoot window APP NEW_TAKE.mov --id ID -s SECONDS`. Check Screen Recording permission for the command's host. Drive the app through app-specific automation or coordinate the owner's interaction during capture; the window command does not operate controls. Look up the ID each take and choose unused output paths. Versioned projects support web and VHS, not native window takes. Do not invent a native run manifest, browser overlay or result assertions. Export with `reshoot edit EDIT.toml NEW_TAKE.mov`, using numeric cuts, and a GIF export profile, or a Python edit. The primary skill can follow this route without supporting plugin skills.

Use made-up data in a separate account, folder, or database. Document and run its reset before each take. Record only a headless browser page, VHS terminal, or one macOS window by ID. Never capture the whole screen or reuse a person's browser profile.

For browser/VHS projects, run `reshoot preview CONFIG`, inspect frames and expected results, then `reshoot run CONFIG`. Read the printed run report. For native apps, inspect a standalone test take, then capture and edit a fresh final in a new folder. Generate check sheets for source and final media with `reshoot check SOURCES --full --review NEW_REVIEW_DIR`. Inspect actual outputs on either route. Execution success does not mean a scan passed or a person reviewed the video. Fix failed inputs and actions rather than suppressing checks. Give the owner the final files and pending review items.

For combined web and VHS edits, configure matching take dimensions. Mixed previews retain the browser's configured dimensions because VHS keeps its tape dimensions.

Keep captions short and explain the result, not the click. Leave time to read. Identify mocked responses or shortened waits. Do not change the product claim merely to make a recording finish.

Inspect captions after page navigation. The overlay restores the current caption on same-origin page loads; zoomed or styled captions are drawn after recording.

Commit, push, or publish only within the owner's existing authorization. Creating local files is not publishing.
