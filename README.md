# reshoot

Demo videos of software, made from scripts, so you can shoot them again when the app changes.

![A made-up notes app: a note is typed and added, then found by searching](docs/demo/notes.gif)

The notes example, recorded and cut by `reshoot run` on a GitHub runner, with no one at the keyboard. Here's
[the full video](docs/demo/notes.mp4), with its terminal part and end card.

I made the launch video for [photosearch](https://github.com/mumit/photosearch) this way, and pulled the tools and
what I learned into this repo. It has:

- **a guide** to the whole process, with the pitfalls I hit ([guide/](guide/README.md));
- **a command-line tool**, `reshoot`, that records a web page from a storyboard, records one app window, puts
  everything a take can show on sheets to check by eye, and cuts the finished video;
- **Claude and Codex skills** that create, refresh, and review a demo;
- **an example app** to try it all on ([examples/notes/](examples/notes/)).

## What it does

| Step | How |
|---|---|
| Plan | Write a TOML storyboard with expected results, or a Python storyboard: named beats, each an action, a caption and a hold. Or click through the app and let `reshoot rec` write it. |
| Record a web page | `reshoot web storyboard.py takes/web.mp4` plays it in headless Chrome, with a drawn cursor, typing and captions, and zooms in on clicks and typing. Only the page is captured. |
| Record a terminal | [VHS](https://github.com/charmbracelet/vhs) plays a tape in a clean shell. |
| Record an app window | `reshoot window TextEdit takes/app.mov` records one window on macOS, never the whole screen. |
| Check | `reshoot check takes/web.assets.json takes/web.mp4` makes numbered sheets of supplied images and sampled video frames, to look at before sharing. A scan flags emails, keys, paths, addresses, faces and your own watch-for words first. `BLUR` hides what has to stay in the app. |
| Cut | A TOML edit file for ordinary cuts and export profiles, or a short Python edit script with `reshoot.cut`: trims at beat names, title and end cards, sped-up parts, a 9:16 version and GIFs. |
| Sound and subtitles | `VOICE` in the storyboard adds a voiceover, with music under it if you like. Every cut gets an `.srt` file. |
| Keep it current | `reshoot run` does the whole shoot from a `reshoot.toml`. A GitHub Action reshoots on each release and opens a pull request ([guide](guide/ci.md)). |

## Install

```bash
brew install ffmpeg
uv tool install 'reshoot[browser] @ git+https://github.com/mumit/reshoot'
```

Terminal takes also need VHS (`brew install vhs` on macOS). On Linux, install ffmpeg and, for terminal takes, [VHS](https://github.com/charmbracelet/vhs#installation) from your package manager. Web
takes need Google Chrome or Chromium (or set `RESHOOT_CHROME` to its path). App windows need macOS. I've used reshoot
on macOS only so far; see [Platforms](guide/README.md#platforms).

**For Claude Code:**

```
/plugin install reshoot --marketplace mumit/reshoot
```

Then ask Claude to make a demo video of your app. The `reshoot-demo` skill starts it off; `reshoot-refresh` updates an existing demo and `reshoot-review` inspects its output.

**For Codex or standalone Claude skills:**

```bash
reshoot skills codex --directory /path/to/project
reshoot skills claude --directory /path/to/project
```

Use the command for your harness. It installs the three primary skills from the CLI package and refuses to overwrite an existing skill. In Codex invoke `$reshoot-demo`; in Claude invoke `/reshoot-demo` (or the plugin's namespaced command).

## Start a project

```bash
reshoot init demo
reshoot doctor --config demo/reshoot.toml
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
```

This uses packaged, made-up notes data. `init demo --url http://localhost:3000/` creates a draft for your own demo app instead; replace its placeholder with one useful task and explicit result checks. New TOML storyboards use Playwright native input; existing Python storyboards remain supported. Versioned projects resolve paths from the config and write separate candidates under `takes/runs/`. Legacy configurations keep their existing paths. A preview is not a reviewed final export.

## Try it

```bash
git clone https://github.com/mumit/reshoot && cd reshoot
reshoot run examples/notes/reshoot.toml
```

That starts the example app, records a web take and a terminal take, cuts them into a finished video with an end
card, a 9:16 version and a GIF, and makes review sheets, all in `takes/`.

## Rules I follow

- I record a headless browser page, a VHS terminal or one window. Never the whole screen.
- The app runs on demo data with nothing private in it.
- I look at every image a take can show, at full size, before cutting.
- I watch the whole video before posting it, and I post it myself.

## Skills

| Skill | For |
|---|---|
| [reshoot-demo](skills/reshoot-demo/SKILL.md) | Create a demo with a brief, preview, and result checks |
| [reshoot-refresh](skills/reshoot-refresh/SKILL.md) | Update an existing demo |
| [reshoot-review](skills/reshoot-review/SKILL.md) | Inspect recordings, scan coverage, and comparisons |
| [plan-demo](skills/plan-demo/SKILL.md) | Planning the takes and the storyboard. Start here. |
| [record-web](skills/record-web/SKILL.md) | A web page from a storyboard |
| [record-terminal](skills/record-terminal/SKILL.md) | A terminal or Claude Code take with VHS |
| [record-window](skills/record-window/SKILL.md) | One macOS app window |
| [check-privacy](skills/check-privacy/SKILL.md) | Checking everything a take can show |
| [cut-video](skills/cut-video/SKILL.md) | The finished video, 9:16 version and GIFs |
| [keep-current](skills/keep-current/SKILL.md) | `reshoot run` and reshooting in CI |

See [Projects, updates, and review](guide/projects.md) for TOML stories, edits, scan coverage, and local comparisons.

## Contributing

New pitfalls, skills and fixes are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), and [ROADMAP.md](ROADMAP.md) for what I'd like to build next.

## License

MIT. See [LICENSE](LICENSE).
