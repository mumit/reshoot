# Pitfalls

What to watch for when you record, cut and review a demo: each one happened in
a real demo, and each still needs a person to do something. For an error
message, see [troubleshooting](troubleshooting.md). Problems reshoot now
handles for you are listed in the [CHANGELOG](../CHANGELOG.md).

## Privacy

- **A full-screen capture shows everything.** Record only a headless browser
  page, a VHS terminal, or one window by its ID.
- **Small things get missed on the first look.** Inspect every image at full
  size, including frame edges, reflections, silhouettes and blurred figures.
  Reject uncertain images.
- **A clean scan isn't a pass.** A scan reads text and finds faces, but misses
  text in pictures, odd fonts, and things it has no rule for. Only a person
  marks an image as checked.
- **A sampled scan can miss something brief.** It looks at a frame every three
  seconds. For a final, use `--full`, or `full = true` in `[check]`, to look at
  every frame.
- **Vision's fast reader misses tiny text.** On Macs where Vision's accurate
  text reader fails, reshoot reads text with the fast one and says so. Look
  closely at small text on the sheets.
- **Screenshots and tours have words too.** Their alt text, titles and
  explanations are scanned, but a passing result check says nothing about
  whether they're safe to share. Read them.
- **Random content shows something new each take.** Checking one take doesn't
  cover every item. Check the whole set the app picks from.
- **Removing something doesn't fix the take.** The take still shows it. Take it
  out of the demo data and record again.
- **The terminal shows more than you think:** the user and machine name in the
  prompt, the folder, shell history, API keys in typed commands. Start a clean
  shell with `env -i`, a plain `PS1` and a folder under `/tmp`, all in a hidden
  part of the tape.
- **`env -i` also removes an agent's credentials.** An agent that reads its
  provider key from the environment fails to connect (omp showed a 401). Don't
  name the key in the tape. Start
  `PS1='$ ' HISTFILE=/dev/null exec bash --noprofile --norc` instead: no
  profile, prompt or history, but the environment stays.
- **An AI agent's banner shows the account, folder and setup.** For Claude
  Code, use a separate `CLAUDE_CONFIG_DIR`, a demo folder, and only the tools
  the take needs (`--strict-mcp-config`, `--allowedTools`).
- **What an agent says.** An agent's answer can include private details. Read
  it before cutting.
- **Expected flags in an agent's terminal.** The scan flagged npm's
  `> token-estimator@1.0.0 start` as an email, struck-through todo lines as
  keys, and costs such as `$0.00002875` as phone numbers. Look at each one
  anyway.

## Web takes

- **A passed check with the result off screen.** A text check found the token
  count in the page, but it was below the fold, so the video never showed it.
  Look at the frame for each result, and add a `scroll` action so the control
  and its result share the view.
- **Watch the video, not only the checks.** A check proves the result was in
  the page, not that the viewer could see it in time. Watch each result appear.
- **Results that take a moment.** A hold long enough on one run is too short on
  the next. Wait for the result with a result check before the hold, and use
  the hold only for reading time.
- **The studio can't see a remote app.** Update preview knows when the project
  files or declared `inputs` changed, not a remote app or its database. After
  those change, use **Record app again**.
- **Don't fix a wrong result by changing the target.** A repair changes how a
  step finds its control. If the result is wrong, fix the app, the demo data
  or the story, and keep the check.
- **A recording issue blocks the story.** When the recorder meets a step it
  can't replay, it saves the rest and marks that step `recording_issue`. Write
  its actions by hand, or record it again, and remove the field.
- **Ids that change.** Frameworks make ids like `css-8f3k2z` that change
  between builds. Prefer a test id, a name, a label or the element's words.
  `reshoot rec` does this for you.
- **An agent builds a different page each take.** Put the `data-testid`s the
  storyboard needs in the agent's conventions file, such as `AGENTS.md` in its
  workspace. The checks then held when the layout changed.
- **A higher pixel ratio makes text sharper, not larger.** `@2` records twice
  the pixels, so zoom stays sharp. To make text larger in a GIF, record a
  narrower viewport, such as `960x540`.
- **A full-width page is hard to read on a phone.** Use auto-zoom, a narrower
  recording view, or a crop. [How the videos look](look.md#auto-zoom) shows
  each.
- **A light or dark page when you wanted the other.** reshoot sets
  `prefers-color-scheme` to dark unless the storyboard asks for light.
- **A fresh profile is logged out.** Each take starts with a fresh browser
  profile. Log in with a demo account before recording starts, and keep
  personal profiles out of it.
- **Blank views when first shown.** Nothing is cached in a fresh profile. For
  Python stories, list slow views such as maps in `WARM` to load them first.
- **Code after a click that opens a page doesn't run.** In a Python story, the
  page it was in has gone. Put that code in the next beat.
- **Legacy Python stories can click covered controls.** TOML stories fail on a
  covered control instead. Move to TOML when you can.
- **A browser take and a terminal take must match in size.** Give both the same
  dimensions in the project, or place the smaller one on a card.
- **The accepted record must reach Git.** A `takes/` line in a `.gitignore` also
  matches `demo/accepted/takes/`. Ignore `/demo/takes/` from the repository
  root, or `/takes/` inside `demo/`, as `reshoot init` does.

## Terminal takes

- **VHS throws away the whole recording when a `Wait` times out.** Use a fixed
  `Sleep` longer than the slowest run, then cut at `reshoot last-change`.
- **`Wait+Screen` misses text that's on screen.** In VHS 0.12.1 it reads an
  empty screen while the tape is hidden (`Hide`), never matches a pattern with
  backslash classes such as `\s`, and timed out on an agent's full-screen
  terminal UI with the awaited line in plain view. The timeout message ends
  `last value was:` with nothing after it. Don't wait for an agent to finish:
  `Sleep` past its slowest run, as above.
- **Agent response times vary between runs.** Allow enough time in `Sleep` for
  the response to finish. Label any speed changes in the edit.
- **A take that varies in length can't be cut by beat.** Terminal takes have no
  beats, so the edit cuts them at seconds. A fixed `Sleep` keeps the length
  fixed; play the part that varies at a labelled speed.
- **The app is built during the take.** `[app]` must answer before the first
  take. Serve a placeholder on the port until the tape touches a file, then
  start the built app on the same port. Tell the agent to test on another port
  and stop its servers. Raise the run's `timeout` (600 s by default) to cover
  the build.
- **Leftovers from the last take.** Demo data from an earlier run can produce
  duplicate results. Reset the demo data in the hidden setup.

## App windows

- **Two scripts driving the same app can stall it.** Drive the window from one
  script at a time, and don't use the app during recording.
- **"could not create image from window"** means the app running the command
  has no Screen Recording permission, or the window is minimized.

## Cutting and sound

- **`end` and `through` differ.** `end = "search"` stops where the search beat
  starts; `through = "search"` includes it and its hold. Use one or the other.
- **A crop can cut off a caption or a result.** Use Fit to keep the whole
  video, or aim the crop and inspect the export at its viewing size. Fit can't
  bring back what the recording didn't show.
- **Text hints aren't a readability pass.** A missing measurement isn't a pass
  either. Look at each export at the size people will watch it.
- **Muted narration still takes its time.** A voice at 0% keeps its timing and
  subtitles. To remove the pause too, remove its words and record again.
- **Clips of different sizes don't join.** A 1280x720 terminal take and a
  1920x1080 web take can't be joined as they are, and `cut.concat` refuses
  them. Place the smaller one on a full-size card with `cut.place` first.
- **Custom ffmpeg edits lose subtitle timing.** reshoot's cut helpers record
  where each part came from; an edit of your own needs its own map.
- **Check the GIF, not only the MP4.** Look at its first frames, last frames
  and length.
- **Odd sizes.** H.264 in yuv420p needs even widths and heights.

## Add a pitfall

When something goes wrong, add it here in a line or two: what happened, and
what avoids it. If reshoot can avoid it, fix it there, say so in the
CHANGELOG, and keep it here only if people still need to do something.
