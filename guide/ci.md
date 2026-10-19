# Reshoot in CI

Once a video's takes are scripts, a CI job can record them again whenever the app changes. I use it so a release
never ships with a stale demo video or README GIF. When a button is renamed and the storyboard breaks, the job fails
and names the beat.

## The shoot file

`reshoot run` does a whole shoot from one `reshoot.toml`: it starts the app, waits until it answers, records each
take, runs the edit script, makes the review sheets, copies the finished files where they're kept, and stops the
app. It's just as useful on my own machine as in CI. The notes example has one:
[examples/notes/reshoot.toml](../examples/notes/reshoot.toml).

```toml
[app]
run = "npm run dev -- --port 8000"
url = "http://localhost:8000/"

[[take]]
web = "tools/demo/storyboard.py"
out = "takes/web.mp4"

[[take]]
tape = "tools/demo/cli.tape"

[edit]
script = "tools/demo/edit.py"
args = ["takes/web.mp4", "takes/cli.mp4"]

[check]
sources = ["takes/web.assets.json", "takes/final.mp4"]
review = "takes/review"

[keep]
"takes/final.mp4" = "docs/demo/demo.mp4"
"takes/web.gif" = "docs/demo/demo.gif"
```

`reshoot run --help` lists every setting. A failed step stops the shoot, stops the app, and exits with an error.
`takes/run.json` says what happened.

## The GitHub workflow

1. Copy [examples/github/reshoot.yml](../examples/github/reshoot.yml) to `.github/workflows/reshoot.yml`.
2. Let workflows open pull requests: in the repo's Settings, Actions, General, turn on "Allow GitHub Actions to
   create and approve pull requests". It's off by default, and the pull request step fails without it.
3. Add the steps your app needs before it can start (installing packages, a demo database).
4. Change the marked lines: where the shoot file is, the takes folder, and where `[keep]` copies files.

On each release (or when started by hand), it:

1. installs ffmpeg, VHS if the shoot has a tape, and reshoot, on Ubuntu (Chrome is already there);
2. runs the shoot;
3. uploads the takes, review sheets and report as an artifact called `reshoot-review`;
4. opens a pull request with the new files from `[keep]`.

## The check by eye still happens

CI doesn't decide what's safe to show. The pull request says how many images haven't been checked. Before merging,
I download the `reshoot-review` artifact, look at every sheet at full size, and watch the new video. If something
fails, I fix the demo data and run the workflow again.

The demo data has to be in the repo (or made by a setup step) for CI to use it. That means it's as public as the
repo. Only put in what anyone may see.

## Pitfalls

- **Linux draws things differently.** Fonts and emoji differ from macOS, so text can wrap in new places. Watch the
  first video from CI closely, and set fonts in the app if it matters.
- **Checks wait on the pull request.** GitHub doesn't run workflows on a pull request opened by
  `github-actions[bot]` until someone approves them: the run shows "action_required". Approve it on the pull
  request's Checks tab, or open the pull request with a GitHub App or personal token instead of `GITHUB_TOKEN`.
- **Something already on the port.** `reshoot run` stops if the app's URL answers before it starts the app, so a
  take never shows a different server by mistake.
- **Agent takes in CI.** A Claude Code take needs an account and a key in CI, and its output varies more than a
  script's. I record those on my own machine and keep the file in the repo.
