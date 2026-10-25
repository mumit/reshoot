# First-run setup and continuation

On 2026-10-25 the local macOS checkout exercised actionable dependency checks
and recovery of a paused first creation with synthetic notes data. These are
automated and agent-operated checks, not independent user research, a clean-host
installation trial or owner acceptance of the media.

## What changed

The earlier creation flow wrote a project, stopped on missing tools and suggested
separate recording commands. Repeating `create` then refused that existing
project. The new flow saves its creation stage and prints an exact resume command.
With the studio enabled, Recording tools shows blockers first, with fixes,
Check again and Continue creation. Successful checks remain under a collapsed
details section. The page distinguishes installed tools from completed synthetic
checks and disables continuation while a required check fails.

`create --resume --directory demo` retains the URL, viewport and saved task.
After a preview failure it retries that story without demonstrating again.
After completion it opens the studio without another capture. Before recording,
changed project files or a different URL/size stop resume from replacing a draft.
During demonstration, the recorder writes a new file; guarded installation
retains both sources if an external edit conflicts.

Doctor, creation and the studio share structured checks and fixes. Existing
doctor JSON fields remain, with a `checks` list and explicit probe results.
`doctor --probe` exercises a temporary H.264 MP4 and ffprobe inspection, a TOML
project's headless Playwright browser with a synthetic page/button/PNG, and a
large synthetic word through the configured OCR backend. Creation runs these
checks before using the app. Check again runs them as a cancellable studio job.
Neither path installs packages, changes scan choices or accepts media.

The studio stores its last probe report under ignored `takes/setup.json`, bound
to configuration bytes, discovered tool file stats, interpreter, selected OCR,
detectors and relevant environment settings. A configuration/environment change
invalidates that cached display. Continue creation performs fresh probes even
when the cached report passed. Creation stages live in `takes/create.json`.

## Fresh synthetic trials

The ignored `takes/setup-20261025/` directory contains `trial.py`, `trial.json`,
CLI logs, `doctor.json`, synthetic projects and their outputs.

| Stage | Result |
|---|---|
| Ordinary fresh notes creation | Run `7ec605b831fe4f3e9b599282db76e34e`; all 3 task checks passed after actual setup probes |
| Missing browser override | `create --no-studio` exited 2 in 0.81 seconds, retained the scaffold and printed fixes plus the resume command |
| Correct the override and resume | Run `ea5d28f19bfa4e67ae3fe2b3455e0c79`; 16.62 seconds; all 3 task checks passed |
| Verify source retention | Config, storyboard and edit-script bytes matched their hashes from before resume |
| Resume completed creation | 0.08 seconds, exit 0, no new run or recording |
| Explicit doctor probe | Encoding/inspection, headless browser capture and configured text recognition passed |

The successful preview retained pending owner review and completed its configured
sampled scan. No media was accepted, pushed, posted or published. The missing
browser was simulated by an invalid `RESHOOT_CHROME` override; no installed tool
was removed or installed during this trial.

The native Chrome inspection used a separate synthetic blocked project. It
confirmed that the browser blocker, actionable override fix, Check again,
disabled Continue creation and resume command were visible without expanding
successful checks. The headless mobile test used a 390 px viewport, verified
no horizontal document overflow and completed recovery into a real preview.

## Verification

| Check | Result |
|---|---|
| Complete fast suite | 246 passed, 52 browser tests deselected |
| Affected browser suite | 8 passed: setup continuation, recorder creation, project previews, studio editing and session recovery |
| Final compact setup browser trial | 1 passed, including missing/corrected tools, recheck, continuation and real task checks |
| Guarded recovery | Failed previews keep recorded tasks; changed drafts, URL/size mismatches and edits during demonstration cannot silently replace source |
| Scan choices | Disabled scanning is not probed; a required OCR failure blocks readiness without switching backend or turning off scanning |
| Cached reports | Configuration and relevant environment changes invalidate the prior report; malformed JSON is ignored |
| Documentation | 139 local links/anchors checked; 32 TOML blocks parsed, including separate target alternatives |
| Static/package checks | Python compilation, studio JavaScript syntax, whitespace, exact wheel module/skill bytes and plugin validation passed |

The fast tests also cover a blocked creation opening the setup studio without
starting the recorder or app, refusing ordinary creation over an existing
project, resuming a saved task only once, and preserving a separate recorded
draft after an external edit. Existing result checks and owner review boundaries
remain intact.

Documentation links/anchors and TOML examples, Python compilation, studio
JavaScript syntax, whitespace, wheel contents and plugin validation were checked.
Plugin validation retains its existing root-context and missing-icon warnings.
No media renderer or export geometry changed, so the gallery was not rebuilt.
Accepted media under `docs/demo/` was untouched.

The dependency guidance was checked against primary documentation for
[Homebrew ffmpeg](https://formulae.brew.sh/formula/ffmpeg),
[Homebrew Chrome](https://formulae.brew.sh/cask/google-chrome),
[Homebrew Tesseract](https://formulae.brew.sh/formula/tesseract),
[Debian Chromium](https://packages.debian.org/bookworm/chromium),
[uv tools](https://docs.astral.sh/uv/concepts/tools/) and
[Playwright browser launch](https://playwright.dev/python/docs/api/class-browsertype).
The package commands are suggestions for the named platform/install method;
the setup controls do not execute them.

## Limits and following work

The CLI must already be installed and runnable. This does not establish how a
newcomer handles a genuinely unconfigured computer. Changing shell settings or
replacing the Python environment requires restarting reshoot so it sees those
changes. Cached probe results describe the last check; they are not continuous
monitoring or a guarantee that the next full take will work.

The probes do not start the target app, validate a reset, authenticate, test
headed desktop display availability, record a full task, exercise VHS capture
or speech, or establish positive face/person detection. The synthetic browser
probe covers TOML projects using Playwright; legacy Python recording remains
outside that probe. A scan probe is not a privacy verdict. The configured full
or sampled media scan and human review still apply to the actual run.

Creation state retains saved stages, not in-progress recorder actions. A forced
interruption can require inspecting a saved draft; this is not an atomic
transaction across project sources and metadata. Arbitrary source edits may
still require the file workflow. Outside-user testing remains deferred, and no
new Linux or Windows installation trial was added. The next planned milestone
compares previous and current checked beat frames inside the studio.
