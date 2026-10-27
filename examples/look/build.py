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
{styled}
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
{framed}padding = 0.06   # each side, as a fraction of the width; these are the defaults
radius = 12      # corner radius in pixels
shadow = true
bar = true       # the title bar with three dots
```

## Shapes

An `[[export]]` makes another size. `fit = "contain"` fits the whole frame,
so text shrinks; `fit = "crop"` fills the shape and loses the edges. For a
phone, record a narrower viewport.

{aspect}

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
{measurements}

These are hints, not proof of readability; look at zoomed, iframe or canvas
text yourself. See [destination framing](studio.md#fit-an-export-to-where-its-shown),
or run `reshoot frame check demo/latest`.

## GIF size

`max_bytes` in an export fails it if the file comes out larger. The notes loop:

| Width | File |
|---|---|
{rows}

## Sound

Each step waits for its voiceover line. Music ducks under speech and fades at
the end. See [balance the sound](studio.md#balance-the-sound).
''')


if __name__ == '__main__':
    main()
