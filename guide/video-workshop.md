# Make a web app demo, then keep it current

Follow one useful task from demonstration to refreshed exports. The workshop
uses the made-up notes app: save “Pick up the bikes,” then find it by “bike.”
All data is synthetic. The same URL-based workflow works with a simple web app
running on your computer.

The [video recipe](../examples/tutorial/README.md) builds the narrated workshop,
short first-demo excerpt, subtitles, transcript and chapter player locally.
The lesson leaves every recording pending owner review.

## Before starting

[Install reshoot](install.md), including its browser and video tools. Start
your app with its normal development command and a separate demo environment.
Use the address that app prints. The notes app needs no account and resets
on reload. A fresh browser profile does not reset your app's database; document
its demo data and reset routine before promising repeatable results.

To try the bundled notes project without starting a server yourself:

```bash
reshoot create --recipe feature --directory notes-demo
```

That starts with a prepared story. To demonstrate your own task instead, use
the running app's URL:

```bash
reshoot create http://127.0.0.1:3000/ --directory demo
```

Replace the address, and use a new directory for a new project. Reshoot checks
the tools and opens a fresh browser profile. [Recording tools](studio.md#open-it)
helps you continue if setup needs attention.

## Record one task

In the recorder's browser, add the synthetic note and press Enter. Choose
**Check result**, then select the saved note. Search for “bike,” add “Find the
matching note” with **Caption here**, and check the matching result.

Choose **Done**. Reshoot saves the story and records its preview. Toolbar
controls stay out of the generated demo. Inspect any suggested result checks
that need attention; keep the ones that prove your task's result.

## Read and shape the preview

Watch the video in Studio. Passing checks confirm the expectations you named;
you still judge whether the story and visual result make sense.

Choose the search step in the filmstrip. Change its caption to “A note found
in a moment” and leave the field. The layout still helps you judge the words
and placement. Increase **Hold result** to 3 seconds, try **Undo**, then
**Redo**. Choose **Update preview** and **Play selected step** to judge the
timing in the actual video.

Under **Style and exports**, inspect framing and viewing width. Check the
result at the size your audience will see. [The Studio guide](studio.md#change-the-story)
explains layout stills and selection; [framing](studio.md#fit-an-export-to-where-its-shown)
covers Fit, Crop and text measurements.

## Demonstrate a replacement

In the search step, open **Change actions by showing them**, then choose
**Replace this step’s actions**. Earlier actions replay in a fresh browser.
Type “bikes” and choose **Done**.

Review **Current actions** and **Proposed actions**. Choose **Use these
actions** when the change is right, or **Discard draft**. The original words,
timing and result checks stay. Update the preview to verify the complete task.
**Undo** restores an applied change. The same panel can add a step; see
[step demonstrations](studio.md#show-a-changed-step) for their current limits.

## Add useful polish

Choose **Midnight** under **Look**. In the selected step's **Narration**, write
“Find the note you saved by typing one of its words,” save it and audition it.
Add an opening card saying “Find a note in seconds.” Update and watch the
rendered result. Use speech and cards where they help explain the task.

The tutorial uses a disclosed local synthetic voice. The demonstration's
own spoken line is included in its exported MP4; the workshop narration
continues over the interface footage so the voices do not compete.

## Refresh after an app change

The workshop changes only its copy of the notes app: the search control's ID
changes from `q` to `note-search`, its script uses that new ID, and the heading
becomes “Notes, refreshed.”

For a project pointing at a running URL, choose **More → Record a preview**
after changing the external app. Studio cannot automatically detect every
remote or external file change. The new recording stops at the old search
target while keeping the previous good video available.

Inspect the suggested **Search notes** control and use it if it is right.
**Choose replacement in app** lets you select another. Keep the useful result
checks, then update the preview. See [repair](studio.md#repair-a-step-that-broke).

Open **More tools → Compare** and choose the earlier polished recording.
Compare corresponding steps, their results and their appearance. Each side
keeps its own recording and timing. The workshop compares pending recordings;
it does not accept either one.

## Finish and keep the source

Choose **Make final**. Watch the final MP4 and each export, open the scan
sheets, inspect findings and read the coverage. A sampled scan can miss frames;
automatic checks do not approve your media. Make your own acceptance decision
after reviewing this exact recording.

**Download all exports** gives you the displayed run's files. Downloading
does not accept or publish them. Keep the project source beside your app and
retain its accepted record when you choose to accept a final.

For an app with login, database setup or complex interactions, follow
[your own web app](your-app.md) or use the [agent quickstart](agent-quickstart.md).
The [command reference](commands.md) and [Studio guide](studio.md) support
individual tasks without replaying the whole workshop.
