---
name: keep-current
description: Set up a reshoot.toml so one command (`reshoot run`) records a project's whole demo video again, and a GitHub Actions workflow that reshoots it on each release and opens a pull request. Use when someone wants their demo video or README GIF to stay up to date, or asks for demo videos in CI.
---

# Keep a demo video current

## Rules

- CI never publishes anything. The workflow opens a pull request; a person checks the review sheets and merges it.
- Demo data used in CI is in the repo, so it's as public as the repo. Only put in what anyone may see.
- Creating or pushing a workflow file is pushing: ask first.

## Steps

1. **Write `reshoot.toml`** at the project root, from the takes the project already has. `reshoot run --help`
   lists every setting; `../../examples/notes/reshoot.toml` (from this skill's folder) is a full example.
   - `[app]`: the command that starts the app on demo data, and the URL to wait for.
   - `[[take]]`: one per take, `web` (with `out`), `tape`, or `run` for any other command.
   - `[edit]`, `[check]`: the edit script and what to check.
   - `[keep]`: where the finished files go in the repo, such as `docs/demo/`.
2. **Run it locally:** `reshoot run`. Fix whatever fails. It stops at the first failed step and names it.
3. **Add the workflow:** copy `../../examples/github/reshoot.yml` to `.github/workflows/reshoot.yml`. Add the steps
   the app needs before it starts (installing packages, making demo data), and change the marked lines.
4. **Tell the person** what the workflow does, and that they review each pull request's sheets (the
   `reshoot-review` artifact) before merging. Push only with their yes.

## Pitfalls

- **Fonts differ on Linux,** so text may wrap differently from the local takes. Look at the first CI video closely.
- **Agent takes** (Claude Code) need an account and key in CI, and vary between runs. Record them locally and keep
  the file instead.
- **A server already running** on the app's port stops the shoot, so a take can't show the wrong server.
