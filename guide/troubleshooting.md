# Troubleshooting

Keep the failed run folder and read its `run.json` before changing the story.
Each versioned attempt has its own directory, so a failed update leaves the
previous recording available.

## A command or dependency is missing

| Symptom | Action |
|---|---|
| `uv` is not found | Follow the [uv installer](https://docs.astral.sh/uv/getting-started/installation/), then open a new terminal |
| `reshoot` is not found after installation | Run `uv tool update-shell`, open a new terminal, then `reshoot --version` |
| `python3` is missing or too old | Install Python 3.11 or newer and check `python3 --version` |
| ffmpeg or ffprobe is missing | Install ffmpeg using the [platform instructions](install.md) |
| Playwright is missing | Reinstall the CLI with the quoted `reshoot[browser]` requirement from the installation guide |
| `init` reports existing files | Continue with that project or choose a new directory; it will not overwrite the story |
| Skill installation reports an existing skill | Preserve local edits and compare an installation in a separate directory before replacing files |

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
the local recording and retain the failed attempt.

## The app will not start

If the log says something is already answering at the app URL, identify the
server and stop it if it is an old demo server. Reshoot refuses to record an existing
server when `[app]` manages startup. To manage the server separately, omit
`[app]` and keep the server running during capture.

Versioned project paths and startup commands resolve from the configuration's folder.
For `demo/reshoot.toml`, `npm run dev` runs in `demo/`; `cd .. && npm run dev`
runs in its parent. Check the command, readiness URL, dependencies and reset
command. An HTTP error response does not count as ready. In the notes tutorial,
changing the port requires changing it in both `reshoot.toml` and `storyboard.toml`.

## An action or result check fails

Read the failing beat in `takes/demo.take.json` and inspect the saved failure
image. Check the selector, page state, login, visibility and expected result.
A matching selector must identify one usable control. Use a stable test ID or
accessible name when possible and allow an appropriate expectation timeout for
real loading.

Earlier passed checks do not verify an interrupted flow. Preserve the expected
task and repair the app fixture or selector. Do not weaken an assertion to make
the run pass. After a repaired preview, make a fresh final recording.

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
| `review/report.json` | Human review of the supplied images, frames and text findings |
| `run.json` → `review_status` | Recording decisions imported for the exact video, beats and findings |
| An already open `review.html` | A static page that may predate the latest local decisions |

For scan sheets, inspect every supplied image and text finding, then record
your decision with `reshoot check --review RUN/review --ok`. Use that command only
after approving those items. For the recording, watch all final exports, inspect
the beats and findings, download decisions from the review page, and import them
with `reshoot review RUN --import-decisions FILE`.

`check --ok` does not accept the recording; importing recording decisions does
not fill the scan checklist. The run report may retain the scan checklist status
captured at recording time; read the current `review/report.json` too.
Regenerate the page with `reshoot review RUN` and reopen it after decisions.
The [tutorial](step-by-step.md#4-review-the-recording-and-scan-sheets) shows both steps.

Do not rescan an accepted take just to refresh a page. Rerunning a check can
replace the sheets and finding labels. New media or changed coverage belong to a
new candidate or a deliberately separate review directory.

## Import says the decision does not match

Check that the selected run matches the downloaded file from its current
page. A browser may rename a download to `decisions (1).json`. The import binds
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
