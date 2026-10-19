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
| `src/reshoot/cut.py` | Helpers for edit scripts, and `reshoot gif` |
| `skills/` | The Claude Code skills |
| `guide/` | The guide for people |
| `examples/notes/` | A made-up app, its storyboards, a tape and an edit script |
| `tests/` | pytest, and storyboards the browser tests use (`tests/boards/`) |

## Commands

```bash
uv run pytest                 # fast tests
uv run pytest -m browser      # records the notes example (slow)
claude plugin validate .      # checks the plugin and skills
```

## When something changes

A change to a command or to `__demo` also changes the skill that documents it, and often the guide. A fixed pitfall
gets "Fixed in reshoot" in [guide/pitfalls.md](guide/pitfalls.md).
