# Documentation journey review

The owner requested a progression from a first recording through feature
discovery, customization, fuller demos or tutorials, maintenance and publishing.
The review covers agent-first use and direct CLI use, starting with source code,
a running web URL or an installed native macOS app.

## Findings and changes

| Gap | Change |
|---|---|
| The first prompt required a web app repository | Use one target-based prompt in the README and quickstart; support a source folder, URL or named macOS window |
| URL-only and installed-app readers had no first-use walkthrough | Add running-web and native-window routes with agent and CLI instructions |
| The first recording led directly into updates | Add optional feature discovery, small customization exercises and fuller-story authoring before maintenance |
| Native recording appeared to share browser run semantics | Distinguish standalone native capture, app-specific or manual interaction, numeric edits and manual comparison from versioned browser/VHS runs |
| Primary skills assumed source inspection and versioned capture | Route the three installed skills by target and preserve native recipes without inventing manifests, assertions or comparison support |
| Automation was introduced before a working local demo | Make local recording the prerequisite, then document candidate-only CI triggers and separate media promotion |

The [guide index](../../guide/README.md) presents all five stages. The README,
quickstart, skill catalog, source-app walkthrough, manual guide, installation,
command map, CI and sharing drafts point to the appropriate routes. Guides use
imperative instructions; the README retains its first-person origin paragraph.

## Verification

Local evidence is retained in ignored `takes/docs-journey-review/`: the pre-edit
snapshot, fresh project sources, run reports, check sheets, installer copies,
frame comparisons and `verification.json`. These recordings are verification
candidates; no visual or scan approval was imported.

- The bundled notes preview passes its three result checks. A second preview
  changes the intro caption, extends the result hold to three seconds and
  exports a 640 × 360 GIF. Source metadata, cue text and exported dimensions
  verify those changes; representative frames show the caption and result.
- A source-free project points to a separately started synthetic notes server.
  It has no `[app]` configuration. Preview and fresh final pass all three checks,
  and the server remains running afterward. The story was authored for known
  fixture controls; this does not measure novice authoring or authenticated
  remote-site setup. The interactive `rec` workflow was not repeated here.
- The fuller-demo edit adds a 1.5-second opening card. Final corrected run
  `bf35c2383c104439abaceb0fa4fcd790` passes all three checks. Its MP4 is 9.88 s
  at 1280 × 720; its GIF is 9.87 s at 800 × 450. Both retain the opening and
  result. A comparison page retains the original baseline.
- The native edit uses a copy of the existing synthetic AppKit fixture MOV,
  leaving its original unchanged. Both the initial and post-fix edit export
  MP4/GIF successfully. The post-fix source and exports undergo a full-frame
  scan with no detector errors; human decisions remain pending. Capture itself
  relies on the [existing one-window trial](2026-10-20-native-window.md), not a
  new native-app automation or permission test.
- Seven successful browser runs retain their three passed checks; two failed
  setup attempts remain. One URL attempt preceded the permitted external server;
  one managed-server attempt was blocked from binding localhost in the sandbox.
  Authorized retries succeeded. The verifier checks all 112 successful-run
  artifact hashes and fully decodes 24 media files, including the copied native
  source and its final exports.
- README and quickstart prompts match. Relative links and heading anchors are
  checked across maintained docs and skills. Fenced TOML/YAML parse, Bash passes
  syntax checks and Python examples parse. Exact counts are in the local audit.
- Both primary installers succeed; all 12 copied files match canonical source.
  The six changed skills pass the skill-creator validator. Plugin validation
  passes with its existing root `CLAUDE.md` warning.
- The regular test suite reports **71 passed, 26 deselected**. The deselected
  browser suite was not rerun; the fresh notes recordings above exercise the
  browser path. No public workflow, posting or package publication was performed.

## GIF defect found during the review

The first title-card MP4 was correct, but its GIF omitted the opening card and
was shorter. A stream-copy card/browser join changes sample-aspect or color
metadata. Resetting ffmpeg's buffering palette graph loses the preceding
section. Disabling reset alone retained duration but could freeze the picture;
that approach was rejected.

The fix in `cut.gif` first writes a temporary lossless RGB stream, then builds
one palette from the full clip. Full-clip palette statistics also preserve solid
scene changes. Two regression cases check both join orders, duration and the
actual first/last colors. Both fail before the fix and pass afterward, along
with the existing edit/GIF checks and regular suite. New tutorial and native
exports verify the corrected path. The failed visual candidates remain intact.

The fix adds a temporary lossless encoding step; long-recording performance
and a fresh Linux run have not been measured in this review. The
[pitfalls](../../guide/pitfalls.md) and editing skill document the corrected
behavior and independent GIF inspection.

## Remaining validation limits

The revised first prompt and target routing have not had fresh end-to-end
Codex/Claude bootstrap sessions or an independent new-user trial. Hosted login
flows and arbitrary native input automation remain app-specific. The CI trigger
fragment follows GitHub's official syntax and parses locally; no GitHub job was
dispatched. New guide URLs become available after the owner pushes the changes.
Previously accepted promotional media and review decisions are unchanged.
