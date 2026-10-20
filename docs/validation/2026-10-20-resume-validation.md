# Resume validation

Date: 2026-10-20

I resumed from [HANDOFF.md](../../HANDOFF.md) at `395890d`, with a clean `main`.
This record extends the [delivery status](2026-10-19-delivery-status.md).
Fresh Claude and Codex trials completed. Authorized synthetic GitHub trials now
cover five app variants across four repositories. The owner accepted the five
selected external candidates, and their imported decisions mark review completed.
Measured user acceptance and product targets remain open; see the
[external trial record](2026-10-20-external-trials.md#owner-acceptance).

## Environment and checks

This host runs macOS 27.0.1 on Apple Silicon. Reshoot 0.2.0 uses Python 3.12.13,
Playwright 1.58.0, Chrome 155.0.8059.85, ffmpeg 9.0.2, and Pillow 13.0.0.
The template server uses `python3` from PATH, Python 3.14.3 on this host.
Tesseract is 5.5.3 and VHS is 0.12.1.

Before edits, all 62 fast tests and 22 browser tests passed. After the fixes,
all 68 fast tests passed, including wheel/package checks. The generated-project
browser integration passed after the expectation fix; the new mixed-preview
integration passed after the preview fix. Six encoded-video caption cases passed
with the final overlay, covering navigation, zoom, and styling. The entire browser
suite was not rerun locally after the fixes. Plugin validation passed with the
same warning: the plugin-root `CLAUDE.md` is not loaded as project context.

[CI for `2bc2a31`](https://github.com/mumit/reshoot/actions/runs/39465360916)
passed the full fast and browser suites on Linux and macOS, plus clean wheel
installation, both packaged skill installers, doctor, and packaged previews.
The separate Linux browser-plus-VHS notes shoot also passed. This validates the
four code fixes; later documentation-only commits do not change that code.

The outer sandbox blocked some attempts to bind a local server port, access
Claude authentication, initialize Codex's app server, and write the Git index.
Authorized retries ran outside that sandbox. One fast-suite attempt had three
port-binding failures; its retry passed. These are recorded environment failures.
Port 8765 was occupied, so the synthetic projects use separate ports. I did not
stop or inspect the application on the occupied port.

## Vision and saved media

An explicit Vision scan of a generated 800 by 200 image detected
`trial@reshoot.invalid`. Vision performed its text, face, and human rectangle
requests without an integration error on that image. The earlier
`CRImageReaderError 1` did not reproduce. The image contains no face or person,
so this is not a positive detection test for either detector.

A generated notes preview completed using Vision, passed three configured
expectations, and reported its scan completed with review pending. Its saved
H.264 export is 720 by 404 and 7.42 seconds long. I inspected frames extracted
from that video: the typed note, saved note, matching search result, and captions
are visible. This is frame inspection, not complete video playback or owner approval.

Preview run: `notes/takes/runs/0b099a509bf348899f3e08222563cb70/`.

## Longer recording

I generated another notes project, changed only its local port and the search
result hold to 120 seconds, and removed its GIF profile. The entire project run,
including capture, edit, and sampled Vision scanning, completed in 161.97 seconds.
All three expectations passed, the scan completed, and review remains pending.

| Measurement | Result |
|---|---|
| Final video | H.264, 1280 by 720, 125.43 seconds, 7,526 encoded frames |
| Captured browser frames | 419 |
| Largest gap between capture timestamps | 1.178 seconds |
| `/usr/bin/time -l` maximum resident set size | 501,170,176 bytes, about 478 MiB |
| Supplied items awaiting review | 29, across eight sheets |

The memory value is the tool's process-accounting measurement for the whole
command with subprocesses, not a measurement of Python frame storage alone or
total simultaneous system memory. The capture count differs from the encoded
frame count because the encoder holds browser frames between paints. The timestamp
gap does not identify dropped frames by itself.

I inspected video frames across the long result hold. This is one mostly static
two-minute fixture, not evidence for hour-long or continuously animated recordings,
bounded memory at arbitrary duration, OCR recall, or complete human review.

Long run: `long-notes/takes/runs/4ce4b8c7a3244ba398aed2aa091a9512/`.

## Doctor regression

With `RESHOOT_CHROME` pointing to a nonexistent file, doctor returned exit 0 and
`ok: true`, with the browser version `unknown`. Commit `9d509fd` checks that the
discovered or configured browser is executable. Missing and nonexecutable overrides
now return exit 2 with `tools.chrome: null`. The installed Chrome still passes.
The create skill and project/pitfall guides document the recovery step.

## Fresh harness trials

The bundles were installed outside this checkout using the editable CLI and the
canonical skill source. This is not a clean wheel-install trial. Each subprocess
started a fresh conversation, with no resume argument or conversation persistence.
Claude loaded project/local settings, no user settings, and no configured MCP
servers. Built-in skills and plugins still appeared alongside the three project
skills; these trials do not establish an otherwise empty harness environment.

Claude Code 2.1.300 used `claude-sonnet-5-5`. Codex CLI 0.163.0 used
`gpt-6.1-sol`, identified by its preflight header. Neither runner overrides the
model. After the owner signed into Codex, both harnesses completed three creation,
three refresh, and three review tasks in fresh sessions. A completed task includes
correctly preserving and reporting a deliberately failed recording.

| Harness and project | Create task | Refresh task | Review task | Refresh outcome |
|---|---:|---:|---:|---|
| Claude `claude-v2-1` | 82.04 s | 70.25 s | 124.97 s | Heading/save-label update, assertions preserved |
| Claude `claude-v2-2` | 78.67 s | 84.07 s | 131.31 s | Ambiguous selector failed, inspected and repaired |
| Claude `claude-v2-3` | 76.92 s | 66.00 s | 126.77 s | Incorrect rockets expectation retained and failed |
| Codex `codex-v4-1` | 137.66 s | 115.07 s | 178.21 s | Heading/save-label update, assertions preserved |
| Codex `codex-v4-2` | 133.74 s | 121.83 s | 149.10 s | Ambiguous selector failed, inspected and repaired |
| Codex `codex-v4-3` | 135.89 s | 110.09 s | 189.59 s | Incorrect rockets expectation retained and failed |

These are whole session times, including model thinking, commands, scans, and
frame inspection. They do not measure first acceptable preview or owner review.
Projects 1 and 3 use implicit skill discovery; project 2 uses explicit `$reshoot-*`
Codex invocations and `/reshoot-*` Claude invocations. Codex read the exact installed
primary skill in all nine sessions. Claude's implicit sessions emit `Skill` calls;
its explicit slash expansion does not emit that same tool event. All corrected
Claude sessions report zero shell permission denials.

Each creation made a preview and final with checked bikes save/search results.
Successful refreshes retained four stable beat IDs and their assertions. The
selector case repaired only the intended search target. Both harnesses retained
the incorrect rockets assertions and failed preview/final evidence. Their reviews
clearly attributed earlier successful media to its own run and did not claim a
new export existed. Every refresh has an explicit baseline comparison. Reviews
ran supplemental full export scans where media existed, read exact subtitle text,
and inspected original frames. They disclosed that complete playback was unavailable.
Tesseract provided text scanning; face/person detection was unavailable. No
review decisions were imported, no baseline was promoted, and all runs retain
pending human review. A post-trial SHA-256 audit found no changed manifest artifacts
in the six corrected projects.

Initial unsuccessful trials remain evidence. Claude's narrow Bash allowlist denied
required commands; the corrected runner permits Bash within the authorized
synthetic tasks. I corrected initial Claude prompts from Codex's `$skill-name` to
`/skill-name`, and report selection from sorting random IDs to modification time.
An initial review had received a preview instead of the final; corrected reviews
use explicit report paths. These were runner interventions.

Codex initially failed app-server initialization inside the outer sandbox, then
HTTP 401 before the owner signed in. The next three creations discovered skills
but could not bind ports in the inner sandbox. Another runner attempt combined
incompatible `--sandbox` and `--approve-for-me` flags and never started a model.
The corrected runner uses `--ephemeral --ignore-user-config --skip-git-repo-check
-c sandbox_workspace_write.network_access=true --approve-for-me --json -C PROJECT`.
It permits loopback networking and uses automatic approval review for required
headless Chrome escalation. Each corrected creation and refresh first retained
an inner Chrome launch failure, then recorded outside that sandbox after escalation.
The ambiguous selector and incorrect assertion failures remain separate from
those environment failures. This validates recovery with these runner settings,
not a recording workflow that needs no escalation.

Each harness also ran a separate preflight session that used the create skill and
read actual doctor output
from a deliberately empty tool PATH and missing browser override, and explained
the missing ffmpeg, ffprobe, and Chrome dependencies without installing or recording.
It also correctly described native window capture as unavailable on Linux and
refused whole-screen substitution. That Linux case is a hypothetical request on
this macOS host, not a performed Linux capture trial.

## Incomplete expectation regression

The Claude ambiguous-selector preview passed its earlier save assertion and then
failed its search action. Its original aggregate incorrectly said expectations
passed. I retained that historical report. Commit `024fafe` leaves incomplete or
missing browser results unverified unless an assertion explicitly failed. Four
regression cases cover action failure, assertion failure, missing second-take
metadata, and complete takes. Counts describe evaluated assertions. The refresh
skill and project/pitfall guides explain the distinction.

The later Codex selector failure correctly reports execution failed, expectations
unverified, and scan skipped. The deliberately incorrect expectation still reports
failed. A later edit failure can retain passed browser expectations because those
assertions were actually completed; execution remains failed.

## Mixed preview regression

The Datasette browser-plus-VHS preview exposed different output sizes: preview
reduced the web take to 720 by 404 while VHS retained 1280 by 720, so the edit
refused to join them. Commit `c38805d` retains the configured browser dimensions
when a project contains VHS takes, while keeping preview encoding and report mode.
Both TOML and legacy Python capture honor this setting. The regression records a
real browser take, joins it with a fixed-size synthetic terminal video, verifies
the 1280 by 720 output, and checks environment restoration. The external Datasette
preview also passed with real VHS. Skills and project/pitfall guides were updated.
Take dimensions still need to match in the project configuration.

## Caption navigation regression

Flaskr's task assertions passed, but inspection of its encoded video showed that
captions vanished after full page loads within a beat. Commit `1f26c1f` persists
the top-level overlay caption in same-origin session storage and restores it when
the next document attaches the overlay. Iframe unloads cannot overwrite that state.
Restoration emits no extra caption event, so subtitle and post-rendered caption
cues retain the original beat timing. Six browser/video cases cover ordinary,
zoomed, and styled captions with and without navigation. An intermediate regression
caught an iframe overwriting caption state; the final fix passes all six cases.

Fresh Flaskr preview, baseline, and heading-change recordings passed their original
expectations. I inspected their actual export frames to confirm captions remain
visible while writing and after saving. Earlier candidates and scans remain intact.
The guide and affected skills were updated. Cross-origin navigation is not covered
by this same-origin persistence behavior.

## Remaining acceptance work

The owner accepted all five selected external candidates on 2026-10-20. I generated
and imported their decisions after that explicit authorization, verified unchanged
artifact hashes, and refreshed the original and copied review pages. This completes
owner acceptance of those candidates. Historical failed runs and other fixtures
retain their existing review states.

- Run maintainer/user trials with measured setup, first acceptable preview, manual
  repair and review time, and a timed comparison with their existing recording method.
- Agree ten update cases before measuring the proposed eight-of-ten target. The
  five successful synthetic UI refreshes are not that acceptance study.
- Broaden compatibility beyond this host, test positive face/person fixtures, and
  measure longer continuously animated recordings. Changing remote services,
  native app-window trials on this host, and Windows remain untested here.

## Local evidence

Working harness projects live under `/private/tmp/reshoot-live-20261020/`.
External clones and project fixtures live under `/private/tmp/reshoot-external-20261020/`.
Prompts, commands, streamed events, timings, environment metadata, runner versions,
artifact audits, and extracted synthetic video frames live under
`takes/validation-20261020/`. Generated media and raw session logs remain ignored
by Git. The external trial record lists pinned sources, repairs, and candidate IDs.

Optional local archive: `takes/reshoot-resume-evidence-2026-10-20.tar.gz`
(282.3 MiB, 3,983 files).

SHA-256: `0eac18a20ee04776498984fee1966d89101644b63aa4bfb7e972454d52cdd1b4`

It retains generated projects, session logs/prompts, failed trials, recordings,
resources, review reports, app patches, recipes, and dependency metadata. It omits
heavy dependencies and most full-scan sheets/decoded duplicates; their original
files remain on this host and can be regenerated from the saved inputs. First/last
full-scan sheets and all scan reports/keys are retained. The archive is ignored by
Git and must be transferred separately. The local review index is
`takes/validation-20261020/index.html`.
