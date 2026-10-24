# Reshoot in CI

Use CI to record a demo again when the app changes. When a renamed button breaks
the storyboard, the recording job fails and identifies the beat. Review the new
run before replacing the previous video or README GIF.

Start with a working local browser/VHS project and its reset procedure. Use the
[local tutorial](step-by-step.md) if you need an example; it is not required for
an app that already records correctly. Native windows require an interactive
macOS capture session and are outside these Ubuntu templates. There are three
CI examples: a refresh workflow that opens a pull request for versioned projects,
a record-only workflow, and the original pull-request workflow for legacy
`[keep]` projects. All pin supporting actions to reviewed commits.

## Versioned projects: open a pull request with the refreshed demo

Copy [examples/github/refresh.yml](../examples/github/refresh.yml) into
`.github/workflows/reshoot.yml` in your app repository and change the marked
lines. Before the first run:

1. Record a final with `reshoot run demo/reshoot.toml`, watch it, and accept
   it with `reshoot accept demo/latest`. `accept` refuses a preview, which is
   made smaller and quicker than a final. It writes `demo/accepted/`, a small
   record of that run: its report, beat results and evidence frames, without
   the media. Commit it with the demo source.
2. In the repository's Settings, Actions, General, turn on "Allow GitHub Actions
   to create and approve pull requests". The pull request step fails without it.
3. Add the steps your app needs before it can start, such as installing packages.

When the app or demo source changes on `main`, or when started by hand, the workflow:

1. records a fresh run of `demo/reshoot.toml`;
2. compares it beat by beat with `demo/accepted`;
3. copies the new MP4 and GIF into `docs/demo/` and the new run's record into
   `demo/accepted/`, with the first frame of each scan finding;
4. uploads the run, its review page and scan sheets as the `reshoot-review` artifact;
5. opens a pull request on the `reshoot/refresh` branch.

The pull request shows the new GIF, a link to the MP4 on its branch, each
scan finding with its first frame, and a table of matched, added and removed
beats, with whether each one's definition, duration, frame pixels and results
changed. Pixel changes are common and small; watch the video. The full scan
sheets and review page stay in the artifact. [Review a refresh pull request](team.md#review-a-refresh-pull-request)
lists the steps. **Merging the pull request accepts the recording**: the next
run compares against it. Close the pull request to keep the current demo.

`reshoot export --markdown` writes the media and findings part of the
description, and `--link` makes its paths URLs on the pull request's branch.
Finding frames go into `demo/accepted/findings/`, and only for findings in the
files the export copies. In a private repository, the images show to people
who can read it.

If the repository has no `demo/accepted/` yet, the first run still opens a pull
request, without a comparison. Merging it starts the record.

When a change breaks the story, such as a renamed input, the run fails on that
beat and opens no pull request. The job's summary page names the beat and its
target, for example `type target {css = '#q'} matched 0 elements`, and the
artifact holds a screenshot of the failure. Repair the story locally or with
the [refresh skill](../skills/reshoot-refresh/SKILL.md), push, and the next run
opens the pull request. The workflow never repairs a story itself.

The `!demo/accepted/**` path keeps a merged refresh from starting another run.
Adapt the other paths to your app's source.

## Versioned projects: record a run only

[examples/github/candidate.yml](../examples/github/candidate.yml) records a
run, writes its review page and uploads `demo/takes/` even when recording
fails. It does not change the repository or open a pull request. Use it to test
CI recording before adopting the refresh workflow. After a run, download the
`reshoot-review` artifact, open `review.html` locally and keep the folder
structure intact so media and original frames remain linked. Review the exports
and sheets as in the [tutorial](step-by-step.md#4-accept-the-recording).
A recording that worked and an uploaded artifact are not an acceptance.

## Choose when to record

The refresh template records on changes to `main` and by hand. The record-only
template starts by hand only. To add releases, or to record a run on
relevant changes, use an `on:` block like this:

```yaml
on:
  workflow_dispatch:
  release:
    types: [published]
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'demo/**'
      - 'package.json'
      - 'package-lock.json'
      - '.github/workflows/reshoot.yml'
```

Adapt the branch, source paths and dependency files to your app. This is a
trigger fragment, not a complete workflow; keep the template's job, permissions
and artifact upload. GitHub combines branch and path filters for a push event;
see its [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
and [trigger guide](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

The job replays the checked-in story. It does not run an agent to repair a
selector, accept exports or publish a post. Repair failures locally and keep
the failed artifact for diagnosis. Use an isolated reachable test service for
URL-only projects; hosted state and rate limits can affect repeatability.
For private test services, use the app's supported CI secret setup and keep
credentials outside the storyboard and artifacts.

Return to [maintaining and publishing](publish.md) to promote reviewed media
locally. The record-only workflow requires read access and does not need
the pull-request permissions described in the legacy section below.

## Legacy projects: open a media pull request

The original [PR workflow](../examples/github/reshoot.yml) uses the legacy
`[keep]` path. It does not copy runs from versioned projects without an
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
  and inspect the diff before keeping those changes. Versioned runs require
  a separate local export.
- **Something already on the port.** `reshoot run` stops if the app's URL answers before it starts the app, so a
  take never shows a different server by mistake.
- **Agent takes in CI.** A Claude Code take needs an account and a key in CI, and its output varies more than a
  script's. Record those locally and retain the file for the CI edit when appropriate.
