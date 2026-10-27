# Manual takes and Python storyboards

The lower-level workflow for Python stories, VHS terminal takes, Python edits
and single macOS windows, in the legacy layout. For a first demo, use
[the tutorial](step-by-step.md) instead.

These steps make a video from a web take, a terminal take and an end card;
leave out what you don't need. Commands run from the project's root, with
stories, tapes and the edit in `tools/demo/` and takes in `takes/`, which Git
ignores. The [notes example](../examples/notes/) has each piece.

## Once

1. **Install** [reshoot](install.md) and VHS (`brew install vhs`, or
   [VHS's instructions](https://github.com/charmbracelet/vhs#installation) on Linux).
2. **For Claude Code,** add the [plugin](install.md#install-the-skills); its
   skills cover the takes below.
3. **Make demo data** the app can be pointed at, with no way to reach real data:
   made-up people with `example.com` emails, no real customers, addresses or
   payment details, revocable test keys, photos without people or homes, and a
   few dozen varied items.
4. **For app windows,** give the app you run commands from Screen Recording
   permission in System Settings, Privacy & Security, then restart it.
5. **For Claude Code takes,** log in once with the demo account in a separate
   configuration folder: `CLAUDE_CONFIG_DIR=~/.claude-demo claude`.

## Plan

Pick three to six things to show, a short caption each, and a take for each:
web, terminal, or an app window only when nothing else can show it.

## Write the storyboard

Draft one by doing the task in a fresh browser, then closing it:

```bash
reshoot rec http://localhost:8000/ tools/demo/storyboard.py
```

Each click or run of typing becomes a step. Add captions and check the selectors.

Or start from [examples/notes/storyboard.py](../examples/notes/storyboard.py).
Each step in `BEATS` is a name, JavaScript run in the page, and seconds to hold:

```python
URL = "http://localhost:8000/"
SIZE = "1280x720@1.5"
BEATS = [
    ("home", "__demo.caption('Notes that are easy to find')", 1.8),
    ("type", "__demo.caption(null); await __demo.type('#text', 'Pick up the bikes')", 0.4),
    ("add", "await __demo.click('#add button')", 1.4),
    ("end", "__demo.caption('Notes'); __demo.hide()", 2.5),
]
```

- `__demo` has `click`, `type`, `key`, `waitFor`, `scroll`, `caption`, `hide`
  and `show`; the [record-web skill](../skills/record-web/SKILL.md) lists them.
- Give a caption about 1.5 seconds and a result 2.5 or more.
- `SETUP` steps run before recording, such as a demo login.
- `BLUR` lists private parts of the app, such as the account name.
- `VOICE = {"home": "Find a note by its words."}` adds a voiceover; see
  [examples/notes/voiced.py](../examples/notes/voiced.py).
- `WARM` lists slow views, such as maps, to load first.
- `ZOOM = True` zooms on each click and bit of typing.

## Record the web take

With the app running on demo data:

```bash
reshoot web tools/demo/storyboard.py takes/web.mp4
```

It writes `web.beats.json` and `web.assets.json` (every image the page loaded). Check frames with
`ffmpeg -ss 5 -i takes/web.mp4 -frames:v 1 frame.png`. For a phone version,
add `--size 390x844@3 --mobile`.

## Record the terminal take

Copy [the template tape](../skills/record-terminal/template.tape), change the
commands, run `vhs tools/demo/cli.tape`, and find where it finished with
`reshoot last-change takes/cli.mp4`.

## Record an app window

```bash
reshoot window --list
reshoot window TextEdit takes/app.mov --id WINDOW_ID -s 8
```

See [a macOS window](macos-window.md).

## Check everything the takes can show

1. Make the sheets, with words that must not appear:

   ```bash
   reshoot check takes/web.assets.json takes/web.mp4 takes/cli.mp4 --review takes/review --watch-for "Acme,Jane Roe"
   ```

   Keep the app running, since the assets list is fetched from it. If the app
   shows things at random, add the whole set it picks from.
2. Open `takes/review/01.jpg` and the rest at full size. Fail any person,
   personal detail, secret, work detail (customers, internal tools, unreleased
   features), or sign of the computer (user names, paths, tabs, notifications).
   Reject what you're unsure of.
3. For a failure, run `reshoot check --review takes/review --fail 3-2` to see
   where it came from, remove it from the demo data, and record the take again.
4. When the rest pass, run `reshoot check --review takes/review --ok`, then
   step 1 again until everything is checked.

## Cut

Copy [examples/notes/edit.py](../examples/notes/edit.py), change the words at
the top, and run:

```bash
reshoot edit tools/demo/edit.py takes/web.mp4 takes/cli.mp4
```

It writes the video, a 9:16 version, a GIF and subtitles next to the web take,
with the voiceover and any `MUSIC`. Watch all of it, including what an agent
wrote in a terminal take.

## Legacy shoot files in CI

A `reshoot.toml` runs the whole shoot, locally or in CI, and copies the files
in `[keep]`. From
[examples/notes/reshoot.toml](../examples/notes/reshoot.toml):

```toml
[app]
run = "npm run dev -- --port 8000"
url = "http://localhost:8000/"

[[take]]
web = "tools/demo/storyboard.py"
out = "takes/web.mp4"

[[take]]
tape = "tools/demo/cli.tape"

[edit]
script = "tools/demo/edit.py"
args = ["takes/web.mp4", "takes/cli.mp4"]

[check]
sources = ["takes/web.assets.json", "takes/final.mp4"]
review = "takes/review"

[keep]
"takes/final.mp4" = "docs/demo/demo.mp4"
"takes/web.gif" = "docs/demo/demo.gif"
```

`takes/run.json` says what happened. `[keep]`
copies on every run, local ones too, so check the diff. New projects should
use the [versioned files](projects.md).

For CI, copy [examples/github/reshoot.yml](../examples/github/reshoot.yml) to
`.github/workflows/reshoot.yml`, change its marked lines, add your app's setup
steps, and turn on "Allow GitHub Actions to create and approve pull requests"
in Settings, Actions, General. On each release, or by hand, it runs the shoot,
uploads the `reshoot-review` artifact and opens a pull request with the
`[keep]` files. Look at every sheet before merging.

## When the app changes

- **A control changed:** fix the selector and record the web take again.
- **Steps renamed or added:** update the names the edit script uses.
- **New demo data:** check it; `reshoot check` shows only what's new.
