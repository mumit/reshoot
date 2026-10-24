# Changelog

Each release names what changed for people making demos. Versions follow
[semantic versioning](https://semver.org/); before 1.0, a minor version may
change project files or commands.

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
