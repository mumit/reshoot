# Pitfalls

Use this reference to diagnose recording, editing and review problems.
"Fixed in reshoot" identifies problems the tool now handles automatically.

## Privacy

- **A full-screen capture shows everything.** Record only a headless browser page,
  a VHS terminal, or one window by its ID.
- **Small things get missed on the first look.** Inspect every image at full size,
  including frame edges, reflections, silhouettes and blurred figures. Reject
  uncertain images.
- **Random content shows something new each take.** Checking one take does not cover
  every possible item. Check the whole set the app selects from.
- **A scan finds a key, and prints it.** Listing what was found would put a key in the terminal and in a CI log.
  Fixed in reshoot: `reshoot check` shows only enough to recognize it (`sk-a•••`).
- **Trusting a clean scan.** A scan reads text and finds faces, but misses text in pictures, odd fonts, and things it
  has no rule for. Only a person marks an image as checked.
- **Removing something doesn't fix the take.** The take still shows it. Record again after taking it out of the
  demo data.
- **The terminal shows more than you think:** the user and machine name in the prompt, the folder, shell history,
  API keys in typed commands. Start a clean shell with `env -i`, a plain `PS1` and a folder under `/tmp`, all in a
  hidden part of the tape.
- **`env -i` also removes an agent's credentials.** An agent that reads its provider key from the environment
  fails to connect (omp showed a 401). Don't name the key in the tape. Start
  `PS1='$ ' HISTFILE=/dev/null exec bash --noprofile --norc` instead: no profile, prompt or history, but the
  environment stays.
- **An AI agent's banner shows the account, folder and setup.** For Claude Code, use a separate
  `CLAUDE_CONFIG_DIR`, a demo folder, and only the tools the take needs (`--strict-mcp-config`, `--allowedTools`).
- **What an agent says.** An agent's answer can include private details. Read it before cutting.
- **Expected flags in an agent's terminal.** The scan flagged npm's `> token-estimator@1.0.0 start` as an email,
  struck-through todo lines as keys, and costs such as `$0.00002875` as phone numbers. Look at each one anyway.

## Web takes

- **A caption disappeared when a native click loaded a new page.** Fixed in reshoot:
  the overlay restores its current caption after a full page load on the same origin,
  along with the cursor position. Subtitle events still describe the original beat.

- **A browser and terminal preview could not be joined.** Preview reduced the browser
  output while VHS kept its tape dimensions. Fixed in reshoot: previews with VHS
  takes retain the configured browser dimensions. Configure matching sizes for both takes.

- **A stale browser override passed setup checks.** `RESHOOT_CHROME` could point to a
  missing or nonexecutable file while `doctor` reported success. Fixed in reshoot:
  the dependency check requires an executable browser and exits with an error
  when the configured path is unavailable. Correct or unset the override.

- **Chrome sends no frames while the page is still.** The last frame (the end card) got almost no time in the
  video. Fixed in reshoot: each frame is held until the next, and the last until recording stops.

- **A result showed up a whole hold late, while every check passed.** The evidence screenshot taken after each
  beat's checks could take the frame that showed the result, and a still page sends no other, so the video kept
  the old page until the next beat. A React app at `960x540@2` did this on every take. Fixed in reshoot: the
  evidence frame is the last frame the video shows, saved at the end of the hold, and no screenshot is taken
  during capture. Watch the video, not only the checks.

- **A higher pixel ratio doesn't sharpen the video.** Chrome sends screencast frames at the page's CSS size, so
  `@1.5` or `@2` scales them up. A narrower viewport, such as `960x540`, makes text larger in the GIF.
- **A 5-second take came out 389 seconds long.** The Mac went to sleep during it. The beats and the end of recording
  were timed with the system clock, which keeps counting through sleep; Chrome's frame times don't. Fixed in
  reshoot: it times everything with a clock that stops during sleep too, matched to Chrome's at the first frame.
- **The frame rate goes up and down.** Chrome paints about 45 to 50 frames a second while things move, and none
  when still. Fixed in reshoot: frames keep their times, and ffmpeg makes a steady 60 fps.
- **Blank views when first shown.** Each take starts with a fresh browser profile, so nothing is cached.
  For Python stories, list slow views such as maps in `WARM` to load them before recording.
- **A fresh profile is logged out.** Log in with a demo account in `SETUP` beats, which run before recording.
  Keep personal browser profiles separate from recordings.
- **Headless Chrome won't go below a 500 px window.** For a phone layout the page was too wide. Fixed in reshoot: the
  size is set with device metrics, and it prints a note if `innerWidth` isn't the width asked for.
- **Results that take a moment.** A hold that's long enough on one run is too short on the next. Wait for the
  result with `__demo.waitFor` before the hold.
- **Typed text the app doesn't see.** React and other frameworks ignore `el.value = ...`. Fixed in reshoot: typing
  uses the browser's own value setter and sends input events.
- **Clicks that do nothing.** `el.click()` alone doesn't send pointerdown or mousedown, which many apps listen for.
  Fixed in reshoot: a click sends the same events a mouse does.
- **Following a link to a new page.** The overlay was lost, the cursor jumped, and the next beat could start before
  the page loaded. Fixed in reshoot: the overlay is added to every page, the cursor keeps its place, and the hold
  starts once the new page has loaded. Code in the same beat after the click doesn't run, since its page is gone,
  so put it in the next beat.
- **A small page on a phone.** A full-width page in a 16:9 video is hard to read on a phone. `ZOOM = True` zooms in
  on each action. The first try zoomed right in on a small button and cut off the new note it added. Fixed in
  reshoot: actions close together share one view that holds them all.
- **Zooming out and back in for a pause.** In a recorded storyboard, a 3 s pause between typing a note and clicking
  Add made the view zoom out and straight back in. A pause isn't a reason to move. Fixed in reshoot: the view stays
  while the next action is in view (or just out of it), and moves out only for a long quiet spell, a new caption,
  an action far away, or a change outside the view.
- **Staying zoomed hides results.** With the view staying put, a search that filtered a list below stayed out of
  sight, and a new page appeared zoomed on an old spot. Fixed in reshoot: it compares the frames, moves out when
  something sizeable changes outside the view (just before it, for a new page), and stays out for a second.
- **Zooming the live page breaks it.** Scaling the page itself moves fixed headers and pushes captions off screen.
  reshoot zooms afterwards, from where each action was, and draws captions after the zoom.
- **Enter recorded twice.** Pressing Enter in a form makes the browser click the form's button too. Recording both
  added the note twice on replay. Fixed in reshoot: `reshoot rec` skips clicks no mouse made.
- **Clearing a field recorded as typing nothing.** The first recordings kept only what a field held at the end, so
  emptying a search box replayed as "type nothing" and left the old text there. Fixed in reshoot: `reshoot rec`
  notes what the field held first, and clears it on replay when the text was removed or changed.
- **A click on the page's background.** It was recorded with an empty selector, and the replay stopped there.
  Fixed in reshoot: clicks on the page itself are skipped, since they do nothing.
- **Ids that change.** Frameworks make ids like `css-8f3k2z` that change between builds. `reshoot rec` skips ids
  that look made up and uses a test id, a name, a label or the element's words instead.
- **A light or dark page when you wanted the other.** reshoot sets `prefers-color-scheme` (dark unless asked).
- **A passed check with the result off screen.** Text checks found the token count in the page, but it was below
  the fold, so the video never showed it. Look at the frames for each result, and add a `scroll` action so the
  controls and the result share the view.
- **No `select` action.** TOML storyboards couldn't choose from a `<select>`. Fixed in reshoot: a `select`
  action picks an option by its visible label, and `reshoot rec` writes one.
- **The accepted record lost its evidence in Git.** A `takes/` line in a `.gitignore` also matches
  `demo/accepted/takes/`, so the record's beat results and evidence frames were never committed. Ignore
  `/demo/takes/` from the repository root, or `/takes/` inside `demo/`. Fixed in reshoot: `reshoot init` writes
  `demo/.gitignore` with `/takes/`.
- **A preview accepted as the CI baseline.** `demo/latest` is the newest successful run, previews included, so
  `reshoot accept demo/latest` after a preview committed a small, quick preview as the baseline. Fixed in reshoot:
  `accept` refuses a preview unless given `--preview`.
- **An agent builds a different page each take.** Put the `data-testid`s the storyboard needs in the agent's
  conventions file, such as `AGENTS.md` in its workspace. The checks then held when the layout changed.

## Terminal takes

- **VHS throws away the whole recording when a `Wait` times out.** Use a fixed `Sleep` longer than the slowest
  run, then cut at `reshoot last-change`.
- **`Wait+Screen` misses text that's on screen.** In VHS 0.12.1 it reads an empty screen while the tape is
  hidden (`Hide`), never matches a pattern with backslash classes such as `\s`, and timed out on an agent's
  full-screen terminal UI with the awaited line in plain view. The timeout message ends `last value was:` with
  nothing after it. Don't wait for an agent to finish: `Sleep` past its slowest run, as above.
- **Agent response times vary between runs.** Allow enough time in `Sleep` for the
  response to finish. Label any speed changes in the edit.
- **A take that varies in length can't be cut by beat.** Terminal takes have no beats, so the edit cuts them at
  seconds. A fixed `Sleep` keeps the take's length fixed; play the part that varies at a labelled speed.
- **The app is built during the take.** `[app]` must answer before the first take. Serve a placeholder on the
  port until the tape touches a file, then start the built app on the same port. Tell the agent to test on
  another port and stop its servers. Raise the run's `timeout` (600 s by default) to cover the build.
- **Leftovers from the last take.** Demo data from an earlier run can produce duplicate
  results. Reset the demo data in the hidden setup.

## App windows

- **Two scripts driving the same app can stall it.** Drive the window from one script
  at a time and avoid interacting with the app during recording.
- **"could not create image from window"** means the app running the command has no Screen Recording permission,
  or the window is minimized.
- **The recording includes the window's shadow.** A square crop of the window still showed the black background
  at its round corners. Fixed in reshoot: `cut.window_clip` crops to the window and rounds the corners to match.

## Cutting

- **Clips of different sizes don't join.** A 1280x720 terminal take and a 1920x1080 web take can't be joined as
  they are. `cut.concat` refuses them. Place the smaller one on a full-size card with `cut.place` first.
- **Washed-out cards after a web take.** Chrome's frames are full-range JPEGs, and a joined video is read with its
  first clip's range, so the dark cards after the web take came out gray. Fixed in reshoot: every clip is made in
  standard range, and `cut.concat` refuses clips whose ranges differ.
- **A joined promo failed its exact frame-rate check on Linux.** Stream-copy joins
  accumulated rounded container durations with Debian's ffmpeg. Fixed in reshoot's
  promotional recipe: joins rebuild timestamps from frame count at 30 fps.
- **An extra second at the end of a web take.** ffmpeg's concat list gives the repeated last frame time of its own.
  Fixed in reshoot: the output is cut at the take's real length.
- **The first beat starts before the first frame.** Fixed in reshoot: its start is 0, not a little below.
- **Banded GIFs.** ffmpeg's default palette looks poor. `cut.gif` makes a palette for each GIF.
- **A GIF dropped the opening card or froze at a joined section.** Video metadata
  changed between the card and browser take, resetting ffmpeg's palette filter.
  Fixed in reshoot: GIF exports normalize frames before building one palette
  from the full clip, preserving static sections and scene changes.
  Inspect the beginning, ending and duration of the exported GIF as well as the MP4.
- **Odd sizes.** H.264 in yuv420p needs even widths and heights.

## Add a pitfall

When something goes wrong, add it here in a line or two: what happened, and what avoids it. If reshoot can avoid it,
fix it there too and say so.

## Check failures

- **An interrupted flow reported passed expectations.** An earlier beat's assertion
  passed, but a later action failed before its result could be checked. Fixed in
  reshoot: incomplete or missing browser takes leave expectations unverified. An assertion
  that actually fails still reports failed.

- **Missing sources looked checked.** Fixed in reshoot: failed fetches, invalid images and manifests, and detector errors produce exit 2 and an error report.
- **The server stopped before checking its images.** Fixed in reshoot: URL checks finish before app shutdown.
- **A check crashed but CI reported success.** Fixed in reshoot: the runner requires a fresh completed check report and saves failures before exiting.
- **Old narration entered a new take.** Fixed in reshoot: removing `VOICE` removes the previous take's narration metadata.
- **A browser disappeared and the beat waited forever.** Fixed in reshoot: disconnects reject pending commands, and recordings have timeouts.

- **A failed take replaced the previous project's output.** Fixed in reshoot for versioned projects: each run writes to its own directory.
- **Templates only worked from the source checkout.** Fixed in reshoot: `init` uses resources packaged with the CLI.
- **Long recordings retained every JPEG in memory.** Fixed in reshoot: browser frames are stored in temporary files and read as needed.

- **A script clicked through a covered control.** Fixed for TOML stories: native Playwright actions enforce actionability and fail instead of using JavaScript activation. Legacy Python stories retain their original input behavior.
- **A brief private detail fell between sampled frames.** Fixed in full scan mode: `check --full` decodes every frame. Sampled checks still have this limitation.
- **The review pointed to a different time.** Fixed in reshoot: sampled frames now retain their decoded source timestamps.

- **Cutting changed subtitle timing.** Fixed for mapped edits: cut helpers record source/output ranges and the declarative editor uses them for cues. Custom ffmpeg edits need their own map.
- **Old approval accepted changed media.** Fixed in the local review importer: decisions bind to the run, artifact hashes, and current review policy.
- **A baseline GIF did not animate in the comparison page.** Fixed in reshoot:
  previous GIFs display as images, while MP4s retain video controls.
- **Recorded actions disappeared from a draft.** Fixed for explicitly detected unsupported changes and drops: the recorder stops instead of writing a misleading draft.

- **Zoom can round beyond a captured frame.** Fixed in reshoot: crop coordinates use
  each actual frame dimension and stay inside the decoded image.

- **Some ffmpeg builds omit `drawtext`.** Fixed in reshoot: declarative speed and
  wait labels use a Pillow overlay rather than that optional filter.

- **A browser screenshot fits but its video clips the bottom.** Fixed in reshoot:
  native capture sets the visible CDP surface as well as the emulated viewport.
  The regression records a marker at the bottom of a tall page.
