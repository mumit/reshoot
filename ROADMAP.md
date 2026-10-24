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

1. **Outside users.** Deferred by the owner. Three people who are not the
    maintainer, each starting from the first-demo prompt.

## Later

- In a cold Codex session with an older reshoot, check that `doctor`'s upgrade notice leads it to upgrade. The
  notice itself works: 0.3.3's `doctor` reported 0.3.4 when it came out.
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

- **Review inside the pull request:** a refresh pull request shows the GIF, links the MP4 on its branch and shows
  each scan finding with its frame, so a usual review needs no artifact download.
- **Fewer, clearer guides:** one start-here per reader, including a [team page](guide/team.md), field tables
  for the three project files, an index of error messages, one word for each idea, help text for every command,
  and three overlapping pages merged into others.
- **Review that fits the data:** flagged items are grouped into findings that `accept` names once, the review page
  shows the exports, the findings and the scan sheets in that order, and `run --full` replaces a config edit.
- **Sharp video at higher pixel ratios:** Chrome starts at the recording's pixel ratio, so the screencast sends
  device-size frames: `@2` records twice the pixels, zoomed text stays sharp, and the short first frames are gone.
- **Show the craft:** [How the videos look](guide/look.md) shows the cursor, auto-zoom, captions, title cards,
  export shapes and GIF sizes, recorded from the notes example by a script that rebuilds the page.
- **The same cursor on every route:** TOML storyboards glide, press, ripple and type at an uneven pace like Python
  ones, and a `[cursor]` table sets the size, typing speed and ripple.
- **A clear agent handoff:** agents end with the exports, the checks, "reply accept, or ask for changes" and the
  accept command, and the quickstart lists follow-up requests. `export` copies the exports without naming files
  and prints README Markdown, and `init` writes a `demo/.gitignore` that keeps the accepted record in.
- **A README that sells in ten seconds:** it leads with "Demos that stay current", the install line and three
  commands with their output, then the agent prompt with what to expect, a storyboard, how reshoot differs from
  other tools, and one table of where to go next.
- **A finish line worth reaching:** a run ends with its result checks and the paths of what it made, a failure
  names its run folder and failure image, the app's log goes to a file, `compare` says what changed, and the
  review page opens with one status line. The tutorial uses `latest` and `accepted` and stays quick after a full scan.
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
