# How the videos look

Every picture comes from the notes example, recorded by
[`examples/look/build.py`](../examples/look/build.py), which also writes this
page. Each changes one setting.

## Clickable tour

The checked notes task as one offline HTML walkthrough. The numbered marker
and arrow keys move between result screens.

![The notes walkthrough with a numbered marker on the saved result](../docs/look/tour.jpg)

[Download the notes walkthrough](../docs/look/notes-tour.html) and open it in a
browser. [Make one](studio.md#make-a-clickable-tour) in **Clickable tour**.

## Documentation screenshots

A checked result frame as a PNG: the visible page, without the video's
caption, zoom or frame. The cursor may show.

![Search shows the saved bike note](../docs/look/docs-search.png)

See [documentation screenshots](studio.md#make-screenshots-for-docs).

## Visual styles

A style sets caption colours and placement, title-card colours and the
browser frame. The framed styles shrink the app slightly, so check text at the
exported size.

| Focus | Midnight | Paper |
|---|---|---|
| ![Focus, with dark captions and the page filling the video](../docs/look/caption-bottom.jpg) | ![Midnight, with a blue gradient and browser frame](../docs/look/style-midnight.jpg) | ![Paper, with a warm frame and light captions](../docs/look/style-paper.jpg) |

```bash
reshoot style apply midnight --project demo
reshoot recut demo/latest
```

[Save your own](studio.md#change-the-look) for other projects.

## Beat cuts and sequence

The result, then how the note was made, then the result again. The app still
runs once, in order. `through` includes the last step and its hold; `end`
stops at the named step's start.

![The result first, the creation steps, then the result repeated](../docs/look/sequence.gif)

```toml
[[part]]
take = 0
start = "search"
through = "search"

[[part]]
take = 0
start = "intro"
through = "add"

[[part]]
take = 0
start = "search"
through = "search"
```

**Your cut** in the studio edits these; see
[trim and arrange the video](studio.md#trim-and-arrange-the-video).

## The cursor

The cursor glides on a slight curve, rings on each click, and types at an
uneven pace.

![The cursor gliding to the note field, a ring spreading on the click, then typing](../docs/look/cursor.gif)

```toml
[cursor]       # in storyboard.toml; these are the defaults
size = 1       # 0.5 to 3 times the arrow
typing = 13    # characters a second
ripple = true
```

## Auto-zoom

With `zoom = true`, the camera follows the action, landing as each click
happens and pulling back when something changes elsewhere. Captions stay put.

![The notes demo with auto-zoom, following typing and the search](../docs/look/zoom.gif)

| `zoom` off | `zoom = true` |
|---|---|
| ![Typing the search without zoom](../docs/look/zoom-off.jpg) | ![Typing the search, zoomed in](../docs/look/zoom-on.jpg) |

For larger text without zoom, use a narrower viewport, such as
`size = "960x540@2"`.

## Captions

A `[caption]` table sets colours, margin, font and minimum time on screen.
`position = "top"` suits apps whose content sits low.

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

A `card` part in `edit.toml` adds a title, coloured by `[style]`, which can
also set a font and logo.

![A title card reading "Notes, now with search"](../docs/look/card.jpg)

```toml
[style]
background = "#1d3b53"
foreground = "#f4f1ea"

[[part]]
card = "Notes, now with search"
duration = 2
```

## A browser frame

A `[frame]` table in `edit.toml` puts each take in a window on the `[style]`
background, one colour or a gradient. The page shrinks, so frame only a
recording with large enough text.

![The notes demo in a browser window on a blue gradient](../docs/look/frame.jpg)

```toml
[style]
background = ["#2a3f5f", "#101826"]

[frame]
padding = 0.06   # each side, as a fraction of the width; these are the defaults
radius = 12      # corner radius in pixels
shadow = true
bar = true       # the title bar with three dots
```

## Shapes

An `[[export]]` makes another size. `fit = "contain"` fits the whole frame,
so text shrinks; `fit = "crop"` fills the shape and loses the edges. For a
phone, record a narrower viewport.

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

The `x`, `linkedin` and `readme` [presets](projects.md#export-presets) also
check a platform's limits.

## Destination framing and readability

A crop can be aimed, and can cut off a caption or result:

| Centre crop | Right-biased crop |
|---|---|
| ![Centre crop of the notes result](../docs/look/shape-crop.jpg) | ![Right-biased crop cutting off part of the result and caption](../docs/look/shape-right.jpg) |

```toml
[[export]]
name = "crop-right"
width = 1080
height = 1350
fit = "crop"
focus = [0.85, 0.5]
display_width = 390
```

`focus` runs from 0 (left or top) to 1 (right or bottom). `display_width`
only changes how text size is judged. Measured here:

| Export | Viewing width | Small app-text samples | Smallest caption text |
|---|---|---|---|
| contain | 640 px | 7.0 px | 14.5 px |
| crop | 640 px | 15.6 px | 32.2 px |
| crop-right | 390 px | 10.8 px | 19.6 px |

These are hints, not proof of readability; look at zoomed, iframe or canvas
text yourself. See [destination framing](studio.md#fit-an-export-to-where-its-shown),
or run `reshoot frame check demo/latest`.

## GIF size

`max_bytes` in an export fails it if the file comes out larger. The notes loop:

| Width | File |
|---|---|
| 800 wide (the default) | 333 KB |
| 640 wide | 236 KB |

## Sound

Each step waits for its voiceover line. Music ducks under speech and fades at
the end. See [balance the sound](studio.md#balance-the-sound).
