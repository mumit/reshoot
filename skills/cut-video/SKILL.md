---
name: cut-video
description: "Cut checked takes into a finished demo video with ffmpeg and the `reshoot.cut` helpers: trims at beat names, title and end cards, sped-up parts, a 9:16 version for phones, and one GIF per section. Use after the takes are recorded and checked."
---

# Cut the video

## Declarative edits

A versioned project cuts its takes with `edit.toml`: ordered `[[part]]` entries (a beat range of a take, or a title card) and `[[export]]` profiles. `reshoot init` writes an example, and the guide's `projects.md` lists every field. `reshoot edit EDIT.toml TAKE...` runs one by itself.

- **Ranges.** A part takes `start` and either `end` or `through`, by beat name. `end = "search"` stops where that beat starts; `through = "search"` includes it and its hold. Named boundaries follow a new recording's timing. A file's `take` starts at 0. A cut never splits a spoken line.
- **Order.** `reshoot sequence list --project demo` shows the parts; `range`, `move`, `duplicate`, `remove` and `add` change them (numbers start at 1 there). The recording still runs the whole task and all its checks. Never weaken a check to make a shorter cut pass.
- **Exports.** An `[[export]]` can name a `preset`: `readme`, `readme-video`, `x`, `x-square`, `x-portrait`, `linkedin`, `linkedin-square` or `linkedin-portrait`. It sets the size, format and frame rate and fails the export when it breaks that platform's limits; fields you give override it.
- **Framing.** `fit = "crop"` fills the shape and `focus = [x, y]` aims it; Fit keeps the whole video. `display_width` is the width people watch at. `reshoot frame set 1 --fit crop --x 50 --y 50 --view-width 390 --project demo` sets these. `reshoot frame check RUN` reads hints about small text, clipped captions and subtitle pace. They are heuristics, not a readability pass, and a missing measurement is not a pass: inspect the MP4 and GIF at viewing size. To enlarge app text, record a narrower view with `reshoot frame record --size 640x480@2 --project demo` and a fresh preview.
- **Look.** A `[frame]` puts each take in a browser-like window on the `[style]` background (a colour, or `[top, bottom]`); the page shrinks, so check its text. `reshoot style list` and `reshoot style apply midnight --project demo` set captions, card colours and the frame together, keeping the story, timing, audio, exports and scan. `reshoot style save NAME --project demo` saves the look, and `--out FILE` makes a portable style for another project.
- **Sound.** `[audio]` sets `voice_volume` (0 to 2), `music_volume` (0 to 1) and `duck`. `reshoot audio set --music-volume 0.15 --duck --project demo` saves them. The mix limits peaks; that is not loudness normalization. Muted narration keeps its timing and subtitles. Changing narration words or the voice needs a new recording; `reshoot audio audition BEAT --project demo` plays a line first.
- **Waits.** `trim_waits = true` shortens beats marked `trim_wait = true` that have a passed result check. Keep `min_reading` long enough to read the result. Speed changes need a visible label and never shorten narration.

After a change to `edit.toml`, a caption's words or the `[caption]` look, `reshoot recut RUN` draws the captions again and edits and scans the same takes into a new run, without recording. Each caption keeps its beat's recorded time, so a change to actions or holds needs a new recording. Use `recut` only while the recording is still current. `reshoot export RUN --directory DIR` copies the exports, checking their hashes and never overwriting a file.

The studio does the same edits by pointing; the owner uses it, not you.

## Python edits

For a cut the declarative edit can't express, write an edit script. Start from `../../examples/notes/edit.py` (from this skill's folder): it joins a web take, a terminal take on a labelled card, and an end card. Run it with `reshoot edit tools/demo/edit.py takes/web.mp4`, which makes `reshoot.cut` importable even when reshoot is installed as a tool.

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
cut.add_audio(video, out, voice=wav, music=None, music_volume=0.25, voice_volume=1, duck=True)  # loops, fades, limits mix peaks
cut.write_srt(cut.cues(take, start, end, offset), srt) # subtitles: the voiceover, or else the captions
```

`cut.ff(...)` runs any other ffmpeg command. Every clip these make is 60 fps H.264 in yuv420p with no sound, and each helper records where its output came from, so subtitles keep their timing. An ffmpeg edit of your own needs its own map.

1. Keep all the words on screen at the top of the script, so they're easy to change.
2. Cut each web part at its beats; the take's own end beat is usually replaced by a proper end card.
3. Cut a terminal take at `cut.last_change`. Speed up the waiting part and label it ("8x speed").
4. Join the parts with `cut.concat`. They must be the same size: a web take at 1280x720@1.5 is 1920x1080, a VHS take is its tape's `Width` and `Height`. Place smaller takes on a full-size card with `cut.place`.
5. Make the 9:16 version: the landscape video on a 1080x1920 card, with the name above and the link below.
6. Make one GIF per section, from beat to beat.
7. Add sound last, to the finished video: `cut.add_audio` with the voice track and any music. Place each part's lines with `offset`: a part that starts 12 s in uses `cut.lines(take, a, b, offset=12)`. Write subtitles the same way.

## Finish

Watch the whole video, with sound if it has any, and every GIF: its first frames, last frames and length. Check the end card's spelling and link. Then give the person the files and say where they are. Don't post them.

## Pitfalls

- **Clips of different sizes** don't join: `cut.concat` refuses them.
- **Colours change when joined.** A full-range clip, such as a camera clip, makes later clips look washed out. `cut.concat` refuses a mix; run such a clip through `cut.trim` first.
- **Odd sizes.** H.264 in yuv420p needs even widths and heights. Scale to `-2`, as the helpers do.
- **Joining clips with sound.** `cut.concat` joins video only. Join the silent parts, then add the sound.
- **Fonts.** Cards use SF on macOS, and DejaVu Sans on Linux if installed.
- **Subtitles.** Captions on screen can't be read by a screen reader or searched, so the `.srt` carries them too; with a voiceover, it carries what's said. Upload it with the video where the site allows.
- **Music you can use.** Only use music you have the right to post, and keep it quiet (0.15 to 0.3).
- **Limits for posting.** Sites limit size and length, and change them. Check before uploading.
