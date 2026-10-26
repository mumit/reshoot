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
| `src/reshoot/create.py` | `reshoot create`: demonstrate a task, make a preview and open the studio |
| `src/reshoot/setup.py` | Actionable dependency checks, synthetic probes and first-run setup state |
| `src/reshoot/workspace.py` | Studio revisions and reversible edits |
| `src/reshoot/editor.js` | Keyboard story filmstrip and one selected-step inspector |
| `src/reshoot/stills.py`, `stills.js` | Bounded representative still feedback using production caption, window and export renderers |
| `src/reshoot/session.py` | Persistent studio history, explicit recovery and saved-source copies |
| `src/reshoot/styles.py` | Portable visual styles shared by the CLI and studio |
| `src/reshoot/sequence.py` | Beat ranges and video-part ordering shared by the CLI and studio |
| `src/reshoot/framing.py`, `readability.py`, `layout.js` | Shared export geometry and measured text/crop feedback |
| `src/reshoot/repair.py`, `repair.js`, `targets.js` | Explicit locator repair and shared control discovery |
| `src/reshoot/expectations.py` | Failed result explanations and corrections that preserve the control and neighboring checks |
| `src/reshoot/rec.py`, `rec.js` | `reshoot rec`: a storyboard written by watching someone use the app |
| `src/reshoot/zoom.py` | Zoom on clicks, and captions drawn after the zoom |
| `src/reshoot/captions.py` | TOML storyboard captions, drawn on a take after recording and again on a re-cut |
| `src/reshoot/studio.py` | `reshoot studio`: a local page for the latest run: its beats, captions, edit, exports and acceptance |
| `src/reshoot/journey.py`, `delivery.py` | Saved/rendered/captured source state and exact-run local export bundles |
| `src/reshoot/comparison.py`, `comparison.js` | Read-only studio comparison of checked frames and evidence from two exact runs |
| `src/reshoot/playback.py`, `playback.js` | Paired export videos and per-cut step seeking for those same two runs |
| `src/reshoot/voice.py` | The voiceover: each line spoken before recording, so beats can wait for it |
| `src/reshoot/audio.py` | Narration auditions and validated voice/music balance shared by the CLI and studio |
| `src/reshoot/screenshots.py` | Documentation PNGs from checked result frames, with stable names and bound provenance |
| `src/reshoot/tours.py`, `tour.js` | Offline HTML walkthroughs of checked frames, their editor and run-bound provenance |
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

A change to a command or to `__demo` also changes the skill that documents it, and often the guide. Explain each
thing once, where it belongs, and link to it from elsewhere:

| What | Where |
|---|---|
| A studio panel or button | [guide/studio.md](guide/studio.md), in the order a person meets it, with its command in the table at the end |
| A file field | [guide/projects.md](guide/projects.md), under its file |
| A command | [guide/commands.md](guide/commands.md), under its job, and `--help` |
| A picture of a setting | [guide/look.md](guide/look.md), by editing `examples/look/build.py` |
| A fixed problem | [CHANGELOG.md](CHANGELOG.md). Keep it in [guide/pitfalls.md](guide/pitfalls.md) only if people still need to do something |

Write for the person using reshoot: what to do, in the studio's own words, then why. Leave out how the code keeps
things safe unless the reader has to act on it.
