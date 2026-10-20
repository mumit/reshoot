# Reshoot handoff

Saved: 2026-10-20

Resumed on 2026-10-20. See the [resume validation](docs/validation/2026-10-20-resume-validation.md)
for host checks, four fixes, all 18 corrected Claude/Codex tasks, and remaining
acceptance work. The [external trial record](docs/validation/2026-10-20-external-trials.md)
describes five synthetic app variants from four authorized GitHub repositories.

The owner accepted all five selected external candidates on 2026-10-20. Their
decisions are imported, and each selected run reports review completed. For a later
resume, start with measured user acceptance in those records. Codex authentication
and external-project selection are resolved. Do not repeat the historical setup
and trials below unless new changes require them.
The original state and instructions below remain the record of the transfer.

This file carries the working context to another Codex account and machine. The
repository contains the code, review, plan, skills, and validation record. Resuming
does not require the previous chat or its machine-local Codex memory.

## Current state

Repository: `https://github.com/mumit/reshoot`

Branch: `main`

The working tree was clean before this handoff. All implementation and validation
documents were committed and pushed. No application change or test process is in
progress. The handoff itself is a later documentation commit.

| Commit | What it contains |
|---|---|
| `98e053e` | Product review, implementation plan, and truthful failure/report fixes |
| `cb7d5ad` | CLI 0.2.0 project workflow, native browser input, shared skills, review, and output improvements |
| `b08055e` | Validation record, platform guidance, and sample Action pinned to the tested implementation |
| `b8b99e2` | Documentation cleanup; last commit before this handoff |

[CI for the implementation](https://github.com/mumit/reshoot/actions/runs/39382679939)
passed on Linux and macOS. It covered browser tests, clean wheel installation and
packaged previews, plus a separate Linux browser-and-terminal notes shoot. The
following documentation-only commits used `[skip ci]`.

## Goal and instructions

The product focus is repeatable software demos that stay current as an app changes.
The main distinction is the update process: check expected results, compare stable
beats across releases, and make the new recording easy to inspect. Claude and
Codex use the same CLI, project files, and skill source. Routine runs need no LLM.

The owner's last implementation instruction was: “Now work through each, only stop
when blocked. Commit and push as appropriate.” That authorized conventional commits
and pushes for this work despite the default restriction in `AGENTS.md`. It did not
authorize public releases, posting, or publishing demo media.

Read `AGENTS.md`, `README.md`, and `CONTRIBUTING.md`. Continue to use only the notes
example or made-up demo data. Never capture the whole screen. Record a headless
browser page, a VHS terminal, or one window by its ID.

Writing should be simple, direct, and natural. Use active voice and first person
where it helps. Avoid fluff, jargon, em dashes, and repeated “I would.” Keep
implemented behaviour, measured results, proposals, and untested claims distinct.
These preferences came from the owner and their local writing guide; that local
file does not need to be present on the new machine.

## Read these next

1. [Delivery status](docs/validation/2026-10-19-delivery-status.md): evidence, limits, and open acceptance work.
2. [Implementation plan](docs/plans/2026-10-19-implementation-plan.md): intended scope and acceptance checks.
3. [Product review](docs/reviews/2026-10-19-product-review.md): the original critique, retained as a dated record.
4. [Project guide](guide/projects.md): current commands and file formats.
5. [Roadmap](ROADMAP.md): next priorities.

The core workflow is implemented. The plan is not fully accepted: live harness
trials, external projects, long-take measurements, and broader compatibility checks
remain open. Do not turn the passing fixture tests into a claim that those trials
have happened.

## Set up the new machine

Clone the repository, or pull `main` in an existing clean checkout. Do not reset or
overwrite unrelated local work. Authenticate to GitHub and Codex with the new
account's own access. Credentials and local dependencies are not in this handoff.

```bash
git clone https://github.com/mumit/reshoot.git
cd reshoot
git status --short
uv sync --extra browser
```

The project requires Python 3.11 or newer and uv. Install ffmpeg, Chrome or Chromium,
and Tesseract. On macOS, ffmpeg and Tesseract can be installed with
`brew install ffmpeg tesseract`. VHS is needed for terminal takes, not the first
browser demo. Window capture requires macOS. Windows has not been validated.

Reshoot uses the installed browser, not a Playwright browser download. Set
`RESHOOT_CHROME` if discovery cannot find it. Playwright is pinned to 1.58.0; record
the actual browser and tool versions on the new machine.

Run the existing checks before changing code:

```bash
uv run --extra browser pytest --ocr-backend=tesseract
uv run --extra browser pytest -m browser --ocr-backend=tesseract
```

The previous local results were **62 fast tests and 22 browser tests passed**. The
browser suite took about 160 seconds. Plugin validation also passed with a warning:
plugin-root `CLAUDE.md` is not loaded as context. Essential instructions are inside
each primary skill. Run `claude plugin validate .` if Claude Code is available.

A fresh synthetic preview on macOS or Linux:

```bash
reshoot_demo_dir=$(mktemp -d "${TMPDIR:-/tmp}/reshoot-resume.XXXXXX")
uv run --extra browser reshoot init "$reshoot_demo_dir"
RESHOOT_OCR=tesseract uv run --extra browser reshoot doctor --config "$reshoot_demo_dir/reshoot.toml" --json
RESHOOT_OCR=tesseract uv run --extra browser reshoot preview "$reshoot_demo_dir/reshoot.toml"
```

The generated app uses port 8765. Reshoot refuses to start if another app is already
answering there. Inspect the actual video and poster, not only browser screenshots.
The reports will still say human review is pending.

## Resume work here

### 1. Validate the installed skills in fresh sessions

The canonical source is `skills/`. The wheel bundles it; the installer copies the
three primary skills without depending on a source checkout. Do not create separate
handwritten Claude and Codex versions.

For an authorized trial project, install the desired bundle:

```bash
uv run --extra browser reshoot skills codex --directory /path/to/trial-project
uv run --extra browser reshoot skills claude --directory /path/to/trial-project
```

Codex receives `.agents/skills/`; Claude receives `.claude/skills/`. Start a fresh
session in that project. The skills are `reshoot-demo`, `reshoot-refresh`, and
`reshoot-review`. Test implicit discovery as well as explicit invocation. In Codex,
explicit invocation uses `$reshoot-demo`; in standalone Claude skills it uses
`/reshoot-demo`. The Claude plugin route remains available.

Repeat creation, refresh, and review three times per harness. Include missing tools,
unavailable capture, an ambiguous selector, and an incorrect expected result. Save
harness/model versions, prompts, interventions, failures, and artifact references.
The new Codex session is an opportunity to test discovery. Do not count merely
reading this file or installing a bundle as a passed trial. If Claude is unavailable,
record that boundary and continue work that does not require it.

### 2. Get external trial projects

The owner has not supplied the three to five project paths or repositories requested
for acceptance trials. Ask for authorized projects with synthetic data and reset
instructions. Include a static app, a backend app, and a browser-plus-terminal flow.
Do not choose unrelated working repositories or real accounts as substitutes.

Measure setup, first acceptable preview, update time, manual repairs, review time,
and successful runs. Compare updates with the maintainer's existing recording
method. The proposed 15-minute and eight-of-ten targets remain unmeasured.

### 3. Check Vision on the new host and broaden validation

Apple Vision failed on the previous macOS 27.0.1 host with
`CRImageReaderError 1`, including probes of recognition revisions. Reshoot reports
that as an error. Tesseract was installed and explicitly selected for successful
text scans. It provides no face or person detection.

Do not silently fall back from a failed explicit Vision scan or claim that
Tesseract validates Vision. Test Vision separately if the new host supports it.
`doctor` reports installed capabilities and versions; it does not probe a final
scan. Add framework-app and long-recording evidence as suitable fixtures become
available.

## Implementation map

| Area | Files |
|---|---|
| Project validation and isolation | `src/reshoot/config.py`, `project.py`, `run.py` |
| Native TOML stories and results | `src/reshoot/story.py`, `browser.py` |
| Legacy Python capture and presentation | `src/reshoot/web.py`, `overlay.js`, `zoom.py` |
| Disk-backed frames and hashes | `src/reshoot/artifacts.py` |
| Privacy checks and source redaction | `src/reshoot/check.py`, `scan.py`, `safety.py` |
| Declarative edits and source time maps | `src/reshoot/timeline.py`, `cut.py` |
| Comparison, HTML, and bound decisions | `src/reshoot/review.py` |
| Speech cache | `src/reshoot/voice.py` |
| Packaged templates and shared skills | `src/reshoot/templates/`, `src/reshoot/skills.py`, `skills/` |
| Regression evidence | `tests/test_failures.py`, `test_project.py`, `test_story.py`, `test_review.py`, `test_edit.py`, `test_distribution.py` |

New versioned projects resolve paths from their config and write separate runs
under `takes/runs/ID/`. Legacy configs retain their old path and `[keep]` behaviour.
Legacy Python actions remain unverified unless their results can be inspected.

Keep execution, expectations, scan coverage, and human review distinct. A successful
run is not approval. Comparisons require an explicit previous run; no baseline
updates itself. Imported decisions must match the run, artifacts, and scan policy.
A CLI or overlay change also needs the affected skills and guide updated.

## Local evidence and what transfers

Git contains everything needed to continue development and regenerate the synthetic
demos. It does not contain the old virtual environments, built wheels, caches, or
temporary generated recordings. Recreate those on the new machine.

An optional archive preserves the previous three-run package trial, its review
pages and media, and the historical trial script:

`takes/reshoot-handoff-2026-10-20.tar.gz` (4.1 MB)

SHA-256: `17e7cf2eddc6d0119bc4013d5ffb674dfbb18ba8695bf4e77128a3074cccf73b`

It contains only generated notes data. It is ignored by Git, so copy it separately
if you want the exact old recordings. Resuming does not depend on this archive. The
script inside records old machine paths; use it as evidence, not as an unchanged
setup script for the new machine. Trial timings and tool versions are already saved
in the delivery status.

## Prompt for the new Codex session

> Read HANDOFF.md and the linked delivery status, plan, and review. Check the current
> branch and working tree. Continue the remaining acceptance work without redoing
> completed implementation. Start with environment validation and fresh-session
> skill discovery. Ask for the missing external project paths when needed, and keep
> untested items explicit. Use synthetic data and follow AGENTS.md. Continue the
> existing authorization to commit and push appropriate work; do not publish releases
> or demo media without my instruction. Use plain, natural writing without fluff.
