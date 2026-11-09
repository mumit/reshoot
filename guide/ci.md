# Reshoot in CI

Check the demo on each pull request, and record it again when the app changes.
Start from a browser or VHS project that records locally. Native windows can't
be recorded in CI. Legacy `[keep]` projects use the
[manual workflow](manual.md#legacy-shoot-files-in-ci).

## Check the demo on each pull request

Copy [examples/github/check.yml](../examples/github/check.yml) to
`.github/workflows/reshoot-check.yml`, change the marked lines, and add the
steps your app needs before it starts. On each pull request it records
`demo/reshoot.toml` and keeps one comment on the pull request up to date:

- **The demo still works with this change**, with its result checks. With a
  committed `demo/accepted/`, it also lists each check added or removed since
  the accepted run on the base branch, so a demo can't pass by checking less,
  and says when the pull request changes `demo/accepted/` as well.
- **This change stops the demo**, with the step that stopped and why, such as
  `Type search notes stopped: it couldn't find the control matching #q. It's
  probably "Search notes" now`, and the suggested repair as a patch to the
  storyboard. Look at the failure frame in the `reshoot-review` artifact, then
  apply the patch with `git apply` and push. Nothing changes until you do.
- **The demo check could not run**, when it stopped before recording, such as
  for a storyboard that doesn't parse or an app that didn't start. The job's
  log says why.

A stopped step or failed check also fails the job, so you can make the check
required in your branch rules. A wrong result has no suggested repair: fix the
app or the demo data, or change the expected result in the
[studio](studio.md#correct-a-failed-result-check) if the story should show
something different. Pull requests from forks get a read-only token and see
the job's summary instead of a comment.

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
