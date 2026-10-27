# Troubleshooting

A failed run prints its folder and failure image; the full output is in the
run's `output.log`.

## Error messages

- `can't find Chrome or Chromium`: install one, or set `RESHOOT_CHROME`; see [Chrome](#chrome-is-missing-or-will-not-start).
- `Chrome could not start`, `Vision failed (com.apple.Vision 8)`: usually an agent's sandbox: approve running reshoot outside it before installing anything.
- `net::ERR_UNSAFE_PORT`: see [Chrome](#chrome-is-missing-or-will-not-start).
- `something is already answering at`: stop the old server or change the port; see [the app](#the-app-will-not-start).
- `the app didn't answer at URL within N s`, `the app stopped before it answered`: read `app.log`; raise `[app] timeout`.
- `demo data reset failed`: run the `[app] reset` command by hand from the `reshoot.toml` folder.
- `couldn't find the control matching #q`: use the suggested control or fix the target; see [a step fails](#an-action-or-result-check-fails).
- `found more than one control that could be`: add `name` or `text` to the target.
- `The storyboard changed since this failure`, `Project settings changed since this failure`: record a new preview, then repair its failed run.
- `The suggested control changed or is ambiguous`: **Choose replacement in app**, or `reshoot repair RUN --pick`.
- `This run has no repairable control diagnosis`: fix the app state, demo data or result; keep the expected values.
- `beat 'search' failed: Locator expected ...`: a result check didn't pass in time; see [a step fails](#an-action-or-result-check-fails).
- `page error:`: often a step ran before the page was ready: add a `wait` action.
- `run exceeded its timeout`: raise `timeout` in `reshoot.toml`, or shorten the story.
- `unknown storyboard option: NAME`, `unknown option X; type takes ...`: fix the field; see the [project reference](projects.md#storyboardtoml).
- `required text scan unavailable`: install Tesseract; see [scanning](#scanning-fails-or-reports-unavailable-detectors).
- `edit would cut a narration line`: move the cut to a step boundary.
- `export exceeds its configured max_bytes`: shorten it, lower `fps` or `width`, or raise `max_bytes`.
- `an exported caption is shorter than min_reading`: raise the step's `hold`, or lower `min_reading`.
- `run ID is a preview`: record a final with `reshoot run`.
- `accepting needs the owner`: run `accept` yourself, or pass `--yes` only as the owner.
- `cannot accept a failed run or failed check`: fix it and record a new run.
- `not on the current sheets: LABEL`: use the labels `accept` listed.
- `items on these sheets were rejected`: fix the demo data and record a new run.
- `this is a run record without its media`: accept the run folder under `takes/runs/` instead of `demo/accepted`.
- `no successful run in`, `no accepted run in`: record or accept a run first.
- `decision belongs to another run`: see [the decision does not match](#accept-or-import-says-the-decision-does-not-match).
- `existing files would be overwritten`: `init` found a project: use it, or another folder.

## A command or dependency is missing

**Recording tools** in the studio lists a fix for each missing tool. Run the
fixes, choose **Check again**, then **Continue creation**. With `--no-studio`,
or after changing `PATH`, `RESHOOT_CHROME`, browser flags or Python, stop
reshoot and run `reshoot create --resume --directory demo`.
`reshoot doctor --config demo/reshoot.toml --probe` tries every tool.

- `uv` not found: use the [uv installer](https://docs.astral.sh/uv/getting-started/installation/) and open a new terminal.
- `reshoot` not found: run `uv tool update-shell` and open a new terminal.
- Python older than 3.11, or ffmpeg missing: see [install](install.md).
- Playwright missing: reinstall with the quoted `'reshoot[browser]'`.

## Chrome is missing or will not start

- Check `RESHOOT_CHROME` points at a browser that exists, or `unset
  RESHOOT_CHROME`. Quote paths with spaces.
- On minimal Linux, use the distribution's browser package.
- `net::ERR_UNSAFE_PORT`: Chrome blocks ports such as 5060, 5061, 6000 and
  6665 to 6669. Use another, or set
  `RESHOOT_CHROME_FLAGS=--explicitly-allowed-ports=5060`.
  `RESHOOT_CHROME_FLAGS` takes any space-separated Chrome flags.

## The app will not start

- Port in use: find it with `lsof -nP -iTCP:PORT -sTCP:LISTEN` and stop it, or
  move the demo to a free port. To run the server yourself, leave out `[app]`.
- Commands run from the `reshoot.toml` folder: for `demo/reshoot.toml`,
  `cd .. && npm run dev` runs in the app's root. An HTTP error doesn't count as
  ready.
- To change the notes port, edit `reshoot.toml` and `storyboard.toml`.

## An action or result check fails

Find the run with `reshoot runs demo` and look at the failing step in
`takes/demo.take.json` and `takes/demo.failure.png`. Check the target, page
state, login and visibility. Fix the data or target; don't weaken the check.

- **An exact `count` fails on the next take:** the app kept data. Add
  `[app] reset`, or check for the new item instead of a total.
- **A cookie banner:** close it with a `[[setup]]` click, which runs before
  recording:

  ```toml
  [[setup]]
  type = "click"
  target = {role = "button", name = "Accept"}
  ```

- **A slow page:** give the step a longer `timeout` (10000 ms by default) or
  add a `wait` action. Use `hold` only for reading time.

## Scanning fails or reports unavailable detectors

- On Linux, install Tesseract (`tesseract-ocr` on Debian).
- To use Tesseract anywhere, add `ocr = "tesseract"` in `[check]`, or pass
  `--ocr tesseract`. It doesn't detect faces or people: check those yourself.
- On Macs where Vision's accurate reader fails, reshoot uses the fast reader
  and says so. It can miss very small text; look closely or use Tesseract.
- `--no-scan` skips detection; it doesn't fix a failed scan.

## Review still says pending

`reshoot accept RUN` records both the recording and the scan;
`reshoot check --review RUN/review --ok` and `--import-decisions` record only
one. An open `review.html` may be out of date: rebuild it with
`reshoot review RUN`. Don't rescan an accepted run.

## Accept or import says the decision does not match

A file changed or the scan ran again since. Look at the run again and accept
it, or record a new one. Import only the decisions file from that same run's
page (it may be renamed `decisions (1).json`), and don't edit it by hand.

## Standalone check exits with code 1

Items need a person: `reshoot check` exits 1 when review is pending, 2 on an error.

## Export can't find a file

`export --file` names are relative to the run folder, such as
`takes/demo-final.mp4`.

## A run takes too long

Most of a long run is a full scan, which grows with frames and with images in
a take's `.assets.json`. An 81-second three-take video took 8 minutes to
record and 27 to scan in full.

| Change | How | Gives up |
|---|---|---|
| Sample the scan | Leave out `full`; set `every` (3 s) | Something briefer than `every` can be missed |
| Skip the scan | `scan = false`, or `reshoot check --no-scan` | Only your eyes check it |
| Scan fewer sources | Leave `takes/web.assets.json` out of `sources` | Loaded images are checked only as they appear |
| Preview less | Preview after story or tape changes only | A broken refresh shows up in the final |
| Preview one step | `reshoot preview CONFIG --from BEAT` | No edit or scan |
| Re-cut | `reshoot recut demo/latest`, or **Update preview** | Actions and holds stay as recorded |
| Tighten agent waits | Set a tape's last `Sleep` to the slowest run plus a margin | A slower agent gets cut off |
| Export less | One MP4 and one GIF | Fewer formats |

Keep the full scan when the data is new, the app picks content at random, or
the video is going public for the first time. Always read what an AI agent
writes in a terminal take.

## What to watch for

### Privacy

- **Never capture the whole screen.** Record a headless page, a VHS terminal
  or one window by its ID.
- **A clean scan isn't a pass.** Look at every image at full size, including
  edges, reflections and blurred figures, and at screenshot alt text and tour
  words. Reject what you're unsure of.
- **A sampled scan can miss something brief.** Use `--full` or `full = true`
  for a final.
- **Random content changes each take.** Check the whole set the app picks from.
- **Removing something later doesn't fix the take.** Remove it from the demo
  data and record again.
- **The terminal shows the user, machine, folder, history and typed keys.**
  In a hidden part of the tape, start
  `PS1='$ ' HISTFILE=/dev/null exec bash --noprofile --norc` in a folder under
  `/tmp`. `env -i` also removes an agent's credentials, so it fails to connect.
- **An agent's banner shows the account and folder.** For Claude Code, use a
  separate `CLAUDE_CONFIG_DIR`, a demo folder, `--strict-mcp-config` and
  `--allowedTools`. Read what the agent says before cutting.
- **Expected terminal flags:** npm's `> name@1.0.0 start` reads as an email,
  `$0.00002875` as a phone number. Look at each anyway.

### Web recordings

- **A check passes but the result is off screen.** Look at each result frame;
  add a `scroll` so the result is in view.
- **The studio can't see a remote app or database.** Use **Record app again**.
- **A wrong result isn't a broken target.** Fix the app, data or story, and keep the check.
- **Build-generated ids such as `css-8f3k2z`.** Use a test ID, name, label or
  words; `reshoot rec` does.
- **An agent builds a different page each take.** List the needed
  `data-testid`s in its `AGENTS.md`.
- **Small text in a GIF.** `@2` sharpens but doesn't enlarge; record a narrower
  viewport such as `960x540`, or use [auto-zoom](look.md#auto-zoom) or a crop.
- **Wrong colour scheme.** Pages record dark unless `theme = "light"`.
- **Logged out.** See [login and demo data](your-app.md#login-and-demo-data).
- **Blank views in Python stories.** List slow views, such as maps, in `WARM`.
- **Python story code after a click that opens a page doesn't run.** Move it
  to the next step.
- **`demo/accepted/` missing from Git.** A `takes/` ignore line also matches
  `demo/accepted/takes/`. Ignore `/takes/` inside `demo/`, as `reshoot init` does.

### Terminal recordings

- **A VHS `Wait` that times out discards the recording, and `Wait+Screen`
  misses text in VHS 0.12.1.** Use a fixed `Sleep` longer than the slowest run,
  then cut at `reshoot last-change`. Label any speed change.
- **The app is built during the take.** `[app]` must answer before the first
  take: serve a placeholder on the port, then start the built app there. Tell
  the agent to test on another port, and raise `timeout`.
- **Leftovers from the last take.** Reset demo data in the hidden part of the tape.

### App windows

- **The app stalls.** Drive the window from one script, and don't use the app
  while recording.
- **"could not create image from window":** grant Screen Recording permission
  or unminimize the window.

### Cutting and sound

- **`end` and `through` differ.** `end = "search"` stops where search starts;
  `through = "search"` includes it and its hold.
- **A crop can cut off a caption or result.** Use Fit, or aim the crop and
  inspect the export at its viewing size. Text hints aren't a readability pass.
- **Muted narration still takes its time.** Remove its words and record again.
- **Clips of different sizes don't join.** Put the smaller on a full-size card
  with `cut.place` before `cut.concat`.
- **Your own ffmpeg edits lose subtitle timing.** Use reshoot's cut helpers.
- **Check the GIF too:** its first and last frames and its length.
- **Odd sizes.** Widths and heights must be even.

### In CI

- **Linux fonts differ.** Text can wrap differently; watch the first CI video.
- **Checks show "action_required".** GitHub waits for approval on pull requests
  opened by `github-actions[bot]`. Approve them on the Checks tab, or open the
  pull request with a GitHub App or personal token
  ([GitHub's docs](https://docs.github.com/en/actions/concepts/security/github_token)).
- **Agent takes.** Record them locally; CI would need an account and key.

## Report a problem

Give the reshoot, OS, browser and ffmpeg versions, the command, what you
expected and got, and a small made-up reproduction. Check logs for private
details first. See the [contribution guide](../CONTRIBUTING.md).
