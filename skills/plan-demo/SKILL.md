---
name: plan-demo
description: Start here to make a demo video of software (a web app, a CLI, an AI agent such as Claude Code, a desktop app). Plans the takes and writes the storyboard, then hands off to record-web, record-terminal, record-window, check-privacy, cut-video and keep-current. Use when someone asks for a demo video, launch video, screencast, product tour or GIF of their app.
---

# Plan a demo video

Keep a recipe for every take so the video can be shot again when the app changes.
Use browser storyboards, VHS tapes or app-specific native automation. For a
native app without automation, coordinate manual interaction during one-window
capture and save the steps; disclose that replay is manual.

## Rules

- Never record the whole screen. Record a headless browser page, a VHS terminal, or one window by its id.
- Use demo data only, never the person's real data. If there is no demo data yet, making it is the first job.
- Nothing is posted, pushed or shared without the person's yes. The finished files stay local.

## Steps

1. **Ask what the video is for** if it isn't clear: where it will be posted (X, LinkedIn, a README, a talk), how
   long (30 to 60 seconds suits social posts), and the 3 to 6 things it should show.
2. **Pick a take for each part:**

   | What's shown | Take | Skill |
   |---|---|---|
   | A web page or web app | headless Chrome from a storyboard | record-web |
   | A terminal, a CLI, an AI agent | a VHS tape | record-terminal |
   | A desktop app | one window, by its id (macOS) | record-window |

   Match the take to the actual target. Use a browser for a web app, VHS for a
   CLI, and one-window capture for a native app. Do not substitute a mock web
   page for the native app the owner asked to show.
3. **Set up demo data.** A separate database, data folder or account with only things anyone may see. Check that the
   app can point at it (an environment variable, a flag) and that it can't touch real data during a take. Good demo
   data has made-up people (emails at `example.com`), no real customers or colleagues, test keys only, photos
   without people, and enough varied items to look real. If the app needs a login, make a demo account.
4. **Write the storyboard** as beats. Each beat is one action and a hold. For each section of the video:
   - a caption that says what the app does, in plain words, at most about 8 words, with an optional small line;
   - the action (type, click, open a view);
   - for a web take, what has to happen before recording (logging in, clearing old state) and which views load
     slowly (maps, charts, big images);
   - a hold long enough to read: about 1.5 s for a short caption, 2.5 s or more for a result.
   Name the beats. The cut uses beat names to trim and to make one GIF per section.
5. **Record each take** with its skill, then **check it** with check-privacy, then **cut** with cut-video.
6. **Show the person the finished files** and the list of what was checked. They watch it all before it goes
   anywhere.
7. **Offer to keep it current** with the keep-current skill for browser/VHS projects: a `reshoot.toml` for `reshoot run`, and a workflow
   that reshoots on each release. Keep native capture/edit scripts separately and compare recordings manually.

## Files to keep in the project

Put the storyboards, tapes and edit script in the project (for example `tools/demo/`), and the takes and cuts in a
git-ignored folder (for example `takes/`). Write a short README there with the commands in order, so the next
reshoot is quick. This plugin's guide (`../../guide/` from this skill's folder) explains each step and lists the
pitfalls, and `../../examples/notes/` has a full example to copy from.

## Install

The skills run the `reshoot` command. If it's missing: `uv tool install 'reshoot[browser]'`. It
also needs ffmpeg, VHS for terminal takes, and Chrome or Chromium for web takes. On macOS: `brew install ffmpeg vhs`.
On Linux, use the package manager.

## Project setup

For browser/VHS projects, run `reshoot doctor --config reshoot.toml` when a project exists. For a new browser project, `reshoot init demo --url URL` supplies packaged templates without a source checkout. Fill in `BRIEF.md`, replace the placeholder action, then use `reshoot preview demo/reshoot.toml` before a full `run`. Versioned project outputs are isolated per run. Use standalone capture and editing for native windows.
