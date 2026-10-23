# Roadmap

Planned work, most important first. The direction is an agent-first workflow:
describe a task, make a demo, keep its source beside the app, then ask the agent
to refresh it after the UI changes.

Each item says what it is and why it matters. When one ships, move it to Done
with a line on what it does. Trial evidence lives in the
[validation records](docs/validation/README.md), not here.

## Now: make it adoptable

1. **Versioned releases.** Publish 0.3.0 to PyPI with a Git tag and a changelog,
   so `uvx reshoot` works and the plugin and installed skills name a matching
   version. Today the only install is the Git default branch, which is a hard
   stop for most people and gives agents nothing stable to pin. Publishing needs
   the owner's yes.
2. **One-step acceptance.** Replace the current sequence (inspect every sheet,
   `check --ok`, regenerate the page, set each beat, download a JSON file, move
   it, import it) with one action: `reshoot accept RUN`, or an Accept button on a
   locally served review page. Show flagged items first and let clean ones be
   approved together. Keep the hash binding underneath. The maintainer's own
   trials left scan sheets pending in nine records; users will skip it too.
3. **First-run friction.** Choose a free port for the bundled example instead of
   a fixed 8765. Print the real address when a port is busy; the message
   currently shows a redacted hash. Add `latest` and `accepted` run aliases and a
   `reshoot runs` listing so a refresh does not need a 32-character ID copied by
   hand. Make `reshoot web --help` describe TOML storyboards and give `review`
   and `compare` real help text.

## Next: prove the promise

4. **CI refresh on GitHub.** Dispatch the candidate workflow on a real
   repository: a UI change opens a pull request with the new MP4, GIF and
   comparison page. This is the claim on the README's first screen and it has
   not run end to end.
5. **Outside users.** Three people who are not the maintainer, each starting
   from the first-demo prompt. Measure time to an accepted video and where they
   got stuck. More maintainer trials on more machines add little now.
6. **Playwright test importer.** Turn an existing end-to-end test into a
   storyboard with beats and expectations. Teams with tests get a demo almost
   for free.

## Later

- Named export presets with verified limits for X, LinkedIn and README use.
- A single first-demo page, with the other guides kept as reference.
- Real changing remote services as a compatibility trial.

## Parked until someone asks

- iOS Simulator and Android emulator takes.
- Windows support and device frames.
- Face and person detection on Linux.
- Translated captions and narration.
- Further duration, platform and workload trials.

## Done

- **Owner review of external candidates:** imported the owner's acceptance for
  all five selected recordings and their beats, bound to unchanged artifact hashes.
- **Guided onboarding:** one TOML tutorial covers preview, final, deliberate
  selector failure and repair, comparison, separate scan and recording review,
  and local export. Installation, own-app and troubleshooting guides support it;
  the Python and individual-take workflow remains available as an advanced guide.
- **Agent-first entry:** the README leads with a first-demo prompt, backed by the
  agent quickstart and skill catalog.
- **Baseline GIF comparisons:** previous GIFs render as images in newly generated
  review pages; MP4s retain video players.
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
