# Troubleshooting

A failed run prints its folder, a failure image of the page and the app's
output. Each run has its own folder, so a failed one never replaces the
recording before it. Find the message below, or the section that matches.

## Error messages

| The message starts with | It means | Do |
|---|---|---|
| `can't find Chrome or Chromium` | No browser where reshoot looks | Install one, or set `RESHOOT_CHROME`; [Chrome](#chrome-is-missing-or-will-not-start) |
| `Chrome could not start` | Usually an agent's sandbox | Approve running reshoot outside the sandbox; [Chrome](#chrome-is-missing-or-will-not-start) |
| `net::ERR_UNSAFE_PORT` | Chrome refuses that port | Use another port; [Chrome](#chrome-is-missing-or-will-not-start) |
| `something is already answering at` | An old server holds the app's port | Stop it, or change the port; [the app](#the-app-will-not-start) |
| `the app didn't answer at URL within N s` | Startup was slow or failed quietly | Read `app.log`; raise `[app] timeout`; [the app](#the-app-will-not-start) |
| `the app stopped before it answered` | The `[app] run` command failed | Read `app.log`; [the app](#the-app-will-not-start) |
| `demo data reset failed` | The `[app] reset` command failed | Run it by hand from the `reshoot.toml` folder |
| `click target {css = '#q'} matched 0 elements` | The control is gone or renamed | Fix the target; [a beat fails](#an-action-or-result-check-fails) |
| `... matched 2 elements; it must match exactly one` | The target is ambiguous | Add `name` or `text`, or use a test ID |
| `The storyboard changed since this failure` / `Project settings changed since this failure` | Repair evidence belongs to older source | Record a new preview, then repair its failed run |
| `The suggested control changed or is ambiguous` | The current app no longer supports the recorded suggestion | Choose the replacement in the studio or with `reshoot repair RUN --pick` |
| `This run has no repairable control diagnosis` | The failure is not a missing or ambiguous control | Fix the app state, demo data or failing result; retain its expected values |
| `beat 'search' failed: Locator expected ...` | A result check did not pass in time | Look at the failure image; [a beat fails](#an-action-or-result-check-fails) |
| `page error:` | The page threw a JavaScript error | Often a beat ran before the page was ready: add a `wait` action |
| `run exceeded its timeout` | The whole run took over `timeout` seconds | Raise `timeout` in `reshoot.toml`, or shorten the story |
| `unknown storyboard option: NAME` | A misspelled or unsupported field | Check the [project reference](projects.md#storyboardtoml) |
| `unknown option X; type takes ...` | A field that action or result check doesn't take | Use one of the fields it lists |
| `required text scan unavailable` | No Vision or Tesseract | Install Tesseract; [scanning](#scanning-fails-or-reports-unavailable-detectors) |
| `edit would cut a narration line` | A cut falls inside a voiceover line | Move the cut to a beat boundary |
| `speed changes need a label` | A sped-up part has no `label` | Add a visible `label`, such as "Sped up 2x" |
| `card text does not fit` | A title card's words are too long | Shorten them |
| `export exceeds its configured max_bytes` | The export is larger than its limit | Shorten it, lower `fps` or `width`, or raise `max_bytes` |
| `an exported caption is shorter than min_reading` | A caption is too brief in an export | Lengthen its beat's `hold`, or lower `min_reading` |
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

For a paused first creation, use the studio's **Recording tools** fixes and
**Check again**, then **Continue creation**. From a terminal, run
`reshoot create --resume --directory demo`. It preserves the saved task after
setup and preview failures. `reshoot doctor --config demo/reshoot.toml --probe`
tests temporary synthetic encoding, browser capture and configured OCR without
using the app. Restart reshoot after changing shell or Python environment settings.

| Symptom | Action |
|---|---|
| `uv` is not found | Follow the [uv installer](https://docs.astral.sh/uv/getting-started/installation/), then open a new terminal |
| `reshoot` is not found after installation | Run `uv tool update-shell`, open a new terminal, then `reshoot --version` |
| `python3` is missing or too old | Install Python 3.11 or newer and check `python3 --version` |
| ffmpeg or ffprobe is missing | Install ffmpeg using the [platform instructions](install.md) |
| Playwright is missing | Reinstall the CLI with the quoted `reshoot[browser]` requirement from the installation guide |
| `init` reports existing files | Continue with that project or choose a new directory; it will not overwrite the story |
| Skill installation reports an existing skill | After an upgrade, commit or copy any changes to them, then pass `--replace` |

`reshoot doctor --config demo/reshoot.toml --json` reports tool paths, versions
and installed scan capabilities. It does not probe the final capture or scan.

## Chrome is missing or will not start

Install Google Chrome or Chromium, then check whether `RESHOOT_CHROME` points
to a browser that still exists. Correct it to an executable path, or remove
the stale override with `unset RESHOOT_CHROME` and let reshoot discover Chrome.
Paths containing spaces need shell quotes.

On a minimal Linux machine, the browser also needs its system libraries and
fonts. Use the distribution's browser package or install the dependencies
required by the Chrome package. Reshoot uses the installed browser, not a
Playwright-downloaded binary. If a harness sandbox prevents starting Chrome or
binding a loopback port, use that harness's permission mechanism to authorize
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
failing beat in its `takes/demo.take.json` and look at the failure image
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

## Scanning fails or reports unavailable detectors

On Linux, install Tesseract (`tesseract-ocr` on Debian) before running a project
with scanning enabled. On macOS, Vision normally supplies text, face and person
detection. A Vision integration failure is an error, not an empty findings list.

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
| `run.json` → `review_status` | The verdict for the exact exports, beats and findings |
| `review/report.json` | The scan checklist for the supplied images, frames and text findings |
| An already open `review.html` | A static page that may predate the latest verdict |

Watch the final exports, look at the scan items, and run `reshoot accept RUN`.
It records both the recording and the scan checklist. If it stops and lists
findings, name each with `--flagged F1`, or `--reject F1` if it must not be
shared; the [tutorial](step-by-step.md#4-accept-the-recording) walks through
it. `reshoot check --review RUN/review --ok` and
`reshoot review RUN --import-decisions FILE` each record only one of the two,
leaving the other pending. After accepting, rebuild the page with
`reshoot review RUN` and reopen it.

Do not rescan an accepted take just to refresh a page. Rerunning a check can
replace the sheets and finding labels. New media or changed coverage belong to a
new run or a deliberately separate review directory.

## Accept or import says the decision does not match

`reshoot accept` and the importer both check the run ID, media hashes and scan
policy. A file changed after recording, or the scan ran again, so record a new
run or accept the current one again. For an import, check that the selected run
matches the downloaded file from its current page. A browser may rename a download to `decisions (1).json`. The import binds
the run ID, media hashes and scan policy; decisions from the preview or another
final do not apply. If the media or policy changed, inspect the new artifacts
and generate new decisions rather than editing the binding by hand.

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
Give joined browser and VHS takes matching dimensions. Detailed rendering
pitfalls are in [Pitfalls](pitfalls.md).

Export takes names relative to the run folder, such as `takes/demo-final.mp4`.
It refuses missing or changed artifacts and will not overwrite existing output
files. Choose a new destination directory after reviewing the new recording.

## Report a problem

Include the reshoot version and installation revision if known, OS and CPU,
browser and ffmpeg versions, exact command, expected result, actual result and
a small synthetic reproduction. Inspect logs and screenshots before attaching
them; they may contain local paths or app details. The [contribution guide](../CONTRIBUTING.md)
explains how to try a fix.
