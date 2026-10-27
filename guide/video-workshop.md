# Make a web app demo, then keep it current

The companion to the video workshop: one task in the made-up notes app, from
showing it to a refreshed export. Save "Pick up the bikes," then find it by
"bike." The [video recipe](../examples/tutorial/README.md) builds the narrated
workshop on your computer.

## Before starting

[Install reshoot](install.md). Then serve the notes app and leave it running:

```bash
reshoot init notes-app
python3 -m http.server 8765 --bind 127.0.0.1 --directory notes-app
```

In another terminal:

```bash
reshoot create http://127.0.0.1:8765/ --directory demo
```

For your own app, use its address and demo data, and know how to reset them.
If port 8765 is busy, use another in both commands.

## Record one task

In the browser that opens, add the note and press Enter. Choose **Check
result** and click the saved note. Search for "bike," choose **Caption here**
and write "Find the matching note," then check the matching note. Choose
**Done**. Keep only suggested checks that prove the task worked.

## Read and shape the preview

Choose **Type search notes** in the filmstrip. Change its caption to "A note
found in a moment" and leave the field. Set **Hold result** to 3 seconds, then
try **Undo** and **Redo**. Choose **Update preview**, then **Play selected
step**.

## Change a step by showing it

In the search step, open **Change actions by showing them** and choose
**Replace this step's actions**. Type "bikes" and choose **Done**. Compare
**Current actions** and **Proposed actions**, then choose **Use these
actions** or **Discard draft**. Update the preview.

## Add polish

Choose **Look**, then **Midnight** under **Visual styles**. In the step's
**Narration**, write "Find the note you saved by typing one of its words" and
save it. Add an opening card saying "Find a note in seconds." Update the
preview and watch it.

## Refresh after an app change

The workshop renames the search box from `q` to `note-search` and the heading
to "Notes, refreshed." Choose **Record app again**; the studio can't see a
running app change. The recording stops at the search step. Choose **Use
"Search notes"**, or **Choose replacement in app**, then update the preview.

Open **More tools**, then **Compare**, choose the polished recording and
**Play both**.

## Finish and keep the source

Choose **Make final**. Watch the MP4 and each export, open the scan sheets,
and [accept it](studio.md#review-and-accept) if it's right. **Download all
exports** gives you the files. Keep the project beside your app.

For a login, database setup or complex interactions, see
[your own web app](your-app.md) or the [agent quickstart](agent-quickstart.md).
