# The studio

The studio is a page on your computer for shaping a demo. It shows the latest
recording, lets you change its story and look by pointing, and is where you
review and accept the final. If first creation stops, it helps you correct the
story and continue. Your project files stay the source of truth: everything
you change in the studio is saved to them.

**Start with a story.** The studio doesn't write a story or
choose what to show. To make the first one, ask your
[agent](agent-quickstart.md), try the made-up notes app with `reshoot create`,
or [show the task yourself](your-app.md#show-the-task) in a simple web app.

## Open it

`reshoot create` opens the studio once it has made the first preview. To open
it for an existing project:

```bash
reshoot studio demo        # the folder holding reshoot.toml; demo is the default
```

It runs until you press Ctrl-C. `--no-open` prints the address instead of
opening it, and `--port 8800` picks the port. It listens on `127.0.0.1` only,
behind a random address, and takes changes only from its own page.

If a tool is missing when you create a project, **Recording tools** lists what
to install. Choose **Check again** once it's installed, then **Continue
creation**. From the terminal, `reshoot create --resume --directory demo` does
the same.

## Find your way

The line above the preview says where you are: unsaved fields, saved changes
not in the video yet, a current preview, or a final ready to review. It
highlights the next thing to do.

The links under it jump to **Preview**, **Story**, **Cut**, **Look**, **Review**
and **Download**. **More tools** holds **Compare**, **Audio**, **Screenshots**
and **Tour**. Before the first recording, only the story and creation tools
are shown.

## Change the story

The filmstrip under the video shows the story's steps. Choose one to open its
inspector beside the preview. Left and right arrow keys move between steps;
Home and End choose the first or last. The inspector shows that step's last
frame, result checks, caption, second line and hold.

- **Caption and second line:** change them and leave the field. They're saved
  to `storyboard.toml`, and the step says the change isn't in the video yet.
- **Hold result (seconds):** how long the result stays on screen. Raise it
  when a caption needs more reading time.
- **Narration:** open it under a step, write **Spoken words** and choose
  **Save narration**. **Audition saved line** plays it without starting the
  app. Clear the words and save to remove the line.

Choose a step's frame, a mark on the timeline or one of its fields to select
it. **Editing step** above the preview keeps that step named while you work.
**Play selected step** plays it; **Edit this step** returns to its fields.
Saved changes say when an update is still needed. The shown video keeps its
recorded words until you update it.

To change how a step is done, edit its actions in `storyboard.toml`, or record
the task again.

### Correct a failed result check

When a check fails, the studio explains what it expected and what appeared.
If the expected result is right, fix the app or its demo data. If the expected
result is wrong, change the expected count, text, field value, address or
ticked state and choose **Save expected result**. The control and neighboring
checks stay the same. Choose the continuation named on the page to verify it.
Change a check's target or kind in `storyboard.toml`.

If the check does not prove anything useful, open **Remove a check that is
not needed**, then choose **Remove this check**. **Undo** restores a correction
or removal. A saved correction still needs a new preview to pass.

## Update the preview, then make the final

**Update preview** makes a new preview and chooses the quickest way:

- Changes to captions, the look, the cut or audio levels reuse the recording.
  This takes seconds.
- Changes to actions, result checks, holds, narration, the recording size or
  declared demo `inputs` record the task again.

It says which it did, then shows the new run. **Cancel update** stops it and
keeps the previous video. Editing waits while an update is running.

Under **More**, **Re-cut** and **Record a preview** do one or the other
explicitly. Use **Record a preview** after a change the studio can't see, such
as a change to a remote app or its database.

**Record from here**, on a step, records from that step on, replaying the
earlier steps without recording them. A step whose actions, checks or hold
changed since the recording is marked in red.

When the preview looks right, **Make final** records the whole run at full
size. A preview is for looking at; accept a final.

## Undo, and edits made elsewhere

**Undo** and **Redo** cover every change you save in the studio, including a
style, a cut, a repair or a screenshot. They keep up to 50 changes.

The history survives a restart. When the files still match, the studio keeps
your Undo and Redo automatically so you can carry on editing.

You or an agent can edit the files while the studio is open. When you come
back to the page, it offers **Reload project**. If a field won't save, fix it or
choose **Reset unsaved edits** to reload the saved project.

If your files differ from saved editing history, the studio lists the changed
files and keeps them. **Download saved source copy** gives you the files as the studio last
saved them, so you can compare and copy over what you want by hand.
Choose **Start with current files** to begin a new history with those files.
The previous history stays in a local archive.

## Change the look

Open **Style and exports** once the story works.

- **Visual styles:** Focus keeps the app large; Midnight and Paper put it in a
  frame. **Save style** keeps the current look by name in `styles.toml`.
  **Download current style** makes a file that **Import a style** applies in
  another project.
- **Caption look:** top or bottom, background and text colours. Colours are
  hex values, such as `#ffffff`.
- **Title cards:** add an opening or closing card, reword it, set its seconds
  and colours, or remove it.
- **Frame:** put the app in a browser window, on a background colour or a
  two-colour gradient.
- **Exports:** change, add or remove an export by its preset, such as
  `readme` or `linkedin`. Each export is shown in its own shape, with its size
  and the limits of the place its preset is for. Each export is also added to
  the scan.

The look, cards, frame and exports are saved to `storyboard.toml` and
`edit.toml`, so a style keeps working without the style file.
[How the videos look](look.md) shows each setting in pictures.

### Fit an export to where it's shown

Under each export:

- **Framing:** Fit keeps the whole video and adds space around it. Crop fills
  the shape and can cut off part of the video. Click the crop guide, or set
  **Horizontal** and **Vertical position (%)**, to aim the crop.
- **Viewing width (px):** the width people will watch at. It doesn't change
  the file, only how the studio judges text size.

Choose **Save framing**, then **Update preview**. **Inspect at viewing size**
shows the export at that width, with hints about text that may be too small
or a crop that cuts off a caption or a result. The hints are a guide: look at
the export yourself.

If the app's text is too small, **Recording view** records the task again at a
compact or portrait size. A different layout may need a step repaired.

## Balance the sound

Open **Audio** to choose a **Voice** and a **Music track** from the project
folder. **Narration level** and **Music level** are percentages: 100% keeps the
original level and 0% mutes it. **Lower music while narration speaks** keeps the
voice clear. Choose **Save balance**, then **Update preview**, and listen to the
MP4.

The default voice is macOS `say`, or `espeak-ng` elsewhere. A custom voice is a
command you set in the storyboard, which runs with your permissions.

## Trim and arrange the video

**Your cut** lists the parts of the video: recorded clips and title cards.

- Choose a clip's **From beat** and **Through beat (included)**, then **Save
  range**. Through includes that step's result hold.
- **Earlier** and **Later** move a part, **Duplicate** repeats it, and
  **Remove** leaves it out. **Add clip to end** adds another range.

The recording still runs the whole task and all its checks; the cut only
chooses what the video shows. Choose **Update preview**, then **Play part** to
watch each part. Steps left out say **not in this cut**.

## Make screenshots for docs

Choose **Use for docs** beside a step with result checks. Write its **Alt
text**, a file name, and a maximum width if you want one, then **Save
screenshot**. **Crop** lets you drag a rectangle on the page; **Use whole
captured page** removes the crop.

After **Update preview**, the run has a PNG of that step's result. It's made
again on every run, scanned and reviewed with the video, so it stays current.
It shows the page as recorded, without the video's captions, zoom or frame.
Check the PNG and its alt text before accepting.

## Make a clickable tour

Open **Clickable tour**, give it a title and a file name, and choose **Create
from checked steps**. Each step shows a checked result, with a title, an
explanation and alt text.

- **Earlier**, **Later**, **Add step** and **Remove step** shape it.
- **Click marker:** click the image to place a numbered marker that the viewer
  clicks to go on. **Show a click marker** turns it on or off.

After **Update preview**, **Open walkthrough** opens the tour and **Download
HTML** saves it. It's one HTML file that works offline, with keyboard
navigation. It's made again on every run and scanned with the video.

## Compare with an earlier recording

Open **More tools**, then **Compare**. Choose **Earlier recording**; an accepted
run is offered first. Each side names its recording and links to its own review.

**Watch the exports** shows an exported MP4 or MOV from each recording. Choose
an export on each side, then **Play both** or **Pause both**. **Listen to**
chooses one side's audio or mutes both. The videos start together and keep
their own timing.

Choose **Step in the cut** to seek to that step on both sides. **Play step**
plays each appearance to its own end. Repeated appearances are paired by their
order in each cut; a side says when an appearance is absent. Older recordings
without saved cut timing still play with the video controls.

Below the videos, checked result frames show added, removed and changed steps.
These are the captured pages before later captions or edits. Comparing neither
accepts a recording nor switches the current recording when a newer one arrives.

## Repair a step that broke

When the app changes and a step can't find its control, the studio keeps the
last working video and shows the **Failure frame**.

- **Use "Report a problem"**, named after the control it found, appears when
  reshoot can tell what the control became: one that goes to the same place,
  has the same id, or sits where the old one was in the last recording that
  worked. It replays the earlier steps and checks the control before changing
  the step. When it can't tell, the message lists the controls of that kind
  the page has now.
- **Choose replacement in app** opens a fresh browser at the broken step. Click
  the control, then confirm it. Clicking it there doesn't press it.

For a failed **result check**, [review and correct its expected result](#correct-a-failed-result-check).

A repair changes only how the step finds its control. Its action and expected
result stay the same. Choose **Update preview** to check the whole task again.
If the result itself is wrong, fix the app, the demo data or the story, not
the check.

## Review and accept

Open **Review this recording**:

1. Watch the final MP4 and each export.
2. Open **Inspect scan sheets** and look at each sheet at full size. **What the
   scan found** marks each finding on the timeline.
3. Choose whether each finding may be shared, tick that you watched
   everything, and accept or reject the run.

This does what `reshoot accept` does. The studio accepts only the run shown on
the page, and only when every saved change is in it.

## Download

**Download all exports** gives you a ZIP of the shown run's videos, GIFs,
screenshots, tour and subtitles. It includes the Markdown for each image and a
list of the files with their review status. It leaves out your project files
and logs. **Download individual files** offers each one alone. Downloading
doesn't accept or publish anything.

## The same work from the terminal

Each studio change has a command. They take `--project demo`, and the numbers
for parts, takes, exports and steps start at 1. Run `reshoot recut demo/latest`
afterwards to see a change on the same recording, or `reshoot preview
demo/reshoot.toml` to record again.

| In the studio | Command |
|---|---|
| Visual styles | `reshoot style list`, `reshoot style apply midnight`, `reshoot style save "Launch look"` |
| Your cut | `reshoot sequence list`, `reshoot sequence range 1 --from add --through search` |
| Framing and viewing width | `reshoot frame set 1 --fit crop --x 50 --view-width 390`, `reshoot frame check demo/latest` |
| Recording view | `reshoot frame record --size 640x480@2` |
| Narration and balance | `reshoot audio set --beat search --text '...'`, `reshoot audio audition search` |
| Screenshots | `reshoot screenshot set search-result --beat search --alt '...'` |
| Clickable tour | `reshoot tour create --title '...'`, `reshoot tour set 1 --text '...'` |
| Repair | `reshoot repair RUN`, then `--apply` or `--pick` |
| Accept | `reshoot accept demo/latest` |
| Copy the exports | `reshoot export demo/latest --directory docs/demo` |

[Commands](commands.md) lists every option, and [the project
reference](projects.md) every field the studio writes.
