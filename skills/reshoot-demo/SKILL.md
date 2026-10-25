---
name: reshoot-demo
description: Create a repeatable software demo with reshoot from an app and demo data. Use for product demos, release videos, README clips, and launch recordings.
---

# Create a demo

The studio status distinguishes unsaved fields, saved changes and the displayed
recording. Section links open the relevant controls. Fix invalid fields or use
Reset unsaved edits; reload when another editor changes the project. Download
all exports produces a ZIP of the shown run, with subtitles, image Markdown
and a hash/status manifest. It does not accept or publish anything.

Saved Undo/Redo survives a studio restart. Resume history only when tracked
files match; Start with current files preserves the project and archives the
old checkpoint. Download saved source copy supports manual comparison after
external edits. Recovery choices do not restore files or accept media. Unsaved
fields and running jobs are not checkpointed.

Requires reshoot CLI 0.3.6 or newer. Run `reshoot --version`; if it is older, or `reshoot doctor` says a newer release is out, upgrade with `uv tool install --upgrade 'reshoot[browser]'` before going on. Run `reshoot doctor --config CONFIG` for an existing project. If the CLI is missing, use the repository's documented installation; do not invent commands for a different version.

Resolve missing required tools before recording. If `RESHOOT_CHROME` is set, it must name an executable browser; correct or unset a stale path. Use `reshoot doctor --config CONFIG --probe` to test temporary synthetic video encoding, TOML browser capture and configured OCR. Default doctor checks availability/versions and the required Vision text reader; neither mode validates the app, positive face detection or final media. Respect the configured OCR/scan choice and fix failures instead of turning scans off.

Creation keeps its first-run state under ignored `takes/`. Recording tools in
the studio offers fixes, Check again and Continue creation. Use `reshoot create
--resume --directory demo` after fixing setup or a failed preview. It retains
the saved story, URL and viewport; completed creation opens the studio without
recording again. Do not pass another app URL or size when resuming. If a draft
changed before or during demonstration, preserve it and compare the separately
saved recording; do not overwrite those changes. Restart reshoot after changing
shell settings or its Python environment. Probe/check buttons install nothing.

Identify the target: app source, a running web URL, or an installed native macOS app. Source code is optional. Inspect code and demo fixtures when available; otherwise inspect the actual page or window. Choose one useful task with a visible result, audience and destination. Ask only for missing details that materially affect the story.

If the owner wants to demonstrate the task themselves, offer `reshoot create URL --directory demo`. It opens a fresh browser with Done, Pause, Caption here, Check result, Hide and Remove last step controls, then makes a preview and opens the studio. Without a URL it tries notes. This is interactive: do not start it and wait for the owner during an autonomous agent recording. The studio edits captions and holds, supports Undo/Redo, chooses the work with Update preview, makes a final and shows scan sheets. Decisions stay bound to the displayed run. Unresolved `recording_issue` steps must be repaired, never silently removed to make a recording pass.

For a new browser project, use `reshoot init DIR --url DEMO_URL`; omit `--url` to try the packaged notes example. Fill in `BRIEF.md`. Replace the placeholder with actual actions and result checks, keeping an `end` beat if the edit uses it. Inspect the page's DOM or use `reshoot rec URL DRAFT.toml` when no source is available. Recorder drafts suggest result checks from what each action changed, marked `# suggested`; keep the ones that show the result and delete the rest, then add captions, purposes and better beat IDs. An external URL project has no managed server unless `[app]` is added. Resolve login with an isolated demo account in a fresh profile. The generated files are in the project, not in this skill folder. Read `reshoot web --help` for storyboard settings and `reshoot run --help` for configuration.

For a native macOS app, save a brief, capture recipe and edit script in a demo folder. Use `reshoot window --list` to select the exact demo window, then `reshoot window APP NEW_TAKE.mov --id ID -s SECONDS`. Check Screen Recording permission for the command's host. Drive the app through app-specific automation or coordinate the owner's interaction during capture; the window command does not operate controls. Look up the ID each take and choose unused output paths. Versioned projects support web and VHS, not native window takes. Do not invent a native run manifest, browser overlay or result checks. Export with `reshoot edit EDIT.toml NEW_TAKE.mov`, using numeric cuts, and a GIF export profile, or a Python edit. The primary skill can follow this route without supporting plugin skills.

Use made-up data in a separate account, folder, or database. Document and run its reset before each take. When a running app keeps data and offers no reset, ask for one before the first take, or write checks that pass however many times the task has run: check the item the take created, not totals that earlier takes change. Record only a headless browser page, VHS terminal, or one macOS window by ID. Never capture the whole screen or reuse a person's browser profile.

For browser/VHS projects, run `reshoot preview CONFIG`, inspect frames and result checks, then `reshoot run CONFIG`. The run ends with its result checks, scan items, exports and review page; read its `run.json` for detail. For native apps, inspect a standalone test take, then capture and edit a fresh final in a new folder. Generate check sheets for source and final media with `reshoot check SOURCES --full --review NEW_REVIEW_DIR`. Inspect actual outputs on either route. Execution success does not mean a scan passed or a person reviewed the video. When the owner wants a quicker refresh of checked data, follow the trade-offs in the guide's `speed.md` and say which checks were reduced; agent-written terminal text always needs reading. Fix failed inputs and actions rather than suppressing checks. End with the same handoff each time: one sentence on the task and its result; the MP4, GIF and review page paths, opened when possible; the run's status line; anything the owner must look at, such as flagged items, reduced checks or mocked data; "Reply accept, or ask for changes such as:" with two or three changes that fit, such as shorter captions, a longer hold on the result or a narrower viewport for GIF text; and the `reshoot accept` command the run printed, with `reshoot review RUN --serve` for deciding on the page and `reshoot studio DIR` for shaping captions, cards, the frame, music and exports, re-cutting, recording from a beat and accepting; both wait for the owner, so do not start them or click their buttons yourself. Changes the owner makes in the studio are saved to the storyboard, `edit.toml` and `[check] sources`; read them again before editing them. Run `reshoot accept RUN --yes` only when the owner replies accept or otherwise explicitly asks. After accepting, offer `reshoot export demo/accepted --directory docs/demo` and the README Markdown it prints.

For combined web and VHS edits, configure matching take dimensions. Mixed previews retain the browser's configured dimensions because VHS keeps its tape dimensions.

Keep captions short and explain the result, not the click. Leave time to read. Judge text size in the README GIF, which is usually 800 px wide: when the app's content is a narrow column in the 1280x720 frame, set a narrower `size`, such as `"960x540"`, or `zoom = true`, so the result stays readable. A narrower viewport enlarges the text; a higher pixel ratio does not. For a dropdown, use a `select` action with the option's visible label rather than key presses. Identify mocked responses or shortened waits. Do not change the product claim merely to make a recording finish.

Inspect captions after page navigation. TOML storyboard captions are drawn after recording, as plain text, so `reshoot recut RUN` can change their words and look; Python storyboard captions are drawn in the page unless zoomed.

Commit, push, or publish only within the owner's existing authorization. Creating local files is not publishing. Keep changes in the demo folder: don't edit the app's README, `.gitignore` or other files unless the owner asks; offer the Markdown that would add the GIF instead.
