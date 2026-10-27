# reshoot

**Demos that stay current.**

Script a task in your app once. reshoot records it as a captioned MP4 and a
README GIF, checks that the result really appeared, and keeps the script beside
your code. When the UI changes, run it again: the same story, freshly recorded.

![The same notes task recorded before and after a UI update, from one reshoot storyboard](docs/demo/reshoot.gif)

Before and after a UI change, from one storyboard.
[Watch the 21-second social cut](docs/demo/reshoot.mp4).

- **Re-record, don't redo.** The demo is a `storyboard.toml` of clicks, typing,
  captions and the result that should appear. Run it after every UI change.
- **Checked, not just captured.** Each run confirms that the result you named
  appeared, stops on the step whose control no longer matches, and scans the
  frames for email addresses, keys and faces before you share anything.
- **Your agent can drive it.** Skills for Claude Code and Codex write the story
  from your app, and a GitHub workflow records it again when the app changes and
  opens a pull request with the new video.

## Make a demo of your app

Open **Claude Code or Codex** in your app's repository, or in an empty folder
if you only have a running app, and paste:

```text
Make a short demo with reshoot.
Read https://github.com/mumit/reshoot/blob/main/guide/agent-quickstart.md
and follow its setup and creation workflow.

Target: the app in this repository.
Choose one useful task with a clear visible result. Use synthetic demo data.
Produce a short captioned MP4 and a README GIF. Keep the recording source in
demo/ so it can be updated later.

Inspect a preview, then record a fresh final and open both exports for review.
Ask only for permissions or missing details needed to proceed.
```

Change `Target:` to a URL, or to a macOS app and its window, if there's no
source, and add a task if you have one. The agent installs reshoot, reads your
app, writes the story and the checks that prove it worked, and fixes it until
it records cleanly. In
[trials on new apps](docs/validation/2026-10-23-cold-first-demo.md) that took
2 to 5 minutes in Claude Code and 4 to 9 in Codex. It opens the MP4 and GIF;
reply "accept" or ask for changes. Nothing is published. reshoot needs no
API key: see
[what your agent needs](guide/agent-quickstart.md#what-your-agent-needs).

## Or see it on a made-up app first

```bash
uv tool install 'reshoot[browser]'
reshoot create        # make the notes demo and open it in the studio
```

It needs [uv](https://docs.astral.sh/uv/), ffmpeg and Chrome or Chromium, and
runs on macOS or Linux; [installation](guide/install.md) covers each, and
`reshoot create` says what's missing. It makes a made-up notes app and a story
for it, records a preview in about 25 seconds, and opens it in
[the studio](guide/studio.md).

## Then shape it in the studio

The studio is a page on your computer for a demo that has a recording: change
captions, timing, the look and the cut by pointing, then make the final and
accept it. `reshoot studio demo` opens it. [The tutorial](guide/step-by-step.md)
walks through it on the notes app: change the demo, break the app, watch the
story stop on the step that broke, repair it, and compare.

## Show the task yourself

For a simple web app, start it with demo data and run
`reshoot create http://127.0.0.1:3000/ --directory demo` with its address. Show
one task in the browser that opens, and choose **Done**.
[Record your own web app](guide/your-app.md#show-the-task) has the details.

## The story is a file

```toml
[[beat]]
id = "search"
caption = "Find the matching note"
hold = 2.0
[[beat.action]]
type = "type"
target = {css = "#q"}
text = "bike"
[[beat.expect]]
type = "text"
target = {css = "#list li"}
contains = "Pick up the bikes"
```

reshoot types into the real page with a visible cursor, shows the caption, and
holds on the result. When the app renames `#q`, the run stops on that step:
`type target {css = '#q'} matched 0 elements`. Fix the target, or pick the new
one in the studio, and run again.

## Keep it current

Accept a final once; that writes `demo/accepted/`, a small record to commit.
After the app changes, record again, compare, accept the update and copy it
into your docs:

```bash
reshoot run demo/reshoot.toml
reshoot compare demo/accepted demo/latest --out demo/comparison.json
reshoot accept demo/latest
reshoot export demo/accepted --directory docs/demo --replace
```

Or let CI do it: the [GitHub workflow](guide/ci.md) records the demo when the
app changes on `main` and opens a pull request with the new video, GIF and a
step-by-step comparison. A broken story fails on its step and opens nothing.

## How it differs

| If you use | reshoot adds |
|---|---|
| Screen Studio, Loom, ScreenFlow | Re-recording on demand. You give up some hand polish; you never record the same flow by hand again |
| [VHS](https://github.com/charmbracelet/vhs) | The same idea for web apps and macOS windows. reshoot uses VHS for terminals |
| Playwright video | A cursor, typing, captions, zoom, cuts, a GIF, result checks and a privacy scan |
| Arcade, Supademo | Ordinary MP4 and GIF files, made locally from open source, that CI can refresh |

## What it records

| Show | How |
|---|---|
| A web app | Headless Chrome: the page only, never your desktop |
| A CLI or an agent at work | [VHS](https://github.com/charmbracelet/vhs) terminal recordings |
| A native app on macOS | One window, by its ID |
| A narrated explanation | Voiceover timed to the steps, music under it, subtitles |
| Other formats | Edits, portrait crops and size limits for each export |

[Platforms](guide/README.md#platforms) lists what runs where.

## Skills for Claude Code and Codex

| When | Skill | Ask for |
|---|---|---|
| The first demo | [reshoot-demo](skills/reshoot-demo/SKILL.md) | "Show a customer saving a search and seeing its results." |
| The app changed | [reshoot-refresh](skills/reshoot-refresh/SKILL.md) | "Record that task again with the updated UI." |
| Before sharing | [reshoot-review](skills/reshoot-review/SKILL.md) | "Check the final video and GIF against the accepted run." |

Skills are instructions for a coding agent and its model; the CLI also runs
without a coding agent. The first-demo prompt installs the skills, and
[installation](guide/install.md#install-the-skills) shows other ways. The [skill catalog](skills/README.md) describes all ten.

## Where next

| To | Read |
|---|---|
| Learn it step by step | [The tutorial](guide/step-by-step.md) |
| Record your own app | [A web app](guide/your-app.md), or [a macOS window](guide/macos-window.md) |
| Change a demo | By pointing in [the studio](guide/studio.md), or by its [files](guide/projects.md) |
| See the cursor, zoom, captions and shapes | [How the videos look](guide/look.md) |
| Use it on a team | [Ownership, review, alerts and CI cost](guide/publish.md#on-a-team) |
| Keep it current in CI | [GitHub Actions](guide/ci.md) |
| Look something up | [Project reference](guide/projects.md) · [Commands](guide/commands.md) · [Troubleshooting](guide/troubleshooting.md) |
| Rebuild the video above | [Before-and-after recipe](examples/promo/README.md) |

## Why reshoot exists

I made the launch video for [photosearch](https://github.com/mumit/photosearch)
this way, and pulled the tools and what I learned into reshoot. Keeping a
demo's story beside the app makes the work of making it pay off again every
time the product changes.

The [original notes recording](docs/demo/notes.mp4) and its
[source files](examples/notes/) are still here.

## Contributing

New pitfalls, skills and fixes are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md)
for how to work on it and [ROADMAP.md](ROADMAP.md) for what's planned.

## License

MIT. See [LICENSE](LICENSE).
