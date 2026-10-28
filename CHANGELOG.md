# Changelog

Each release names what changed for people making demos. Versions follow
[semantic versioning](https://semver.org/); before 1.0, a minor version may
change project files or commands.

## Unreleased

### Fixed

- In `examples/github/refresh.yml`, a refresh pull request now shows its own
  GIF and links to its own video. Before, every pull request linked to the
  `reshoot/refresh` branch, so GitHub could show an older cached GIF, and an
  earlier pull request showed the latest recording. Copy the new last step
  into your workflow. The note at the end of the pull request also no longer
  breaks in the middle of a sentence.

## 0.3.12 (2026-10-27)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.12. Refresh pull requests name steps in words,
in story order, and read plainly.

### Changed

- The comparison in a refresh pull request and from `reshoot review
  --previous` names steps as the studio does ("Type search notes"), lists them
  in story order, and says "Steps" and "kept" instead of "Beats" and
  "matched". It shows short recording ids, "3 of 3 passed", "App or demo
  data changed", and leaves out the "In the story" column unless a step was
  added or removed. The review page says **Play this step**.
- A stopped recording names its step in words, "Search stopped: it couldn't
  find…", in the studio and from `reshoot repair`, and no longer lists the
  changed files or "recording a fresh preview" under the stop.

## 0.3.11 (2026-10-27)

Use this instead of 0.3.10, which failed on every command under Python 3.11
and has been yanked. Upgrade the project skills with `reshoot skills claude
--directory . --replace` (or `codex`): they now need 0.3.11.

### Fixed

- reshoot runs on Python 3.11 again. In 0.3.10 every command stopped with
  `SyntaxError: f-string: unterminated string` there.
- After an update finishes, the studio no longer keeps showing "Loading the
  new run..." with an empty player each time the page opens.

## 0.3.10 (2026-10-27)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.10. The studio welcomes a first demo with the
video, the GIF and its README line ready, `create` prints a few lines instead
of every stage, and the editing column splits into **This step** and **Whole
video**.

### Added

- The studio welcomes a first preview: it plays once, says how long it took
  and which result checks passed, and offers **Download the video**,
  **Download the GIF** and **Copy readme Markdown**. It opens on a checked step
  with a caption, and keeps layout controls out of the way until the first
  edit.
- In the made-up notes app, **Change the notes app and record again** gives the
  search box a new id, so you can watch the step stop and repair it. **Put the
  app and story back** returns both.
  The offer stays after the first preview until a recording is accepted.
- **Your files** has **Copy readme Markdown** for every recording with a GIF.

- Optional local Kokoro English narration, selectable in Studio or with
  `reshoot audio set --engine 'kokoro --voice af_heart'`. Auditions share the
  recording cache; the workshop recipe uses connected passages and model word
  timings, with a short voice comparison before a full rebuild.
- A local narrated web-app workshop recipe, first-demo excerpt, chapter
  player, subtitles and written companion using only synthetic notes data.
  The recipe preserves original page footage and leaves owner review pending.
  Its `renarrate` operation makes a separate narration edition from existing
  footage; the workshop uses Kokoro Heart with consistent playback loudness.
  A packaging recipe prepares a portable video/caption/transcript ZIP and
  draft upload descriptions without publishing anything.
- Demonstrate replacement actions or an added step from the studio or
  `reshoot step record`. Earlier actions replay first; Done saves a separate
  draft for review. Applying retains existing result checks, supports studio
  Undo and requires a fresh preview before final review.
- A keyboard-accessible story filmstrip selects one step inspector beside the
  preview, keeping other steps' forms out of the way while retaining edits.
- Layout stills show caption, window and crop changes as you edit, using the
  recording's clean frames and the video renderers. Saved videos and review
  stay associated with their recording while outdated still responses are ignored.
- Feature highlight, Task walkthrough and Release update starting recipes
  set pacing, look and export choices while retaining the task, checks and
  current cut. Apply one in the studio with Undo, use `reshoot recipe apply`,
  or start with `reshoot create --recipe feature`.

- Correct a failed check's expected count, text, address, field value or ticked
  state in the studio, with Undo, before recording a preview to verify it.
- A selected-step bar keeps the step being edited beside the preview, with
  playback and a way back to its fields.
- Compare two recordings' exported videos in the studio, choose which side
  to hear, and play matching steps with each cut's timing and repeated
  appearances. Both players keep their chosen recordings as newer runs arrive.

### Changed

- `reshoot create` prints a few lines: the tools are ready, the preview is
  recording, and the result. Each stage's output is kept in the run's
  `output.log`, and a failure names that file. `reshoot --help` groups the
  commands, starting with `create`, `studio` and `doctor`.
- The studio header names the project folder instead of `storyboard.toml`.
- Recorded steps take the control's own words, so a search box with the
  placeholder "Search notes" records as `type-search-notes`, not `type-q`. The
  studio shows step names as words ("Type search notes"), and a missing
  control is named by its words: `couldn't find the field "Search notes"`.
- The studio's editing column has two tabs. **This step** holds the selected
  step's inspector; **Whole video** holds recipes, audio, screenshots, the
  tour, **Your cut** and **Style and exports**, which used to sit below it.
- The studio header has one way to record again: **Record app again**, for
  changes the studio can't see, such as a running app's page. It replaces
  the **More** menu's **Re-cut** and **Record a preview**; **Update preview**
  still re-cuts when that's enough, and `reshoot recut` remains.
- Colour fields in the studio have a colour picker beside them; a typed
  alpha value stays. A step changed since its recording says so plainly
  instead of in red, an empty second line reads "Optional", and accepting
  asks for one short confirmation.
- `create` ends with one next step, and the setup check leaves out its
  disclaimer. A preview's "record final" command uses a short path.
- The workshop is shorter, about half its length, with one point per scene.
  It records at `create`'s default size so the app's text is readable from the
  start, shows the studio at 125%, and clicks **Use these actions** after the
  narration describes the draft. Subtitles avoid one-word lines, the app
  opening matches the dark recordings, and the closing card names the
  repository.
- Choosing a step in the filmstrip brings its inspector into view beside
  the preview. The preview stays in place on windows 640 px tall or more,
  down from 700.
- **Your cut** says "step" and "Recording 1" instead of "beat" and a take's
  file path, and Compare names steps in words and says "Looks different"
  rather than "Frame file changed."
- The studio resumes Undo and Redo automatically when the project still
  matches the saved session. Changed files and unreadable history still offer
  recovery choices and a saved source copy when available.
- Recording controls and recovery messages use the same next step, including
  tool setup, first creation and a stopped preview.
- Optional comparison, audio, screenshot and tour tools sit under **More
  tools**. Removing a failed check takes a deliberate choice after correction.
- A failed studio update opens its failure details while retaining the last
  successful recording.

### Fixed

- Recorded steps keep unique names when a task repeats a control beside one
  with a numbered name, such as Save and Save 2.
- A finished run's review and acceptance instructions keep referring to that
  recording after a newer one is made.
- After fixing a first preview, the studio names the available continuation.
- Repair can find the last working recording after several failed attempts.
- Failed-check correction and control repair wait for saved-history recovery
  just like the rest of the editor.

## 0.3.9 (2026-10-25)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.9. When the app changes and a step can't find
its control, the run says what broke and suggests what the control became.

### Added

- When a step can't find its control, it says so in words, such as
  `couldn't find the link "New issue"`. It also suggests what the control
  became, such as "Report a problem", when one goes to the same place, has the
  same id or sits where the old one was in the last recording that worked. Use it with
  **Use "Report a problem"** in the studio or `reshoot repair RUN --apply`.
  This works for any story, not only recorded ones. When it can't tell, it
  lists the controls of that kind the page has now.
- `reshoot accept demo/latest --export docs/demo` accepts the run and copies its
  video and GIF in one step. The README Markdown it prints describes the GIF
  with the task from `BRIEF.md`.

### Changed

- A finished run ends with its files and two next steps: keep it, or change it
  in the studio.

### Fixed

- `reshoot studio` starts on Python 3.11 again; 0.3.8's studio needed 3.12.
- The studio shows where each step plays after the project folder is moved or
  renamed, or for a run made elsewhere, such as in CI. A last step that takes
  no time shows its moment instead of "not in this cut".
- When the latest recording stopped, the studio's status says so, instead of
  "Accepted recording" for the last one that worked.
- On a slow machine, the start of a browser take is no longer cut from the
  video: recording waits for Chrome's first frame before the first step.
- A Chrome call that stalls during a take fails within 30 s and says what it
  was, and a take that runs over its timeout says which step it was on,
  instead of waiting 10 minutes and printing only `TimeoutError`.

## 0.3.8 (2026-10-25)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.8. Recorded drafts name their steps after what
they did, and the studio explains a failed result check and can remove it.

### Added

- Recorded steps are named after what they did, such as `click-albums` or
  `type-email`, instead of `action-1`.
- When a result check fails, the studio says in plain words what it expected
  and what the page showed, and offers **Remove this check**, with Undo.
- Before a first working recording, the studio shows only the story and what
  to do next, and says which steps have result checks still to run.

### Fixed

- `BRIEF.md` for a project made from a URL names the app and how to start and
  reset it, instead of the notes app, and uses paths as you'd type them.
- The recorder no longer suggests that a list a tab hid has 0 items: it counts
  hidden items as the replay does, and never suggests a count of none. A
  **Check result** on a large element checks the start of its words, not all of
  them.
- When Vision fails inside an agent's sandbox, such as Codex's, `reshoot doctor`
  and the scan say to run reshoot outside it before suggesting Tesseract.

## 0.3.7 (2026-10-25)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.7 and know `reshoot create`, repair and the
studio's new panels. Existing projects keep working; every new setting is
optional.

### Added

- `reshoot create [URL] --directory demo` makes a project, checks the tools,
  records a task you show with a toolbar, makes a preview and opens the studio.
  `--resume` continues after a setup fix; running it again opens the project.
- The recording toolbar: Done, Pause, Caption here, Check result, Hide and
  Remove last step. Checkbox and radio choices replay with a `check` action.
- `reshoot doctor --probe` tries encoding, a browser capture and the text scan
  on temporary made-up data.
- The studio, reworked: the story first, with holds; Update preview, which
  re-cuts or records as needed; Make final; Undo and Redo that survive a
  restart; a status line with the next step; and links to each section.
- Repair a step whose control changed: `reshoot repair RUN`, `--apply` for a
  checked suggestion, or `--pick` to choose the control in the app. The studio
  offers both.
- Styles: Focus, Midnight and Paper looks, saved and portable styles, with
  `reshoot style`.
- Your cut and `reshoot sequence`: trim, reorder, repeat or remove parts of the
  video by beat, while the recording still runs the whole task.
- Framing: Fit or Crop for each export, a viewing width, and hints about small
  or cut-off text, with `reshoot frame`. Recording view records a narrower take.
- Narration for each step, heard before recording, plus voice and music levels
  and music that drops under the voice, with `reshoot audio`.
- Screenshots for docs, made from checked steps on every run, with
  `reshoot screenshot`.
- Clickable tours: one offline HTML walkthrough of the checked steps, with
  `reshoot tour`.
- Compare in the studio shows an earlier run's result frames beside the current
  ones, step by step.
- Download all exports: a ZIP of the shown run's videos, screenshots, tour and
  subtitles.
- A studio page in the guide, and a tutorial that starts with `reshoot create`.

### Fixed

- On Macs whose Vision accurate text reader fails
  (`TextRecognition.CRImageReaderError 1`), the scan uses the fast reader and
  says so, and `reshoot doctor` tries Vision first.
- The studio's video, downloads and acceptance always refer to the run shown,
  even after another command makes a newer one.
- A studio edit no longer overwrites a change made in another tab or editor,
  and a field that fails to save stays visible until it's fixed.
- The recorder keeps its draft when it meets a step it can't replay, marking
  that step `recording_issue`.
- A cut can include a beat's result hold with `through`, and repeated beats
  play at the right place.
- Changing a frame background no longer changes the title cards.
- The studio's colour fields take the hex values they suggest.
- Videos no longer open on a blank frame.

## 0.3.6 (2026-10-24)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.6 and know the studio and `recut`. Runs on
0.3.6 draw TOML captions after recording, so evidence frames no longer show
captions, and the first comparison with a run accepted on 0.3.5 shows each
beat's frame as changed once.

### Changed

- `reshoot rec URL draft.toml` suggests result checks from what each action
  changed on the page: the words typed showing up in a list, a list getting
  shorter, a new address, a label that changed. Each is marked as a
  suggestion to keep or delete. The draft also ends with the `end` beat the
  generated edit needs.
- `reshoot review RUN --serve` accepts or rejects a run on its review page: a
  choice for each finding, a box to say you watched everything, and a button.
  It serves the page on `127.0.0.1` behind a random address, takes the decision
  only from that page, records it as `reshoot accept` does, and stops.
- After `accept`, the review page says the run is accepted, instead of still
  showing how to accept it.
- Export presets: `preset = "readme"`, `"x"`, `"linkedin"` and square and
  portrait versions set the size, format and frame rate, and fail the export
  when it breaks that platform's limits, read from each platform's own pages.
  New projects' README GIF uses `preset = "readme"`.
- A `[frame]` table in `edit.toml` puts each take in a browser-like window with
  a title bar, rounded corners and a shadow, on the `[style]` background, which
  can now be a gradient.
- `reshoot recut RUN` edits and scans a run's takes again into a new run, after
  a change to `edit.toml`, without starting the app or recording. The new run
  names the run it came from and keeps its result checks.
- TOML storyboard captions are drawn after recording, from the storyboard, on
  a take recorded without them (`NAME.clean.mp4`). A re-cut draws them again,
  so it can change their words and `[caption]` look; each keeps its beat's
  recorded time. Captions are now plain text on every TOML take, and evidence
  frames no longer show them, so a comparison with an older accepted run
  shows each beat's frame as changed once.

- `reshoot studio [PROJECT]` opens a page on this computer for shaping a demo:
  the latest run's video with its beats on a timeline, each beat's frame,
  result checks and caption, what the scan found, and the exports side by side
  with their platform limits. Captions and their look, title cards, the frame,
  music and export presets are saved to the storyboard and edit file as you
  edit, with `[check] sources` following the exports. Re-cut shows them on the
  same recording in seconds; a beat whose actions changed is marked and can be
  recorded again from that beat; Record records the run; and the run is
  accepted beside the beats.

## 0.3.5 (2026-10-24)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.5. To show findings in refresh pull requests,
copy the export step from `examples/github/refresh.yml` into your workflow.

### Changed

- The scan groups what it flags into findings: one email address on screen for
  a whole video is one finding, such as `F1`, not hundreds of frames to name.
  `accept --flagged F1` or `--reject F1` covers every frame it is in; a label
  such as `1-2` still names one frame.
- The review page reads in review order: the exports, each finding with its
  frame, the scan sheets as images, then the beats, with the run's other files
  folded into one list.
- `reshoot run --full` scans every frame this time, without editing the
  config. The tutorial uses it.
- Scan messages say to look at findings first and then look over the rest for
  what a scan can miss, instead of asking for every item at full size.
- A refresh pull request shows what to review without downloading anything:
  the GIF, a link to the MP4 on its branch, and each scan finding with its
  first frame, boxed in red. `reshoot export --markdown FILE --link URL` writes
  that part, and `--record` keeps the frames in `demo/accepted/findings/`, only
  for findings in the files it copies. Update the refresh workflow from
  `examples/github/refresh.yml`.
- The review page names the file and time each scan item comes from, such as
  `takes/demo-final.mp4 at 6 s`, instead of an opaque source ID.
- Every command's `--help` describes it with examples. `run --help` shows a
  complete versioned `reshoot.toml`, with the legacy format after it.
- An unknown field in `reshoot.toml`, a storyboard, a beat, an action or a
  target is named in the error, with the fields that are allowed.
- The guide has one start-here for each kind of reader, a page for teams
  (ownership, reviewing a refresh pull request, failure alerts, CI cost), a
  table of every field in the three project files, an index of error messages,
  and one word for each idea. The running-URL, build-a-demo and features pages
  are merged into the own-app, customize and index pages.

## 0.3.4 (2026-10-24)

Upgrade the project skills with `reshoot skills claude --directory . --replace`
(or `codex`): they now need 0.3.4.

### Fixed

- A higher pixel ratio records sharper video. Chrome's screencast had sent
  frames at the page's CSS size whatever the ratio, so `@2` was only scaled up
  and zoomed text went soft. Chrome now starts at the recording's pixel ratio;
  on the notes example at `960x540@2`, a sharpness measure of the same frame
  doubled. The odd short frames at the start of a take are gone too.

### Added

- [How the videos look](guide/look.md): the cursor, auto-zoom, captions,
  title cards, export shapes and GIF sizes, recorded from the notes example by
  `examples/look/build.py`.
- TOML storyboards get the cursor Python storyboards have: a glide that takes
  longer for longer trips, a press and a ring on each click, and typing at an
  uneven pace set by `seed`. A `[cursor]` table sets `size`, `typing` speed and
  `ripple`.
- `reshoot init` writes `demo/.gitignore`, which keeps recordings out of Git
  and the `demo/accepted/` record in.
- `reshoot export RUN --directory DIR` copies the run's videos, GIFs and video
  subtitles without naming each `--file`, and prints the README Markdown for
  the GIF. `accept` says how.
- Agents end a first demo with a fixed handoff: the exports, the checks,
  "reply accept, or ask for changes", and the accept command. The quickstart
  has a table of follow-up requests.

### Changed

- A run ends by saying what it made: its result checks, scan items and
  whether it is accepted, then the paths of the video, the GIF and the review
  page. A preview says to record the final; a final gives the accept command.
- A failed run prints its run folder, failure image and the app's output.
- The app's own output, such as a server's request log, goes to `app.log` in
  the run folder instead of between reshoot's lines.
- `reshoot compare --out` prints which beats matched and which changed their
  steps or results.
- The review page opens with one status line; the raw data is folded away.
- Previews sample frames even when `full = true`, so they stay quick.
- The tutorial uses `demo/latest` and `demo/accepted` instead of pasted run
  IDs, and exports to `docs/demo/`.
- The brief `init` writes gives the commands from the folder that holds
  `demo/`, and drops its note on review IDs and hashes.
- With no accepted run, the refresh skill compares against the newest final
  and says it was never accepted.
- The README leads with what reshoot is for, the install line and three
  commands, shows a storyboard, says how it differs from other tools and what
  to expect from the agent prompt, and has one table of where to go next.

- `reshoot accept` refuses a preview unless given `--preview`. The CI guide's
  `reshoot accept demo/latest` could commit a preview as the baseline.
- `reshoot skills` takes `--replace` to install the new version over skills
  already there, such as after an upgrade. The agent quickstart had told agents
  both to install skills after an upgrade and to keep the old ones.

### Fixed

- Docs that had drifted: the "no `select`" claims, the CLI 0.2 requirement in
  the project reference, the archive-by-ID baseline in the publishing guide,
  the skills' hedges about commands every supported CLI has, and the claim that
  zoomed text stays sharp at a higher pixel ratio.

## 0.3.3 (2026-10-23)

### Added

- `reshoot doctor` says when a newer release is on PyPI. `RESHOOT_OFFLINE=1`
  skips the check.

### Fixed

- A browser that cannot start says why it usually happens in an agent's
  sandbox, such as Codex's, instead of only Playwright's error.
- The skills require 0.3.2 and say how to upgrade, and the agent quickstart
  reuses an existing install only when it is the latest release. A cold Codex
  session had recorded a whole demo with a stale 0.2.0.
- Agents keep their changes in `demo/`: the quickstart and demo skill say not
  to edit the app's README or other files unless asked.

## 0.3.2 (2026-10-23)

### Added

- A `select` action chooses a dropdown option by its value or visible label,
  and `reshoot rec` writes one for each dropdown choice.

### Fixed

- A result could appear a whole hold late in the video while every check passed: the evidence screenshot after
  each beat could take the frame showing it. The evidence frame is now the last frame the video shows, saved at
  the end of the hold. Frame times also no longer depend on when the first frame arrives.
- Storyboard errors name the beat and the action or check, such as
  `beat 'fill', action 2 (key): target needs exactly one of css, test_id, or role`.
- The demo skill says to narrow the viewport or zoom when an app's content is
  too small to read in the README GIF.
- A port Chrome refuses, such as 5060, is explained with the flag that allows
  it, and a failure while opening the page no longer reports `beat None`.
- The demo skill and guides say how to write checks for apps that keep data
  between takes and have no reset.

## 0.3.1 (2026-10-23)

### Added

- `reshoot accept RUN` records the owner's verdict in one step: the exports,
  every beat, every scan item and the scan checklist, bound to the run's exact
  files and scan policy. Each flagged item must be named with `--flagged`, and
  `--reject` marks an item that must not be shared. It asks for confirmation,
  and without a terminal it refuses unless given `--yes`.
- `reshoot run` and `reshoot preview` write the review page and print the
  `reshoot accept` command for the run.
- `reshoot runs PROJECT` lists a project's runs, newest first, with their
  result and review status. Run paths accept `latest` (the newest successful
  run) and `accepted` (the newest accepted run), such as `demo/accepted`.
  Run reports record `finished_at`.
- A refresh pull request in CI. `examples/github/refresh.yml` records the demo
  when the app changes, compares it with the accepted run and opens a pull
  request with the new MP4, GIF and a beat table. Merging it accepts the
  recording.
- `reshoot accept` writes `demo/accepted/`, a small committed record of the run
  (report, beat results and evidence frames), so CI and fresh clones can
  compare against it. `reshoot export --record DIR` writes one for any run.
- `reshoot export --replace` updates media already in the destination, and
  `reshoot compare --markdown FILE` writes a summary for a pull request.
- In GitHub Actions, each run writes a job summary with its checks, scan and
  errors.

### Fixed

- `reshoot init` moves the notes example off port 8765 when something else
  is using it.
- A busy port names its loopback address instead of a redacted hash.
- `reshoot web --help` describes TOML storyboards, and `review`, `compare`
  and `export` explain their arguments.
- A target that matches no element, or several, names the target and the count.
- A run's report includes the failed beat's error, not only the failed step.

## 0.3.0 (2026-10-23)

The first release on PyPI. Install it with `uv tool install 'reshoot[browser]'`.

### Added

- Published to PyPI, with a release workflow that builds, checks and publishes
  each tagged version.
- An agent-first entry point: a first-demo prompt in the README, the agent
  quickstart and a skill catalog.
- Guides for each stage after the first recording: features, customizing,
  fuller demos and tutorials, publishing, CI and faster shoots.

### Fixed

- Review pages show baseline GIFs as images; MP4s keep their video players.
- Joined title cards no longer vanish or freeze in GIF exports.
- Clip joins keep an exact frame rate.
- Captions stay visible across same-origin page loads.
- Previews that mix web and VHS takes keep matching dimensions.
- Runs leave incomplete expectations unverified instead of passing them.
- `doctor` rejects a `RESHOOT_CHROME` that does not name a usable browser.

## 0.2.0

Repeatable demo projects: `reshoot.toml`, TOML storyboards with checked
expectations, `init`, `doctor`, `preview`, isolated versioned runs, `compare`,
`review` with bound decisions, `export`, and shared Claude Code and Codex skills
installed by `reshoot skills`. Installed from Git only.
