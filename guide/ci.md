# Reshoot in CI

Record the demo again when the app changes. Start from a browser or VHS
project that records locally. Native windows can't be recorded in CI. Legacy
`[keep]` projects use the [manual workflow](manual.md#legacy-shoot-files-in-ci).

## Versioned projects: open a pull request with the refreshed demo

Copy [examples/github/refresh.yml](../examples/github/refresh.yml) to
`.github/workflows/reshoot.yml` and change the marked lines. Then:

1. Record, watch and accept a final, and commit
   [`demo/accepted/`](publish.md#the-accepted-run) with the demo source.
2. In Settings, Actions, General, turn on "Allow GitHub Actions to create and
   approve pull requests".
3. Add the steps your app needs before it starts, such as installing packages.

On a change to `main`, or when started by hand, the workflow records
`demo/reshoot.toml`, compares it with `demo/accepted`, copies the new exports
into `docs/demo/` and the run's record into `demo/accepted/`, uploads the
review as the `reshoot-review` artifact, and opens a pull request on
`reshoot/refresh`. **Merging it accepts the recording.** Close it to keep the
current demo. [Review a refresh pull request](publish.md#review-a-refresh-pull-request)
says what to check. Without a `demo/accepted/`, the first pull request has no
comparison.

The template copies every export, including
[documentation screenshots](studio.md#make-screenshots-for-docs) and
[clickable tours](studio.md#make-a-clickable-tour). If your workflow lists
files with `--file`, add `--file screenshots/NAME.png` or
`--file tours/NAME.html`. Removing a screenshot doesn't delete its old PNG;
delete it in the same pull request. GitHub shows a tour's HTML as source, so
download it to check it.

When a step breaks, the run fails and opens no pull request. Its summary names
the step and target, such as `step 'search' stopped: it couldn't find the
control matching #q`, and the artifact has a screenshot. Repair the story
locally or with the [refresh skill](../skills/reshoot-refresh/SKILL.md) and push.

The `!demo/accepted/**` path keeps a merged refresh from starting another run.
Adapt the other paths to your app.

## Versioned projects: record a run only

[examples/github/candidate.yml](../examples/github/candidate.yml) records a run
and uploads `demo/takes/`, even when recording fails, without changing the
repository. It needs read access only. Use it to try CI before the refresh
workflow: download the `reshoot-review` artifact and open `review.html` with
its folders intact.

## Choose when to record

The refresh template records on changes to `main` and by hand; the record-only
one by hand. To add releases or narrow the paths, change the `on:` block:

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

Keep the template's job, permissions and artifact upload. See GitHub's
[workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

## Demo data and secrets

Keep demo data in the repository or generate it in a setup step; in a public
repository it is public. For URL-only projects, use an isolated test service.
Keep credentials in CI secrets, never in the storyboard. On Linux the scan
reads text with Tesseract, which the action installs; check faces and people
yourself.

Problems seen in CI are under [What to watch for](troubleshooting.md#in-ci).
