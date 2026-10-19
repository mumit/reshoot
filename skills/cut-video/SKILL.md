---
name: cut-video
description: "Cut checked takes into a finished demo video with ffmpeg and the `reshoot.cut` helpers: trims at beat names, title and end cards, sped-up parts, a 9:16 version for phones, and one GIF per section. Use after the takes are recorded and checked."
---

# Cut the video

Each project has a short edit script, since the order of takes and the words on screen differ. Start from
`../../examples/notes/edit.py` (from this skill's folder) and copy it into the project. It joins a web take, a
terminal take on a labelled card, and an end card. Run it with `reshoot edit tools/demo/edit.py
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
7. Watch the whole thing. Check the end card's spelling and link. Then give the person the files and say where they
   are. Don't post them.

## Pitfalls

- **Joining clips of different sizes** fails or looks wrong. `cut.concat` refuses them; make every part the same size.
- **Odd sizes.** H.264 in yuv420p needs even widths and heights. Scale to `-2` (as the helpers do).
- **GIF colours.** The default palette bands badly. `cut.gif` makes a palette for each GIF.
- **Fonts.** Cards use SF on macOS, and DejaVu Sans on Linux if installed.
- **Faststart.** Joined videos are written with `+faststart`, so they play in a browser before they finish loading.
- **Limits for posting.** Sites limit size and length, and change them. Check before uploading.
