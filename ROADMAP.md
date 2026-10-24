# Roadmap

Planned work, most important first. The direction is an agent-first workflow:
describe a task, make a demo, keep its source beside the app, then ask the agent
to refresh it after the UI changes.

Each item says what it is and why it matters. When one ships, move it to Done
with a line on what it does. Trial evidence lives in the
[validation records](docs/validation/README.md), not here.

## Now: make reshoot a joy to use

A [persona review of the docs](docs/validation/2026-10-23-persona-review.md)
found that the tool does the hard part well and loses the joy where a user
meets it first: the README, the end of a run and the agent's handoff. Items
are ordered by how early a user meets them.

1. **A finish line worth reaching.** End every run with what was made: checks
   passed, the MP4 and GIF paths and the review page, then the accept command.
   Keep the app server's log out of the output. A failed run prints its folder
   and failure image, `compare` prints which beats matched and changed, and the
   review page opens with one status line. The tutorial uses `latest` and
   `accepted` instead of pasted run IDs and turns the full scan off again.
2. **A README that sells in ten seconds.** Lead with "Demos that stay
   current", the install line and three commands, show five lines of a
   storyboard, say what reshoot does that VHS, Screen Studio and Playwright
   video don't, and give the requirements in one line. One "where next" table
   instead of four, and warmer words than "verdict" and "approval".
3. **A clear agent handoff.** Tell the human before they paste the prompt what
   it takes: minutes, cost, the files it writes, the permissions it asks for.
   End with a fixed handoff: the exports, the checks, "reply accept, or ask for
   changes like these", and follow-up prompts for shorter captions, slower
   pacing, a portrait cut, a voiceover and CI. After accepting, export to
   `docs/demo/` as the CI template expects, and have `init` write a
   `demo/.gitignore` for `takes/`.
4. **The same cursor on every route.** TOML storyboards get the click ripple,
   press and varied typing speed that Python storyboards have, with options
   for cursor size and typing speed.
5. **Show the craft.** A look gallery made from the notes example: zoom on and
   off, the cursor, caption positions, cards, 16:9, 4:5 and 9:16, GIF widths
   with sizes. Name auto-zoom and audio ducking, and turn the camera's fixed
   bugs into a page on how the camera moves.
6. **Sharp video at higher pixel ratios.** Chrome sends screencast frames at
   the page's CSS size, so `@1.5` and `@2` only scale them up, including the
   `1280x720@1.5` default. Capture at the device resolution, or say plainly
   that the ratio only sets the output size.
7. **Review that fits the data.** With made-up data, show flagged scan items
   first and say the rest can be skimmed. Make the full scan a flag on `run`
   instead of a config edit.
8. **Fewer, clearer guides.** Merge the overlapping pages, give each audience
   one start-here (agent user, CLI user, team lead, pull-request reviewer),
   add field tables for the three TOML files, a team page (who owns
   `demo/accepted/`, failure alerts, CI cost) and an index of error messages.
   Pick one word each for run, result check, accept and baseline. Give every
   command help text that describes the current format.
9. **Review inside the pull request.** Link the MP4 on the pull request's
    branch and show flagged scan items as images, so reviewing a refresh needs
    no artifact download.
10. **Outside users.** Deferred by the owner. Three people who are not the
    maintainer, each starting from the first-demo prompt.

## Later

- When a release after 0.3.3 is out, check in a cold Codex session that `doctor`'s upgrade notice leads it to
  upgrade an older install. The notice first shipped in 0.3.3, so nothing could show it yet.
- Checks suggested by `reshoot rec` from what each action changed on the page. The cold runs showed agents
  write good stories and checks unaided, so this helps people working without an agent.
- Accept from the review page itself, served locally, instead of a terminal command.
- Named export presets with verified limits for X, LinkedIn and README use, and a brand table for fonts, colors,
  a logo and a framed browser look with padding, rounded corners and a shadow.
- Re-cut a run, changing captions, cards and music, without recording it again.
- A single first-demo page, with the other guides kept as reference.
- Real changing remote services as a compatibility trial.

## Parked until someone asks

- A Playwright test importer: turn an end-to-end test into a storyboard.
- iOS Simulator and Android emulator takes.
- Windows support and device frames.
- Face and person detection on Linux.
- Translated captions and narration.
- Further duration, platform and workload trials.

## Done

- **Docs that had drifted:** `accept` refuses a preview, so the CI guide can no longer commit one as the baseline,
  and `reshoot skills --replace` installs new skills after an upgrade. The "no `select`" claims, the CLI 0.2
  requirement, the archive-by-ID baseline, the skills' hedges and the sharp-zoom claim are gone.
- **Cold first-demo runs:** from the README's prompt alone, Claude Code made postable demos of three made-up apps
  in under 3 minutes each, and Codex of four in 5 to 9 minutes. The runs led to `select`, located storyboard
  errors, on-time results at higher pixel ratios, stale-install and sandbox fixes, and agents staying in `demo/`.
  See the [cold-run record](docs/validation/2026-10-23-cold-first-demo.md). Released in 0.3.2 and 0.3.3.
- **CI refresh on GitHub:** `examples/github/refresh.yml` records the demo after a change, compares it with the
  committed `demo/accepted/` record and opens a pull request with the new media and a beat table; merging accepts it.
  A broken story fails on its beat and opens nothing. Proven in a private trial repository; see the
  [CI refresh record](docs/validation/2026-10-23-ci-refresh.md). Released in 0.3.1.
- **First-run fixes:** `init` moves the notes example off a busy port, busy ports are named, `reshoot runs` lists
  runs, and `latest` and `accepted` stand in for run IDs. `web --help` covers TOML storyboards. Released in 0.3.1.
- **One-step acceptance:** `reshoot accept RUN` covers the exports, beats, scan items and scan checklist in one
  verdict, bound to the exact run. Flagged items must be named; the run prints the command and writes the review
  page. The two-step check and import route remains for separate verdicts per beat. Released in 0.3.1.
- **PyPI releases:** 0.3.0 is on PyPI, so `uv tool install 'reshoot[browser]'` and `uvx reshoot` work.
  A version tag runs the release workflow, which tests, builds, checks the wheel and publishes through
  trusted publishing.
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
