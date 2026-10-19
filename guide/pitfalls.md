# Pitfalls

These came up while making real demo videos and building reshoot. "Fixed in reshoot" means the tool handles it now,
but it helps to know why.

## Privacy

- **A full-screen capture shows everything.** Once, a full-screen capture showed my mail and calendar. I only record
  a headless browser page, a VHS terminal, or one window by its id.
- **Small things get missed on the first look.** In a photo app's demo, a first check missed a straw hat at the edge
  of a frame, a silhouette in a mesh railing and a blurred head in the background. I now look at every image at
  full size, and when in doubt it fails.
- **Random content shows something new each take.** A home page that picked items at random showed different ones
  in each take, so checking one take wasn't enough. I check the whole set it picks from.
- **A scan finds a key, and prints it.** Listing what was found would put a key in the terminal and in a CI log.
  Fixed in reshoot: `reshoot check` shows only enough to recognise it (`sk-a•••`).
- **Trusting a clean scan.** A scan reads text and finds faces, but misses text in pictures, odd fonts, and things it
  has no rule for. Only a person marks an image as checked.
- **Removing something doesn't fix the take.** The take still shows it. Record again after taking it out of the
  demo data.
- **The terminal shows more than you think:** the user and machine name in the prompt, the folder, shell history,
  API keys in typed commands. I start a clean shell with `env -i`, a plain `PS1` and a folder under `/tmp`, all in a
  hidden part of the tape.
- **An AI agent's banner shows the account, folder and setup.** For Claude Code I use a separate
  `CLAUDE_CONFIG_DIR`, a demo folder, and only the tools the take needs (`--strict-mcp-config`, `--allowedTools`).
- **What an agent says.** An agent's answer can describe or name things. I read it before cutting.

## Web takes

- **Chrome sends no frames while the page is still.** The last frame (the end card) got almost no time in the
  video. Fixed in reshoot: each frame is held until the next, and the last until recording stops.
- **A 5-second take came out 389 seconds long.** The Mac went to sleep during it. The beats and the end of recording
  were timed with the system clock, which keeps counting through sleep; Chrome's frame times don't. Fixed in
  reshoot: it times everything with a clock that stops during sleep too, matched to Chrome's at the first frame.
- **The frame rate goes up and down.** Chrome paints about 45 to 50 frames a second while things move, and none
  when still. Fixed in reshoot: frames keep their times, and ffmpeg makes a steady 60 fps.
- **Blank views when first shown.** Each take starts with a fresh browser profile, so nothing is cached. A map's
  tiles were still downloading, and it showed black for a second or two. I list slow views in `WARM`, to load
  before recording.
- **A fresh profile is logged out.** I log in with a demo account in `SETUP` beats, which run before recording.
  I never reuse my own browser profile: it has my accounts and history.
- **Headless Chrome won't go below a 500 px window.** For a phone layout the page was too wide. Fixed in reshoot: the
  size is set with device metrics, and it prints a note if `innerWidth` isn't the width asked for.
- **Results that take a moment.** A hold that's long enough on one run is too short on the next. I wait for the
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

## Terminal takes

- **VHS throws away the whole recording when a `Wait` times out.** I use a fixed `Sleep` longer than the slowest
  run, then cut at `reshoot last-change`.
- **An agent's time varies a lot.** Claude Code took one to three minutes for the same prompt. The long `Sleep`
  covers it, and the cut speeds up the working part.
- **Leftovers from the last take.** In the notes example, a second run would have shown the note twice, since the
  first run's file was still there. I clean up in the hidden setup.

## App windows

- **Two scripts driving the same app can stall it.** A desktop app driven by AppleScript stopped answering until it
  was force-quit. I leave the app alone while a take drives it.
- **"could not create image from window"** means the app running the command has no Screen Recording permission,
  or the window is minimized.
- **The recording includes the window's shadow.** A square crop of the window still showed the black background
  at its round corners. Fixed in reshoot: `cut.window_clip` crops to the window and rounds the corners to match.

## Cutting

- **Clips of different sizes don't join.** A 1280x720 terminal take and a 1920x1080 web take can't be joined as
  they are. `cut.concat` refuses them. I place the smaller one on a full-size card with `cut.place` first.
- **Washed-out cards after a web take.** Chrome's frames are full-range JPEGs, and a joined video is read with its
  first clip's range, so the dark cards after the web take came out grey. Fixed in reshoot: every clip is made in
  standard range, and `cut.concat` refuses clips whose ranges differ.
- **An extra second at the end of a web take.** ffmpeg's concat list gives the repeated last frame time of its own.
  Fixed in reshoot: the output is cut at the take's real length.
- **The first beat starts before the first frame.** Fixed in reshoot: its start is 0, not a little below.
- **Banded GIFs.** ffmpeg's default palette looks poor. `cut.gif` makes a palette for each GIF.
- **Odd sizes.** H.264 in yuv420p needs even widths and heights.

## Adding a pitfall

When something goes wrong, add it here in a line or two: what happened, and what avoids it. If reshoot can avoid it,
fix it there too and say so.
