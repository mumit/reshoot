# Keep a demo current and share it

Keep the recording source with the app, or in its own repository when you only
have a URL or an installed app. Get a recording working locally before you
automate it.

## The accepted run

[Accepting a final](studio.md#review-and-accept) writes `demo/accepted/`: the
run's report, step results and evidence frames, without the videos. Later runs
are compared with it, and `demo/accepted` names it in every command. A newer
run never replaces it until you accept that run, so treat a change to it like a
release decision.

| Path | What it is | Commit it |
|---|---|---|
| `demo/BRIEF.md`, `storyboard.toml`, `edit.toml`, `reshoot.toml` | The story and how to record it, with any demo-data reset scripts, without credentials | Yes |
| `demo/accepted/` | The accepted run's record | Yes |
| `docs/demo/` | The MP4 and GIF the README shows, copied by `reshoot export` | Yes |
| `demo/takes/` | Every run's recordings, scan sheets and review page | No; `demo/.gitignore` keeps it out |
| `.github/workflows/reshoot.yml` | The [refresh workflow](ci.md), if you use it | Yes |

## Record it again after a change

Ask the agent with the
[refresh prompt](agent-quickstart.md#update-the-demo-when-the-app-changes), or
use the CLI:

```bash
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
reshoot compare demo/accepted demo/latest --out demo/comparison.json
reshoot review demo/latest --previous demo/accepted
```

`demo/latest` is the newest successful run. Keep the step IDs and the result
checks. When a renamed control breaks a step, repair its target rather than
deleting its result check; the [tutorial](step-by-step.md#6-change-the-app-and-repair-the-demo)
walks through one. Watch the new exports, look at the new scan items, and
accept the new run: accepting the old one says nothing about it.

For a native window, record into a new folder with the saved
[capture recipe](macos-window.md), look up the current window ID, and compare
the old and new videos yourself. Native recordings have no step comparison and
no `reshoot export`.

## Share the files

After accepting, copy the files into your repository:

```bash
reshoot export demo/accepted --directory docs/demo
```

It copies the accepted run's videos, GIFs and subtitles, and prints the README
Markdown for the GIF, linked to the video and described by the task in
`BRIEF.md`. It won't overwrite files already there: add `--replace` when you
update the repository's demo. `--file` picks single files. It copies locally
and uploads nothing. `reshoot accept demo/latest --export docs/demo` accepts
and copies in one step, replacing what's there.

| Destination | Prepare |
|---|---|
| GitHub README | A short, readable GIF with alt text, linked to the full MP4; the `readme` preset keeps it under GitHub's 10 MB |
| X or LinkedIn | An MP4 that makes sense without sound, from the `x` or `linkedin` [preset](projects.md#export-presets); look at any crop at actual size |
| Product guide or tutorial | The fuller MP4, its subtitles, and the prerequisites in writing |

Check the rendered README and the playback before you push. The `.srt` file
suits players and upload forms that take subtitles. Ask the agent to prepare
these files and draft the copy if you like; it commits, pushes or posts only
when you say so.

## Refresh it in CI

Once a local run works and `demo/accepted/` is committed, the
[GitHub workflow](ci.md) records the demo after relevant changes to `main`,
compares it with the accepted run and opens a pull request with the new media.
Merging the pull request accepts it. A broken story fails on its step and opens
nothing; repair it locally and push. CI never writes or repairs a story, and
it does not record native windows.

## On a team

This part is for whoever adopts reshoot for a team, and whoever reviews the
pull requests the workflow opens.

### Who owns what

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

### How a refresh works

1. Someone merges an app change to `main`.
2. The workflow records the demo again, about a minute and a half on a hosted
   Ubuntu runner for a short demo with a sampled scan.
3. If every result check passes, it opens a pull request on `reshoot/refresh`
   with the new GIF, a link to the MP4, each scan finding with its frame,
   `demo/accepted/` and a step-by-step comparison.
4. The owner reviews it, below, and merges it to accept the new recording, or
   closes it to keep the current one.

If a result check fails, no pull request opens. The run fails on the step that
broke, and its summary names the step and the control, such as
`step 'search' stopped: it couldn't find the control matching #q`.

### Review a refresh pull request

Everything a usual review needs is in the pull request's description:

1. Watch the GIF, then follow "Watch demo-final.mp4" and watch the video to the
   end. Check that the result each caption promises is on screen long enough
   to read.
2. Look at each finding under "What the scan found": what was found, how many
   frames it is in, and its first frame with a red box round it. Decide whether
   it may be shared: real names, email addresses, keys, other people's data.
3. Read the comparison table: which steps matched, and whether each one's
   definition, duration, frame and results changed. Small pixel changes are
   normal; a changed result is not.
4. Merge to accept. To ask for changes, comment and close the pull request;
   the next refresh opens a new one.

The scan points at likely problems; it does not prove a frame is safe, so the
video itself is the review. For the full scan sheets, every flagged frame and
the review page, download the `reshoot-review` artifact from the workflow run,
on the Checks tab, and open its `review.html` with the folders intact.
Each finding's first frame is kept in `demo/accepted/findings/`, taken from
the MP4 and GIF the pull request already adds.

Merging is the acceptance: the workflow already wrote the new run into
`demo/accepted/`. Nothing is posted anywhere else.

### Hear about a broken story

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

### What it costs

| Cost | Size |
|---|---|
| CI time per refresh | About 1.5 minutes on `ubuntu-latest` for the notes example, scanning a frame every 3 seconds |
| A full scan | Grows with the number of frames; [A run takes too long](troubleshooting.md#a-run-takes-too-long) has a worked example |
| Repository size | One MP4 and one GIF per accepted refresh, and `demo/accepted/`: about 200, 340 and 280 KB for the notes example. Git keeps every old version |
| Artifact storage | The `reshoot-review` artifact, kept 14 days |
| People | A few minutes of the owner's time per refresh pull request |
| An agent | Only when someone asks one to write or repair a story; CI never runs one |

Public repositories get hosted runner minutes free; private ones use the
account's included minutes. Record only on changes that can change the demo by
narrowing the workflow's `paths`, as [CI](ci.md#choose-when-to-record) shows.

### What reshoot does not do for a team

- It does not repair a story. A broken story fails and waits for a person or
  an agent.
- It does not decide what is safe to share. A person reviews every refresh.
- It does not post. Copying files into `docs/demo/` and merging is the only
  route to the README.
- It does not record native macOS windows in CI.
