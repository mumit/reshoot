# Notes for coding agents

Read [README.md](README.md) for what reshoot does and [CONTRIBUTING.md](CONTRIBUTING.md) for how to work on it.

## Rules

- **Never capture the whole screen.** Record a headless browser page, a VHS terminal, or one window by its id.
- **Use the notes example or demo data,** never anyone's real files, photos or accounts.
- **Nothing goes public without the owner's yes.** No pushing, posting or publishing.
- Commit only when asked, in conventional-commit style.

## Layout

| Path | What it is |
|---|---|
| `src/reshoot/web.py` | `reshoot web`: headless Chrome from a storyboard |
| `src/reshoot/overlay.js` | The cursor, typing and captions added to the recorded page (`__demo`) |
| `src/reshoot/window.py` | `reshoot window`: one macOS window |
| `src/reshoot/check.py` | `reshoot check`: contact sheets and the list of what passed |
| `src/reshoot/scan.py` | The privacy scan: text (Vision or Tesseract), faces and people (Vision) |
| `src/reshoot/cut.py` | Helpers for edit scripts, and `reshoot gif` |
| `src/reshoot/run.py` | `reshoot run`: a whole shoot from a reshoot.toml |
| `src/reshoot/rec.py`, `rec.js` | `reshoot rec`: a storyboard written by watching someone use the app |
| `src/reshoot/zoom.py` | Zoom on clicks, and captions drawn after the zoom |
| `src/reshoot/voice.py` | The voiceover: each line spoken before recording, so beats can wait for it |
| `action.yml` | The GitHub Action: installs everything and runs `reshoot run` |
| `skills/` | The Claude Code skills |
| `guide/` | The guide for people |
| `examples/notes/` | A made-up app, its storyboards, a tape, an edit script and a reshoot.toml |
| `examples/github/` | The workflow a project copies to reshoot in CI |
| `tests/` | pytest; `tests/boards/` has pages and storyboards for the browser tests, and `tests/person.py` stands in for someone using Chrome |

## Commands

```bash
uv run pytest                 # fast tests
uv run pytest -m browser      # records the notes example (slow)
claude plugin validate .      # checks the plugin and skills
```

## When something changes

A change to a command or to `__demo` also changes the skill that documents it, and often the guide. A fixed pitfall
gets "Fixed in reshoot" in [guide/pitfalls.md](guide/pitfalls.md).
