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


def record(name, story=None, edit=None, config=None):
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
'''
    takes, beats = record('plain', edit=lambda t: t + exports)
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

    write_page(shapes, gifs, styled)
    print(PAGE.relative_to(ROOT), 'and', MEDIA.relative_to(ROOT))


def write_page(shapes, gifs, styled):
    rows = '\n'.join(f'| {name} | {size(path)} |' for name, path in gifs.items())
    aspect = '| ' + ' | '.join(shapes) + ' |\n|' + '---|' * len(shapes) + '\n| ' + ' | '.join(
        f'![{name} export](../docs/look/{out})' for name, out in shapes.items()) + ' |'
    PAGE.write_text(f'''# How the videos look

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

## GIF size

A README GIF is made with its own palette. `max_bytes` in an export profile
fails the export if the file comes out larger, so a GIF never silently grows
past a page's limit. The notes example's loop:

| Width | File |
|---|---|
{rows}

## Sound

A voiceover is spoken before recording, so each beat waits for its line.
Music plays under it and ducks while someone speaks, then fades out at the end.
See [Grow it into a fuller demo](customize.md#grow-it-into-a-fuller-demo).
''')


if __name__ == '__main__':
    main()
