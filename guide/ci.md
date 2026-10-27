# Reshoot in CI

Use CI to record a demo again when the app changes. When a renamed button breaks
the storyboard, the recording job fails and identifies the step. Review the new
run before replacing the previous video or README GIF.

Start with a working local browser/VHS project and its reset procedure. Use the
[local tutorial](step-by-step.md) if you need an example; it is not required for
an app that already records correctly. Native windows require an interactive
macOS capture session and are outside these Ubuntu templates. There are two
examples: a refresh workflow that opens a pull request, and a record-only
workflow. Both pin supporting actions to reviewed commits. The older workflow
for legacy `[keep]` projects is in the [manual workflow](manual.md#legacy-shoot-files-in-ci).

## Versioned projects: open a pull request with the refreshed demo

Copy [examples/github/refresh.yml](../examples/github/refresh.yml) into
`.github/workflows/reshoot.yml` in your app repository and change the marked
lines. Before the first run:

1. Record a final with `reshoot run demo/reshoot.toml`, watch it, accept
   it with `reshoot accept demo/latest`, and commit
   [`demo/accepted/`](publish.md#the-accepted-run) with the demo source.
2. In the repository's Settings, Actions, General, turn on "Allow GitHub Actions
   to create and approve pull requests". The pull request step fails without it.
3. Add the steps your app needs before it can start, such as installing packages.

When the app or demo source changes on `main`, or when started by hand, the workflow:

1. records a fresh run of `demo/reshoot.toml`;
2. compares it step by step with `demo/accepted`;
3. copies the new MP4 and GIF into `docs/demo/` and the new run's record into
   `demo/accepted/`, with the first frame of each scan finding;
4. uploads the run, its review page and scan sheets as the `reshoot-review` artifact;
5. opens a pull request on the `reshoot/refresh` branch.

The pull request shows the new GIF, a link to the MP4 on its branch, each
scan finding with its first frame, and a table of matched, added and removed
steps, with whether each one's definition, duration, frame pixels and results
changed. Pixel changes are common and small; watch the video. The full scan
sheets and review page stay in the artifact. [Review a refresh pull request](publish.md#review-a-refresh-pull-request)
lists the steps. **Merging the pull request accepts the recording**: the next
run compares against it. Close the pull request to keep the current demo.

Configured [documentation screenshots](studio.md#make-screenshots-for-docs)
are copied with the exports, shown with their alt text in the pull request and
included in the comparison table. Inspect each image and its crop before
merging. The template copies all final exports; if an older workflow names only
the MP4 and GIF with `--file`, add each `--file screenshots/NAME.png` or omit the
file list. Previously copied PNGs are not deleted when a selection is removed;
remove obsolete files and documentation references in the same pull request.

An optional [clickable tour](studio.md#make-a-clickable-tour) is
staged with the other exports. With an explicit file list, include
`--file tours/NAME.html`. The Markdown links to the HTML; GitHub displays HTML
source rather than executing the tour, so download it and open it locally to
inspect navigation and every step. Its images are embedded. Comparison records
tour additions, removals and changes; no external tour hosting is required.

`reshoot export --markdown` writes the media and findings part of the
description, and `--link` makes its paths URLs on the pull request's branch.
Finding frames go into `demo/accepted/findings/`, and only for findings in the
files the export copies. In a private repository, the images show to people
who can read it.

If the repository has no `demo/accepted/` yet, the first run still opens a pull
request, without a comparison. Merging it starts the record.

When a change breaks the story, such as a renamed input, the run fails on that
step and opens no pull request. The job's summary page names the step and its
target, for example `step 'search' stopped: it couldn't find the control matching #q`, and the
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
and sheets as in [Review and accept](studio.md#review-and-accept).
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

The record-only workflow needs read access only, not the pull-request
permission.

## Review CI outputs

CI doesn't decide what's safe to show. [Review a refresh pull request](publish.md#review-a-refresh-pull-request)
lists what to look at before merging. On Linux the scan reads text with
Tesseract, which the action installs; faces and people need your eyes.

Keep demo data in the repository or generate it in a setup step so CI can use
it. Data committed to a public repository is public too.

Problems seen in CI are under [What to watch for](troubleshooting.md#in-ci).
