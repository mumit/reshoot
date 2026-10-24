# Install reshoot

To let a coding agent handle setup, start with the
[first-demo prompt](agent-quickstart.md). Use this page to install the tools
yourself or resolve a missing dependency. Install the CLI once, then keep each
demo's story and edit files in its own project.

## Requirements

| Tool | Purpose |
|---|---|
| Python 3.11 or newer | Runs reshoot; `python3` also starts the tutorial's local app |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Installs the CLI in its own environment |
| Git | Fetches the installation source from GitHub |
| ffmpeg and ffprobe | Encode, edit and inspect recordings |
| Google Chrome or Chromium | Records browser pages |
| Tesseract on Linux | Reads text during automatic checks |

macOS uses Apple's Vision framework for text, face and person detection by
default. Tesseract provides text detection only. Select it explicitly on either
platform when needed; it does not provide face or person detection.

## macOS

With [Homebrew](https://brew.sh/) installed:

```bash
brew install uv python git ffmpeg
brew install --cask google-chrome
```

If Chrome or Chromium is already installed, keep that browser instead of
installing another. Headless browser recording does not need Screen Recording
permission. Recording a native app window does; see the [manual workflow](manual.md#once).
For native-only capture, skip Chrome; use the [window walkthrough](macos-window.md)
after installing the CLI. The bundled notes project below is a browser example.

## Linux

Install uv using its [installation instructions](https://docs.astral.sh/uv/getting-started/installation/).
On Debian 12, install the remaining tools with:

```bash
sudo apt-get update
sudo apt-get install -y python3 git ffmpeg chromium tesseract-ocr fonts-dejavu-core
```

On other distributions, install the equivalent packages, using Python 3.11 or
newer. Browser package names vary. A supported Google Chrome installation also
works. If automatic discovery misses it, set its executable path:

```bash
export RESHOOT_CHROME=/absolute/path/to/chromium
```

The tested Linux environments and platform limits are listed in
[Platforms](README.md#platforms). Windows is not currently validated.

## Install the CLI

On either platform:

```bash
uv tool install 'reshoot[browser]'
reshoot --version
python3 --version
```

The `browser` extra installs the Python Playwright dependency. Reshoot uses the
Chrome or Chromium executable installed above; the tutorial does not require
`playwright install`. If `reshoot` is not on the shell's path, run
`uv tool update-shell`, start a new terminal and try again.

This installs the latest release from [PyPI](https://pypi.org/project/reshoot/).
To pin a release, name its version, such as `'reshoot[browser]==0.3.0'`. To
try unreleased changes from the default branch, install from Git instead:

```bash
uv tool install --force 'reshoot[browser] @ git+https://github.com/mumit/reshoot'
```

Append `@COMMIT_SHA` to the Git URL to reproduce an exact revision, following
uv's [Git source syntax](https://docs.astral.sh/uv/guides/tools/#requesting-different-sources).
Run `uv tool install --force` with a release requirement to return to PyPI.

## Check a project

```bash
reshoot init demo
reshoot doctor --config demo/reshoot.toml
```

`doctor` reports available tools and detectors. It does not install them or
prove that capture and scanning work. The next step is the
[first-demo tutorial](step-by-step.md#2-record-a-preview). If `demo` already exists,
continue at the preview step instead of running `init` twice.

## Upgrade and remove

`reshoot doctor` says when a newer release is out. To upgrade:

```bash
uv tool upgrade reshoot
reshoot --version
```

uv respects the original source and version constraints when upgrading; see its
[tool upgrade guide](https://docs.astral.sh/uv/guides/tools/#upgrading-tools).
To change a pinned version or a Git revision, reinstall as described above.

`reshoot skills` installs project-local copies of the three primary skills.
Upgrading the CLI does not replace those copies. After an upgrade, run
`reshoot skills codex --directory . --replace`, or `claude`, to install the
new version over them. If you changed the installed skills, commit or copy
those changes first; `--replace` discards them.

To remove the CLI, run `uv tool uninstall reshoot`. Demo projects and their
recordings remain in their existing directories.

## Optional tools

Install [VHS](https://github.com/charmbracelet/vhs#installation) only for terminal
takes (`brew install vhs` on macOS). For Codex or Claude Code, install the
[skill package](../skills/README.md) after the recording tools. The
[agent quickstart](agent-quickstart.md) includes setup, invocation and example
prompts. To use the CLI alone, follow the [notes tutorial](step-by-step.md).

For missing tools, browser errors or scan failures, see
[Troubleshooting](troubleshooting.md).
