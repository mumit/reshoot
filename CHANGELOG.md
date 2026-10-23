# Changelog

Each release names what changed for people making demos. Versions follow
[semantic versioning](https://semver.org/); before 1.0, a minor version may
change project files or commands.

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
