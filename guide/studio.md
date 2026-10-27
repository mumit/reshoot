# The studio

The studio is a local page for changing a demo by pointing, then accepting the
final. Every change is saved to the project's files. For a first story, ask your
[agent](agent-quickstart.md), run `reshoot create` for the notes app, or
[show the task yourself](your-app.md#show-the-task).

## Open it

`reshoot create` opens it after the first preview. For an existing project:

```bash
reshoot studio demo        # the folder holding reshoot.toml; demo is the default
```

`--no-open` prints the address; `--port 8800` picks the port.

A first preview shows "Your first demo is ready", with **Download the video**,
**Download the GIF** and **Copy readme Markdown**.

In the notes app, **Change the notes app and record again** renames the search
box, so the recording stops at the search step for you to
[repair](#repair-a-step-that-broke). **Put the app and story back** undoes the
trial.

If a tool is missing, **Recording tools** lists what to install. Choose
**Check again**, then **Continue creation**, or run
`reshoot create --resume --directory demo`.

## Find your way

The line above the preview highlights the next thing to do. The links under the header jump to Preview, Story, Cut, Look, Review and
Download; **More tools** holds Compare, Audio, Screenshots, Tour and Recipes.

Beside the preview, **This step** edits the selected step. **Whole video**
holds **Starting recipes**, **Audio**, **Documentation screenshots**,
**Clickable tour**, **Your cut** and **Style and exports**.

## Choose a starting recipe

Under **More tools**, **Recipes**:

- **Feature highlight:** one result in about 15 seconds, Focus look, MP4 and GIF.
- **Task walkthrough:** explained steps in about 45 seconds, Paper look, MP4 and subtitles.
- **Release update:** opening, task and result in about 25 seconds, Midnight look, MP4 and GIF.

Enter an optional card title and choose **Apply recipe**. It changes holds,
caption colours, the frame and exports, and keeps your actions, checks, cut
and cards.

## Change the story

Choose a step in the filmstrip under the video, or use the arrow keys.
**This step** shows its last frame, result checks and fields:

- **Caption** and second line: saved when you leave the field.
- **Hold result (seconds):** how long the result stays on screen.
- **Narration:** write **Spoken words** and choose **Save narration**.
  **Audition saved line** plays it. Clear the words and save to remove it.
  [Kokoro voices](install.md#local-neural-narration) appear after installing;
  restart the studio if it was open.

**Play selected step** plays it.

### Show a changed step

Open **Change actions by showing them** and choose **Replace this step’s
actions** or **Add step after this** (**Add step before ending** on the last
step). Chrome opens and replays the earlier steps. Do just the new actions
with demo data, using **Check result** for the result, then choose **Done**.
Review the draft and choose **Use these actions** or **Discard draft**.
Replacing keeps the step's words, timing and result checks.

Change iframes, popups, file selection, drops, passwords and blurs in the story
file. Add a new step to a custom cut under **Your cut**.

### See layout changes as you edit

Editing a caption, colours, frame or crop shows a **layout still** of the
step as the video will draw it. **Preview shape** picks the main video or an
export; **Show recorded video** returns to playback.

### Correct a failed result check

The studio shows what a failed check expected and what appeared. If the
expectation is right, fix the app or data; if not, change it and choose
**Save expected result**. If the check proves
nothing useful, open **Remove a check that is not needed** and choose
**Remove this check**. Change a check's target or kind in `storyboard.toml`.

## Update the preview, then make the final

**Update preview** re-cuts the recording in seconds after a change to
captions, the look, the cut or audio levels. After a change to actions, result
checks, holds, narration, the recording size or declared `inputs`, it records
the task again. **Cancel update** keeps the previous video.

**Record app again** records the whole task, for a change the studio can't
see, such as to a database. **Record from here**, on
a step, records from that step on.

When the preview looks right, **Make final** records the full-size run you accept.

## Undo, and edits made elsewhere

**Undo** and **Redo** cover every saved change, up to 50, and survive a restart.

If the files change while the studio is open, it offers **Reload project**.
If a field won't save, choose **Reset unsaved edits**. If the files no longer
match the studio's history, **Download saved source copy** gives its last
saved files, and **Start with current files** begins a new history.

## Change the look

Open **Style and exports**:

- **Visual styles:** Focus keeps the app large; Midnight and Paper frame it.
  **Save style** keeps the look by name in `styles.toml`; **Download current
  style** makes a file for **Import a style** in another project.
- **Caption look:** top or bottom, and hex colours such as `#ffffff`.
- **Title cards:** add, reword, time, colour or remove an opening or closing card.
- **Frame:** a browser window, on a colour or a two-colour gradient.
- **Exports:** change, add or remove an export by preset, such as `readme`.

[How the videos look](look.md) shows each setting.

### Fit an export to where it's shown

Under each export:

- **Framing:** Fit adds space around the video; Crop fills the shape and can
  cut part off. Click the crop guide, or set **Horizontal** and **Vertical
  position (%)**.
- **Viewing width (px):** the width people watch at, used to judge text size.

Choose **Save framing**, then **Update preview**. **Inspect at viewing size**
shows the export at that width, with hints about small text or a bad crop. If the app's text is too small, **Recording
view** records again at a compact or portrait size; a step may then need repair.

## Balance the sound

In **Audio**, choose a **Voice** and a **Music track**.
**Narration level** and **Music level** are percentages; 0% mutes.
**Lower music while narration speaks** keeps the voice clear. Choose **Save
balance**, then **Update preview**. The default voice is macOS `say`, or
`espeak-ng` elsewhere.

## Trim and arrange the video

**Your cut** lists the clips and title cards.

- Choose a clip's **From step** and **Through step (included)**, then **Save range**.
- **Earlier** and **Later** move a part, **Duplicate** repeats it, **Remove**
  leaves it out and **Add clip to end** adds another range.

Every step and check still runs. After **Update preview**, **Play part**
plays each part.

## Grow it into a fuller demo

Add a part only when it helps the viewer. A product demo leads with the
result; a tutorial holds each step long enough to repeat. Keep each step small,
with a stable ID, and the video clear when muted. Start from the **Task
walkthrough** or **Release update** recipe, or ask an agent:

```text
Expand the existing demo/ into a short tutorial of creating an item and finding
it by search. Read its brief and current recording first. Use synthetic data.
Keep the working task and result checks; add only the context needed to follow
it. Use clear captions, readable result holds and a short closing instruction.
Inspect previews, record a fresh final, and show the MP4 and README GIF.
```

## Make screenshots for docs

Choose **Use for docs** beside a step with result checks. Write its **Alt
text**, a file name and an optional maximum width, then **Save screenshot**.
**Crop** lets you drag a rectangle; **Use whole captured page** removes it.
Every run then makes a PNG of that step's result, without captions, zoom or
frame, and scans it with the video.

## Make a clickable tour

Open **Clickable tour**, give it a title and file name, and choose **Create
from checked steps**. Give each step a title, explanation and alt text.
**Earlier**, **Later**, **Add step** and **Remove step** shape it. Click the
image to place a numbered **click marker**; **Show a click marker** turns it
on or off. After **Update preview**, **Open walkthrough** opens it and
**Download HTML** saves the single offline file.

## Compare with an earlier recording

Open **More tools**, then **Compare**, and choose an **Earlier recording**; the
accepted run is offered first. Under **Watch the exports**, choose an export on
each side, then **Play both** or **Pause both**. **Listen to** picks a side's
audio. **Step in the cut** seeks both sides to a step, and **Play step** plays
it. Below, checked result frames show added, removed and changed steps.

## Repair a step that broke

When a step can't find its control, the studio shows the **Failure frame**:

- **Use "<name>"** appears when reshoot can tell what the control became. It
  checks the control on the current app, then changes how the step finds it.
- **Choose replacement in app** opens a browser at the broken step. Click the
  control there, which doesn't press it, and confirm.

The action and expected result stay the same. Then choose **Update preview**.

## Review and accept

Accepting says the video shows the task clearly and nothing in it is private.
A clean scan decides neither. Open **Review this recording**:

1. Watch the final MP4 and each export to the end: captions, text size, typing,
   the result, subtitles and narration.
2. Open **Inspect scan sheets** and look at each sheet at full size, flagged
   images first, for names, accounts, keys, file paths or people.
   **What the scan found** marks each finding on the timeline.
3. Choose whether each finding may be shared, tick that you watched
   everything, and accept or reject.

This writes [`demo/accepted/`](publish.md#the-accepted-run). If something is
private, reject the run, fix the data or story, and record again.

## Download

**Download all exports** gives a ZIP of the run's videos, GIFs, screenshots,
tour, subtitles and Markdown. **Download individual files** offers each alone.

## The same work from the terminal

Commands take `--project demo` and number parts, exports and steps from 1.
Run `reshoot recut demo/latest` or `reshoot preview demo/reshoot.toml` after.

| In the studio | Command |
|---|---|
| Visual styles | `reshoot style list`, `style apply midnight`, `style save "Launch look"` |
| Your cut | `reshoot sequence list`, `sequence range 1 --from add --through search` |
| Framing | `reshoot frame set 1 --fit crop --x 50 --view-width 390`, `frame check demo/latest` |
| Recording view | `reshoot frame record --size 640x480@2` |
| Audio | `reshoot audio set --beat search --text '...'`, `audio audition search` |
| Screenshots | `reshoot screenshot set search-result --beat search --alt '...'` |
| Clickable tour | `reshoot tour create --title '...'`, `tour set 1 --text '...'` |
| Repair | `reshoot repair RUN`, then `--apply` or `--pick` |
| Show a changed step | `reshoot step record search`, `step show DRAFT`, `step apply DRAFT` |

[Commands](commands.md) lists every option, and [the project
reference](projects.md) every field.
