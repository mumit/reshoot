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
| ffmpeg and ffprobe | Encode, edit and inspect recordings |
| Google Chrome or Chromium | Records browser pages |
| Tesseract on Linux | Reads text during automatic checks |

macOS uses Apple's Vision framework for text, face and person detection by
default. Tesseract provides text detection only. Select it explicitly on either
platform when needed; it does not provide face or person detection.

## macOS

With [Homebrew](https://brew.sh/) installed:

```bash
brew install uv python ffmpeg
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
sudo apt-get install -y python3 ffmpeg chromium tesseract-ocr fonts-dejavu-core
```

On other distributions, install the equivalent packages, using Python 3.11 or
newer. Browser package names vary. A supported Google Chrome installation also
works. If automatic discovery misses it, set its executable path:

```bash
export RESHOOT_CHROME=/absolute/path/to/chromium
```

Windows is untested. Recording one app window and detecting faces and
people need macOS.

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
To pin a release, name its version, such as `'reshoot[browser]==0.3.0'`.
[Contributing](../CONTRIBUTING.md#install-an-unreleased-version) covers
installing from Git.

## Check a project

```bash
reshoot init demo
reshoot doctor --config demo/reshoot.toml
```

Skip `init` if `demo/` already exists. `doctor` reports each tool, its
version and how to fix what's missing. To
also try the tools on a tiny made-up video, page and text image, run:

```bash
reshoot doctor --config demo/reshoot.toml --probe
```

These checks don't start your app or install anything, and a full recording
can still fail.

`reshoot create` runs the same checks before it uses your app and lists
anything missing with its fix. [Troubleshooting](troubleshooting.md#a-command-or-dependency-is-missing)
covers **Recording tools**, **Check again** and resuming a paused creation.

Next, make your first demo with [the tutorial](step-by-step.md) or
[your agent](agent-quickstart.md).

## Install the skills

Skip this if your agent already set itself up. A skill is a set of
instructions for a coding agent. reshoot's three primary skills cover
creating, refreshing and reviewing a demo; the CLI does the recording.
From the app repository or demo folder, run the command for your agent:

| Agent | Run in a terminal | Installed in |
|---|---|---|
| Codex | `reshoot skills codex --directory .` | `.agents/skills/` |
| Claude Code | `reshoot skills claude --directory .` | `.claude/skills/` |

Start with `$reshoot-demo` in Codex or `/reshoot-demo` in Claude Code,
followed by a task. If a new skill doesn't appear, start a new session in the
same folder. See the
[Codex skill documentation](https://developers.openai.com/codex/skills) and
[Claude Code skill documentation](https://code.claude.com/docs/en/skills).

For the Claude Code plugin, with all ten skills, run these inside Claude Code:

```text
/plugin marketplace add mumit/reshoot
/plugin install reshoot@reshoot
```

Then invoke `/reshoot:reshoot-demo` with the task. The plugin still needs the
CLI and its tools. Choose one route per project. The
[skill catalog](../skills/README.md) describes every skill.

## Upgrade and remove

`reshoot doctor` says when a newer release is out. To upgrade:

```bash
uv tool upgrade reshoot
reshoot --version
```

uv respects the original source and version constraints when upgrading; see its
[tool upgrade guide](https://docs.astral.sh/uv/guides/tools/#upgrading-tools).
To change a pinned version, install again with `uv tool install --force`.

`reshoot skills` installs project-local copies of the three primary skills.
Upgrading the CLI does not replace those copies. After an upgrade, run
`reshoot skills codex --directory . --replace`, or `claude`, to install the
new version over them. If you changed the installed skills, commit or copy
those changes first; `--replace` discards them.

To remove the CLI, run `uv tool uninstall reshoot`. Demo projects and their
recordings remain in their existing directories.

## Optional tools

Install [VHS](https://github.com/charmbracelet/vhs#installation) only for
terminal takes (`brew install vhs` on macOS).

### Local neural narration

Kokoro is an optional local speech engine for English narration. Install it
with the browser tools:

```bash
uv tool install --upgrade 'reshoot[browser,kokoro]'
```

From a source checkout, use `uv sync --extra browser --extra kokoro` instead.
The extra includes PyTorch and adds a substantial download. The first audition
also downloads the public Kokoro model, selected voice and English language
data. Speech is generated on your CPU; no account, API key or speech service
is needed. Subsequent synthesis can run offline with the downloaded files.

Choose a voice and [audition a saved line](commands.md#shape):

```bash
reshoot audio set --engine 'kokoro --voice af_heart' --project demo
reshoot audio audition search --project demo
```

The step needs saved spoken words before it can be auditioned.
Heart (`af_heart`), Bella (`af_bella`), Michael (`am_michael`) and British
Emma (`bf_emma`) also appear in Studio's voice selector after installation.
Use `--speed 0.9` for slower speech; the supported range is 0.5 to 2.
Audition the actual words before recording a long explanation.
For offline synthesis after the first successful audition of a voice, set
`HF_HUB_OFFLINE=1` to use downloaded model files without checking the Hub.

The [Kokoro voice catalog](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
lists other English voice IDs. Try an unfamiliar ID with an audition first.

For missing tools, browser errors or scan failures, see
[Troubleshooting](troubleshooting.md).
