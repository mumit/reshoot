# Contributing

Thanks for helping. The most useful things to send are:

- **a pitfall** you hit, in a line or two: what happened, and what avoids it ([guide/pitfalls.md](guide/pitfalls.md));
- **a fix** in `reshoot` so the pitfall can't happen again;
- **a skill** for a kind of take that isn't covered yet, such as an iOS simulator, an Electron app or Linux windows;
- **a report from another project or platform.** Linux and macOS have CI and
  maintainer-operated trials; independent new-user testing is deferred and
  Windows remains unvalidated.

To make a demo, start with the [agent quickstart](guide/agent-quickstart.md) or
the [CLI tutorial](guide/step-by-step.md). This page covers working on reshoot itself.

## Report a bug

Use the repository's bug-report form with a small synthetic reproduction. Include:

- OS and CPU, reshoot version and installation revision if known;
- relevant browser, ffmpeg and OCR backend versions (`reshoot doctor --json` helps);
- the exact command, expected behavior and what happened;
- a minimal storyboard, configuration or fixture, and the failing beat or error.

Inspect logs, reports and images before attaching them; they may contain local
paths or app details. Use made-up data. For setup and review questions, check
[Troubleshooting](guide/troubleshooting.md) first.

## Setup

```bash
uv sync --extra browser
uv run pytest               # fast tests
uv run pytest -m browser    # records the notes example in headless Chrome (slow)
```

The tests need ffmpeg; browser tests also need Chrome or Chromium. See
[installation](guide/install.md) for platform dependencies. To test text scanning
with an explicit backend, install Tesseract and run
`uv run --extra browser pytest --ocr-backend=tesseract`. A failed Vision integration
remains an error; selecting Tesseract does not validate face detection.

## Try a change

Record a new packaged project and inspect the output alongside the test results:

```bash
uv run reshoot init takes/contributor-demo
uv run reshoot doctor --config takes/contributor-demo/reshoot.toml
uv run reshoot preview takes/contributor-demo/reshoot.toml
```

Each run prints its folder. Generate its review page with
`uv run reshoot review RUN`, open `RUN/review.html` and watch both exports.
For a final take, run `uv run reshoot run takes/contributor-demo/reshoot.toml`.
Choose a new project directory if that name already exists.

For changes to the legacy Python recorder or mixed web/terminal editing, also
exercise the original notes files:

```bash
python3 -m http.server 8000 --directory examples/notes &
uv run reshoot web examples/notes/storyboard.py takes/notes.mp4
uv run reshoot web examples/notes/phone.py takes/phone.mp4
vhs examples/notes/terminal.tape
uv run reshoot edit examples/notes/edit.py takes/notes.mp4 takes/terminal.mp4
```

Look at a few frames (`ffmpeg -ss 5 -i takes/notes.mp4 -frames:v 1 frame.png`) and play the video.

## Documentation changes

The primary entry point is the [agent quickstart](guide/agent-quickstart.md).
Keep it aligned with the README's first-demo prompt and the [skill catalog](skills/README.md).
The [installation guide](guide/install.md), [CLI tutorial](guide/step-by-step.md)
and [own-app walkthrough](guide/your-app.md) provide the detailed tool instructions.
The [manual guide](guide/manual.md) keeps Python and individual-take examples.
Keep the [five-stage guide](guide/README.md) usable from source code, a running
web URL and a native macOS window. Do not make CLI reference reading or CI setup
a prerequisite for the first clip. Keep native standalone recipes distinct from
versioned browser/VHS projects.
Update the reference and relevant skill when changing a documented command.

Check relative links and anchors, parse TOML examples, and execute changed
tutorial steps against a fresh synthetic project. Keep validation runs under
ignored `takes/`, without replacing accepted media in `docs/demo/`. Documentation
verification is not an owner's visual or scan-sheet approval.

When changing project messaging, keep the README, package description and plugin
description aligned. Lead with the first demo and the create, refresh and
review workflow. Keep detailed CLI instructions available for direct use.

## Add a skill

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

Use plain words, active verbs and short paragraphs. Write instructions in the
imperative: “Run the command,” “Open the file,” “Review the export.” Use “you” or
“your” when needed for clarity. Describe tool behavior in the present tense.

Use sentence case for headings and consistent terms from the
[guide's definitions](guide/README.md#the-workflow). Keep command names, paths,
options and output fields exact. Distinguish automatic checks from human review.
Avoid personal anecdotes and first-person narration in guides, examples and
reference material. The README's project origin may use first person. Preserve
attributed quotations and historical evidence in validation records. No em dashes.

## Privacy

Never add a recording, screenshot or sheet of anyone's real data to the repository, including in an issue or a pull
request. Use the notes example, or demo data you made.

## Commits

Conventional commits, such as `feat(web): …`, `fix(check): …`, `docs(guide): …`.
