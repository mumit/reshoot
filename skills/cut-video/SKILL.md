---
name: cut-video
description: "Cut checked takes into a finished demo video with ffmpeg and the `reshoot.cut` helpers: trims at beat names, title and end cards, sped-up parts, a 9:16 version for phones, and one GIF per section. Use after the takes are recorded and checked."
---

# Cut the video

Each project has a short edit script, since the order of takes and the words on screen differ. Start from
`../../examples/notes/edit.py` (from this skill's folder) and copy it into the project. It joins a web take, a
terminal take on a labeled card, and an end card. Run it with `reshoot edit tools/demo/edit.py
takes/web.mp4`, which makes `reshoot.cut` importable even when reshoot is installed as a tool.

## The helpers

```python
from reshoot import cut

b = cut.beats("takes/web.mp4")                         # {beat name: seconds}
cut.trim(src, start, end, out, fade_in=0, fade_out=0.4)
cut.speed(src, start, end, 8, out)                     # 8x as fast
cut.still(png, 3, out)                                 # an image held 3 s, faded in
cut.place(bg_png, src, x, y, out, width=None)          # a video placed on a background
cut.vertical(src, bg_png, out)                         # 9:16, the video across the middle
cut.concat([a, b, c], out)                             # joined without encoding again
cut.gif(src, start, end, out, fps=15, width=800)
cut.last_change(take)                                  # when a terminal take finished
cut.window_clip(mov, bg_png, x, y, out, width=None)    # a window recording, cropped, corners rounded, on a card
cut.window_box(mov)                                    # (w, h, x, y) of a window in its shadow
cut.Card(1920, 1080, bg).text(None, 400, "Title", 112, 700).badge(None, 600, "8x speed").save(png)

said = cut.lines(take, start, end, offset)             # a take's voiceover lines in [start, end), moved to offset
cut.voice_track(said, wav, total)                      # those lines laid out on a track `total` seconds long
cut.add_audio(video, out, voice=wav, music=None, music_volume=0.25)   # music loops, fades, ducks under the voice
cut.write_srt(cut.cues(take, start, end, offset), srt) # subtitles: the voiceover, or else the captions
```

`cut.ff(...)` runs any other ffmpeg command. Every clip made by these is 60 fps H.264 in yuv420p with no sound.

## Steps

1. Keep all the words on screen at the top of the edit script, so they're easy to change.
2. Cut each web part at its beats: the take's own end beat is usually replaced by a proper end card.
3. Cut a terminal take at `cut.last_change`. Speed up the waiting part and label it ("8x speed").
4. Join the parts with `cut.concat`. They must all be the same size: a web take at 1280x720@1.5 is 1920x1080, a VHS
   take is its tape's `Width` and `Height`. Place smaller takes on a full-size card with `cut.place`.
5. Make the 9:16 version: the landscape video on a 1080x1920 card, with the name above and the link below.
6. Make one GIF per section, from beat to beat.
7. Add sound last, to the finished video: `cut.add_audio` with the voice track (if the storyboard had `VOICE`)
   and any music. Give each part's lines its place in the finished video with `offset`: a part that starts 12 s
   in uses `cut.lines(take, a, b, offset=12)`. Write subtitles the same way.
8. Watch the whole thing, with sound if it has any. Check the end card's spelling and link. Then give the person the files and say where they
   are. Don't post them.

## Pitfalls

- **Joining clips of different sizes** fails or looks wrong. `cut.concat` refuses them; make every part the same size.
- **Colors change when joined.** A clip in full color range (a camera clip, or one made outside these helpers)
  makes the clips after it look washed out. `cut.concat` refuses a mix; run such a clip through `cut.trim` first.
- **Odd sizes.** H.264 in yuv420p needs even widths and heights. Scale to `-2` (as the helpers do).
- **GIF colours.** The default palette bands badly. `cut.gif` makes a palette for each GIF.
- **Joined GIF sections.** `cut.gif` normalizes frames before building a palette from the full clip, preserving card/browser joins and static scene changes. Inspect the opening, ending and duration so an omitted or frozen section cannot pass on MP4 playback alone.
- **Fonts.** Cards use SF on macOS, and DejaVu Sans on Linux if installed.
- **Faststart.** Joined videos are written with `+faststart`, so they play in a browser before they finish loading.
- **Joining clips with sound.** `cut.concat` joins video only. Join the silent parts first, then add the sound.
- **Subtitles and burned-in captions.** Captions on screen can't be read by a screen reader or searched, so the
  `.srt` carries them too. With a voiceover, it carries what's said instead. Upload it with the video where the site
  allows.
- **Music you can use.** Only use music you have the right to post. Keep it quiet (`music_volume` 0.15 to 0.3).
- **Limits for posting.** Sites limit size and length, and change them. Check before uploading.

## Declarative edits

For beat trimming and ordering in a versioned project, use Your cut in the
studio or `reshoot sequence list --project demo`. Part and take numbers in
the CLI start at 1. `reshoot sequence range 1 --from add --through search --project demo`
includes the search beat and its hold. `sequence move 2 --to 1`, `sequence duplicate 1`,
`sequence remove 1` and `sequence add --take 1 --from intro --through add` accept
the same `--project demo`; keep at least one part. `--run RUN` selects a complete
successful run from that project. A file's `[[part]] take` still starts at 0.
It can use `start = "add"` and `through = "search"`; do not also set `end`.
An `end` beat is exclusive, while `through` includes that beat's end. Named
boundaries follow newly recorded timing. These edits preserve the full capture
task and checks. Update preview or re-cut a still-current recording, then inspect
the reordered MP4, GIF and subtitles. Never weaken checks to make a shorter cut
pass, or cut through a spoken line. Studio range choices must be saved or reset
before other edits; each operation supports Undo/Redo. Numeric custom ranges
and nested part tables remain available by editing the file.

For a versioned browser project, choose a reusable look with
`reshoot style list --project demo` and `reshoot style apply midnight --project demo`,
or use Visual styles in the studio's Style and exports. A style changes caption
placement, margin and colours, title-card colours and browser framing across
the project's TOML browser takes. It keeps the story, timing, fonts, logos,
audio, exports and scan settings. Update the preview and inspect app text and
caption overlap at the export size. `reshoot style save "Launch look" --project demo`
saves it in the project's library; `--out launch-style.toml` makes a portable
file for `reshoot style apply launch-style.toml --project another-demo`. Existing
names and files need `--replace`. Studio applies and saves are undoable together
with the other edits. Importing applies a portable style; Save style keeps it
in the new project. Use `recut` only when the existing recording is still current.

`reshoot edit EDIT.toml TAKE...` accepts schema-version-1 edit files with ordered `[[part]]` entries and output profiles. The packaged project provides an example. Cut helpers write `.timeline.json` mappings; trims, speed changes, placement, and concatenation retain source times. Speed changes need a visible label and cannot shorten narration. For a versioned project, after a change to `edit.toml`, a caption's words or the storyboard's `[caption]` look, `reshoot recut RUN` draws the captions again and edits and scans that run's takes into a new run without recording. Each caption keeps its beat's recorded time, so a change to actions or holds needs a new recording. An `[[export]]` can name a `preset`: `readme`, `readme-video`, `x`, `x-square`, `x-portrait`, `linkedin`, `linkedin-square` or `linkedin-portrait`. It sets the size, format and frame rate and fails the export when it breaks that platform's limits, which guide/projects.md lists with their sources; fields given override it. A `[frame]` table puts each take in a browser-like window with a title bar, rounded corners and a shadow, on the `[style]` background (a colour, or `[top, bottom]`); the page shrinks, so check its text is still readable. Explicit local copies use `reshoot export RUN --directory DIR --file PATH`; hashes must match the report, and existing destinations are not overwritten.

Declarative edits can use `trim_waits = true` for beats explicitly marked
`trim_wait = true` with a passed result check. Keep `min_reading` long enough to
read the result. Reshoot preserves speech and labels shortened waits.
