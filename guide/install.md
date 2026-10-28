# Install reshoot

The [first-demo prompt](agent-quickstart.md) has your agent do this for you.

## Requirements

| Tool | For |
|---|---|
| Python 3.11 or newer | reshoot, and the tutorial's local app |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Installing the CLI |
| ffmpeg and ffprobe | Editing recordings |
| Google Chrome or Chromium | Recording browser pages |
| Tesseract, on Linux | Reading text in the scan |

On macOS the scan uses Apple's Vision for text, faces and people. Tesseract
reads text only.

## macOS

With [Homebrew](https://brew.sh/):

```bash
brew install uv python ffmpeg
brew install --cask google-chrome
```

An installed Chrome or Chromium is fine. Only a native window needs Screen
Recording permission ([once](manual.md#once)); to record only native windows,
skip Chrome and see [a macOS window](macos-window.md).

## Linux

Install [uv](https://docs.astral.sh/uv/getting-started/installation/). On
Debian 12:

```bash
sudo apt-get update
sudo apt-get install -y python3 ffmpeg chromium tesseract-ocr fonts-dejavu-core
```

Elsewhere, install the equivalents. If reshoot can't find the browser:

```bash
export RESHOOT_CHROME=/absolute/path/to/chromium
```

## Install the CLI

```bash
uv tool install 'reshoot[browser]'
reshoot --version
```

reshoot uses the browser installed above; no `playwright install` is needed.
If `reshoot` isn't found, run `uv tool update-shell` and open a new terminal.
To pin a release, use `'reshoot[browser]==0.3.0'`.
[Contributing](../CONTRIBUTING.md#install-an-unreleased-version) covers
installing from Git.

## Check a project

```bash
reshoot init demo                                # skip if demo/ exists
reshoot doctor --config demo/reshoot.toml        # each tool and how to fix it
reshoot doctor --config demo/reshoot.toml --probe  # also try each tool on made-up input
```

`reshoot create` runs the same checks. Next: [the tutorial](step-by-step.md).

## Install the skills

From the app repository or demo folder:

| Agent | Run | Installed in |
|---|---|---|
| Codex | `reshoot skills codex --directory .` | `.agents/skills/` |
| Claude Code | `reshoot skills claude --directory .` | `.claude/skills/` |

Start with `$reshoot-demo` in Codex or `/reshoot-demo` in Claude Code, then the
task. If a skill doesn't appear, start a new session.

Or install the Claude Code plugin, with all ten skills, inside Claude Code:

```text
/plugin marketplace add mumit/reshoot
/plugin install reshoot@reshoot
```

Then use `/reshoot:reshoot-demo`. Choose one route per project. The
[skill catalog](../skills/README.md) describes every skill.

## Upgrade and remove

`reshoot doctor` says when a newer release is out. To install it:

```bash
reshoot upgrade
```

It shows the command it will run and a link to what changed, then asks. It
keeps the extras you installed, such as `kokoro`. `reshoot upgrade 0.3.11`
installs an exact version, such as to go back. For a uv or pipx install it
runs uv or pipx; for a source checkout or pip it says what to run. Restart an
open studio afterwards.

Upgrading doesn't update the project's skill copies: run
`reshoot skills codex --directory . --replace` (or `claude`), after committing
any changes you made to them, since `--replace` discards them.

`uv tool uninstall reshoot` removes the CLI and leaves your projects.

## Optional tools

[VHS](https://github.com/charmbracelet/vhs#installation) for terminal takes
(`brew install vhs`).

### Local neural narration

Kokoro speaks English narration on your CPU, with no account or key:

```bash
uv tool install --upgrade 'reshoot[browser,kokoro]'   # from source: uv sync --extra browser --extra kokoro
reshoot audio set --engine 'kokoro --voice af_heart' --project demo
reshoot audio audition search --project demo
```

It adds PyTorch, and the first audition downloads the model and voice. After
that, `HF_HUB_OFFLINE=1` works offline. A step needs saved spoken words to
[audition](commands.md#shape). Heart (`af_heart`), Bella (`af_bella`), Michael
(`am_michael`) and Emma (`bf_emma`) appear in the studio's voice selector.
`--speed` runs from 0.5 to 2. The
[voice catalog](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
lists other voices.
