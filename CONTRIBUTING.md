# Contributing

Thanks for helping. The most useful things to send are:

- **a pitfall** you hit, in a line or two: what happened, and what avoids it ([guide/pitfalls.md](guide/pitfalls.md));
- **a fix** in `reshoot` so the pitfall can't happen again;
- **a skill** for a kind of take that isn't covered yet, such as an iOS simulator, an Electron app or Linux windows;
- **a report from Linux or Windows.** reshoot has only been used on macOS so far.

## Setup

```bash
uv sync
uv run pytest               # fast tests
uv run pytest -m browser    # records the notes example in headless Chrome (slow)
```

The tests need ffmpeg. The browser test needs Chrome or Chromium.

## Trying a change

Record the notes example and look at the result, not just the tests:

```bash
python3 -m http.server 8000 --directory examples/notes &
uv run reshoot web examples/notes/storyboard.py takes/notes.mp4
uv run reshoot web examples/notes/phone.py takes/phone.mp4
vhs examples/notes/terminal.tape
uv run reshoot edit examples/notes/edit.py takes/notes.mp4 takes/terminal.mp4
```

Look at a few frames (`ffmpeg -ss 5 -i takes/notes.mp4 -frames:v 1 frame.png`) and play the video.

## Adding a skill

A skill is a folder in `skills/` with a `SKILL.md`:

```markdown
---
name: record-simulator
description: What it does, and when Claude should use it, in a sentence or two.
---

# Title

Steps, commands, and the pitfalls for this kind of take.
```

Keep the steps short and the commands exact. Put the pitfalls where they matter, in the skill that hits them, and
add them to the guide too. Check the plugin with `claude plugin validate .`.

## Writing style

Plain words, active verbs, short paragraphs. Say who does what. No em dashes. The guide is in first person.

## Privacy

Never add a recording, screenshot or sheet of anyone's real data to the repo, including in an issue or a pull
request. Use the notes example, or demo data you made.

## Commits

Conventional commits, such as `feat(web): …`, `fix(check): …`, `docs(guide): …`.
