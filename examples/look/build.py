"""Record the notes example a few ways and write guide/look.md, the gallery of how reshoot's videos look.

    uv run python examples/look/build.py

Each variant changes one setting. The frames and clips go to docs/look/, and the page is written from what was
recorded, so run this again whenever the cursor, captions, zoom or exports change. Uses only the made-up notes app.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'takes/look'
MEDIA = ROOT / 'docs/look'
PAGE = ROOT / 'guide/look.md'
WIDTH = 960  # stills and clips on the page


def cli():
    local = Path(sys.executable).parent / 'reshoot'
    found = str(local) if local.exists() else shutil.which('reshoot')
    if not found:
        raise SystemExit('Install reshoot and run this in its Python environment')
    return found


def ff(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *map(str, args)], check=True)


def record(name, story=None, edit=None, config=None, style=None):
    """A final of the notes example with one change, without the scan, which the gallery doesn't need."""
    folder = WORK / name
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    subprocess.run([cli(), 'init', 'demo'], cwd=folder, check=True, capture_output=True)
    demo = folder / 'demo'
    toml = (demo / 'reshoot.toml').read_text()
    (demo / 'reshoot.toml').write_text((config or (lambda t: t))(toml[:toml.index('[check]')]))
    for file, change in (('storyboard.toml', story), ('edit.toml', edit)):
        if change:
            (demo / file).write_text(change((demo / file).read_text()))
    if style:
        subprocess.run([cli(), 'style', 'apply', style, '--project', 'demo'], cwd=folder, check=True, capture_output=True)
    subprocess.run([cli(), 'run', 'demo/reshoot.toml'], cwd=folder, check=True, capture_output=True)
    run = max((demo / 'takes/runs').iterdir(), key=lambda p: p.stat().st_mtime)
    beats = {b['id']: b for b in json.loads((run / 'takes/demo.take.json').read_text())['beats']}
    return run / 'takes', beats


def still(video, at, out, crop=None):
    ff('-ss', at, '-i', video, '-frames:v', 1, '-vf', (crop + ',' if crop else '') + f'scale={WIDTH}:-2',
       '-q:v', 3, MEDIA / out)


def clip(video, start, seconds, out, crop=None, width=WIDTH, fps=20):
    ff('-ss', start, '-t', seconds, '-i', video, '-vf', (crop + ',' if crop else '') +
       f'fps={fps},scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=bayer',
       '-loop', 0, MEDIA / out)


def size(path):
    n = Path(path).stat().st_size
    return f'{n / 1e6:.1f} MB' if n >= 1e6 else f'{n / 1e3:.0f} KB'


def tour_preview(run):
    from playwright.sync_api import sync_playwright
    from reshoot import tours, web
    row = json.loads((run / 'tours.json').read_text())['tours'][0]
    (MEDIA / 'notes-tour.html').write_text(tours.document(row['title'], row['steps'], run))
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True, args=web.chrome_flags())
        page = browser.new_page(viewport={'width': 1040, 'height': 1000})
        page.goto((MEDIA / 'notes-tour.html').as_uri())
        page.screenshot(path=str(MEDIA / 'tour.jpg'), full_page=True, quality=88)
        browser.close()


def main():
    shutil.rmtree(MEDIA, ignore_errors=True)
    MEDIA.mkdir(parents=True)
    exports = '''
[[export]]
name = "gif640"
format = "gif"
width = 640
height = 360

[[export]]
name = "contain"
format = "mp4"
width = 1080
height = 1350
fit = "contain"

[[export]]
name = "crop"
format = "mp4"
width = 1080
height = 1350
fit = "crop"

[[export]]
name = "crop-right"
format = "mp4"
width = 1080
height = 1350
fit = "crop"
focus = [0.85, 0.5]
display_width = 390
'''
    takes, beats = record('plain', edit=lambda t: t + exports, config=lambda t: t + '''
[[screenshot]]
name = "search-result"
beat = "search"
alt = "Search shows the saved bike note"
width = 960

[tour]
name = "notes-tour"
title = "Save and find a note"

[[tour.step]]
beat = "add"
title = "Save a note"
text = "The new note appears in the list."
alt = "The saved bike note appears above the earlier notes"
hotspot = [0.5, 0.44]

[[tour.step]]
beat = "search"
title = "Find it by a word"
text = "Search narrows the list to the matching note."
alt = "Search shows the saved bike note"
''')
    shutil.copyfile(takes.parent / 'screenshots/search-result.png', MEDIA / 'docs-search.png')
    tour_preview(takes.parent)
    result = beats['search']['end'] - .3
    intro = beats['intro']['start'] + .9
    click = beats['add']['start']
    final = takes / 'demo-final.mp4'
    still(final, intro, 'caption-bottom.jpg')
    clip(final, click + .2, 2.4, 'cursor.gif', crop='crop=840:300:220:20', width=640)
    shapes = {}
    for name, file, out in (('16:9', 'demo-final.mp4', 'shape-wide.jpg'),
                            ('4:5, fit = "contain"', 'demo-final-contain.mp4', 'shape-contain.jpg'),
                            ('4:5, fit = "crop"', 'demo-final-crop.mp4', 'shape-crop.jpg')):
        ff('-ss', result, '-i', takes / file, '-frames:v', 1, '-vf', 'scale=-2:540', '-q:v', 3, MEDIA / out)
        shapes[name] = out
    gifs = {'800 wide (the default)': takes / 'demo-final-readme.gif', '640 wide': takes / 'demo-final-gif640.gif'}
    still(takes / 'demo-final-crop-right.mp4', result, 'shape-right.jpg')
    quality = {name: json.loads((takes / f'demo-final-{name}.readability.json').read_text()) for name in ('contain', 'crop', 'crop-right')}

    takes, beats = record('zoom', story=lambda t: t.replace('seed = 1', 'seed = 1\nzoom = true'))
    zoomed = takes / 'demo-final.mp4'
    typing = beats['search']['start'] + 1.2
    still(zoomed, typing, 'zoom-on.jpg')
    still(final, typing, 'zoom-off.jpg')
    start = beats['add']['start'] + .3
    clip(zoomed, start, beats['search']['end'] - .6 - start, 'zoom.gif', width=480, fps=12)

    styled = '[caption]\nbackground = "#f4f1ea"\nforeground = "#1d1b18"\nmargin = 0.12'
    takes, beats = record('styled', story=lambda t: t.replace('seed = 1', 'seed = 1\n\n' + styled))
    still(takes / 'demo-final.mp4', beats['intro']['start'] + .9, 'caption-styled.jpg')

    card_edit = lambda t: re.sub(r'\[\[part\]\]', '[style]\nbackground = "#1d3b53"\nforeground = "#f4f1ea"\n\n'
                                 '[[part]]\ncard = "Notes, now with search"\nduration = 2\n\n[[part]]', t, count=1)
    takes, beats = record('card', edit=card_edit)
    still(takes / 'demo-final.mp4', 1, 'card.jpg')

    framed = '[style]\nbackground = ["#2a3f5f", "#101826"]\n\n[frame]\n'
    takes, beats = record('frame', edit=lambda t: t.replace('[[part]]', framed + '\n[[part]]', 1))
    still(takes / 'demo-final.mp4', result, 'frame.jpg')

    for name in ('midnight', 'paper'):
        takes, beats = record('style-' + name, style=name)
        still(takes / 'demo-final.mp4', beats['intro']['start'] + .9, 'style-' + name + '.jpg')

    outcome_first = lambda text: text.replace('start = 0\nend = "end"',
        'start = "search"\nthrough = "search"\n\n[[part]]\ntake = 0\nstart = "intro"\nthrough = "add"'
        '\n\n[[part]]\ntake = 0\nstart = "search"\nthrough = "search"')
    takes, _ = record('sequence', edit=outcome_first)
    video = takes / 'demo-final.mp4'
    from reshoot.cut import duration
    clip(video, 0, duration(video), 'sequence.gif', width=480, fps=12)

    write_page(shapes, gifs, styled, framed, quality)
    print(PAGE.relative_to(ROOT), 'and', MEDIA.relative_to(ROOT))


def write_page(shapes, gifs, styled, framed, quality):
    rows = '\n'.join(f'| {name} | {size(path)} |' for name, path in gifs.items())
    aspect = '| ' + ' | '.join(shapes) + ' |\n|' + '---|' * len(shapes) + '\n| ' + ' | '.join(
        f'![{name} export](../docs/look/{out})' for name, out in shapes.items()) + ' |'
    measurements = '\n'.join('| ' + name + ' | ' + str(q['display_width']) + ' px | ' +
        (str(q['metrics']['app_font_p10_px']) + ' px' if q['metrics']['app_font_p10_px'] is not None else 'not measured') + ' | ' +
        (str(q['metrics']['caption_min_px']) + ' px' if q['metrics']['caption_min_px'] is not None else 'not measured') + ' |'
        for name, q in quality.items())
    PAGE.write_text(f'''# How the videos look

Every picture here comes from the bundled notes example, recorded by
[`examples/look/build.py`](../examples/look/build.py). Each one changes a
single setting, or combines them in a reusable visual style. Run the script again to bring the page up to
date.

## Clickable tour

The same checked notes task becomes a single HTML walkthrough. Next, the
numbered marker and keyboard arrows move between captured result screens.
The embedded images, words and navigation work offline.

![The notes walkthrough with a numbered marker on the saved result](../docs/look/tour.jpg)

[Download the offline notes walkthrough](../docs/look/notes-tour.html), then open
the HTML file in a browser. Create and edit one in the studio's **Clickable tour**
panel; see [offline tours](studio.md#make-a-clickable-tour).

## Documentation screenshots

A selected result frame becomes a PNG beside the videos. This is the captured
page after the search checks passed, without the video's caption, camera zoom
or decorative frame. The recorded cursor may remain visible. It is a viewport
image, not a stitched full-page capture.

![Search shows the saved bike note](../docs/look/docs-search.png)

Choose **Use for docs** beside a checked step in the studio, describe the image,
save it and update the preview. Its name stays stable across fresh recordings.
See [documentation screenshots](studio.md#make-screenshots-for-docs)
for cropping, local export and refresh review.

## Visual styles

Choose a complete look in the studio's **Style and exports**, or apply one
from the command line. Each changes caption colours and placement, title-card
colours and browser framing. Fonts, story content, timing, audio and exports
stay as they are. The app is large in Focus; the framed styles give it a
background and slightly shrink it, so check text at the exported size.

| Focus | Midnight | Paper |
|---|---|---|
| ![Focus, with dark captions and the page filling the video](../docs/look/caption-bottom.jpg) | ![Midnight, with a blue gradient and browser frame](../docs/look/style-midnight.jpg) | ![Paper, with a warm frame and light captions](../docs/look/style-paper.jpg) |

```bash
reshoot style apply midnight --project demo
reshoot recut demo/latest
```

Save your own look and use it in another project with
[reusable styles](studio.md#change-the-look).

## Beat cuts and sequence

This cut shows the search result, then how the note was created, then the
result again. The app still runs once in its original order and verifies all
three result checks. Only the video parts move. `through` includes the last
step and its reading hold; `end` stops at the named step's start.

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

The studio's **Your cut** edits these ranges and their order, with Undo and
Redo. See [trim and arrange the video](studio.md#trim-and-arrange-the-video)
for the CLI equivalents. Update preview reuses a current recording and
retains repeated captions and narration at their new times.

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
{styled}
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

## A browser frame

A `[frame]` table in `edit.toml` puts each take in a window with a title bar,
rounded corners and a soft shadow, on the `[style]` background: one colour, or
a top and bottom colour for a gradient. Title cards stay full size. The page is
shrunk to fit, so text gets smaller: frame a recording whose text is large
enough already.

![The notes demo in a browser window on a blue gradient](../docs/look/frame.jpg)

```toml
{framed}padding = 0.06   # each side, as a fraction of the width; these are the defaults
radius = 12      # corner radius in pixels
shadow = true
bar = true       # the title bar with three dots
```

## Shapes

An `[[export]]` profile makes another size from the same recording.
`fit = "contain"` fits the whole frame in, so the text shrinks; `fit = "crop"`
fills the shape from the middle, so the text stays large but the edges go. For
a portrait video people read on a phone, record a narrower viewport, or a take
of its own.

{aspect}

```toml
[[export]]          # in edit.toml
name = "crop"
format = "mp4"
width = 1080
height = 1350
fit = "crop"
```

The `x`, `linkedin` and `readme` [presets](projects.md#export-presets) make
these shapes for a platform and check its limits.

## Destination framing and readability

Each export can Fit the whole video or Crop to fill its shape, with horizontal
and vertical crop positions. The studio's crop guide helps aim it; Update
preview renders the choice. A crop can cut off a caption or checked result.
These are the centre and right-biased versions of the same held notes result:

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

The same geometry frames MP4 and GIF. `focus` uses fractions from 0 (left or
top) to 1 (right or bottom). Viewing width changes inspection and text-size
estimates, not encoded dimensions. The gallery's measured values are:

| Export | Viewing width | Small app-text samples | Smallest caption text |
|---|---|---|---|
{measurements}

These are editing hints from sampled main-page text and rendered caption
geometry. They do not establish readability or accessibility. Camera zoom,
custom placement, iframe or canvas text need visual inspection. The studio's
**Inspect at viewing size** keeps the requested width, with scrolling when
needed. See [destination framing](studio.md#fit-an-export-to-where-its-shown)
for the controls and CLI. `reshoot frame check demo/latest` reads the feedback
measured on that run.

## GIF size

A README GIF is made with its own palette. `max_bytes` in an export profile
fails the export if the file comes out larger, so a GIF never silently grows
past a page's limit. The notes example's loop:

| Width | File |
|---|---|
{rows}

## Sound

A voiceover is spoken before recording, so each step waits for its line.
Music plays under it and ducks while someone speaks, then fades out at the end.
See [Grow it into a fuller demo](studio.md#grow-it-into-a-fuller-demo).
''')


if __name__ == '__main__':
    main()
