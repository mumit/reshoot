# Validation records

Each record describes one trial: what ran, what passed, what the owner accepted
and what it does not establish. Records are dated and kept as written. Use them
as evidence; use the [roadmap](../../ROADMAP.md) for planned work.

## What the evidence covers

- **Update workflow.** All ten agreed update cases produced owner-accepted
  finals with no manual video edits, meeting the eight-of-ten target. Five
  needed a demo repair and two a fixture correction. This was an assisted
  maintainer study; active human effort was not measured.
- **Method comparison.** Two assisted pairs, in opposite orders, compared
  reshoot with the earlier photosearch director. Elapsed ordering flipped
  between pairs, and review waiting dominated both. No general speedup is
  established.
- **Fresh agent sessions.** Codex and Claude Code each discovered the refresh
  skill, repaired one locator and produced accepted exports on a second Mac.
  Codex reused local memory, so this is maintainer reproduction, not novice use.
- **Platforms.** macOS (two machines) and Debian 12 ARM64 in Podman pass the
  test suites and packaged workflow. Linux scanning uses Tesseract for text
  only; the Linux promo exports were scanned with macOS Vision.
- **Compatibility.** A five-minute animated recording, a native AppKit window,
  positive face and person detection, and a local service-change simulation
  all passed. Real remote services and other desktop apps remain untested.
- **First demo from cold.** The README prompt, in fresh Claude Code sessions
  with no reshoot installed, made postable demos of three new apps unaided in
  2 to 7 minutes; a URL-only run correctly stopped to ask for a data reset.
- **CI refresh.** In a private trial repository, app changes on `main` opened
  pull requests with the new media and a comparison with the accepted record;
  a breaking change failed on its beat and opened nothing.

## What it does not cover

- Anyone other than the maintainer setting up or using reshoot.
- Windows, mobile simulators, and face or person detection on Linux.

## Records

| Date | Record |
|---|---|
| 2026-10-24 | [Beat trimming and sequencing](2026-10-24-beat-sequencing.md): inclusive ranges, video order, repeats, undo and preserved source checks |
| 2026-10-24 | [Reusable visual styles](2026-10-24-visual-styles.md): starting looks, saved and portable styles, grouped undo, preserved tasks and rendered previews |
| 2026-10-24 | [Explicit locator repair](2026-10-24-locator-repair.md): suggested and visual replacements, preserved checks, stale-edit protection and studio undo |
| 2026-10-24 | [Creation and revision](2026-10-24-creation-and-revision.md): one-command creation, recording controls, studio updates, undo, cancellation and exact-run review |
| 2026-10-19 | [Delivery status](2026-10-19-delivery-status.md): original implementation and limits |
| 2026-10-20 | [Resume validation](2026-10-20-resume-validation.md): host checks, fixes, 18 harness tasks |
| 2026-10-20 | [External trials](2026-10-20-external-trials.md): five synthetic app variants from four repositories |
| 2026-10-20 | [Photosearch refresh](2026-10-20-photosearch-refresh.md): one assisted refresh after a renamed input |
| 2026-10-20 | [Recording-method comparison](2026-10-20-recording-method-comparison.md): two timed pairs |
| 2026-10-20 | [Ten-case update study](2026-10-20-ten-case-update-study.md): ten accepted updates |
| 2026-10-20 | [Continuous animation](2026-10-20-continuous-animation.md): a 309-second recording |
| 2026-10-20 | [Positive detection](2026-10-20-positive-detection.md): face and person flags on generated images |
| 2026-10-20 | [Native window](2026-10-20-native-window.md): one AppKit window by ID |
| 2026-10-21 | [Changing service](2026-10-21-changing-service.md): delay, 503, schema change and recovery |
| 2026-10-21 | [Podman Linux](2026-10-21-podman-linux.md): Debian 12 tests, packaged workflow and promo build |
| 2026-10-21 | [Promotional demo](2026-10-21-promotional-demo.md): the README before-and-after exports |
| 2026-10-21 | [Separate Mac](2026-10-21-separate-mac.md): packaged workflow on a second machine |
| 2026-10-22 | [Separate-Mac harnesses](2026-10-22-separate-mac-harnesses.md): fresh Codex and Claude refreshes |
| 2026-10-22 | [Agent-first review](2026-10-22-agent-first.md): the first-demo prompt and skill catalog |
| 2026-10-22 | [Documentation onboarding](2026-10-22-documentation.md): synthetic runs of the guides |
| 2026-10-22 | [Documentation journey](2026-10-22-documentation-journey.md): the five-stage guide review |
| 2026-10-23 | [CI refresh](2026-10-23-ci-refresh.md): pull requests from app changes, in a trial repository |
| 2026-10-23 | [Cold first-demo runs](2026-10-23-cold-first-demo.md): the README prompt in fresh sessions on four new apps |
| 2026-10-24 | [Review inside the pull request](2026-10-24-pr-review.md): the GIF, MP4 link and finding frames in a refresh pull request |
| 2026-10-23 | [Persona review](2026-10-23-persona-review.md): the docs read by five kinds of user, and the tutorial run by one |

Generated evidence lives under `takes/`, which Git ignores.
