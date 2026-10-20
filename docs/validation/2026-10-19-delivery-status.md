# Delivery status

Started: 2026-10-19  
Validation finished: 2026-10-20

I have implemented the workflow in the [plan](../plans/2026-10-19-implementation-plan.md).
The code and package checks are separate from the live harness and external project
trials. Those trials are still required before claiming the product targets were met.

## Milestones

| Milestone | Implemented | Acceptance still needed |
|---|---|---|
| M0: truthful failures | Operational errors, scan status, review status, result status, cleanup, redaction, and timeouts | Vision integration on a working macOS host |
| M1: predictable projects | Packaged `init`, `doctor`, previews, isolated runs, disk-backed capture, voice cache, reset commands, and explicit local export | Broader setup and long-recording measurements |
| M2: Claude and Codex | Three shared skills, complete local installers, packaged templates, Codex metadata, and Claude plugin validation | Fresh-session discovery and repeated live tasks in both harnesses |
| M3: browser results | TOML stories, native Playwright input, result checks, beat evidence, partial replay, resource capture, and a recorder draft | Trials with actual framework apps and changing remote services |
| M4: release review | Full-frame scan option, direct text checks, edit maps, beat comparison, local HTML, and bound review decisions | External reviewer trials |
| M5: output and trials | TOML edits, labelled speed changes and marked wait cuts, reading holds, narration, music, styled captions and cards, export profiles, posters, and before/after fixtures | Three to five external projects and measured product targets |

## Browser decision

New TOML stories use Playwright 1.58.0 for input and Chromium CDP for capture. The
overlay draws the cursor, blur, and default captions. It does not activate controls.
Native clicks are trusted events; covered, disabled, hidden, absent, and ambiguous
targets fail. The fixtures also exercise a controlled input, iframe, open shadow
root, upload, navigation, partial replay, and captions with and without zoom.

Legacy Python stories retain their overlay input. Their opaque actions and missing
result assertions remain unverified. I kept that path for compatibility rather than
rewriting existing projects during this change.

Reshoot uses the installed Chrome rather than downloading a browser. Playwright is
pinned and the actual browser version is recorded. A new Chrome version still needs
validation. This differs from the plan's proposed fully pinned browser environment.

## Validation

The automated tests cover missing and corrupt inputs, stale reports, interrupted
browsers, synthetic privacy markers, exact frame timestamps, subtitle timing, review
binding, native input, and output dimensions. The test workflow also builds the
wheel, installs it outside the checkout, installs both skill bundles, and records
the packaged notes example.

The full-scan fixture contains a brief synthetic email between sampled frames.
The sampled check misses it; the full check finds it. That demonstrates the coverage
difference on this fixture. It does not establish OCR recall or privacy safety.

A clean temporary environment installs the built wheel and browser extra without
using source-tree imports. The local trial creates the packaged app, installs both
skill bundles, records three isolated runs, changes the synthetic UI, compares
matching beats, and generates review after the app has stopped. Run times measure
CLI execution on this machine, including rendering and scanning. They exclude
installation, story authoring, repairs, and human review.

Local package trial on macOS 27.0.1, Python 3.14.3, Chrome 155.0.8059.85,
Playwright 1.58.0, ffmpeg 9.0.2, and Tesseract 5.5.3:

| Run | Measured CLI time | Result |
|---|---:|---|
| Preview, original app | 12.89 s | Passed configured expectations; text scan completed; human review pending |
| Final, original app | 13.97 s | Passed configured expectations; text scan completed; human review pending |
| Final, changed heading and save label | 13.65 s | Passed the same expectations; text scan completed; human review pending |

The two final runs match four beat IDs and retain the same expectation results.
Their evidence frames change, and the comparison reports changed inputs. I inspected
the new poster and a recorded frame to confirm that the result and caption fit.
This is a small static synthetic app, not an external product trial.

Local automated checks: 62 fast tests and 22 browser tests passed.
[CI for `cb7d5ad`](https://github.com/mumit/reshoot/actions/runs/39382679939)
passed on Linux and macOS, including browser fixtures and clean wheel installation
with a packaged preview. The separate Linux job completed the browser-plus-terminal
notes shoot through the GitHub Action. Plugin validation passes with the existing warning
that a plugin-root `CLAUDE.md` is not loaded as context. Required instructions are
inside each primary skill. All three primary skills pass the skill validator.

## Limits

- Apple Vision fails locally with `CRImageReaderError 1`, including probes of its
  supported recognition revisions. The failure remains an error. Tesseract is an
  explicit, tested text-only alternative; it does not validate face detection.
- Full mode decodes every frame and reuses scans of exact duplicates. It costs more
  than sampling, and detectors can still miss private content.
- Resource capture saves image and media response bodies when Chrome makes them
  available. Unsupported formats and failed bodies are listed as gaps. It does not
  reconstruct a runnable copy of an external application.
- Declared fixture files, configuration, stories, edits, Git commit, tracked diff,
  and final artifacts are hashed. Unlisted untracked files and external services
  are not captured by those hashes.
- The recorder produces a draft. Recognized unsupported select, checkbox, radio,
  and drop interactions fail. Other custom gestures need authored actions and
  explicit tests.
- Portrait uses a responsive take or an intentional crop. Generic profiles do not
  guarantee readable text at every destination. Named social-platform presets and
  current platform limits are not included.
- The legacy `[keep]` path still copies local candidates before review. Versioned
  projects require an explicit export. Neither path publishes a file.

## Blocked acceptance work

I need three to five authorized project paths or repositories with synthetic demo
data and reset instructions. The trial set should include a static app, a backend
app, and a browser-plus-terminal workflow. I have not substituted unrelated working
projects or real accounts.

For each project, record dependency versions, setup time, first acceptable preview,
update time, manual interventions, review time, and successful runs. Repeat agreed
update cases and compare the effort with the maintainer's current recording method.
The plan's 15-minute and eight-of-ten targets remain unmeasured.

Live harness validation also remains open. Start fresh Claude and Codex sessions
with only the installed bundles. Run creation, refresh, and review three times per
harness. Include implicit discovery, explicit invocation, missing dependencies,
unavailable capture, ambiguous selectors, and failed expectations. Save harness and
model versions, prompts, interventions, outcomes, and artifact references. Package
installation tests are not evidence that an agent discovers or follows a skill.
