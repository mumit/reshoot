# Troubleshooting

A failed run prints its folder, a failure image of the page and the app's
output; each stage's full output is in the run's `output.log`. A failed run
never replaces the recording before it. Find the message below, or the
section that matches. [What to watch for](#what-to-watch-for) lists mistakes
that don't show an error, and [A run takes too long](#a-run-takes-too-long)
covers speed.

## Error messages

| The message starts with | It means | Do |
|---|---|---|
| `can't find Chrome or Chromium` | No browser where reshoot looks | Install one, or set `RESHOOT_CHROME`; [Chrome](#chrome-is-missing-or-will-not-start) |
| `Chrome could not start` | Usually an agent's sandbox | Approve running reshoot outside the sandbox; [Chrome](#chrome-is-missing-or-will-not-start) |
| `Vision failed (com.apple.Vision 8)` | Usually an agent's sandbox | Approve running reshoot outside the sandbox before installing anything; [scanning](#scanning-fails-or-reports-unavailable-detectors) |
| `net::ERR_UNSAFE_PORT` | Chrome refuses that port | Use another port; [Chrome](#chrome-is-missing-or-will-not-start) |
| `something is already answering at` | An old server holds the app's port | Stop it, or change the port; [the app](#the-app-will-not-start) |
| `the app didn't answer at URL within N s` | Startup was slow or failed quietly | Read `app.log`; raise `[app] timeout`; [the app](#the-app-will-not-start) |
| `the app stopped before it answered` | The `[app] run` command failed | Read `app.log`; [the app](#the-app-will-not-start) |
| `demo data reset failed` | The `[app] reset` command failed | Run it by hand from the `reshoot.toml` folder |
| `couldn't find the control matching #q` | The control is gone or renamed | Use the control it suggests, or fix the target; [a step fails](#an-action-or-result-check-fails) |
| `found more than one control that could be` | The target is ambiguous | Add `name` or `text`, or use a test ID |
| `The storyboard changed since this failure` / `Project settings changed since this failure` | Repair evidence belongs to older source | Record a new preview, then repair its failed run |
| `The suggested control changed or is ambiguous` | The current app no longer supports the recorded suggestion | Choose the replacement in the studio or with `reshoot repair RUN --pick` |
| `This run has no repairable control diagnosis` | The failure is not a missing or ambiguous control | Fix the app state, demo data or failing result; retain its expected values |
| `beat 'search' failed: Locator expected ...` | A result check did not pass in time | Look at the failure image; [a step fails](#an-action-or-result-check-fails) |
| `page error:` | The page threw a JavaScript error | Often a step ran before the page was ready: add a `wait` action |
| `run exceeded its timeout` | The whole run took over `timeout` seconds | Raise `timeout` in `reshoot.toml`, or shorten the story |
| `unknown storyboard option: NAME` | A misspelled or unsupported field | Check the [project reference](projects.md#storyboardtoml) |
| `unknown option X; type takes ...` | A field that action or result check doesn't take | Use one of the fields it lists |
| `required text scan unavailable` | No Vision or Tesseract | Install Tesseract; [scanning](#scanning-fails-or-reports-unavailable-detectors) |
| `edit would cut a narration line` | A cut falls inside a voiceover line | Move the cut to a step boundary |
| `speed changes need a label` | A sped-up part has no `label` | Add a visible `label`, such as "Sped up 2x" |
| `card text does not fit` | A title card's words are too long | Shorten them |
| `export exceeds its configured max_bytes` | The export is larger than its limit | Shorten it, lower `fps` or `width`, or raise `max_bytes` |
| `an exported caption is shorter than min_reading` | A caption is too brief in an export | Lengthen its step's `hold`, or lower `min_reading` |
| `run ID is a preview` | `accept` refuses previews | Record a final with `reshoot run` |
| `accepting needs the owner` | `accept` ran without a terminal | Run it yourself, or pass `--yes` only as the owner |
| `cannot accept a failed run or failed check` | The run or its scan failed | Fix it and record a new run |
| `not on the current sheets: LABEL` | That label or finding isn't in this run's scan | Use the labels `accept` listed |
| `items on these sheets were rejected` | Something was marked not to share | Fix the demo data and record a new run |
| `this is a run record without its media` | `demo/accepted` in a fresh clone has no video | Accept the run folder under `takes/runs/` |
| `no successful run in` / `no accepted run in` | `latest` or `accepted` has nothing to name | Record or accept a run first |
| `decision belongs to another run` | Files or scan settings changed since | [Accept again](#accept-or-import-says-the-decision-does-not-match) |
| `export would overwrite a file` | The destination already has that file | Pass `--replace` to update it on purpose |
| `existing files would be overwritten` | `init` found a project there | Use that project, or another folder |
| `will not overwrite existing skill` | The skills are already installed | After an upgrade, pass `--replace` |

## A command or dependency is missing

When `reshoot create` finds a missing or broken tool, the studio opens
**Recording tools** with a fix for each one. Run the fixes in a terminal,
choose **Check again**, then **Continue creation**. **Check again** doesn't
install anything. Tools that passed are under **All tool checks**.

With `--no-studio`, creation stops and prints the command that continues it:

```bash
reshoot create --resume --directory demo
```

It keeps the saved address, size and story. After a failed preview it tries
the saved story again without asking you to show the task again, and a
finished creation just opens the studio. If you change `PATH`,
`RESHOOT_CHROME`, browser flags or the Python environment, stop reshoot and
continue with this command so it sees the change.

`reshoot doctor --config demo/reshoot.toml --probe` tries the tools on made-up
data without using your app.

| Symptom | Action |
|---|---|
| `uv` is not found | Follow the [uv installer](https://docs.astral.sh/uv/getting-started/installation/), then open a new terminal |
| `reshoot` is not found after installation | Run `uv tool update-shell`, open a new terminal, then `reshoot --version` |
| `python3` is missing or too old | Install Python 3.11 or newer and check `python3 --version` |
| ffmpeg or ffprobe is missing | Install ffmpeg using the [platform instructions](install.md) |
| Playwright is missing | Reinstall the CLI with the quoted `reshoot[browser]` requirement from the installation guide |
| `init` reports existing files | Continue with that project or choose a new directory; it will not overwrite the story |
| Skill installation reports an existing skill | After an upgrade, commit or copy any changes to them, then pass `--replace` |

## Chrome is missing or will not start

Install Google Chrome or Chromium, then check whether `RESHOOT_CHROME` points
to a browser that still exists. Correct it to an executable path, or remove
the old override with `unset RESHOOT_CHROME` and let reshoot discover Chrome.
Paths containing spaces need shell quotes.

On a minimal Linux machine, the browser also needs its system libraries and
fonts. Use the distribution's browser package or install the dependencies
required by the Chrome package. Reshoot uses the installed browser, not a
Playwright-downloaded binary. If a harness sandbox prevents starting Chrome or
listening on a local port, use that harness's permission mechanism to authorize
the local recording and keep the failed run. In Codex's default sandbox,
`Chrome could not start` is the usual sign: approve running the reshoot command
outside the sandbox.

`net::ERR_UNSAFE_PORT` means Chrome refuses the app's port; it blocks a few,
such as 5060, 5061, 6000 and 6665 to 6669. Run the app on another port, or pass Chrome
a flag with `RESHOOT_CHROME_FLAGS=--explicitly-allowed-ports=5060`.
`RESHOOT_CHROME_FLAGS` adds any Chrome flags, separated by spaces.

## The app will not start

If the log says something is already answering at a port, identify the server
with `lsof -nP -iTCP:PORT -sTCP:LISTEN` and stop it if it is an old demo server.
Otherwise move the demo to a free port. Reshoot refuses to record an existing
server when `[app]` manages startup. To manage the server separately, omit
`[app]` and keep the server running during capture.

Versioned project paths and startup commands resolve from the configuration's folder.
For `demo/reshoot.toml`, `npm run dev` runs in `demo/`; `cd .. && npm run dev`
runs in its parent. Check the command, readiness URL, dependencies and reset
command. An HTTP error response does not count as ready. In the notes tutorial,
changing the port requires changing it in both `reshoot.toml` and `storyboard.toml`;
`reshoot init` picks a free one when 8765 is taken.

## An action or result check fails

Run `reshoot runs demo` to find the failed run's folder, then read the
failing step in its `takes/demo.take.json` and look at the failure image
beside it, such as `takes/demo.failure.png`. Check the target, page state, login, visibility and the result check.
A matching selector must identify one usable control. Use a stable test ID or
accessible name when possible, and give a result check a longer `timeout` for
real loading.

If the app keeps data between takes, a take that created something leaves it
behind, and an exact `count` check fails on the next take. Reset the data
before each take with `[app] reset`, or, when there is no reset, check for the
item the take created rather than a total that depends on earlier takes.

Earlier passed checks do not verify an interrupted flow. Keep the task and
repair the demo data or the target. Do not weaken a result check to make the
run pass. After a repaired preview, make a fresh final recording.

## A cookie banner or a slow page gets in the way

Every take starts with a fresh browser profile, so a cookie or consent banner
appears every time. Close it with a `[[setup]]` click on its button in
`storyboard.toml`. Setup actions run before recording starts, so the video
opens without the banner:

```toml
[[setup]]
type = "click"
target = {role = "button", name = "Accept"}
```

A single-page app may show its content a moment after the page loads, and a
hold long enough on one run can be too short on the next. Each
action and result check waits up to its `timeout`, 10000 milliseconds by
default. Give a slow step a longer `timeout`, or add a `wait` action for the
control before the step uses it. Use `hold` only for reading time.

## Scanning fails or reports unavailable detectors

On Linux, install Tesseract (`tesseract-ocr` on Debian) before running a project
with scanning enabled. On macOS, Vision normally supplies text, face and person
detection. A Vision integration failure is an error, not an empty findings list.

On some Macs, Vision's accurate text reader fails with
`TextRecognition.CRImageReaderError 1` while its fast one works. reshoot then
reads text with the fast reader, says so when it scans, and records
`text_reader = "fast"` in the scan report. `reshoot doctor` tries Vision and
names the reader it will use. The fast reader can miss very small text: look
closely at it on the sheets, or use Tesseract as below.

To select Tesseract explicitly, add this inside the existing `[check]`
table, or pass `--ocr tesseract` to a standalone check:

```toml
ocr = "tesseract"
```

This changes the backend and coverage: Tesseract does not detect faces or people.
Inspect those by eye and do not describe the result as a Vision pass. Missing
inputs and required detector failures must be fixed. `--no-scan` explicitly skips
detection; it does not repair a failed scan.

## Review still says pending

First identify which review is pending:

| Location | What it means |
|---|---|
| `run.json` → `review_status` | The verdict for the exports, steps and findings |
| `review/report.json` | The scan checklist for the supplied images, frames and text findings |
| An already open `review.html` | A static page that may predate the latest verdict |

Watch the final exports, look at the scan items, and run `reshoot accept RUN`.
It records both the recording and the scan checklist. If it stops and lists
findings, name each with `--flagged F1`, or `--reject F1` if it must not be
shared; [the tutorial](step-by-step.md#5-review-and-accept) walks through
it. `reshoot check --review RUN/review --ok` and
`reshoot review RUN --import-decisions FILE` each record only one of the two,
leaving the other pending. After accepting, rebuild the page with
`reshoot review RUN` and reopen it.

Do not rescan an accepted take just to refresh a page. Rerunning a check can
replace the sheets and finding labels. New media or changed coverage belong to a
new run or a deliberately separate review directory.

## Accept or import says the decision does not match

A file changed after recording, or the scan ran again. Record a new run, or
look at the current one again and accept it. For an import, use the decisions
file downloaded from that same run's page; decisions from a preview or another
run don't apply. A browser may rename the download to `decisions (1).json`.
Make new decisions rather than editing the file by hand.

## Standalone check exits with code 1

That means the supplied items need human review, not that recording or scanning
crashed. `reshoot check` uses 0 for accepted supplied items, 1 for review pending,
and 2 for an operational error. `reshoot run` tolerates a completed check that
needs human review and prints a reminder. These are different commands with
different exit semantics.

## Captions, crops or exports look wrong

Inspect the actual MP4 and GIF, not just a screenshot. Shorten long captions
or increase the appropriate hold; check text after navigation and after zoom.
For portrait output, choose a deliberate crop or record a separate mobile take.
Give joined browser and VHS takes matching dimensions. More is under
[Cutting and sound](#cutting-and-sound).

`export --file` takes names relative to the run folder, such as
`takes/demo-final.mp4`. It won't overwrite a file already there unless you add
`--replace`.

## A run takes too long

Most of a long run is the scan, not the recording. In an 81-second launch
video with a web take, a Claude Code terminal take and a window clip, scanned
at full frame rate, recording took 8 minutes and the two full scans 27. A full
scan's time grows with the number of frames and with every image listed in a
take's `.assets.json`; a page with a map loads hundreds of tiles.

Each row is independent. The top ones save the most.

| Change | How | Gives up |
|---|---|---|
| Sample the scan | Leave `full` out of `[check]`; set `every = SECONDS` (default 3) | Something on screen for less than `every` seconds can be missed |
| Skip the scan | `scan = false` in `[check]`, or `reshoot check --no-scan` | Only your eyes check the video |
| Scan fewer sources | Leave `takes/web.assets.json` out of `[check] sources` | Loaded images are seen only as they appear in frames. Content picked at random goes unchecked |
| Preview less | Preview after changing the story or a tape, not on every refresh | A refresh that broke shows up in the final, which you then run again |
| Preview one step | `reshoot preview CONFIG --from BEAT` | Skips the edit and scan, so it shows only that step working |
| Re-cut, don't record | `reshoot recut demo/latest`, or **Update preview**, after a change to captions or `edit.toml`; see [the studio](studio.md#update-the-preview-then-make-the-final) | Actions, holds and the app stay as recorded |
| Tighten agent waits | Set a tape's final `Sleep` to the slowest run you've seen plus a margin | A slower agent is cut off before its answer |
| Export less | One MP4 and one GIF | Each export is scanned, so fewer exports scan faster |

Sample or skip the scan only when the demo data was checked and hasn't
changed, the app shows the same things each time, and you watch the finished
video. Keep the full scan when the data is new, the app picks content at
random, or the video is going somewhere public for the first time. Whatever
the settings, read anything an AI agent writes in a terminal take.

## What to watch for

These happened in real demos and still need a person to do something.
Problems reshoot now handles for you are in the [CHANGELOG](../CHANGELOG.md).

### Privacy

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

### Web recordings

- **A passed check with the result off screen.** A text check found the token
  count in the page, but it was below the fold, so the video never showed it.
  Look at the frame for each result, and add a `scroll` action so the control
  and its result share the view.
- **Watch the video, not only the checks.** A check proves the result was in
  the page, not that the viewer could see it in time. Watch each result appear.
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
- **A fresh profile is logged out.** Log in with a demo account in
  `[[setup]]`; see [login and demo data](your-app.md#login-and-demo-data).
- **Blank views when first shown.** Nothing is cached in a fresh profile. For
  Python stories, list slow views such as maps in `WARM` to load them first.
- **Code after a click that opens a page doesn't run.** In a Python story, the
  page it was in has gone. Put that code in the next step.
- **Legacy Python stories can click covered controls.** TOML stories fail on a
  covered control instead. Move to TOML when you can.
- **The accepted record must reach Git.** A `takes/` line in a `.gitignore` also
  matches `demo/accepted/takes/`. Ignore `/demo/takes/` from the repository
  root, or `/takes/` inside `demo/`, as `reshoot init` does.

### Terminal recordings

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
- **A take that varies in length can't be cut by step.** Terminal takes have no
  steps, so the edit cuts them at seconds. A fixed `Sleep` keeps the length
  fixed; play the part that varies at a labelled speed.
- **The app is built during the take.** `[app]` must answer before the first
  take. Serve a placeholder on the port until the tape touches a file, then
  start the built app on the same port. Tell the agent to test on another port
  and stop its servers. Raise the run's `timeout` (600 s by default) to cover
  the build.
- **Leftovers from the last take.** Demo data from an earlier run can produce
  duplicate results. Reset the demo data in the hidden part of the tape.

### App windows

- **Two scripts driving the same app can stall it.** Drive the window from one
  script at a time, and don't use the app during recording.
- **"could not create image from window"** means the app running the command
  has no Screen Recording permission, or the window is minimized.

### Cutting and sound

- **`end` and `through` differ.** `end = "search"` stops where the search step
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

### In CI

- **Linux draws things differently.** Fonts and emoji differ from macOS, so
  text can wrap in new places. Watch the first video from CI closely, and set
  fonts in the app if it matters.
- **Checks wait on the pull request.** GitHub doesn't run workflows on a pull
  request opened by `github-actions[bot]` until someone approves them: the run
  shows "action_required". Approve it on the pull request's Checks tab, or
  open the pull request with a GitHub App or personal token instead of
  `GITHUB_TOKEN`. [GitHub documents this](https://docs.github.com/en/actions/concepts/security/github_token).
- **Agent takes in CI.** A Claude Code take needs an account and a key in CI,
  and its output varies more than a script's. Record those locally.

## Report a problem

Include the reshoot version and installation revision if known, OS and CPU,
browser and ffmpeg versions, exact command, expected result, actual result and
a small synthetic reproduction. Inspect logs and screenshots before attaching
them; they may contain local paths or app details. The [contribution guide](../CONTRIBUTING.md)
explains how to try a fix.
