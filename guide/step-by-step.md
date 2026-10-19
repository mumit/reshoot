# Step by step

These steps make a video from a web take, a terminal take and an end card. Leave out what you don't need. The
commands run from the project's root. Storyboards, tapes and the edit script go in the project (here
`tools/demo/`). Takes and cuts go in `takes/`, which git should ignore.

The [notes example](../examples/notes/) goes through each step on a small made-up app, so you can try it first.

## Once

1. **Install the tools.** On macOS:

   ```bash
   brew install ffmpeg vhs
   uv tool install git+https://github.com/mumit/reshoot
   ```

   On Linux, install ffmpeg and [VHS](https://github.com/charmbracelet/vhs#installation) from your package manager.
   `pipx install git+https://github.com/mumit/reshoot` works instead of uv. Web takes also need Google Chrome or
   Chromium; set `RESHOOT_CHROME` to its path if reshoot can't find it.
2. **For Claude Code,** add the skills:

   ```
   /plugin install reshoot --marketplace mumit/reshoot
   ```

   Then ask Claude to "make a demo video of this app", and it follows the steps below.
3. **Make demo data.** Give the app its own database, data folder or account, with only things anyone may see.
   Check that the app can be pointed at it with a flag or an environment variable, and can't reach real data while
   it does. Good demo data:
   - uses made-up people, with names that are clearly made up and emails at `example.com`;
   - has no real customers, colleagues, addresses, phone numbers or payment details;
   - has test keys only, which you can revoke after recording;
   - has photos without people, and of places that aren't near anyone's home;
   - looks real enough to be interesting: a few dozen varied items, not three called "test".
4. **For app windows (macOS),** give the app you run commands from (Terminal, iTerm, an editor) Screen Recording
   permission: System Settings, Privacy & Security, Screen Recording. Then restart it.
5. **For Claude Code takes,** make a separate config folder, so nothing of your usual setup shows. Log in once, with
   the account that should appear:

   ```bash
   CLAUDE_CONFIG_DIR=~/.claude-demo claude
   ```

## Plan

1. Decide where the video goes and how long it is. Thirty to sixty seconds suits a social post.
2. List the three to six things it shows. Each gets a caption of a few plain words.
3. Pick a take for each: web if it's in a browser, terminal for a CLI or an AI agent, an app window only when
   nothing else can show it.

## Write the storyboard

Start from [examples/notes/storyboard.py](../examples/notes/storyboard.py). Each beat is a name, some JavaScript run
in the page, and seconds to hold:

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

- `__demo` has `click`, `type`, `key`, `waitFor`, `scroll`, `caption`, `hide` and `show`. The
  [record-web skill](../skills/record-web/SKILL.md) lists them all.
- Give a caption about 1.5 seconds to be read, and a result 2.5 seconds or more.
- If the app needs a login, log in with a demo account in `SETUP` beats. They run before recording starts.
- Views that load slowly the first time (maps, charts, big images) go in `WARM`, so they're ready when shown.
- `ZOOM = True` zooms in on each click and bit of typing, then back out, so the video is readable on a phone.

## Record the web take

1. Start the app on its demo data, and leave it running.
2. Record:

   ```bash
   reshoot web tools/demo/storyboard.py takes/web.mp4
   ```

   It prints each beat and how long it took, then the frame rate and any page errors. Next to the video it writes
   `web.beats.json` (when each beat starts) and `web.assets.json` (every image and media file the page loaded).
3. Look at a few frames: `ffmpeg -ss 5 -i takes/web.mp4 -frames:v 1 frame.png`.
4. For a phone version, record again with `--size 390x844@3 --mobile`.

## Record the terminal take

1. Copy [the template tape](../skills/record-terminal/template.tape) and change the commands.
2. Record: `vhs tools/demo/cli.tape`.
3. Find where it finished: `reshoot last-change takes/cli.mp4`.

## Record an app window

```bash
reshoot window --list                         # check the window is there
reshoot window TextEdit takes/app.mov -s 8
```

## Check everything the takes can show

1. Make sheets:

   ```bash
   reshoot check takes/web.assets.json takes/web.mp4 takes/cli.mp4 --review takes/review
   ```

   Keep the app running: the assets list holds URLs, which are fetched from it. If the app shows things at random
   (suggestions, featured items, a shuffled gallery), add the whole set it picks from, such as its image folder.
2. Open `takes/review/01.jpg` and the rest. Look at each image at full size.

   **What fails:**
   - a person, including faces at the edge, tiny figures, reflections and people behind windows;
   - personal details: names, emails, phone numbers, addresses, number plates, house numbers;
   - secrets: keys, tokens, passwords, URLs with tokens in them;
   - work details: customers, colleagues, internal tools, unreleased features, private repo names;
   - the computer itself: user names, file paths, other apps, browser tabs, bookmarks, notifications.

   When in doubt, it fails.
3. **If something fails:**
   1. Note its label, such as `3-2`, and run `reshoot check --review takes/review --fail 3-2`. It prints where it came
      from.
   2. Take it out of the demo data.
   3. Record the take again, since the old take still shows it.
4. **When the rest pass:** `reshoot check --review takes/review --ok`.
5. Run step 1 again. Repeat until it says everything has been checked.

## Cut

1. Copy [examples/notes/edit.py](../examples/notes/edit.py) into the project and change the words at the top.
2. Run it:

   ```bash
   reshoot edit tools/demo/edit.py takes/web.mp4 takes/cli.mp4
   ```

   The example writes the finished video, a 9:16 version and a GIF next to the web take.
3. Watch all of it. Read any text on screen, including what an AI agent wrote in a terminal take.

## All at once

Once each step works, put them in a `reshoot.toml` and `reshoot run` does the whole shoot. A GitHub workflow can
then reshoot on each release. See [reshoot in CI](ci.md).

## When the app changes

- **A button or name changed:** fix the selector in the storyboard and record the web take again.
- **Beats renamed or added:** update the beat names the edit script uses for trims and GIFs.
- **New content in the demo data:** check it before cutting. `reshoot check` shows only what's new.

## Before posting

Nothing posts on its own. I watch the video all the way through, at full size, once more, and then post it myself.
