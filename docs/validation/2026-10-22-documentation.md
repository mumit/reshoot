# Documentation onboarding verification

The subsequent [agent-first revision](2026-10-22-agent-first.md) changes the
primary entry point to a first-demo prompt and skill catalog. This record
retains the initial tutorial verification and style audit below.

The owner deferred independent new-user testing and requested the documentation
overhaul. The recommended entry path is now installation, the packaged TOML
tutorial, and the own-app walkthrough. The previous Python tutorial is retained
as the manual workflow. This work changes documentation, one tutorial image,
issue forms and a copyable CI template; product code and accepted demo media
are unchanged.

## What changed

- [Installation](../../guide/install.md): platform dependencies, Linux Tesseract,
  executable discovery, Git revision pins, upgrades and optional tools.
- [Tutorial](../../guide/step-by-step.md): a packaged preview and final, full-frame
  checking, separate sheet and recording decisions, caption change, deliberate
  locator failure, repair, comparison and local export.
- [Own-app walkthrough](../../guide/your-app.md): managed or external startup,
  a complete native story with result checks, fixture and login setup, and concrete
  create, refresh and review prompts for both harnesses.
- [Command map](../../guide/commands.md) and
  [troubleshooting](../../guide/troubleshooting.md): paths, failures, coverage,
  exit status and review-state distinctions.
- README, guide navigation, reference, contribution and example introductions
  now lead to that same workflow and describe completed maintainer trials.
- The [candidate workflow](../../examples/github/candidate.yml) retains modern
  run folders for local review. The legacy media-PR workflow stays available.

## Live checks

Source implementation: `4621320` with documentation-only working changes.
The existing development environment supplied Python, Playwright, Chrome
155.0.8059.85, ffmpeg 9.0.2 and macOS Vision on macOS 27.0.1. These checks did
not reinstall system dependencies or measure installation time. Commands and
evidence are retained locally under ignored `takes/docs-onboarding/`.

| Step | Run ID | Result |
|---|---|---|
| Initial notes preview | `870e34ef2bbb4dee973b0a0ed1a1c288` | Three expectations passed; sampled Vision check completed |
| Notes baseline final | `2c52f8d586a14e7a9104fd8ad89fcbb8` | Three expectations passed; full check covered 555 frames |
| Caption-change preview | `9a887c9742234a71aa7eb801fae4aeb8` | Three expectations passed |
| Changed input ID, unchanged story | `e750f58c2b394dc287b4cce0e841b1e1` | Expected search-target failure; overall expectations unverified |
| Repaired preview | `971e54f0130a4c3eb7c2145b56011a05` | Three expectations passed after changing one selector |
| Updated notes final | `3a489a6ec87643038ac9f05b5726f57a` | Three expectations passed; full check covered 553 frames |
| Own-app example preview | `421a1db6a5a54993809460eee617e281` | Three expectations passed using the exact documented story and npm startup command against an isolated synthetic fixture |

All six successful runs completed their configured Vision checks with zero flags
or errors. Full checks were also enabled for the caption and repaired previews
once the tutorial changed the project's check setting. All 100 retained manifest
hashes match, including the failed attempt's evidence. All 18 successful-run
MP4/GIF files fully decode. Baseline and updated final MP4s are 1280 by 720.

The app-change Python snippet and own-app TOML story/startup table were extracted
from the Markdown itself. The comparison has four matched beats: only intro and
search definitions changed, while expectation results are unchanged. Generated
review-page local links resolve, and baseline/current GIFs use image elements.
The three selected exports copy byte for byte; a repeated export refuses an
overwrite. Both project-local harness skill bundles install successfully.

The review-page download button was exercised in headless Chrome against the
synthetic local final. The actual downloaded decisions imported successfully
with every decision still pending. A screenshot of those controls was inspected
and included in the tutorial. No acceptance was invented: all trial recording
and scan-sheet verdicts remain pending. These candidates verify documentation
mechanics and do not replace any accepted promotional or harness export.

## Static checks and limits

The initial static pass resolved 146 local documentation links and 14 heading
anchors across 17 entry-point, reference, example and validation documents. Tutorial and
own-app TOML snippets parse, and the complete own-app story passes the native
story validator. Ruby Psych parses both issue forms and the candidate workflow;
`git diff --check` passes. The candidate workflow has not been dispatched on
GitHub, and issue-form presentation has not been tested on GitHub.

The Linux installation path is grounded in the existing Debian 12 ARM64
[Podman evidence](2026-10-21-podman-linux.md), not a new Linux run. System
installation and upgrades were checked against the linked upstream uv
documentation; no installation or release was published. The optional agent
prompts were not rerun as fresh harness sessions; existing
[harness trials](2026-10-22-separate-mac-harnesses.md) remain the evidence for
skill activation. Independent new-user validation remains deferred.
Claude plugin installation syntax and namespaced commands were checked against
the current official plugin documentation and local CLI help; the plugin was
not installed again during this documentation check.

## Language and style audit

The owner requested imperative instructions throughout the documentation, with
first person allowed for the README's project origin. The previous contributor
policy explicitly required first-person guide prose. That policy now requires
direct instructions, present-tense descriptions of tool behavior, sentence case
headings and consistent workflow terms.

The audit covered 29 maintained Markdown documents: the README, contribution
guide, roadmap, ten guide pages, three example documents, ten skills, two agent
instruction files and the packaged brief. The issue forms were also reviewed.
Tutorials, installation, troubleshooting, CI, reference and navigation now use
direct instructions. Personal anecdotes in the pitfalls reference were replaced
with the problem and its remedy. The second pass corrected awkward transitions,
mixed spelling, inconsistent terminology and list spacing.

First-person prose remains only in the README's origin story within that scope.
Historical plans, reviews, validation reports and attributed owner verdicts
retain their original wording. They record past evidence rather than instructing
the reader.

Verification against the pre-edit snapshot found 60 unchanged fenced blocks.
Only the three plain-text agent prompts changed wording; executable fenced
examples are unchanged. One inline voiceover sample now uses a concrete caption
instead of a first-person placeholder. All other inline code in the snapshot
is unchanged, as are the edited skill's code blocks. Eight TOML snippets parse,
46 Bash snippets pass syntax checking and three Python snippets parse.
Local links and anchors resolve in both the main documentation and the extended
skill/template scope; `git diff --check` passes. No product tests or recording
trials were repeated for these prose-only edits. The local audit snapshot and
results are retained under ignored `takes/docs-style-audit/`.
