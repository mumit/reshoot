# Roadmap

Planned work, most important first. The direction is an agent-first workflow:
describe a task, make a demo, keep its source beside the app, then ask the agent
to refresh it after the UI changes.

Each item says what it is and why it matters. When one ships, move it to Done
with a line on what it does. Trial evidence lives in the
[validation records](docs/validation/README.md), not here.

## Now: refine the creation and revision loop

A [persona review of the docs](docs/validation/2026-10-23-persona-review.md)
found that the tool does the hard part well and loses the joy where a user
meets it first. The studio now gives a local place to see a story and shape it
by pointing, with the files in the repository still the source of truth. Recording,
repair, visual styles, beat cuts, destination framing, audio and documentation
screenshots now share that workflow. The
[creation and revision plan](UX_PLAN.md) defines implementation and acceptance.

1. **A clickable tour.** Export a self-contained HTML tour from verified beats,
    reviewed and refreshed beside the video and screenshots.
2. **Outside users.** Deferred by the owner. Three people who are not the maintainer, each starting from the
    first-demo prompt, and later from the studio. Why: a UI is where real users will surprise us most.

## Later

- **Narrate as you click.** `rec` listens to the microphone and turns what is said during each action into
  that beat's caption or voiceover line.
- **Storyboards in VS Code.** Hovering a beat shows its last frame, the gutter shows whether its checks
  passed, and "Record from here" above each beat starts a partial run, all from the run reports.
- **A web player with chapters.** Each beat is a chapter, and the captions are readable, searchable text
  beside the video.
- **Before and after.** A changed beat's old and new takes play side by side or under a slider, in the
  studio, the review page and the refresh pull request, and can be cut into a short clip for release notes.
- A single first-demo page, with the other guides kept as reference, if `rec` and the studio do not carry a
  newcomer on their own.
- Real changing remote services as a compatibility trial.

## Parked until someone asks

- A Playwright test importer: turn an end-to-end test into a storyboard.
- iOS Simulator and Android emulator takes.
- Windows support and device frames.
- Face and person detection on Linux.
- Translated captions and narration.
- Further duration, platform and workload trials.
- A read-only MCP server: list runs, read a report, fetch a finding's frame as an image, for agents in
  clients without a shell. Not accept, which stays with a person. Claude Code and Codex already run the CLI
  through the skills.

## Done

- **Documentation screenshots that stay current:** named PNGs from checked result
  frames, with alt text, optional crop/downsize, drag and keyboard controls,
  image-size inspection and local downloads. Run-bound provenance, scanning,
  review, export, refresh records and comparison keep them beside the video.

- **Narration auditioning and audio balance:** per-step saved lines, local voice
  choices and cancellable auditions use the recording's cache. Shared CLI/studio
  edits retain checks and undo, and choose a fresh capture after narration changes
  or a re-cut after gain/ducking changes. Mix peaks are limited before encoding.

- **Destination framing and readability:** per-export Fit/Crop, crop guides,
  focus and viewing widths, with shared CLI/studio edits and undo. MP4 and GIF
  share geometry; the inspector retains the selected viewing width. Hashed
  measurements identify small text, subtitle reading pace and bounds outside
  a crop, with explicit coverage limits rather than a readability verdict.
  Recording view can capture the first browser take at a narrower viewport,
  keeping its task and checks. Feedback is available in the studio, CLI and
  review page. Browser frames and edits retain spatial mappings.
- **Beat trimming and sequencing:** Your cut and `reshoot sequence` select
  inclusive named beat ranges, move, duplicate, add and remove video parts.
  The full task and checks still run. Comments, narration boundaries, source
  revisions and recording evidence are preserved; studio operations undo as one
  change. Every repeated or omitted beat is mapped correctly, and finished edit
  maps retain part intervals for playback. Pending range choices must be saved
  or reset before another edit. A current recording can be re-cut in seconds.
- **Reusable visual styles:** Focus, Midnight and Paper starting looks, a project
  style library and portable TOML import/export. The CLI and studio share
  validated edits that preserve the story, timing, fonts, audio, exports and scan
  settings. Studio applies and saves support Undo/Redo; stale or invalid changes
  preserve source files. Finished-export posters show the chosen look before
  playback, and the preview stays beside desktop style controls.
- **Explicit locator repair:** recorder-generated alternatives suggest a replacement only when visible,
  compatible matches agree on one element. Failures and CI show the suggestion; `reshoot repair RUN --apply`
  replays the prefix and revalidates it before changing the locator. The studio also shows failure evidence
  and opens a picker to select and confirm the replacement without activating it. Repairs retain expected
  values, support studio undo and require a new preview. Stale source, conflicting controls and wrong results
  never silently pass. Shared validated file edits support the CLI and studio.
- **Create and revise in one place:** `reshoot create [URL] --directory demo` checks tools, records a task or
  tries notes, makes a preview and opens the studio. The recording toolbar adds captions and explicit result
  checks, hides elements, pauses, removes a step and finishes. Checkbox and radio choices replay their state;
  unsupported interactions remain as blocking repair notes. The studio puts the story first, edits holds,
  supports Undo/Redo, chooses the work with Update preview and cancels updates. Revision checks preserve edits
  from another tab or editor. Media, scan sheets and acceptance stay bound to the displayed run.
- **The studio:** `reshoot studio` serves a local page with the latest run's video, its beats on a timeline
  with their frames, result checks and captions, the exports side by side with their platform limits, the scan's
  findings and the accept panel. Captions and their look, title cards, the frame, music and export presets are
  edited in place and written to the project's files. A beat whose actions changed is recorded again from that
  beat, and Re-cut or Record runs from the page.
- **Captions drawn after recording:** TOML takes are recorded without captions, and the storyboard's are drawn on
  afterwards, so `reshoot recut` can change their words and look.
- **Re-cut without recording:** `reshoot recut RUN` edits and scans a run's takes again into a new run, for
  changes to cards, music, the frame and exports.
- **Presets and a frame:** export presets for README, X and LinkedIn check each platform's limits, and a
  `[frame]` table gives takes a browser window, rounded corners and a shadow on a brand background.
- **Accept from the review page:** `reshoot review RUN --serve` serves the page locally with a choice for each
  finding and an Accept button, recording the same decision as `reshoot accept`.
- **Checks suggested by `reshoot rec`:** a TOML draft suggests result checks from what each action changed on the
  page, and every suggestion in the notes tour passes when the draft is recorded.
- **The upgrade notice in Codex:** a cold Codex session that started on 0.3.4 checked PyPI and upgraded to
  0.3.5 before writing anything ([round 6](docs/validation/2026-10-23-cold-first-demo.md#round-6-the-upgrade-notice-on-035)).
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
