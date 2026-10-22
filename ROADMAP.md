# Roadmap

Planned work, most important first. The direction is an agent-first workflow:
describe a task, make a demo, keep its source beside the app, then ask the agent
to refresh it after the UI changes. The CLI provides the recording and editing
tools; the skills guide creation, refresh and review.

Each item says what it is and why it matters. When one ships, move it to Done with a line on what it does.

## Next

The owner deferred independent new-user testing to focus on documentation.
The primary entry point is now the [agent quickstart](guide/agent-quickstart.md),
with a first-demo prompt and a [skill catalog](skills/README.md). Direct CLI use
remains available through [installation](guide/install.md), the complete
[record-and-update tutorial](guide/step-by-step.md), and
[own-app authoring](guide/your-app.md). Near-term product work is easier access to
polished export templates and predictable versioned distribution; these are
proposed priorities, not shipped features. Existing acceptance and compatibility
evidence below remains available without repeating completed owner reviews.

1. **Measure acceptance with users.** Five app variants from four authorized GitHub
   repositories now have synthetic workflow trials. Measure setup, first acceptable
   preview, repairs, review time, and updates against the maintainer's existing method.
   The owner accepted the photosearch feature demo, reusable follow-up, and one
   assisted refresh. The [recording-method comparison](docs/validation/2026-10-20-recording-method-comparison.md)
   has two completed assisted pairs with opposite orders and both updates accepted.
   Elapsed ordering flipped: pair 01 was 296.128 seconds for the director and
   118.246 for reshoot; pair 02 was 127.632 and 247.200 respectively. Review and
   response waiting account for most of each difference; no general speedup is
   established. Novice setup, other users, and independent comparisons remain open;
   the independent new-user trial is deferred at the owner's request.
   All ten agreed update cases now
   have both final exports accepted without manual video editing, meeting the
   eight-of-ten target in this assisted maintainer study. Five cases needed demo
   repairs and two had fixture corrections; active human effort is unknown.
   See the [study record](docs/validation/2026-10-20-ten-case-update-study.md).
   The owner completed a [separate-Mac packaged workflow](docs/validation/2026-10-21-separate-mac.md)
   on Apple Silicon with 16 GB RAM: pinned provenance, preview/final assertions,
   manifest hashes and media decoding pass; final MP4/GIF visuals are accepted.
   Both full-frame privacy sets are owner approved (106 sheets).
   [Fresh Codex and Claude sessions](docs/validation/2026-10-22-separate-mac-harnesses.md)
   on that machine both loaded refresh guidance implicitly, repaired the same
   locator and produced owner-accepted MP4/GIF pairs with all three assertions
   passing. Baselines and transferred evidence are unchanged. Codex reused local
   memory; independent novice use remains open. The owner approved all four
   receiving-Mac full-frame privacy sets (215 sheets). Subsequent supplied
   sessions verify explicit review-skill invocation in both harnesses; the
   existing approvals cover the exact reviewed exports. The baseline GIF display
   defect found during review is fixed in the local renderer, as described below.
   Retained logs do not measure the initial
   installation duration, since the logged installer found the package present.
   A subsequent Podman trial on the existing Mac passed the
   regular and browser test runs separately, plus the packaged Linux browser
   workflow, with positive owner visual
   review. That adds Linux container compatibility evidence; independent novice
   setup remains open. A new
   [promotional demo](docs/validation/2026-10-21-promotional-demo.md) now has local
   social and README exports accepted by the owner, with both promo scan-sheet
   sets approved (133 sheets). The local README uses these exports; original
   notes media are retained.
   Another machine used by the same maintainer is clean-machine reproduction,
   rather than novice-user evidence.
2. **Broaden compatibility evidence.** A [five-minute continuously animated notes
   trial](docs/validation/2026-10-20-continuous-animation.md) passed technical checks
   on this Mac, including encoded motion and resource measurements; the owner
   accepted the recording and bound run review is completed. Separate scan sheets
   remain pending. [Positive face/person checks](docs/validation/2026-10-20-positive-detection.md)
   also passed on two generated images and a no-person control outside the sandbox;
   a sandboxed Vision failure is retained. A [native AppKit window
   trial](docs/validation/2026-10-20-native-window.md) passed capture, export,
   encoded-text, sampled scan and cleanup checks; the owner accepted its recording
   after confirming the instant text update was intentional. A [controlled local
   service-change trial](docs/validation/2026-10-21-changing-service.md) produced
   four successful finals and two expected assertion failures, covering a delay,
   HTTP 503, a response-schema change, a one-line app repair and recovery. The
   owner accepted all four finals, with bound run reviews completed, and approved
   all four full-frame scan-sheet sets (391 sheets). Actual remote-service
   compatibility stays open.
   A [Podman Linux trial](docs/validation/2026-10-21-podman-linux.md) on Debian 12
   ARM64 passed 68 regular and 26 browser tests, plus packaged notes preview/final
   recording with sampled Tesseract scanning. The owner reported good final
   MP4/GIF appearance. The full promotional build including VHS also passed its
   technical audit after repairing timestamp drift at clip joins in the promo
   recipe. Original failures and recordings are retained; the owner accepted all
   three repaired exports and all three full-frame promo scan sets (208 sheets).
   Those scans used macOS Vision on the Linux exports; broader Linux detection
   coverage remains open. Packaged notes source-run checklists are unchanged.
   Broaden detection coverage, desktop apps, recording
   durations and workloads, changing remote services, and platforms.

The [delivery status](docs/validation/2026-10-19-delivery-status.md) records the
original implementation and its limits. The
[resume validation](docs/validation/2026-10-20-resume-validation.md) records three
creation, refresh, and review tasks in each live harness, Vision and two-minute
smoke tests, and the fixes discovered while running them. The
[external trial record](docs/validation/2026-10-20-external-trials.md) describes the
synthetic GitHub projects and keeps product targets separate from CLI timings.

## Later

- Named export presets with verified destination limits.
- iOS Simulator and Android emulator takes.
- A Playwright test importer.
- Translated captions and narration.
- Face and person detection on Linux.
- Windows support and device frames.

## Done

These features are implemented. Repeated live harness trials completed, and the
owner accepted the five selected external candidates. The first measured owner
creation and standalone refresh trials are accepted; broader user acceptance
remains open as described above.

- **Owner review of external candidates:** imported the owner's acceptance for
  all five selected recordings and their beats, bound to unchanged artifact hashes.
- **Guided onboarding:** one TOML tutorial covers preview, final, deliberate
  selector failure and repair, comparison, separate scan and recording review,
  and local export. Installation, own-app and troubleshooting guides support it;
  the Python and individual-take workflow remains available as an advanced guide.
- **Baseline GIF comparisons:** previous GIFs render as images in newly generated
  review pages; MP4s retain video players. The regression and all 10 review tests pass.
- **Repeatable projects:** packaged templates, dependency checks, previews and
  partial replay, versioned paths, isolated runs, and explicit local export.
- **Shared Claude and Codex skills:** create, refresh, and review from the same
  bundled source, with complete local installers.
- **Checked browser stories:** native Playwright input, stable beats, expectations,
  failure evidence, resource capture, and legacy Python compatibility.
- **Release comparison and review:** beat and environment differences, original
  frames, local HTML, exact artifact hashes, and explicit review decisions.
- **Full scan option:** every decoded video or GIF frame, plus direct checks of
  subtitle and narration text. Sampling remains the default; neither is a safety verdict.
- **Declarative edits and profiles:** source time maps, labeled speed and marked
  wait changes, narration protection, reading holds, styled captions and cards,
  size and file budgets, subtitles, and posters.

- **Subtitles and voiceover:** `VOICE` in a storyboard speaks a line as each beat starts (macOS `say`, `espeak-ng`,
  or any command), and each beat waits for its line. The cut adds the voice and optional music that ducks under it
  and fades out, and writes an `.srt` from the voiceover or the captions.
- **Automatic privacy checks:** `reshoot check` scans supplied images and sampled frames for emails, phone numbers, keys, paths
  with a user name, street addresses and watch-for words (Vision on macOS, Tesseract elsewhere), and for faces and
  people (macOS). Flags come first on the sheets, boxed in red, with what was found masked in the output.
  `BLUR` and `__demo.blur(sel)` hide what has to stay in the app.
- **Write the storyboard by clicking:** `reshoot rec URL OUT.py` opens Chrome with a fresh profile and writes a
  beat for each click and run of typing, with stable selectors and holds from the pauses. Passwords become a
  placeholder.
- **Zoom on clicks:** `ZOOM = True` or `--zoom`. The view moves in on clicks and typing, worked out after
  recording so it lands on each click. It stays through pauses while the next action is in view, and moves out for
  a long quiet spell, a new caption, an action far away, or a change outside the view (seen in the frames).
  Captions are drawn after the zoom. `__demo.zoom()` and `zoomOut()` for exact control.
- **Reshoot in CI:** `reshoot run` does a whole shoot from a `reshoot.toml`, and `action.yml` runs it on GitHub's
  Linux and macOS runners. The example workflow reshoots on each release and opens a pull request with the new
  files for a person to check. reshoot reshoots its own notes example this way.
- **First release:** `reshoot web`, `window`, `check`, `gif`, `last-change` and `edit`; the guide; six Claude Code
  skills; the notes example.
