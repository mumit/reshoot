# Keep a demo current and share it

Keep the recording source with the app, or in its own repository when you only
have a URL or an installed app. Get a recording working locally before you
automate it. On a team, [Reshoot on a team](team.md) covers ownership, review
and alerts.

## The accepted run

Commit the brief, story, edit, `reshoot.toml` and any demo-data reset scripts,
without credentials. `demo/.gitignore` already keeps `demo/takes/` out.

[Accepting a run](step-by-step.md#5-review-and-accept) writes
`demo/accepted/`: the run's report, beat results and evidence frames, without
the media. Commit it with the source. Later runs are compared with it, and
`demo/accepted` names it in every command. A newer run never replaces it until
you accept that run.

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

`demo/latest` is the newest successful run. Keep the beat IDs and the result
checks. When a renamed control breaks a beat, repair its target rather than
deleting its result check; the [tutorial](step-by-step.md#6-change-the-app-and-repair-the-demo)
walks through one. Watch the new exports, look at the new scan items, and
accept the new run: accepting the old one says nothing about it.

For a native window, record into a new folder with the saved
[capture recipe](macos-window.md), look up the current window ID, and compare
the old and new videos yourself. Native recordings have no beat comparison and
no `reshoot export`.

## Share the files

```bash
reshoot export demo/accepted --directory docs/demo
```

It copies the accepted run's videos, GIFs and subtitles, checks their hashes,
and prints the README Markdown for the GIF, linked to the video, described by
the task in `BRIEF.md`. `reshoot accept demo/latest --export docs/demo` accepts
and copies in one step, replacing the files already there. `--file` picks
single files, and `--replace` overwrites files already there, as when updating
the repository's demo. It copies locally and uploads nothing.

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
Merging the pull request accepts it. A broken story fails on its beat and opens
nothing; repair it locally and push. CI never writes or repairs a story, and
it does not record native windows.
