# Keep a demo current and share it

Keep the recording source with the app, or in its own repository if you only
have a URL or an installed app.

## The accepted run

[Accepting a final](studio.md#review-and-accept) writes `demo/accepted/`: the
run's report, step results and evidence frames, without the videos. Later runs
are compared with it. It changes only when you accept another run.

| Path | Commit it |
|---|---|
| `demo/BRIEF.md`, `storyboard.toml`, `edit.toml`, `reshoot.toml` and reset scripts, without credentials | Yes |
| `demo/accepted/` | Yes |
| `docs/demo/`: the MP4 and GIF the README shows | Yes |
| `.github/workflows/reshoot.yml`, if you use [CI](ci.md) | Yes |
| `demo/takes/`: every run's recordings and review | No; `demo/.gitignore` keeps it out |

## Record it again after a change

Use the [refresh prompt](agent-quickstart.md#update-the-demo-when-the-app-changes),
or:

```bash
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
reshoot compare demo/accepted demo/latest --out demo/comparison.json
reshoot review demo/latest --previous demo/accepted
```

Keep the step IDs and result checks. When a renamed control breaks a step,
repair its target, as in the [tutorial](step-by-step.md#6-change-the-app-and-repair-the-demo),
rather than deleting the check. Watch the new exports, look at the new scan
items, and accept the new run.

For a native window, record into a new folder with the saved
[capture recipe](macos-window.md), using the current window ID, and compare the
videos yourself. Native recordings have no step comparison or `reshoot export`.

## Share the files

```bash
reshoot export demo/accepted --directory docs/demo
```

This copies the accepted run's videos, GIFs and subtitles, and prints README
Markdown for the GIF, linked to the video. Add `--replace` to overwrite;
`--file` picks single files. `reshoot accept demo/latest --export docs/demo`
accepts and copies, replacing what's there.

| Destination | Prepare |
|---|---|
| GitHub README | A short GIF with alt text, linked to the MP4; the `readme` preset keeps it under GitHub's 10 MB |
| X or LinkedIn | An MP4 that works without sound, from the `x` or `linkedin` [preset](projects.md#export-presets); check any crop at actual size |
| Product guide | The fuller MP4, its `.srt` subtitles, and the prerequisites in writing |

Check the rendered README before you push.

## On a team

### Who owns what

Give the demo an owner, usually the feature's owner, and require their review
with `CODEOWNERS` and a branch rule:

```text
# .github/CODEOWNERS
/demo/          @your-org/docs-owners
/docs/demo/     @your-org/docs-owners
```

Whoever's app change breaks the story repairs it in the same pull request, as
they would a test. The [refresh workflow](ci.md) then opens a pull request with
the new recording for the owner.

### Review a refresh pull request

1. Watch the GIF, then follow "Watch demo-final.mp4" to the end. Check that
   each caption's result stays on screen long enough to read.
2. Under "What the scan found", look at each finding's first frame and decide
   whether it may be shared: real names, email addresses, keys, other people's
   data. The scan points at likely problems; it doesn't prove a frame is safe.
3. Read the comparison table. Small pixel changes are normal; a changed result
   is not.
4. Merge to accept. To ask for changes, comment and close it; the next refresh
   opens a new one.

For the full scan sheets and review page, download the `reshoot-review`
artifact from the run's Checks tab and open `review.html` with its folders intact.

### Hear about a broken story

GitHub tells whoever triggered a failed run. To tell the demo's owner, add this
step at the end of the job, add `issues: write` to `permissions`, and mention
the owner's team in `--body`:

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

### What it costs

| Cost | Size |
|---|---|
| CI time | About 1.5 minutes on `ubuntu-latest` for the notes example with a sampled scan; a [full scan](troubleshooting.md#a-run-takes-too-long) takes longer |
| Repository | About 200 KB MP4, 340 KB GIF and 280 KB `demo/accepted/` per refresh of the notes example; Git keeps every version |
| Artifacts | The `reshoot-review` artifact, kept 14 days |
| People | A few minutes of the owner's time per pull request |

CI never runs an agent, repairs a story, decides what is safe or posts
anywhere. Narrow the workflow's [`paths`](ci.md#choose-when-to-record) to
record only on relevant changes.
