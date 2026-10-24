# How the videos look

Every picture here comes from the bundled notes example, recorded by
[`examples/look/build.py`](../examples/look/build.py). Each one changes a
single setting, shown beside it. Run the script again to bring the page up to
date.

## The cursor

The cursor glides along a slight curve, taking longer for longer trips,
presses down with a ring on each click, and types at an uneven pace. It is
drawn on the page, so it is in every recording without editing.

![The cursor gliding to the note field, a ring spreading on the click, then typing](../docs/look/cursor.gif)

```toml
[cursor]       # in storyboard.toml; these are the defaults
size = 1       # 0.5 to 3 times the arrow
typing = 13    # characters a second
ripple = true
```

## Auto-zoom

With `zoom = true`, the camera follows the action after recording: it starts
moving before a click, so it lands as the click happens, eases in on a
critically damped spring, stays put through short pauses, and pulls back when
something changes elsewhere on the page. Captions are drawn after the zoom, so
they stay where they are.

![The notes demo with auto-zoom, following typing and the search](../docs/look/zoom.gif)

| `zoom` off | `zoom = true` |
|---|---|
| ![Typing the search without zoom](../docs/look/zoom-off.jpg) | ![Typing the search, zoomed in](../docs/look/zoom-on.jpg) |

The page is recorded at up to twice its pixel ratio while zoom is on, so text
stays sharp as it zooms in. For larger text without zoom, use a narrower
viewport, such as `size = "960x540@2"`.

## Captions

Captions sit at the bottom by default. A `[caption]` table sets their colors,
margin, font and minimum time on screen, and `position = "top"` moves them up,
which suits apps whose content sits low; check that they don't cover a
heading.

| Default | Styled |
|---|---|
| ![A dark caption at the bottom](../docs/look/caption-bottom.jpg) | ![A light caption set higher](../docs/look/caption-styled.jpg) |

```toml
[caption]
background = "#f4f1ea"
foreground = "#1d1b18"
margin = 0.12
```

## Title cards

A `card` part in `edit.toml` adds a still title, colored by `[style]`, which
can also set a font and a logo.

![A title card reading "Notes, now with search"](../docs/look/card.jpg)

```toml
[style]
background = "#1d3b53"
foreground = "#f4f1ea"

[[part]]
card = "Notes, now with search"
duration = 2
```

## Shapes

An `[[export]]` profile makes another size from the same recording.
`fit = "contain"` fits the whole frame in, so the text shrinks; `fit = "crop"`
fills the shape from the middle, so the text stays large but the edges go. For
a portrait video people read on a phone, record a narrower viewport, or a take
of its own.

| 16:9 | 4:5, fit = "contain" | 4:5, fit = "crop" |
|---|---|---|
| ![16:9 export](../docs/look/shape-wide.jpg) | ![4:5, fit = "contain" export](../docs/look/shape-contain.jpg) | ![4:5, fit = "crop" export](../docs/look/shape-crop.jpg) |

```toml
[[export]]          # in edit.toml
name = "crop"
format = "mp4"
width = 1080
height = 1350
fit = "crop"
```

## GIF size

A README GIF is made with its own palette. `max_bytes` in an export profile
fails the export if the file comes out larger, so a GIF never silently grows
past a page's limit. The notes example's loop:

| Width | File |
|---|---|
| 800 wide (the default) | 340 KB |
| 640 wide | 236 KB |

## Sound

A voiceover is spoken before recording, so each beat waits for its line.
Music plays under it and ducks while someone speaks, then fades out at the end.
See [Build the story and edit](make-demo.md).
