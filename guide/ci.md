# Reshoot in CI

Use CI to record a demo again when the app changes. When a renamed button breaks
the storyboard, the recording job fails and identifies the beat. Review the new
candidate before replacing the previous video or README GIF.

First complete the [local tutorial](step-by-step.md). New projects use versioned
run folders and retain candidates until an explicit local export. There are two
CI examples: a candidate-only workflow for these projects, and the original
pull-request workflow for legacy `[keep]` projects. Both pin supporting actions
to reviewed commits.

## Versioned projects: retain a candidate for review

Copy [examples/github/candidate.yml](../examples/github/candidate.yml) into
`.github/workflows/reshoot.yml` in your app repository. Commit the demo's source
files, change the configuration and artifact paths if needed, and add the app's dependency
setup before recording. The sample starts manually with `workflow_dispatch`.

The workflow runs `demo/reshoot.toml`, generates a local review page for a
successful run, and uploads `demo/takes/` even when recording fails. It does not
copy files into the README or open a pull request. The action uses the installed
Chrome on the Ubuntu runner and installs ffmpeg and text scanning dependencies.
For a standalone Linux environment, follow the [installation guide](install.md).

After a run, download the `reshoot-review` artifact, find its run folder and
open `review.html` locally. Keep the folder structure intact so media and
original frames remain linked. Review the exports and sheets as in the
[tutorial](step-by-step.md#4-review-the-recording-and-scan-sheets). Recording
success and an uploaded artifact are not approval.

After recording review decisions locally, use `reshoot export` to copy the chosen
files into a new destination, then update the repository's demo media.
To add a release trigger, use the event syntax in the legacy example.
Verify the template's first run against your app's setup and runner environment.

## Legacy projects: open a media pull request

The original [PR workflow](../examples/github/reshoot.yml) uses the legacy
`[keep]` path. It does not copy candidates from versioned projects without an
explicit export step. Choose this route only when retaining that layout.

### The shoot file

`reshoot run` does a whole shoot from one `reshoot.toml`: it starts the app, waits until it answers, records each
take, runs the edit script, makes the review sheets, copies the finished files where they're kept, and stops the
app. The same configuration works locally and in CI. See the notes example:
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

`reshoot run --help` describes the legacy shoot settings. The
[project reference](projects.md) documents versioned files. A failed step stops
the shoot, stops the app, and exits with an error.
`takes/run.json` says what happened.

### The GitHub workflow

1. Copy [examples/github/reshoot.yml](../examples/github/reshoot.yml) to `.github/workflows/reshoot.yml`.
2. Let workflows open pull requests: in the repository's Settings, Actions, General, turn on "Allow GitHub Actions to
   create and approve pull requests". It's off by default, and the pull request step fails without it.
3. Add the steps your app needs before it can start (installing packages, a demo database).
4. Change the marked lines: where the shoot file is, the takes folder, and where `[keep]` copies files.

On each release (or when started by hand), it:

1. installs ffmpeg, VHS if the shoot has a tape, and reshoot, on Ubuntu (Chrome is already there);
2. runs the shoot;
3. uploads the takes, review sheets and report as an artifact called `reshoot-review`;
4. opens a pull request with the new files from `[keep]`.

## Review CI outputs

CI doesn't decide what's safe to show. The pull request says how many images haven't been checked, and how many the
scan flagged (on Linux it reads text with Tesseract, which the action installs; faces and people need macOS). Flags
come first on the sheets, and the run's log shows only masked parts of what was found. Before merging,
download the `reshoot-review` artifact, inspect every sheet at full size, and watch
the new video. If an item fails, fix the demo data and run the workflow again.

Keep demo data in the repository or generate it in a setup step so CI can use it.
Data committed to a public repository is public too. Use only data suitable for sharing.

## Pitfalls

- **Linux draws things differently.** Fonts and emoji differ from macOS, so text can wrap in new places. Watch the
  first video from CI closely, and set fonts in the app if it matters.
- **Checks wait on the pull request.** GitHub doesn't run workflows on a pull request opened by
  `github-actions[bot]` until someone approves them: the run shows "action_required". Approve it on the pull
  request's Checks tab, or open the pull request with a GitHub App or personal token instead of `GITHUB_TOKEN`.
  [GitHub documents this approval behavior](https://docs.github.com/en/actions/concepts/security/github_token).
- **Legacy local runs change kept files too.** With legacy `[keep]`, `reshoot run`
  copies the new video into `docs/demo/`. Use a disposable checkout for experiments
  and inspect the diff before keeping those changes. Versioned candidates require
  a separate local export.
- **Something already on the port.** `reshoot run` stops if the app's URL answers before it starts the app, so a
  take never shows a different server by mistake.
- **Agent takes in CI.** A Claude Code take needs an account and a key in CI, and its output varies more than a
  script's. Record those locally and retain the file for the CI edit when appropriate.
