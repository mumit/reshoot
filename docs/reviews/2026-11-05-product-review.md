# Product and user review

Date: November 5, 2026. Reviewed checkout: `5cfaec0a81c0ff4dfd439345d6724155e478fc06`
(project version 0.3.13).

This records the review and open source comparison from the working conversation.
It combines source inspection, existing trial records, synthetic recordings,
automated checks and inspection of encoded frames and test-generated studio
screenshots. It is not an independent usability study or a hands-on benchmark
of competing products. Recommendations are proposals, not implemented changes
or approved feature removals.

Start implementation planning with the linked
[prioritized backlog](../plans/2026-11-05-product-improvements.md).

## Assessment

Reshoot has a strong reason to exist: software demos should be maintainable
alongside the software they show. The current implementation makes that
proposition credible. It is a substantial developer tool with a promising niche,
but limited evidence of product fit or usability outside the maintainer's workflow.

The main product risk is dilution. Recording, video editing, narration,
screenshots, tours and review each add useful options, but the combined surface
is growing faster than the evidence about what users repeatedly need.

The recommended focus is developers and documentation engineers maintaining
browser demos across releases. Improve creation, editing, refresh and review
before expanding into a broader video-production product.

## What makes it distinctive

The complete maintenance workflow is more distinctive than any individual effect:

- Keep the task, actions, captions and expected results beside app code.
- Check that specified results appeared, rather than only recording clicks.
- Retain failure evidence and explicitly repair changed controls.
- Regenerate media in CI and compare it with the accepted recording.
- Associate review and acceptance with the exact recording and artifacts.
- Produce videos, GIFs and documentation screenshots from the same checked task.

This makes the demo a maintained project asset. It does not make every recording
deterministic: app state, browser versions, services and timing still matter.

Proposed positioning:

> Keep demos alongside your code. Re-record checked workflows when the app changes,
> repair broken steps, and review the updated media before sharing.

The README's claim that users never record the same flow by hand again is too
absolute. Changed tasks and unsupported interactions can require demonstration
or source edits. Local exports, cursor effects and agent support are valuable,
but are already available in other products.

## Product and user fit

| Person and job | Fit today | Main reservation |
|---|---|---|
| Developer maintaining README demos | Strongest | Setup and repairs must cost less than occasional manual recording. |
| Documentation engineer maintaining videos and screenshots | Strong | Needs dependable demo data, useful comparisons and manageable review effort. |
| Developer advocate producing recurring tutorials | Promising | Pacing, narration and creative quality still require substantial judgment. |
| Product marketer making one launch video | Weaker | Repository structure and checked execution may add work without enough recurring benefit. |
| Nontechnical person recording a native app | Weak | Automation, permissions and standalone capture differ substantially from the browser experience. |

These are product judgments, not measured user preferences.

## Strengths worth preserving

1. **Maintenance is the central job.** Most capture tools emphasize the first
   recording. Reshoot also addresses the next interface change.
2. **Users own readable source and ordinary media.** Local files and repository
   ownership make inspection, repair and integration practical.
3. **Execution, checks, scanning and human review are separate.** A completed
   command does not silently become permission to share.
4. **Repair and reversible editing support continued use.** Locator repair,
   Undo, previous recordings and re-cutting can reduce repeated work.
5. **Documentation screenshots are a natural extension.** They reuse the same
   task, result checks and captured evidence rather than requiring another shoot.
6. **Validation records state their limits.** Preserve the distinction between
   controlled trials, maintainer reproduction and independent user evidence.

## Findings and recommendations

### R01: repeatable app state remains the hardest prerequisite

The recorder can replay actions, but somebody must establish the account,
starting data, reset procedure and intended result. Authentication, databases
and remote services make this harder than the notes example suggests.
Startup and reset commands already exist; the gap is helping a user configure
and verify them. See [the own-app guide](../../guide/your-app.md).

Guide the author through running the task twice from the same starting state.
Provide a few tested setup examples and actionable explanations for reset or
login failures. Never infer permission to reset an arbitrary service.

### R02: direct recording still has technical escape hatches

File selection, multiple-choice lists and drops can produce blocking
`recording_issue` entries that require TOML edits. Some iframe and popup changes
also require the story file. The replay engine supports more interactions than
the recorder and studio can author. See [rec.js](../../src/reshoot/rec.js),
[browser.py](../../src/reshoot/browser.py) and
[studio instructions](../../guide/studio.md).

Prioritize common interaction coverage and immediate, actionable explanations.
Preserve a demonstrated draft when an interaction cannot be translated. Do not
make someone finish a task before learning that technical repair is required.

### R03: readable output requires too much diagnosis

The fresh notes final passed its checks, but its readability report estimated
small app text at **9.3 px at a 640 px viewing width**. This is a bounded editing
hint, not proof that the entire video is unreadable. The product already detects
the issue and already supports narrower capture and viewing-size inspection.

Connect the existing finding to an understandable correction: inspect at the
destination width, offer a suitable recording view, show its consequences and
record again. Preserve result visibility and avoid silent cropping. See
[readability.py](../../src/reshoot/readability.py),
[framing.py](../../src/reshoot/framing.py) and
[the visual guide](../../guide/look.md).

### R04: comparison detects changes more readily than it explains them

Evidence frames are compared by hash. Minor changes, including cursor position,
can produce a difference; the report explicitly warns about this. A reviewer
still has to decide what matters. See [review.py](../../src/reshoot/review.py)
and [comparison.js](../../src/reshoot/comparison.js).

Separate task-definition changes, expected-result changes, meaningful visual
changes and incidental variation. Evaluate dynamic-region exclusions or
perceptual comparisons before adding them. Any similarity estimate remains
advisory and must not override failed checks or accept media.

### R05: a passing check can prove too little

Matching text or a count need not prove that a new item was saved or persisted.
An agent can author both the action and an inadequate check. The intended task
still needs human judgment.

Explain the proof beside the check, for example: "The newly created item appears
in the filtered results." Make changed and removed checks clear during refresh
review. Reuse existing fixtures where practical without turning a demo into a
duplicate end-to-end test suite. See [story.py](../../src/reshoot/story.py) and
[expectations.py](../../src/reshoot/expectations.py).

### R06: the editing interface carries substantial operational detail

The filmstrip, selected-step inspector and layout stills improve editing.
The inspected editing screenshot still divides attention among the preview,
status information, global recording controls, navigation and production tools.
This observation concerns an editing state, not a measured first-run experience.

Keep the immediate job prominent: edit a caption, inspect a result or repair a
step. Explain re-cut versus re-record when it affects the next action. Retain
advanced tools without giving them equal prominence. Build on the existing
[journey model](../../src/reshoot/journey.py) rather than introducing a second
set of workflow rules or a wholesale studio rewrite.

### R07: native capture is materially different from the browser workflow

The native macOS route captures a window but adds no cursor, captions or result
checks during capture. Its guide requires manual comparison, and the browser
acceptance workflow does not apply. See [native recording](../../guide/macos-window.md).

Present checked browser automation as the primary product. Keep native capture
as an advanced helper until its workflow supports a comparable promise. Also
keep scan coverage explicit: sampling is the default, and Tesseract is text-only.

### R08: value across repeated updates is not established

The [ten-case study](../validation/2026-10-20-ten-case-update-study.md) produced
ten owner-accepted finals without manual video editing. Five cases needed demo
repairs and two needed fixture corrections. Active human effort was not measured.
This establishes feasibility under assisted conditions, not a general speedup.

Compare setup plus refresh, repair and review effort against manual recording
over several changes. Measure active effort, interventions, failures and output
quality; elapsed time alone is insufficient. Independent users remain explicitly
deferred in [the roadmap](../../ROADMAP.md). Revisit that decision before treating
further feature expansion as evidence of product fit.

## Open source comparison

Project documentation was checked on November 5, 2026. Competitors were not
installed or benchmarked. An undocumented workflow is not proof of absence.

| Tool | Strongest use | Keeping demos current | Implication for reshoot |
|---|---|---|---|
| Reshoot | Checked browser demos beside app code | Saved actions, result checks, repair, CI refresh, comparison and acceptance | Strong maintenance proposition; technical setup and uneven native support. |
| [VHS](https://github.com/charmbracelet/vhs) | Scripted terminal demos | Versioned tapes, CI regeneration and golden-file testing | For terminal-only demos, VHS may already be sufficient; reshoot uses it. |
| [Playwright](https://github.com/microsoft/playwright) | Browser automation and testing | Replay actions and assertions in CI | Broader automation flexibility; reshoot packages presentation, exports and review around the task. |
| [OpenScreen](https://github.com/getopenscreen/openscreen) | Polished desktop product demos | Headless CLI, editable projects, CI support, agent skills and MCP | Closest overall competitor in this review. Agent-driven creation and automated exports already overlap. |
| [Reelbird](https://github.com/btahir/reelbird) | Native macOS recording and sharing | CLI/MCP editing, open projects, captions and sensitive-information detection | Local processing, agent support and privacy features overlap; checked task replay is the clearer distinction. |
| [Cap](https://github.com/CapSoftware/Cap) | Recording, sharing and team feedback | Editable recordings, local or self-hosted storage and collaboration | Emphasizes sharing and collaboration rather than maintained task replay. |
| [Screenity](https://github.com/alyssaxuu/screenity) | Browser recording, annotation and quick editing | Capture and edit footage; checked app replay is not documented | A direct alternative for occasional recordings; repeated refreshes must justify reshoot's setup cost. |

Use the continued OpenScreen repository linked above; the original
`siddharthvaddem/openscreen` repository is archived. Its continued project documents
headless recording, programmatic editing, CI exports and a demo skill for coding
agents. Do not position agent support or a CLI alone as unique to reshoot.

## Features to retain, simplify or defer

There is no usage evidence that establishes zero value for an existing feature.
The following are proposed investment choices, not instructions to delete code.

| Feature | Recommendation | Reason |
|---|---|---|
| Result checks, repair and exact-recording review | Retain and improve | Directly support trustworthy refreshes. |
| Captions, useful export presets and readable framing | Retain and improve | Necessary for a useful short demo. |
| Documentation screenshots | Retain | Reuse the same checked task and evidence. |
| Clickable-tour editor | Freeze expansion; retain simple export | Introduces another authoring model without established recurring demand. |
| Music and extensive voice controls | Keep optional; defer expansion | Basic narration helps tutorials; broader audio production is less central. |
| Style libraries and import/export | Keep presets; defer deeper management | Cross-project brand management needs evidence of recurring team use. |
| Advanced sequencing and repeated clips | Keep under advanced tools | Useful for tutorials, unnecessary for many short demos. |
| Legacy Python routes | Maintain compatibility; reduce equal promotion | Multiple authoring systems increase support and documentation costs. |
| VS Code extension and narrate-as-you-click | Defer | Add interfaces and dependencies before independent usability evidence. |
| New MCP server | Keep parked | Existing shell-based agents work; add it for a demonstrated client limitation. |
| More platforms and simulators | Defer | Multiply capture, interaction, rendering and support combinations. |

## Verification and limits

Earlier in this conversation, against the reviewed checkout:

- The fast suite passed: **355 passed, 66 deselected**, using
  `.venv/bin/python -m pytest --ocr-backend=tesseract` outside the agent sandbox.
- Five focused browser tests passed in a completed run. They covered demonstrated
  step editing, trusted native browser input, wrong-result failure, the bottom of
  a tall recorded viewport and result visibility throughout its hold.
- The full browser suite was interrupted. Six tests had passed; the interruption
  surfaced as a `KeyboardInterrupt` failure. The interrupted demonstration test
  passed in the focused rerun. This is not a complete browser-suite pass.
- Fresh notes preview and final runs each passed three result checks and completed
  sampled scans with six items and no flags. Neither recording was accepted.
- Encoded frame samples and test-generated desktop/mobile studio screenshots
  were inspected. A direct interactive studio walkthrough through the browser
  connector could not be completed because the connector failed.
- The existing editable environment reported installed metadata version 0.2.0
  while importing this checkout's source. These are checkout checks, not a clean
  installation or distribution validation of release 0.3.13.

Local synthetic artifacts are under ignored `takes/critical-review-2026-11-05/`:
preview `debd75ee93e149ff953b4745df5edd11`, final
`610552fb9a994bce88150f5d0729ca6e`, the extracted preview frame and final contact
sheet. They are local evidence, not portable inputs required to use this review.
The final's readability reports contain the 9.3 px estimate at 640 px viewing width.

Historical trial scope and platform evidence are summarized in the
[validation index](../validation/README.md). This review adds no Linux or Windows
run, independent users, comparative usability benchmark or publication approval.
The earlier [October 26 review](2026-10-26-joyful-use-review.md) has its own
follow-up validation; its fixed defects are not carried forward as open bugs.
