"""Pieces for cutting takes into a finished video with ffmpeg: trims, still cards, speed-ups, a 9:16 version, GIFs.

Each project writes its own short edit script from these, since the order of takes and the words on screen differ
from one video to the next. examples/notes/edit.py is a small one to start from.

Every clip made here is 60 fps H.264 in yuv420p, standard range, with no sound, so clips of the same size can be
joined without encoding them again.
"""
import json, math, re, subprocess, tempfile
from pathlib import Path

FPS = 60
# Standard ("tv") range for every clip. Chrome's frames are JPEGs in full range, and a joined video is read with
# its first clip's range, so one full-range clip at the start made every card after it look washed out.
ENC = ["-r", str(FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-color_range", "tv",
       "-an"]
FONTS = ["/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Helvetica.ttc",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"]
GIF_PALETTE = ("split[a][b];[a]palettegen=stats_mode=full:max_colors=200[p];"
               "[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle")


def ff(*args):
    """Runs ffmpeg quietly; raises on failure."""
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *map(str, args)], check=True)


def _probe(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,color_range:format=duration", "-of", "json", str(f)],
                       capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    return j["streams"][0], float(j["format"]["duration"])


def probe(f):
    """(width, height, seconds) of a video."""
    s, d = _probe(f)
    return s["width"], s["height"], d


def duration(f):
    """Seconds, for a video or a sound file."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


def beats(take):
    """When each beat starts in a `reshoot web` take: {name: seconds}, from TAKE.beats.json."""
    return json.loads(Path(take).with_suffix(".beats.json").read_text())


def trim(src, start, end, out, fade_in=0, fade_out=0):
    """src from start to end seconds, with optional fades from and to black."""
    vf = [f"fps={FPS}"]
    if fade_in:
        vf.append(f"fade=in:st=0:d={fade_in}")
    if fade_out:
        vf.append(f"fade=out:st={end - start - fade_out}:d={fade_out}")
    ff("-ss", start, "-to", end, "-i", src, "-vf", ",".join(vf), *ENC, out)
    from reshoot import timeline
    timeline.trim(src, start, end, out)
    return out


def speed(src, start, end, factor, out):
    """src from start to end, played factor times as fast."""
    ff("-i", src, "-vf", f"trim={start}:{end},setpts=(PTS-STARTPTS)/{factor},fps={FPS}", *ENC, out)
    from reshoot import timeline
    timeline.trim(src, start, end, out, factor)
    return out


def frame(src, out, background="#1d2433", padding=0.06, radius=12, shadow=True, bar=True, bar_color="#2b2f36"):
    """src shrunk into a browser-like window on a background, the same size as src: rounded corners, a soft shadow and,
    with bar, a title bar with three dots. background is a colour or [top, bottom] for a gradient; radius is in the
    output's pixels; padding is a fraction of the width on each side."""
    from PIL import Image, ImageColor, ImageDraw, ImageFilter
    import tempfile
    w, h, seconds = probe(src)
    pad = round(w * padding)
    top = round(h * 0.045) if bar else 0
    scale = min((w - 2 * pad) / w, (h - 2 * pad - top) / h)
    cw, ch = int(w * scale) // 2 * 2, int(h * scale) // 2 * 2
    x, y = (w - cw) // 2, (h - ch - top) // 2
    colors = [background] * 2 if isinstance(background, str) else list(background)
    a, b = (ImageColor.getrgb(c) for c in colors)
    canvas = Image.new("RGB", (w, h))
    for row in range(h):  # a vertical gradient, or one colour
        f = row / max(1, h - 1)
        canvas.paste(tuple(round(a[i] + (b[i] - a[i]) * f) for i in range(3)), (0, row, w, row + 1))
    window = (x, y, x + cw - 1, y + top + ch - 1)
    if shadow:
        soft = Image.new("L", (w, h), 0)
        ImageDraw.Draw(soft).rounded_rectangle((window[0], window[1] + h // 60, window[2], window[3] + h // 60),
                                               radius, fill=110)
        soft = soft.filter(ImageFilter.GaussianBlur(h / 40))
        canvas.paste((0, 0, 0), (0, 0), soft)
    if bar:
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle((x, y, x + cw - 1, y + top + radius), radius, fill=ImageColor.getrgb(bar_color))
        dot = max(3, top // 5)
        for n, colour in enumerate(("#ff5f57", "#febc2e", "#28c840")):
            cx = x + top // 2 + n * dot * 3
            d.ellipse((cx - dot, y + top // 2 - dot, cx + dot, y + top // 2 + dot), fill=colour)
    mask = Image.new("L", (cw, ch), 0)  # the page's corners: rounded at the bottom, and at the top without a bar
    ImageDraw.Draw(mask).rounded_rectangle((0, -radius if bar else 0, cw - 1, ch - 1), radius, fill=255)
    with tempfile.TemporaryDirectory() as temp:
        canvas.save(Path(temp) / "back.png")
        mask.save(Path(temp) / "mask.png")
        # The pictures are looped only as long as the clip, or ffmpeg would wait on them for ever.
        ff("-loop", 1, "-t", seconds, "-i", Path(temp) / "back.png", "-i", src,
           "-loop", 1, "-t", seconds, "-i", Path(temp) / "mask.png",
           "-filter_complex", f"[1:v]scale={cw}:{ch},format=rgba[page];[2:v]format=gray[m];[page][m]alphamerge[cut];"
           f"[0:v][cut]overlay={x}:{y + top}:shortest=1,fps={FPS},format=yuv420p", "-an", *ENC, out)
    from reshoot import timeline
    timeline.copy(src, out)
    return out


def still(png, seconds, out, fade_in=0.5):
    """An image held for some seconds, such as a title or end card."""
    ff("-loop", 1, "-i", png, "-vf", f"fps={FPS},format=yuv420p" + (f",fade=in:st=0:d={fade_in}" if fade_in else ""),
       "-t", seconds, *ENC, out)
    from reshoot import timeline
    timeline.write(out, [], seconds)
    return out


def place(bg_png, src, x, y, out, width=None):
    """src placed at (x, y) on a background image, scaled to width if given; as long as src."""
    scale = f"scale={width}:-2:flags=lanczos," if width else ""
    ff("-loop", 1, "-i", bg_png, "-i", src, "-filter_complex",
       f"[1:v]{scale}fps={FPS}[v];[0:v][v]overlay={x}:{y}:shortest=1,format=yuv420p", *ENC, out)
    from reshoot import timeline
    timeline.copy(src, out)
    return out


def vertical(src, bg_png, out, y=None):
    """A 9:16 version: the landscape video across a 1080x1920 background (with the words above and below it)."""
    w, h, _ = probe(src)
    vh = round(1080 * h / w) // 2 * 2
    return place(bg_png, src, 0, (1920 - vh) // 2 if y is None else y, out, width=1080)


def concat(parts, out):
    """Joins clips end to end without encoding again. They must share size, frame rate, pixel format and colour
    range, as the clips made here do."""
    info = [_probe(p)[0] for p in parts]
    sizes = {(s["width"], s["height"]) for s in info}
    if len(sizes) > 1:
        raise ValueError(f"clips of different sizes can't be joined as they are: {sorted(sizes)}")
    ranges = {s.get("color_range") if s.get("color_range") in ("pc", "tv") else "tv" for s in info}  # unmarked is tv
    if len(ranges) > 1:
        raise ValueError(f"clips with different colour ranges ({', '.join(sorted(ranges))}) would change colour when "
                         "joined: make each one with the helpers here, such as cut.trim")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("".join(f"file '{Path(p).resolve()}'\n" for p in parts))
    try:
        ff("-f", "concat", "-safe", 0, "-i", f.name, "-c", "copy", "-movflags", "+faststart", out)
    finally:
        Path(f.name).unlink()
    from reshoot import timeline
    timeline.concat(parts, out)
    return out


def gif(src, start, end, out, fps=15, width=800, height=None, fit="contain"):
    """A GIF of src from start to end, with a palette made for these frames (much better than the default)."""
    vf = f"scale={width}:-1:flags=lanczos"
    if height is not None:
        if fit not in ('contain', 'crop'):
            raise ValueError('GIF fit must be contain or crop')
        vf = f"scale={width}:{height}:flags=lanczos:force_original_aspect_ratio=" + ('increase' if fit == 'crop' else 'decrease')
        vf += f",crop={width}:{height}" if fit == 'crop' else f",pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    # A card/browser join can change SAR or color metadata. Normalize into one
    # lossless RGB stream before buffering frames for the palette; a filtergraph
    # reset otherwise drops earlier sections.
    with tempfile.TemporaryDirectory() as temp:
        normalized = Path(temp) / "frames.nut"
        ff("-ss", start, "-t", end - start, "-i", src,
           "-vf", f"fps={fps},{vf},format=bgr0,setsar=1", "-an",
           "-c:v", "ffv1", "-pix_fmt", "bgr0", "-color_range", "pc", normalized)
        ff("-i", normalized, "-vf", GIF_PALETTE, out)
    from reshoot import timeline
    timeline.trim(src, start, end, out)
    return out


def last_change(take, threshold=0.002):
    """The time of the last real change in a video. For a terminal take recorded with a long fixed Sleep, this is
    about when the command (or Claude) finished; after it only a cursor or a spinner moves."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(take), "-vf", f"select='gt(scene,{threshold})',showinfo",
                        "-f", "null", "-"], capture_output=True, text=True)
    times = [float(t) for t in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    if not times:
        raise ValueError(f"no change found in {take}")
    return times[-1]


def _window_frame(mov, at=None):
    """One frame of a `reshoot window` recording, in greys, with a pixel reader."""
    from PIL import Image
    with tempfile.TemporaryDirectory() as t:
        png = Path(t) / "f.png"
        ff("-ss", min(4, duration(mov) / 2) if at is None else at, "-i", mov, "-frames:v", 1, png)
        im = Image.open(png).convert("L")
    return im, im.load()


def window_box(mov, at=None):
    """(w, h, x, y) of a window inside its recorded shadow, from one frame of a `reshoot window` recording."""
    im, px = _window_frame(mov, at)
    w, h = im.size
    rows = [y for y in range(h) if sum(px[x, y] > 12 for x in range(0, w, 4)) > w / 8]
    cols = [x for x in range(w) if sum(px[x, y] > 12 for y in range(0, h, 4)) > h / 8]
    return cols[-1] - cols[0] + 1, rows[-1] - rows[0] + 1, cols[0], rows[0]


def corner_radius(mov, at=None):
    """How round the window's corners are, in the recording's pixels. Going in from the box's corner along the
    diagonal, a round corner leaves the background showing for r * (1 - 1/sqrt 2) pixels."""
    w, h, x0, y0 = window_box(mov, at)
    _, px = _window_frame(mov, at)
    k = next((k for k in range(min(w, h) // 2) if px[x0 + k, y0 + k] > 12), 0)
    return max(0, min(round(k / (1 - 2 ** -0.5)), min(w, h) // 4))


def window_clip(mov, bg_png, x, y, out, width=None, radius=None):
    """A `reshoot window` recording, cropped to the window with its corners rounded, placed at (x, y) on a
    background image and scaled to width if given. The square crop alone shows the background at each corner."""
    from PIL import Image, ImageDraw
    w, h, bx, by = window_box(mov)
    r = corner_radius(mov) if radius is None else radius
    ow = (width or w) // 2 * 2
    oh = round(ow * h / w) // 2 * 2
    with tempfile.TemporaryDirectory() as t:
        mask = Path(t) / "mask.png"
        m = Image.new("L", (ow, oh), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, ow - 1, oh - 1), radius=round(r * ow / w), fill=255)
        m.save(mask)
        ff("-loop", 1, "-i", bg_png, "-i", mov, "-loop", 1, "-i", mask, "-filter_complex",
           f"[1:v]fps={FPS},crop={w}:{h}:{bx}:{by},scale={ow}:{oh}:flags=lanczos,format=rgba[w];[2:v]format=gray[m];"
           f"[w][m]alphamerge[p];[0:v][p]overlay={x}:{y},format=yuv420p", "-t", duration(mov), *ENC, out)
    from reshoot import timeline
    timeline.copy(mov, out)
    return out


def font(size, weight=600):
    """The system font at a size and weight. SF on macOS has a weight axis; DejaVu on Linux has no axis but a
    separate bold file, used from weight 600 up."""
    from PIL import ImageFont
    for path in FONTS:
        if Path(path).exists():
            bold = path.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
            if weight >= 600 and bold != path and Path(bold).exists():
                path = bold
            f = ImageFont.truetype(path, size)
            try:  # SF on macOS: width, optical size, grade, weight
                f.set_variation_by_axes([100, max(17, min(96, size)), 400, weight])
            except (OSError, ValueError):
                pass
            return f
    return ImageFont.load_default(size)


def wrap_text(text, selected_font, width, draw):
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if draw.textlength(candidate, font=selected_font) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ''
            for ch in word:
                if line and draw.textlength(line + ch, font=selected_font) > width:
                    lines.append(line)
                    line = ''
                line += ch
        lines.append(line)
    return lines


class Card:
    """A frame of words drawn with PIL, on a colour or transparent (bg=None), for title cards and labels."""
    def __init__(self, w=1920, h=1080, bg=(14, 13, 12), font_path=None):
        from PIL import Image, ImageDraw
        self.w, self.im = w, Image.new("RGBA" if bg is None else "RGB", (w, h), (0, 0, 0, 0) if bg is None else bg)
        self.d = ImageDraw.Draw(self.im)
        self.font_path = font_path

    def text(self, x, y, s, size, weight=600, fill=(255, 255, 255)):
        """s at (x, y); x=None centres it."""
        from PIL import ImageFont
        f = ImageFont.truetype(str(self.font_path), size) if self.font_path else font(size, weight)
        lines = wrap_text(s, f, self.w * .9 if x is None else self.w-x-20, self.d)
        if y + len(lines)*size*1.25 > self.im.height:
            raise ValueError('card text does not fit; shorten it or reduce the size')
        for index, line in enumerate(lines):
            self.d.text(((self.w-self.d.textlength(line, font=f))/2 if x is None else x, y+index*size*1.25), line, font=f, fill=fill)
        return self

    def badge(self, x, y, s, size=30, fill=(245, 180, 60), ink=(20, 20, 20)):
        """s in a pill, such as "8x speed"; x=None centres it."""
        f = font(size, 700)
        w = self.d.textlength(s, font=f)
        x = (self.w - w - 40) / 2 if x is None else x
        self.d.rounded_rectangle((x, y, x + w + 40, y + size + 24), radius=(size + 24) // 2, fill=fill)
        self.d.text((x + 20, y + 9), s, font=f, fill=ink)
        return self

    def save(self, path):
        self.im.save(path)
        return path


def gifs_main(a):
    """`reshoot gif TAKE.mp4 OUT.gif FROM [TO]`: FROM and TO are beat names or seconds; TO defaults to the end."""
    def at(v):
        try:
            return float(v)
        except ValueError:
            return beats(a.take)[v]
    end = at(a.end) if a.end else duration(a.take)
    gif(a.take, at(a.start), end - 0.1, a.out, a.fps, a.width)
    print("wrote", a.out)



def lines(take, start=0, end=None, offset=0):
    """The voiceover lines of a take that fall in [start, end), moved to start at offset in the finished video:
    [(at, seconds, text, file)]. Empty if the take has no VOICE."""
    p = Path(take).with_suffix(".voice.json")
    if not p.exists():
        return []
    end = math.inf if end is None else end
    return [(v["t"] - start + offset, v["seconds"], v["text"], v["file"]) for v in json.loads(p.read_text())
            if start <= v["t"] < end]


def cues(take, start=0, end=None, offset=0):
    """Subtitles for part of a take, moved like lines(): [(from, to, text)]. They're the voiceover when there is
    one; otherwise the captions, which are on screen already but can't be read by a screen reader or searched."""
    if said := lines(take, start, end, offset):
        return [(at, at + s, text) for at, s, text, _ in said]
    from reshoot import captions
    if (drawn := captions.cues(take, start, end, offset)) is not None:
        return drawn
    p = Path(take).with_suffix(".events.json")
    events = json.loads(p.read_text()) if p.exists() else []
    end = math.inf if end is None else end
    out, cur = [], None
    for e in events + [{"t": math.inf, "kind": "caption", "text": None}]:
        if e.get("kind") != "caption":
            continue
        if cur:
            a, b = max(cur[0], start), min(e["t"], end)
            if a < b:
                out.append((a - start + offset, b - start + offset, cur[1]))
        text = re.sub(r"<[^>]+>", "", e.get("text") or "")
        cur = (e["t"], text + (f" ({re.sub(r'<[^>]+>', '', e['sub'])})" if e.get("sub") else "")) if text else None
    return out


def write_srt(cues, path):
    """An .srt subtitle file, which LinkedIn, YouTube and most players take alongside the video."""
    def stamp(t):
        ms = round(t * 1000)
        return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    Path(path).write_text("".join(f"{i}\n{stamp(a)} --> {stamp(b)}\n{text}\n\n" for i, (a, b, text) in enumerate(cues, 1)))
    return path


def voice_track(said, out, total):
    """A sound track `total` seconds long with each line at its time: said is lines() from one or more takes."""
    if not said:
        raise ValueError("no voiceover lines to put in the track")
    inputs, chain = [], []
    for k, (at, _, _, f) in enumerate(said, 1):
        inputs += ["-i", f]
        ms = max(0, round(at * 1000))
        chain.append(f"[{k}:a]adelay={ms}|{ms}[a{k}]")
    mix = "".join(f"[a{k}]" for k in range(1, len(said) + 1))
    ff("-f", "lavfi", "-t", total, "-i", "anullsrc=r=48000:cl=mono", *inputs, "-filter_complex",
       ";".join(chain) + f";[0:a]{mix}amix=inputs={len(said) + 1}:normalize=0:duration=first[out]", "-map", "[out]", out)
    return out


def add_audio(video, out, voice=None, music=None, music_volume=0.25):
    """The video with sound: a voice track, music, or both. Music loops to the video's length, fades out over its
    last 2 seconds, and gets quieter while the voice speaks."""
    d = duration(video)
    args, n = ["-i", video], 1
    if voice:
        args += ["-i", voice]; vi = n; n += 1
    if music:
        args += ["-stream_loop", "-1", "-i", music]; mi = n
    parts = []
    if music:
        parts.append(f"[{mi}:a]aresample=48000,volume={music_volume},afade=t=out:st={max(0, d - 2)}:d=2[m]")
    if voice and music:  # the music ducks under the voice
        parts += [f"[{vi}:a]aresample=48000,asplit[v1][v2]", "[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[md]",
                  "[md][v2]amix=inputs=2:normalize=0[a]"]
    elif voice:
        parts.append(f"[{vi}:a]aresample=48000[a]")
    elif music:
        parts.append("[m]anull[a]")
    else:
        raise ValueError("give a voice track, music, or both")
    ff(*args, "-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
       "-t", d, "-movflags", "+faststart", out)
    from reshoot import timeline
    timeline.copy(video, out)
    return out
