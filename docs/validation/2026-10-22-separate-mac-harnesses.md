# Separate-Mac harness discovery and refresh

Status: both fresh conversations loaded the installed refresh guidance from an
implicit task prompt and completed the controlled notes refresh. Copied package
provenance, skill files, assertions, comparisons, media decoding and baseline
preservation pass independent verification. The owner watched and accepted both
final MP4/GIF pairs and approved all four full-frame privacy sets. All four
full-frame checklists report review completed. The separate explicit review
invocation also passed in both harnesses in subsequent supplied review sessions.

## Scope and environment

The same owner operated the Apple Silicon Mac with 16 GB RAM from the
[packaged workflow trial](2026-10-21-separate-mac.md). Both projects use reshoot
0.2.0 pinned to `898502277c1e57e872799682358b28e2d54c3e8e`. The copied installer
provenance matches that revision. All six installed skill files in each harness
match the canonical source at that commit.

Codex CLI reports 0.163.0; its transcript does not identify the selected model.
Claude Code reports 2.1.304, with an Opus 5.5 banner. These are recorded versions,
not a model comparison. The recording metadata reports Chrome 155.0.8059.85,
1280 by 720 final browser captures, dark theme, UTC, en-US and seed 1.

Each harness received its own copy of accepted baseline
`4f83ba850e73435595b794f6b075e87b`. The preparation helper changed the heading
to “Notes, refreshed”, the button to “Save note”, and the search input ID plus
its JavaScript reference. The unchanged storyboard still targeted `#q`.
The task remained saving “Pick up the bikes” and searching for “bike”.

This is one owner-operated case per harness. Codex read existing local reshoot
memory during preparation; its conversation was fresh, but the account was not
free of prior context. Neither case establishes novice success, general skill
reliability, or a timing advantage. The sessions ran Codex first, then Claude;
active human effort was not measured.

## Discovery and repair

The initial prompt named no skill and requested read-only preparation. Codex
reported the three skills registered locally and read
`.agents/skills/reshoot-refresh/SKILL.md` before runtime work. Claude's transcript
shows `Skill(reshoot-refresh)` loading successfully from its project bundle in
`.claude/skills/`. Neither session required an explicit refresh fallback.

Both retained the unchanged-story failure at the search action and its screenshot,
then changed exactly one storyboard line: `#q` to `#note-search`. Every other
story field and all three assertions are unchanged. Heading/button changes,
fixture data, captions, beat IDs, holds, edit and export settings were preserved.
The add assertion passed before the failed search action; the two search
assertions were unverified in that incomplete flow.

Codex also retained a prior preview blocked by sandbox denial of the local
server bind. Its authorized retry ran outside the sandbox without a config
change. A later frame-extraction shell quoting error and correction are retained.
Claude recorded the locator repair and a comparison-output filename correction.

| Harness | Retained locator failure | Repaired preview | Fresh final |
|---|---|---|---|
| Codex | `807aef1c657046c288a7a105e007ba50` | `34598ecee5cd44e8851d26dd2f6eb2c6` | `6f20837216c1449597172c57390c5636` |
| Claude | `595c74ea0f5741ca8e0e557427ceacc7` | `f16a2960e3734d3a96d623328e386a83` | `a0da93c82fc34ac0bb527e12862f13cc` |

Codex's earlier sandbox-blocked run is
`0454c50465624d2d91e209ab04bf41a6`. All failed attempts remain in the copied
evidence. Each repaired preview and final passed three assertions. All 64
manifest file hashes across these four successful runs match; all eight exports
fully decode. Preview MP4s use the configured reduced preview dimensions,
720 by 404; final MP4s are 1280 by 720, and GIFs are 800 by 450.

Independent comparisons reproduce the supplied JSON exactly. Both comparisons
match all four beat IDs; only the search definition changes, and assertion
results are unchanged. All 30 files in each copied baseline match the preparation
snapshot, including its reports and checklists. The retained preservation command
also reports the original source and both copies unchanged on the other Mac.
The initial receiving audit left all 387 transferred non-Git files unchanged.

## Final exports and owner verdict

| Harness | MP4 | GIF |
|---|---|---|
| Codex | 7.40 s, 444 frames, 198,454 bytes | 7.40 s, 111 frames, 326,240 bytes |
| Claude | 7.45 s, 447 frames, 194,408 bytes | 7.47 s, 112 frames, 309,141 bytes |

| Export | SHA-256 |
|---|---|
| Codex MP4 | `d8760c7be1c5864f9378ea4e26303b1daf7e7e537e76ba1aca326231cd9cca7f` |
| Codex GIF | `6887e3b76d2ebe2e7198b33eed32444393cd6cf0aa9d3a9ed3a19ee75b9c5b5d` |
| Claude MP4 | `65224e4a85625d7e8c1df0fc5dbd3a4904e8a780b74b0d67954eaa358e8171b1` |
| Claude GIF | `ce11ebc1b6345c993378a611d53eb0560bfe0da488794336f6b442ef0260ef8b` |

Asked about these exact run IDs and both export pairs, the owner replied
“I watched and accept both pairs”. Local `acceptance.json` binds that verdict
to the exports and native run/policy bindings. The transferred native recording
review flags and sampled scan checklists remain pending and unchanged; the
receiving receipt records visual acceptance separately. No approval was inherited
from the old baseline. Decoded temporal sheets were also inspected locally;
that inspection is separate from the owner's complete playback verdict.

## Privacy coverage and remaining review

The native preview/final Vision scans completed with zero flags/errors. They
sample every three seconds: six samples and two exact subtitle files per run.
The original refresh sessions do not contain the packet's separate explicit
`reshoot-review` invocation or its requested full-frame scan step. Loading review
guidance during preparation did not establish that explicit invocation test;
the subsequent review sessions below supply that evidence.

Fresh full-frame Vision scans of all four final exports and their exact SRTs ran
on the receiving Mac. They completed with zero flags/errors. Re-decoding verified
all 1,114 frame identities and original image pixels: 850 distinct images on 215
sheets. These are receiving-Mac scans, separate from the sampled scans executed
on the other Mac. The owner approved all four sets with “Reviewed all four harness
scan sets; approved.” The CLI applied `check --ok` to these four full-frame review
directories. Every checked image matches its reviewed policy; all four checklists
report review completed. No final-export visual or full-frame privacy verdict
remains open for these harness finals.

The numbered viewer is `review/scan-sheets.html` under the local audit folder. It
links all four approved sets and full-size originals. `scan-acceptance.json` and
`scan-acceptance-audit.json` bind the verdict to the 215 sheets, 850 distinct
images, 1,114 decoded frames, exact subtitles, policies and export hashes.
Pre-approval results, reports and both viewer pages are retained under
`scan-approval-evidence/`. At approval, all 387 transferred files, native run
reports, sampled checklists, baseline copies, accepted exports and the visual
receipt were unchanged.

## Explicit review follow-up

The owner supplied five additional Markdown files: findings and session transcript
for each harness, plus Codex intervention notes. Codex's transcript begins with
`$reshoot-review` and shows the project
`.agents/skills/reshoot-review/SKILL.md` being read. Claude's transcript begins
with `/reshoot-review`, shows `Skill(reshoot-review)` successfully loading, and
identifies `.claude/skills/reshoot-review/SKILL.md`. Both review the intended final
against the exact baseline. The Claude follow-up banner reports 2.1.307 and
Opus 5.5; its earlier refresh used 2.1.304. The Codex follow-up supplies no new
harness/model version measurement.

Both reports describe all three passed assertions, four matched beat IDs,
readable captions and the expected saved-note/search result in decoded frames.
They distinguish sampled native scans from the owner's separately approved
full-frame privacy sets. Neither reports a new blocking visual problem. Codex
reports complete decoding and new frame inspections; Claude reports periodic
frame inspection. This evidence establishes explicit invocation and existing-media
review, not an additional recording, scan or real-time playback verdict.

Claude asked whether the receiving-Mac privacy approval covered these exact
files. The follow-up audit verified all four export hashes against the visual
receipt, full-frame approval receipt, policies and completed checklists. They
match. The local sampled reports correctly remain pending; their historical
status does not reopen the later owner approvals.

Two nonblocking presentation findings remain recorded. The inherited edit ends
at the start of the end beat and omits its separate half-second hold, as in the
accepted baseline. The comparison page embeds the baseline GIF in a video
element; source inspection confirms that renderer defect. The final GIFs were
inspected by independent decoding, so this does not change their acceptance.
After committing this validation follow-up as `9496e9f`, the owner authorized the
renderer repair. Baseline GIFs now use image elements in newly generated pages;
MP4s retain video players. A regression reproduced the defect before the fix,
then all 10 review tests passed with Tesseract selected. The regression also
checks the copied animation, source preservation and unchanged review binding.
Plugin validation passed with the existing plugin-root CLAUDE.md warning.
Archived media and review pages are unchanged.

The follow-up audit is `explicit-review-audit.json`. All 386 remaining original
transfer files match their earlier hashes; accepted media, baseline trees, native
reports, privacy evidence and prior receiving audit/approval receipts are unchanged.
The standalone `codex-response-1.md` note is absent from the latest transfer; the
original `codex/evidence/harness-session.txt` still contains that initial response.
Only the five new Markdown files were supplied. New Codex inspection logs, JSON
and frame grabs linked from its report were not transferred; Claude's transcript
has collapsed tool activity. These limits are retained in the follow-up receipt.

## Evidence

Transferred evidence:
`takes/separate-machine/harness-8985022-20261022T033230Z/`.
Each harness retains its session transcript, repair diff, failures, previews,
finals, comparison, command outputs and baseline copy. Top-level logs retain
package provenance, harness versions, skill installation and preservation checks.

Receiving audit:
`takes/separate-machine/harness-audit-8985022-20261022T033230Z/`.
It contains `audit.py`, `results.json`, the unchanged transferred-file hash
snapshot, reproduced comparisons, bound `acceptance.json`, full-scan commands
and logs, four `full-scans/` directories, verified `scan-review.json`, the
numbered viewer, privacy approval receipts and preserved pre-approval evidence.
`audit-explicit-reviews.py` and `explicit-review-audit.json` append the explicit
invocation verification and hash-based resolution of the privacy coverage question.
Do not rerun the one-shot audit, review preparer or approval script over these
accepted receipts. No product code, accepted promo media, commit, push or
publication changed during this verification.
