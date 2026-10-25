# Change and grow a demo

Make one small change at a time and record a preview to see it: a caption, a
hold, the cursor, an export size. Then, once the short clip works, grow it into
a fuller product demo or tutorial. [How the videos look](look.md) shows each
setting in pictures. Start with the project from your first browser demo, or
the bundled notes example:

```bash
reshoot init demo
reshoot preview demo/reshoot.toml
```

Keep the printed run folder as your original. Open its
`takes/demo-final.mp4` and `takes/demo-final-readme.gif`. Each preview below
creates another run, so the original stays available for comparison.

For the agent route, ask:

```text
Use the existing demo/ project. Show me where its captions, result holds and
export settings live. Change one caption and hold the result one second longer.
Keep the task and result checks. Record a preview and show both versions.
```

## Shape it in the studio

To see the whole demo and change it by pointing, open the studio:

```bash
reshoot studio demo
```

It opens a page on this computer with the latest run's video and its beats on
a timeline under it, green where the result checks passed. Each beat shows its
last frame, its result checks, and its caption and second line, ready to edit.
Click a beat to play just that part.

The status above the preview separates unsaved fields, saved changes waiting
for an update, a current preview and a final ready for review. It highlights
the next action. **Preview**, **Story**, **Compare**, **Cut**, **Look**, **Audio**,
**Screenshots**, **Tour**, **Review** and **Download** jump to their sections
without leaving the page. Open panels and unsaved fields stay in place.

If a field will not save, fix it or choose **Reset unsaved edits** to reload
the saved project. That resets every unsaved field, including fields in closed
panels. When you return from another editor, the studio checks for file changes
and offers **Reload project**. Reset local drafts first if both have changed.

- **Change a caption or result hold** and leave the field: it is saved to
  `demo/storyboard.toml`, and the beat says it is not in the video yet.
- **Change the caption look**, its place and colours, the same way.
- **Choose a visual style** under **Style and exports**: Focus keeps the app
  large; Midnight and Paper frame it. The sketches show the look; choose
  **Update preview** to see it on your video. Save a look by name, download it,
  or import a style from another project. Applying a style is one Undo step.
- **Shape the video in Your cut**: choose From and Through beats, save the
  range, move a part earlier or later, repeat it with Duplicate, or remove it.
  Add clip appends another recorded range. The storyboard still runs the whole
  task and its checks. Choose Update preview to see the new order.
- **Change the edit**: add, reword, time or remove an opening or closing title
  card, set card colours, turn the browser frame on and set its background or
  two-colour gradient, choose a music file
  from the project folder, and change, add or remove exports by preset. These
  are saved to `demo/edit.toml`, and `[check] sources` in `reshoot.toml` follows
  the exports, so each one is still scanned.
- **Update preview** chooses the work: caption and edit changes reuse the
  recording; changes to actions, checks, timing, settings or declared demo
  inputs record again. It says which work it chose and loads the new run.
- **Undo** and **Redo** restore studio edits, including changes to exports and
  their scan sources. Saved history survives a studio restart. A change in
  another tab or editor requires a reload and a recovery choice, preserving
  those edits.
- **Style and exports** holds caption colours, cards, framing and export
  presets. Open it when the story works. Colour fields take hex values.
- **Audio** holds voice choices and the music balance. **Use for docs** beside
  a checked step opens its documentation screenshot settings.
- **Record from here**, on a beat, starts the app, replays the beats before it
  off camera and records from that beat on, then shows that take. A beat whose
  actions, checks or hold changed since the recording is marked in red. When
  the take looks right, **Make final** records the whole run at full size.
- **Exports** shows each export in its own shape, with its size, length and
  file size, and the limits of the place its preset is for.
- **Frame a destination** under Style and exports: Fit keeps the whole video;
  Crop fills the shape. Aim the crop with its guide or position fields, set a
  viewing width, then Save framing and Update preview. Inspect at viewing size
  shows the rendered export at that width, with measured text and clipping hints.
- **What the scan found** marks each finding on the timeline. Open **Inspect
  scan sheets** and each sheet at full size before accepting. Media and the
  acceptance decision remain bound to the run shown, even if another command
  creates a newer run.
- **Cancel update** stops the current job and keeps the previous recording.
  Editing is paused while a job uses the project. Save errors stay visible so
  an unsaved change cannot look like a successful update.

**Download** offers a ZIP of the shown run's videos, GIFs, PNGs, offline tour
and video subtitles, plus image Markdown and a manifest of file hashes and
review status. Individual downloads remain available. The bundle excludes
project sources, app logs and review evidence. It stays bound to the shown
recording when another command makes a newer one; saved edits enter its files
only after updating the recording. Downloading does not accept or publish them.

The studio requires pending source edits to be rendered before accepting here.
Existing runs without the new source snapshot say **Earlier recording**; their
exact exports remain reviewable, but the studio cannot compare all sources.
The status compares declared project files and assets, not the running app.
Re-cuts retain the captured actions, holds, voice and demo data, so changing
those still requires a fresh capture even after an explicit re-cut.

**More** retains explicit Re-cut and Record a preview commands for advanced use.
For multiple takes or older recordings without the required metadata, Update
preview records again. Changes to a remote app or an external database cannot
be detected from the files: use More > Record a preview after those change,
even if you also edit captions. Declared `inputs` are checked automatically.

### Compare recorded revisions

Choose **Compare** in the section navigation. The studio opens **Compare
revisions** and loads the selected earlier recording beside the current one.
Choose **Earlier recording** to change the baseline; **Compare frames** reloads
the same pair. The picker offers up to 30 earlier complete local runs and
prefers an accepted one when available. Failed and partial captures are excluded.

Steps match by story and beat ID. Added and removed steps stay visible. Labels
show changes in the frame file, task definition and recorded result details.
Each image needs a complete TOML browser take with passing result checks and
hashes binding its metadata and PNG to the run. Missing or unchecked frames
have an explanation instead of a substitute image. Duplicate story/beat IDs
are rejected so the studio cannot pair the wrong takes.

**Open frame at image size** shows the original PNG. On narrow screens the two
sides stack. **Open review evidence** opens that side's exports and scan evidence.
Both sides retain their run IDs and bindings even if another command creates
a newer run. A changed artifact or scan requires a reload. Comparison does not
change sources, record a new take or accept either run.

These are captured result frames with their privacy masks. They do not include
captions drawn later, zoom, framing, cards or the final cut. A changed file hash
does not measure visual difference or establish correctness. Watch the exports
and inspect both scan reports as part of review. Only local runs with their
media are available here; a committed record without media and legacy takes
without checked browser evidence cannot provide these frames.

### Resume an editing session

After restarting the studio, choose **Resume history** to keep the saved Undo
and Redo steps. This choice is available only when the tracked files still
match the saved session. **Start with current files** begins an empty history
and archives the previous checkpoint. Neither choice replaces current files.
Editing, recording and acceptance wait until you resolve recovery; the displayed
media and its downloads remain available.

If files changed in another editor, the studio lists their names and keeps
them. **Download saved source copy** gives you the checkpoint's source files
for comparison, grouped in numbered folders to avoid name collisions. It is
unreviewed project source. Apply any wanted changes deliberately in your editor,
reload, then choose Start with current files. Source files that the studio
tracks, including an optional style library, stay grouped in one Undo step.

History holds up to 50 saved changes in a checkpoint of at most 32 MB under
`demo/takes/studio/`. Checkpoints and archives remain local and ignored by the
generated project's Git rules. Corrupt checkpoints can be archived by starting
fresh. A storage error says when source edits saved but their history could
not be stored; reload to inspect the current files and recovery choices.
Two studio servers cannot silently overwrite newer history.

Unsaved fields, running jobs and browser panel state are not part of this
checkpoint. An interrupted edit may leave saved source newer than its history;
recovery preserves that source and offers the last saved copy. This is not an
atomic transaction across several source files.

### Repair a changed control

After a failed recording, the studio keeps the previous working video and
shows the failure frame above it. When the recorded alternatives agree on one
replacement, **Use suggested control** replays the earlier steps and rechecks
that control before changing the locator. Otherwise choose **Choose replacement
in app**: a fresh browser replays to the broken step, then lets you select the
control and confirm **Use this control**. Selecting it does not activate it.

The repair keeps the action and expected result values. Undo and Redo also
cover repairs made from the studio. Choose **Update preview** afterwards to
verify the original task; the failed run stays failed. Closing or cancelling
the picker keeps the storyboard unchanged. A source or settings change since
the failure requires another preview before repair. An incorrect result needs
the app, fixture or story corrected, without weakening its result check.

The prefix replay uses the demo app and its configured reset. Use resettable
synthetic data, as for recording. Visual selection currently supports the main
page; repair iframe targets in the storyboard. Handwritten count queries also
stay in the storyboard because selecting one element would change their meaning.

The files stay the source of truth: edit them by hand or ask an agent while the
studio is open, and reload the page to see the change. Actions and result checks
are changed in the storyboard itself; holds are also editable in the studio. The studio serves on
`127.0.0.1` behind a random address, takes changes only from its own page, and
runs until you press Ctrl-C.

## Make an offline clickable tour

Open **Clickable tour** in the studio, give it a title and file name, then
choose **Create from checked steps**. The initial tour uses the first browser
take's steps that have result checks. Each step shows the captured result,
with a title, explanation and image alt text. Save changes and choose
**Update preview** to build it.

Use **Earlier**, **Later**, **Remove step** and **Add step** to shape the tour.
Save/Reset protects drafts; Undo/Redo reverses saved changes. In **Click marker**,
click the image to position a numbered marker, or use the horizontal and
vertical percentage fields. **Show a click marker** turns it on or off. A
marker advances to the next step, or restarts the tour at the last step.
Next, Back and keyboard navigation remain available without markers.

The preview offers **Open walkthrough** and **Download HTML**. The file embeds
its images, styles and navigation and works offline when moved to another
folder. It has no app connection or external assets: interactions move between
captured screens. Titles and explanations are plain text. The viewer supports
arrow keys, Home/End, focus movement to the new heading and a step counter.
Without JavaScript, all steps remain readable by scrolling.

The CLI offers the same edits; step and take numbers start at 1:

```bash
reshoot tour create --title 'Save and find a note' --project demo
reshoot tour set 1 --text 'The saved note appears in the list.' \
  --x 50 --y 44 --project demo
reshoot tour move 2 --to 1 --project demo
reshoot recut demo/latest
reshoot export demo/latest --directory docs/demo
```

`reshoot tour title --title 'Find your saved notes' --project demo` changes
the title; `set 1 --no-marker` removes a marker. `tour add --take 1 --beat search`
adds another checked step, and `tour remove 2` removes one while retaining at
least one. These commands also take `--project demo`. `tour disable` stops
producing the tour in future runs; previously copied HTML files remain yours
to remove.

A re-cut builds the tour from the existing recording's checked result frames.
Record again after the app changes to refresh its images. The source images
retain page privacy masks and possibly the cursor; video captions, zoom and
framing are not added. Advanced step `width` and `crop` settings use the same
downsize and fractional crop rules as documentation screenshots. Markers are
relative to the displayed step image, so inspect them after a crop changes.

The run includes tour images in configured scanning and scans titles,
explanations and alt text directly when detection is enabled. Review every
step and marker in the actual HTML, then inspect the scan evidence. A checked
result does not certify the description, privacy or usability of a tour.
`export` copies the HTML with other final exports; an explicit `--file` list
must include `tours/NAME.html`. Its images need no separate copied folder.
Refresh records, Markdown and comparisons include the walkthrough, and the
review page can show the previous one alongside it. Nothing is published.

## Keep documentation screenshots current

Choose **Use for docs** beside a story step that has result checks. Describe
the visible result in **Alt text**, choose a stable file name and optionally a
maximum width, then **Save screenshot**. **Update preview** makes a PNG from
that beat's captured result frame and includes it in scanning and review.
Screenshot settings live in `reshoot.toml`; Save/Reset and Undo/Redo work as
they do for the video. Saved changes leave the displayed run's PNGs intact
until the preview updates.

The PNG is the captured page viewport after the result hold. It retains
privacy masks and can include the recorded cursor. It does not add the video's
captions, camera zoom or decorative frame, and it does not capture content
outside the viewport. A maximum width downsizes without enlarging the source.
Inspect the actual PNG, its crop and its alt text before accepting the run.
A passing result check does not establish readability or privacy. After saving
a selection, open its **Crop** controls to drag a rectangle on the captured page
or enter percentages. **Use whole captured page** resets the crop. Save and
update the preview to inspect the resulting PNG at image size.

The CLI selects the same images, with take numbers starting at 1:

```bash
reshoot screenshot set search-result --beat search \
  --alt 'Search shows the saved bike note' --width 960 --project demo
reshoot recut demo/latest
reshoot export demo/latest --directory docs/demo
```

The export copies configured PNGs with the videos and prints image Markdown.
To copy just one, add `--file screenshots/search-result.png`. Existing files
are protected; use `--replace` deliberately to refresh them. The studio's PNG
gallery also offers local downloads. Nothing is published.

`reshoot screenshot list --project demo` lists selections;
`reshoot screenshot remove search-result --project demo` stops producing one in
future runs. Previously copied files and Markdown references remain yours to
remove. `--native` removes a width limit, and `--full-frame` removes cropping.
For a crop, give left, top, width and height as fractions of the captured page:

```bash
reshoot screenshot set search-result --crop 0.1 0.05 0.8 0.7 --project demo
reshoot recut demo/latest
```

A re-cut uses the original result frame and retains its original checks, even
if the selected beat is omitted from the video cut. A new recording refreshes
both the video and PNGs from the same task. A missing frame, partial take or
beat without passing result checks fails the run rather than producing an
apparently verified screenshot. Crop coordinates are relative to the page;
review them again after a responsive layout changes.

The [refresh workflow](ci.md) stages these PNGs in the same pull request as the
video. The review page shows them at full image links, and comparison reports
identify added, removed, changed or unchanged named screenshots. Pixel changes
can include cursor movement or rendering noise; inspect the images yourself.

## Audition narration and balance audio

Under a story step, open **Narration**, enter **Spoken words**, and choose
**Save narration**. Choose **Audition saved line** to hear it without starting
the app. Its player shows the line's duration. The recording reuses the same
cached audio. Keep each line short enough to fit the point of the step.
Clear its words and save to remove it. Reset discards unsaved words; Undo and
Redo reverse saved narration, voice and balance changes.

Open **Audio** to choose a local voice and a music track already in the project.
The initial voice is the system default: macOS `say`, or `espeak-ng`/`espeak`
elsewhere. Installed voices appear when the tool can list them. A custom
project voice remains available; edit its command in the storyboard or CLI.
Custom commands run with the project's permissions and handle their own service
credentials. Only choose a command you intend to run.

Set **Narration level** and **Music level**, then **Save balance**. A level of
100% keeps the source level, 50% halves its amplitude, and 0% mutes it.
**Lower music while narration speaks** keeps the voice prominent; turn it off
for a constant music level before the ending fade. A muted narration still
keeps its timing and subtitles. Mix peaks are limited before encoding, which
does not replace listening or normalize perceived loudness.

Choose **Update preview** and listen to the video. Changing spoken words or the
voice records the task again so every beat can wait for its line. Balance or
music changes re-cut the existing recording when the story is current. The
task, expected results, scan sources and acceptance process stay the same.
GIFs have no audio. Auditions are listening samples, outside the run's media
review; review the rendered MP4 and subtitle text before accepting a final.

The same edits work from the CLI:

```bash
reshoot audio set --beat search --text 'Find the matching note.' --project demo
reshoot audio audition search --project demo
reshoot audio set --music-volume 0.15 --voice-volume 1 --duck --project demo
reshoot preview demo/reshoot.toml
```

Mix settings are ordinary `edit.toml` fields:

```toml
[audio]
voice_volume = 1
music_volume = 0.15
duck = true
```

`reshoot audio` and the studio edit the first TOML browser take. For other takes,
edit their storyboard's `voice` and `voice_engine` fields directly. The mix
applies to the whole video, including repeated narration lines after sequencing.

## Reuse a visual style

In the studio, choose **Style and exports**, pick a starting look, then refine
its colours. **Save style** keeps the current look in this project's
`styles.toml`. Names must differ from the starting styles and existing saved
styles. Undo also reverses saving a style. **Download current style** makes a
portable TOML file; **Import a style** applies it in another project. An import
does not add it to the saved list until you choose **Save style**.

The same operations work from the command line:

```bash
reshoot style list --project demo
reshoot style apply midnight --project demo
reshoot recut demo/latest
reshoot style save "Launch look" --project demo
reshoot style save "Launch look" --project demo --out launch-style.toml
reshoot style apply launch-style.toml --project another-demo
```

`another-demo` must already be a versioned project. A saved name becomes a
key such as `launch-look`, shown by `style list`. Existing saved names and
export files are kept unless the CLI receives `--replace`.

Styles set caption placement, margin and colours, title-card colours, and
browser-frame settings across all TOML browser takes in the project. They
keep fonts and logos, the story, holds, checks, narration, music, exports and
scan settings. The values are written into the ordinary storyboard and edit
files, so rendering does not depend on the style library afterwards. If takes
have different looks, saving uses the first browser take's caption look.

For a current recording with editable captions, **Update preview** reuses the
recording. From the CLI, use `recut` only when the app, story and recording
settings still match that run; otherwise record a new preview. Check caption
contrast, overlap and app text at the actual export size, especially after
framing. The [gallery](look.md#visual-styles) shows the starting looks on notes.

## Trim and arrange the video

Open **Your cut** in the studio after recording a complete preview. Each part
is a recorded clip or a title card. For a clip, choose **From beat** and
**Through beat (included)**, then **Save range**. Through includes that beat's
result hold. **Reset** discards an unsaved range; pending choices block updates
and other edits until saved or reset.

Use **Earlier** and **Later** to change the order, **Duplicate** to repeat a
part, or **Remove** to leave it out of the video. Keep at least one part. Add
another range with **Add clip to end**, choosing its recorded take. **Edit title
card** opens its words and duration under Style and exports. Undo and Redo
restore each change in one step, and stale tabs preserve newer edits.

Choose **Update preview** to render the saved cut. A current recording is
reused; changes to the task, timing or app inputs still record again. **Play
part** then plays each part at its new position. Repeated beats appear at each
position on the timeline; the story lists their appearance count, and omitted
beats say **not in this cut**. Checks still describe the full recorded task.

The CLI uses the same operations. Part, take and position numbers start at 1:

```bash
reshoot sequence list --project demo
reshoot sequence range 1 --from search --through search --project demo
reshoot sequence add --take 1 --from intro --through add --project demo
reshoot sequence duplicate 1 --project demo
reshoot sequence move 3 --to 2 --project demo
reshoot recut demo/latest
```

On the notes project, this shows the result, its creation steps, then the result
again. `reshoot sequence remove 2 --project demo` removes the second video part. The
storyboard's actions, captions, holds and expected results remain unchanged.
These operations need a complete successful run from the project; `--run RUN`
selects an older one. Record a new preview to choose newly added beats.

The edit stores named boundaries, so they follow a fresh recording's timing:

```toml
[[part]]
take = 0
start = "add"
through = "search"
```

`take` in the file starts at 0, matching the edit's input arguments. Existing
`end = "search"` stops at the start of search; `through = "search"` includes
its end. Use one or the other. Numeric boundaries remain available in the file;
a custom boundary stays intact until you explicitly save a named range.
Nested custom part tables also stay in the file. Cuts cannot split a narration
line. Repeated clips retain captions, subtitles and complete narration at
their new times. Watch the [gallery example](look.md#beat-cuts-and-sequence)
and both exports before keeping the edit.

## Frame and inspect a destination

Under **Style and exports > Exports**, choose a destination preset, then its
framing. **Fit** keeps the whole video and adds space when the shapes differ.
**Crop** fills the destination and can remove content. Click the crop guide to
aim it, or set horizontal and vertical position: 0 is left or top, 50 is centre,
and 100 is right or bottom. The guide comes from the currently rendered video;
**Update preview** renders the saved choice across the whole cut.

Set **Viewing width (px)** to the width at which people will watch. This changes
inspection and text-size estimates, not the encoded dimensions. Save framing
before updating; Reset discards unsaved choices. The operation supports Undo
and Redo and preserves the story, checks, timing, audio, exports and scan
coverage. Changing a destination preset keeps framing and viewing preferences,
export names and configured size/reading budgets.

In the rendered **Exports**, choose **Inspect at viewing size**. The player or
GIF keeps that width even if the panel needs scrolling. Its feedback describes
the rendered run; update the preview after changing settings. The review page
also includes the run's measured hints.

Measurements include sampled app font sizes at result holds, caption and title
text sizes, subtitle reading rate, and whether a crop crosses a caption box,
title text or checked-result bounds. Text sizes account for the browser frame
and export scaling. A result already outside the recorded page is identified
separately: Fit cannot restore something the recording did not show.

The hints use 12 px for small app-text samples, 14 px for caption/title text,
and 18 characters per second for subtitle reading time. These are editing
heuristics, not a readability or accessibility pass. App samples cover main-page
text at result holds, without storing its content. Iframe, canvas, scaled or
rotated text, custom placement and app text under camera zoom need visual
inspection. Caption geometry is still measured after camera zoom. At most 30
individual hints are listed. Colour contrast and every animation frame are
not measured.

If app text is small, **Recording view** offers wide, compact and portrait
layouts for the first browser take. Save the view and choose Update preview;
this records the full task again with its existing checks. A changed responsive
layout may need a locator repair. The choices set viewport dimensions, not a
device identity. Old recordings need a fresh preview for app-font samples;
re-cutting can refresh caption measurements.

The CLI uses export numbers starting at 1:

```bash
reshoot frame set 1 --fit crop --x 50 --y 50 --view-width 390 --project demo
reshoot recut demo/latest
reshoot frame check demo/latest
reshoot frame record --size 640x480@2 --project demo
reshoot preview demo/reshoot.toml
```

Use `recut` only for a still-current recording. A change to recording size,
timing or the task needs a new capture. The [gallery](look.md#destination-framing-and-readability)
shows how a crop can cut off content and how the measured sizes change.

## Find the files

| File | Change it to |
|---|---|
| `demo/BRIEF.md` | Describe the audience, task and visible result |
| `demo/storyboard.toml` | Change actions, captions, result checks or holds |
| `demo/edit.toml` | Change cuts, title cards or export dimensions |
| `demo/styles.toml` | Keep named visual styles for reuse; created by Save style |
| `demo/reshoot.toml` | Change startup, take paths or check coverage |

These are the files generated for browser projects. For native recordings,
edit the [standalone capture recipe](macos-window.md) and its numeric cuts;
there is no browser storyboard to replay.

## Change the words

In the notes project's `storyboard.toml`, change the `intro` beat's caption to:

```toml
caption = "Find the note you need"
```

Save the file and record another preview:

```bash
reshoot preview demo/reshoot.toml
```

Watch the first seconds of the new MP4. The caption changes; adding the note
and finding it still perform the same task. In your own project, choose one
caption that explains the result rather than naming the click.

## Give the result time

In the same file, find the `search` beat. Change its `hold` from `2.0` to `3.0`:

```toml
hold = 3.0
```

Record another preview and compare the matching-note result. The browser waits
for its explicit checks, then holds the successful result for an extra second.
Use a hold for reading time and a result check to wait for the app.
Do not hide a real service delay by speeding it up without a visible label.

## Change the cursor

The cursor glides to each control, presses down with a ring on each click, and
types at an uneven pace. To make it larger in a small GIF, or type faster, add
this to the top of `demo/storyboard.toml`, above the first `[[beat]]`:

```toml
[cursor]
size = 1.5     # times the default arrow
typing = 20    # characters a second; the default is 13
```

`ripple = false` leaves out the ring. Record another preview to see it.

## Change only the edit, quickly

Title cards, music, the frame, the cuts and the exports are all in
`demo/edit.toml`, which works on what was already recorded. After changing only
that file, skip the recording:

```bash
reshoot recut demo/latest
```

It edits and scans the latest run's takes again, into a new run, in seconds.
It also draws the captions again, so a re-cut picks up new caption words and
a new `[caption]` look in `storyboard.toml`. A caption still shows for as long
as its beat did in the recording: to give a longer caption more time, raise
the beat's `hold` and record again.

## Frame it like a browser window

Add this to `demo/edit.toml`, above the first `[[part]]`:

```toml
[style]
background = ["#2a3f5f", "#101826"]   # a gradient, top to bottom; or one colour

[frame]
```

Each take then sits in a window with a title bar, rounded corners and a soft
shadow, on that background. The page shrinks to fit, so check that its text is
still easy to read. [How the videos look](look.md#a-browser-frame) shows it
and its settings.

## Change a destination

In `demo/edit.toml`, make the README GIF smaller. The `readme` preset makes an
800x450 GIF and checks it against GitHub's 10 MB limit; a field you give
overrides the preset's:

```toml
[[export]]
preset = "readme"
width = 640
height = 360
```

Replace that existing export table; do not append a second export with the same
name. To add a clip for X or LinkedIn, add another export with
`preset = "x"` or `preset = "linkedin"`; the
[presets](projects.md#export-presets) check each platform's limits. Record another preview. Compare the GIF at its actual size: smaller text
may need a tighter task or different framing. Keep the MP4 as the fuller version.
See [export profiles](projects.md#edittoml) for crops, frame rates and
size limits. Fitting a wide page into portrait dimensions does not make a
readable mobile demo.

## Keep the changes that help

Look at each change before adding the next. Keep the task and its result checks
the same while adjusting how it looks. If you change the actions, change the
result checks on purpose and explain the new story in the brief.

Once you choose, record a fresh `reshoot run demo/reshoot.toml` and look at the
final MP4, GIF and scan sheets. A preview is for looking at, not for accepting.

## Grow it into a fuller demo

Expand a working clip only when each extra section helps the viewer. Write the
audience, starting state and visible result in `BRIEF.md`, and decide whether
the video shows why a feature matters or how to use it. A product demo leads
with the result and keeps setup short. A tutorial includes the steps a viewer
must repeat and holds menus and result text long enough to read.

| Section | Show | Result check |
|---|---|---|
| Start | A list with several demo notes | The target is hard to spot |
| Create | Add "Prepare the release notes" | The saved note appears |
| Find | Search for "release" | Only the matching note remains |
| Finish | Hold the result and say what to do next | The result stays readable |

Keep each section small enough to record again on its own, with a stable beat
ID. For native apps, save the starting document and the steps, and check the
visible result yourself: there are no automatic result checks there.

To have the agent do it:

```text
Expand the existing demo/ into a short tutorial of creating an item and finding
it by search. Read its brief and current recording first. Use synthetic data.
Keep the working task and result checks; add only the context needed to follow
it. Use clear captions, readable result holds and a short closing instruction.
Inspect previews, record a fresh final, and show the MP4 and README GIF.
```

Add the audience, destination and length when you know them. Ask for narration
only when it explains something; the video should still make sense muted.

### Add a title card

`demo/edit.toml` picks beat ranges from the takes, joins them and adds cards.
This version opens the notes demo with a title:

```toml
schema_version = 1
output = "demo-final.mp4"

[[part]]
card = "Save a note. Find it again."
duration = 1.5

[[part]]
take = 0
start = 0
end = "end"

[[export]]
preset = "readme"
```

Replace the notes project's edit with it and record another preview. For your
own story, use its beat names. Every edit field, music and card styling is in
the [project reference](projects.md#edittoml). The [manual workflow](manual.md)
covers Python edits, narration and VHS terminal takes; match terminal and
browser take sizes when joining them. The [promo recipe](../examples/promo/README.md)
is a before-and-after video built this way.

### Finish for the viewer

Watch the full MP4 and every shorter GIF or crop. Check that captions name the
outcome, text fits, typing is legible and the result stays on screen. Say so
when a response is mocked or a wait was shortened. Check narration against the
picture, and read the subtitles when there are any.

Next: [keep the demo current and share it](publish.md).
