# Reshoot on a team

This page is for whoever adopts reshoot for a team, and for whoever reviews the
pull requests it opens. It assumes one person has already made a demo that
records correctly: with the [agent quickstart](agent-quickstart.md) or the
[CLI tutorial](step-by-step.md).

## What lives in the repository

| Path | What it is | Commit it |
|---|---|---|
| `demo/BRIEF.md`, `storyboard.toml`, `edit.toml`, `reshoot.toml` | The story and how to record it | Yes |
| `demo/accepted/` | The accepted run: its report, beat results and evidence frames, without media | Yes |
| `docs/demo/` | The MP4 and GIF the README shows, copied by `reshoot export` | Yes |
| `demo/takes/` | Every run's recordings, scan sheets and review page | No; `reshoot init` ignores it |
| `.github/workflows/reshoot.yml` | The [refresh workflow](ci.md) | Yes |

`demo/accepted/` is what later runs are compared with. Changing it changes what
counts as the current demo, so treat it like a release decision.

## Who owns what

Give the demo an owner, usually whoever owns the feature it shows. Make that
owner review every change to the accepted run with a `CODEOWNERS` entry and a
branch rule that requires code-owner review:

```text
# .github/CODEOWNERS
/demo/          @your-org/docs-owners
/docs/demo/     @your-org/docs-owners
```

Anyone may change the app. When a change breaks the story, the person who made
it repairs the story in the same pull request, the way they would fix a test.
The owner reviews the new recording that follows.

## How a refresh works

1. Someone merges an app change to `main`.
2. The workflow records the demo again, about a minute and a half on a hosted
   Ubuntu runner for a short demo with a sampled scan.
3. If every result check passes, it opens a pull request on `reshoot/refresh`
   with the new GIF, a link to the MP4, each scan finding with its frame,
   `demo/accepted/` and a beat-by-beat comparison.
4. The owner reviews it, below, and merges it to accept the new recording, or
   closes it to keep the current one.

If a result check fails, no pull request opens. The run fails on the beat that
broke, and its summary names the beat and the control, such as
`type target {css = '#q'} matched 0 elements`.

## Review a refresh pull request

Everything a usual review needs is in the pull request's description:

1. Watch the GIF, then follow "Watch demo-final.mp4" and watch the video to the
   end. Check that the result each caption promises is on screen long enough
   to read.
2. Look at each finding under "What the scan found": what was found, how many
   frames it is in, and its first frame with a red box round it. Decide whether
   it may be shared: real names, email addresses, keys, other people's data.
3. Read the comparison table: which beats matched, and whether each one's
   definition, duration, frame and results changed. Small pixel changes are
   normal; a changed result is not.
4. Merge to accept. To ask for changes, comment and close the pull request;
   the next refresh opens a new one.

The scan points at likely problems; it does not prove a frame is safe, so the
video itself is the review. For the full scan sheets, every flagged frame and
the review page, download the `reshoot-review` artifact from the workflow run,
on the Checks tab, and open its `review.html` with the folders intact.
The finding frames are kept in `demo/accepted/findings/`. They come only from
the MP4 and GIF the pull request already adds, so they show nothing new; a
finding in any other file is named without a frame.

Merging is the acceptance: the workflow already wrote the new run into
`demo/accepted/`. Nothing is posted anywhere else.

## Hear about a broken story

GitHub tells whoever triggered a failed run, by email or in the web, according
to their notification settings. For a push to `main`, that is the person who
pushed. To tell the demo's owner instead, add a step at the end of the job
that opens an issue when the run fails:

```yaml
      - name: Open an issue when the story breaks
        if: failure()
        env:
          GH_TOKEN: ${{ github.token }}
        run: >
          gh issue create --repo "$GITHUB_REPOSITORY"
          --title "The demo story broke"
          --body "See $GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID"
```

Add `issues: write` to the workflow's `permissions`. Assign the issue or
mention the owner's team in `--body` so it reaches someone.

## What it costs

| Cost | Size |
|---|---|
| CI time per refresh | About 1.5 minutes on `ubuntu-latest` for the notes example, scanning a frame every 3 seconds |
| A full scan | Grows with the number of frames; [Faster shoots](speed.md) has a worked example |
| Repository size | One MP4 and one GIF per accepted refresh, and `demo/accepted/`: about 200, 340 and 280 KB for the notes example. Git keeps every old version |
| Artifact storage | The `reshoot-review` artifact, kept 14 days |
| People | A few minutes of the owner's time per refresh pull request |
| An agent | Only when someone asks one to write or repair a story; CI never runs one |

Public repositories get hosted runner minutes free; private ones use the
account's included minutes. Record only on changes that can change the demo by
narrowing the workflow's `paths`, as [CI](ci.md#choose-when-to-record) shows.

## What reshoot does not do for a team

- It does not repair a story. A broken story fails and waits for a person or
  an agent.
- It does not decide what is safe to share. A person reviews every refresh.
- It does not post. Copying files into `docs/demo/` and merging is the only
  route to the README.
- It does not record native macOS windows in CI.
