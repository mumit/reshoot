# Changelog

Each release names what changed for people making demos. Versions follow
[semantic versioning](https://semver.org/); before 1.0, a minor version may
change project files or commands.

## Unreleased

### Changed

- The scan groups what it flags into findings: one email address on screen for
  a whole video is one finding, such as `F1`, not hundreds of frames to name.
  `accept --flagged F1` or `--reject F1` covers every frame it is in; a label
  such as `1-2` still names one frame.
- The review page reads in review order: the exports, each finding with its
  frame, the scan sheets as images, then the beats, with the run's other files
  folded into one list.
- `reshoot run --full` scans every frame this time, without editing the
  config. The tutorial uses it.
- Scan messages say to look at findings first and then look over the rest for
  what a scan can miss, instead of asking for every item at full size.

## 0.3.4 (2026-10-24)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.4.

### Fixed

- A higher pixel ratio records sharper video. Chrome's screencast had sent
  frames at the page's CSS size whatever the ratio, so `@2` was only scaled up
  and zoomed text went soft. Chrome now starts at the recording's pixel ratio;
  on the notes example at `960x540@2`, a sharpness measure of the same frame
  doubled. The odd short frames at the start of a take are gone too.

### Added

- [How the videos look](guide/look.md): the cursor, auto-zoom, captions,
  title cards, export shapes and GIF sizes, recorded from the notes example by
  `examples/look/build.py`.
- TOML storyboards get the cursor Python storyboards have: a glide that takes
  longer for longer trips, a press and a ring on each click, and typing at an
  uneven pace set by `seed`. A `[cursor]` table sets `size`, `typing` speed and
  `ripple`.
- `reshoot init` writes `demo/.gitignore`, which keeps recordings out of Git
  and the `demo/accepted/` record in.
- `reshoot export RUN --directory DIR` copies the run's videos, GIFs and video
  subtitles without naming each `--file`, and prints the README Markdown for
  the GIF. `accept` says how.
- Agents end a first demo with a fixed handoff: the exports, the checks,
  "reply accept, or ask for changes", and the accept command. The quickstart
  has a table of follow-up requests.

### Changed

- A run ends by saying what it made: its result checks, scan items and
  whether it is accepted, then the paths of the video, the GIF and the review
  page. A preview says to record the final; a final gives the accept command.
- A failed run prints its run folder, failure image and the app's output.
- The app's own output, such as a server's request log, goes to `app.log` in
  the run folder instead of between reshoot's lines.
- `reshoot compare --out` prints which beats matched and which changed their
  steps or results.
- The review page opens with one status line; the raw data is folded away.
- Previews sample frames even when `full = true`, so they stay quick.
- The tutorial uses `demo/latest` and `demo/accepted` instead of pasted run
  IDs, and exports to `docs/demo/`.
- The brief `init` writes gives the commands from the folder that holds
  `demo/`, and drops its note on review IDs and hashes.
- With no accepted run, the refresh skill compares against the newest final
  and says it was never accepted.
- The README leads with what reshoot is for, the install line and three
  commands, shows a storyboard, says how it differs from other tools and what
  to expect from the agent prompt, and has one table of where to go next.

- `reshoot accept` refuses a preview unless given `--preview`. The CI guide's
  `reshoot accept demo/latest` could commit a preview as the baseline.
- `reshoot skills` takes `--replace` to install the new version over skills
  already there, such as after an upgrade. The agent quickstart had told agents
  both to install skills after an upgrade and to keep the old ones.

### Fixed

- Docs that had drifted: the "no `select`" claims, the CLI 0.2 requirement in
  the project reference, the archive-by-ID baseline in the publishing guide,
  the skills' hedges about commands every supported CLI has, and the claim that
  zoomed text stays sharp at a higher pixel ratio.

## 0.3.3 (2026-10-23)

### Added

- `reshoot doctor` says when a newer release is on PyPI. `RESHOOT_OFFLINE=1`
  skips the check.

### Fixed

- A browser that cannot start says why it usually happens in an agent's
  sandbox, such as Codex's, instead of only Playwright's error.
- The skills require 0.3.2 and say how to upgrade, and the agent quickstart
  reuses an existing install only when it is the latest release. A cold Codex
  session had recorded a whole demo with a stale 0.2.0.
- Agents keep their changes in `demo/`: the quickstart and demo skill say not
  to edit the app's README or other files unless asked.

## 0.3.2 (2026-10-23)

### Added

- A `select` action chooses a dropdown option by its value or visible label,
  and `reshoot rec` writes one for each dropdown choice.

### Fixed

- A result could appear a whole hold late in the video while every check passed: the evidence screenshot after
  each beat could take the frame showing it. The evidence frame is now the last frame the video shows, saved at
  the end of the hold. Frame times also no longer depend on when the first frame arrives.
- Storyboard errors name the beat and the action or check, such as
  `beat 'fill', action 2 (key): target needs exactly one of css, test_id, or role`.
- The demo skill says to narrow the viewport or zoom when an app's content is
  too small to read in the README GIF.
- A port Chrome refuses, such as 5060, is explained with the flag that allows
  it, and a failure while opening the page no longer reports `beat None`.
- The demo skill and guides say how to write checks for apps that keep data
  between takes and have no reset.

## 0.3.1 (2026-10-23)

### Added

- `reshoot accept RUN` records the owner's verdict in one step: the exports,
  every beat, every scan item and the scan checklist, bound to the run's exact
  files and scan policy. Each flagged item must be named with `--flagged`, and
  `--reject` marks an item that must not be shared. It asks for confirmation,
  and without a terminal it refuses unless given `--yes`.
- `reshoot run` and `reshoot preview` write the review page and print the
  `reshoot accept` command for the run.
- `reshoot runs PROJECT` lists a project's runs, newest first, with their
  result and review status. Run paths accept `latest` (the newest successful
  run) and `accepted` (the newest accepted run), such as `demo/accepted`.
  Run reports record `finished_at`.
- A refresh pull request in CI. `examples/github/refresh.yml` records the demo
  when the app changes, compares it with the accepted run and opens a pull
  request with the new MP4, GIF and a beat table. Merging it accepts the
  recording.
- `reshoot accept` writes `demo/accepted/`, a small committed record of the run
  (report, beat results and evidence frames), so CI and fresh clones can
  compare against it. `reshoot export --record DIR` writes one for any run.
- `reshoot export --replace` updates media already in the destination, and
  `reshoot compare --markdown FILE` writes a summary for a pull request.
- In GitHub Actions, each run writes a job summary with its checks, scan and
  errors.

### Fixed

- `reshoot init` moves the notes example off port 8765 when something else
  is using it.
- A busy port names its loopback address instead of a redacted hash.
- `reshoot web --help` describes TOML storyboards, and `review`, `compare`
  and `export` explain their arguments.
- A target that matches no element, or several, names the target and the count.
- A run's report includes the failed beat's error, not only the failed step.

## 0.3.0 (2026-10-23)

The first release on PyPI. Install it with `uv tool install 'reshoot[browser]'`.

### Added

- Published to PyPI, with a release workflow that builds, checks and publishes
  each tagged version.
- An agent-first entry point: a first-demo prompt in the README, the agent
  quickstart and a skill catalog.
- Guides for each stage after the first recording: features, customizing,
  fuller demos and tutorials, publishing, CI and faster shoots.

### Fixed

- Review pages show baseline GIFs as images; MP4s keep their video players.
- Joined title cards no longer vanish or freeze in GIF exports.
- Clip joins keep an exact frame rate.
- Captions stay visible across same-origin page loads.
- Previews that mix web and VHS takes keep matching dimensions.
- Runs leave incomplete expectations unverified instead of passing them.
- `doctor` rejects a `RESHOOT_CHROME` that does not name a usable browser.

## 0.2.0

Repeatable demo projects: `reshoot.toml`, TOML storyboards with checked
expectations, `init`, `doctor`, `preview`, isolated versioned runs, `compare`,
`review` with bound decisions, `export`, and shared Claude Code and Codex skills
installed by `reshoot skills`. Installed from Git only.
