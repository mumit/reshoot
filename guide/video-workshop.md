# Make a web app demo, then keep it current

Follow one useful task from demonstration to refreshed exports. The workshop
uses the made-up notes app: save "Pick up the bikes," then find it by "bike."
All data is synthetic. The same steps work with a simple web app running on
your computer.

The [video recipe](../examples/tutorial/README.md) builds the narrated
workshop, a short first-demo excerpt, subtitles, a transcript and a chapter
player on your computer. It leaves every recording pending your review.

## Before starting

[Install reshoot](install.md), including its browser and video tools. Start
your app with its normal development command and demo data, and use the
address it prints. The notes app needs no account and resets on reload. A
fresh browser profile doesn't reset your app's database, so write down how to
reset its demo data before you count on repeatable recordings.

To try the notes app without starting a server:

```bash
reshoot create --recipe feature --directory notes-demo
```

That starts with a prepared story. To follow the video, serve the notes app
yourself. `reshoot init notes-app` makes a folder holding the app's page;
serve that folder:

```bash
reshoot init notes-app
python3 -m http.server 8765 --bind 127.0.0.1 --directory notes-app
```

Leave that server running. In another terminal, show the task:

```bash
reshoot create http://127.0.0.1:8765/ --directory demo
```

For your own app, use its development address instead. If port 8765 is busy,
pick another and use it in both commands. Use a new directory for each
project. reshoot checks its tools and opens a fresh browser.
[Recording tools](studio.md#open-it) helps if setup needs attention.

## Record one task

In the recorder's browser, add the note and press Enter. Choose **Check
result**, then click the saved note. Search for "bike," add "Find the
matching note" with **Caption here**, and check the matching note.

Choose **Done**. reshoot saves the story and records its preview. The toolbar
stays out of the video. If it suggests result checks, keep the ones that prove
your task worked.

## Read and shape the preview

Watch the video in the studio. Passing checks prove the results you named;
you still judge whether the video explains them well.

Choose **Type search notes** in the filmstrip. Change its caption to "A note
found in a moment" and leave the field; the layout still shows the new words.
Set **Hold result** to 3 seconds, then try **Undo** and **Redo**. Choose
**Update preview** and **Play selected step** to judge the pause in the video.
[The studio guide](studio.md#change-the-story) explains layout stills and
selection.

## Change a step by showing it

In the search step, open **Change actions by showing them**, then choose
**Replace this step's actions**. The earlier steps replay in a fresh browser.
Type "bikes" and choose **Done**.

Compare **Current actions** and **Proposed actions**. Choose **Use these
actions** when the change is right, or **Discard draft**. The caption, hold
and result checks stay. Update the preview to check the whole task, and use
**Undo** if you change your mind. The same panel can add a step; see
[step demonstrations](studio.md#show-a-changed-step) for their limits.

## Add polish

Choose **Midnight** under **Look**. In the step's **Narration**, write "Find
the note you saved by typing one of its words" and save it. Add an opening
card saying "Find a note in seconds." Update the preview and watch it.

The workshop's own narration is a local synthetic voice. Your demo keeps its
spoken line in its exported MP4; the workshop talks over the studio footage
instead, so the two voices don't overlap.

## Refresh after an app change

The workshop changes its copy of the notes app: the search box's id goes from
`q` to `note-search`, and the heading becomes "Notes, refreshed."

The studio can't see changes to a running app, so choose **Record app
again**. The new recording stops at the search step, and the previous good
video stays available.

Look at the suggested **Search notes** control and use it if it's right.
**Choose replacement in app** lets you pick another. Then update the preview.
See [repair](studio.md#repair-a-step-that-broke).

Open **More tools → Compare** and choose the polished recording. Play both, or
pick a step to jump both to it. Comparing doesn't accept either recording.

## Finish and keep the source

Choose **Make final**. Watch the final MP4 and each export, open the scan
sheets, and read what the scan covered. A scan samples frames and can miss
things; you decide whether to accept the recording.

**Download all exports** gives you the files from the recording on screen.
Downloading doesn't accept or publish them. Keep the project beside your app,
so the next recording starts from your choices.

For an app with a login, database setup or complex interactions, follow
[your own web app](your-app.md) or the [agent quickstart](agent-quickstart.md).
The [command reference](commands.md) and [studio guide](studio.md) cover each
task on its own.
