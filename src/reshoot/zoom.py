"""Zoom on clicks, done after recording: the view moves in on what's being clicked or typed, follows the cursor from
one action to the next, and moves back out when things go quiet.

The page reports each action with where its element is (overlay.js). Actions close together share one view that
holds all of them, so typing in a field and clicking its button keep the whole row, and what changes near it, in
view. Since the zoom is worked out afterwards, it
can start before a click and land as the click happens. The page is recorded at a higher pixel density, so text
stays sharp when enlarged. Captions are drawn after the zoom, so they stay in place.

    ZOOM = True                                   # in a storyboard, or `reshoot web --zoom`
    ZOOM = {"scale": 1.8, "lead": 0.7, "hold": 1.0, "idle": 1.2}

scale is the most it enlarges; lead is how many seconds before an action the zoom starts; hold is how long it
stays after the last action; actions closer together than idle seconds share one zoom.
"""
import bisect, io, math, re, subprocess

DEFAULTS = {"scale": 1.8, "lead": 0.7, "hold": 1.0, "idle": 1.2}
FPS = 60


def settings(z):
    """ZOOM from a storyboard (True, a number, or a dict) as a full dict, or None for no zoom."""
    if not z:
        return None
    if z is True:
        return dict(DEFAULTS)
    if isinstance(z, (int, float)):
        return {**DEFAULTS, "scale": float(z)}
    return {**DEFAULTS, **z}


def actions(events):
    """[(start, end, rect)] from the page's act events, in seconds and CSS pixels."""
    out, start = [], None
    for t, ev in events:
        if ev.get("kind") != "act":
            continue
        if ev["phase"] == "start":
            start = (t, ev["rect"])
        elif start:
            out.append((start[0], t, ev["rect"] or start[1]))
            start = None
    return out


def fit(rect, w, h, most):
    """The camera (centre x, centre y, scale) for a rect: enlarged up to `most`, keeping the rect in view."""
    x, y, rw, rh = rect
    s = min(most, w * 0.8 / max(rw, 1), h * 0.8 / max(rh, 1))
    return x + rw / 2, y + rh / 2, max(1.0, s)


def union(rects):
    x0, y0 = min(r[0] for r in rects), min(r[1] for r in rects)
    x1, y1 = max(r[0] + r[2] for r in rects), max(r[1] + r[3] for r in rects)
    return [x0, y0, x1 - x0, y1 - y0]


def targets(events, w, h, z):
    """Where the camera should be over time: [(from, to, (cx, cy, s))], everything else being the whole page."""
    acts, out = actions(events), []
    i = 0
    while i < len(acts):  # actions close together share one view that holds them all
        j = i
        while j + 1 < len(acts) and acts[j + 1][0] - acts[j][1] < z["idle"]:
            j += 1
        out.append((acts[i][0] - z["lead"], acts[j][1] + z["hold"], fit(union([a[2] for a in acts[i:j + 1]]), w, h, z["scale"])))
        i = j + 1
    manual, at = [], None  # __demo.zoom() ... zoomOut(): these win over the automatic zoom
    for t, ev in events:
        if ev.get("kind") == "zoom":
            at = (t - z["lead"], fit(ev["rect"], w, h, ev.get("scale") or z["scale"]))
        elif ev.get("kind") == "zoom-out" and at:
            manual.append((at[0], t, at[1]))
            at = None
    if at:
        manual.append((at[0], math.inf, at[1]))
    return out, manual


def camera_path(n, events, w, h, z):
    """The camera for each of n frames at 60 fps: a spring that follows the target, so moves ease in and out."""
    auto, manual = targets(events, w, h, z)
    full = (w / 2, h / 2, 1.0)

    def target(t):
        for a, b, c in manual:
            if a <= t < b:
                return c
        for a, b, c in auto:
            if a <= t < b:
                return c
        return full

    omega, dt = 7.0, 1 / FPS  # settles in about 0.6 s, without overshooting
    pos, vel, path = list(full), [0.0, 0.0, 0.0], []
    for k in range(n):
        goal = target(k * dt)
        for i in range(3):
            vel[i] += (omega * omega * (goal[i] - pos[i]) - 2 * omega * vel[i]) * dt
            pos[i] += vel[i] * dt
        s = max(1.0, pos[2])
        vw, vh = w / s, h / s  # the part of the page in view, kept inside the page
        cx = min(max(pos[0], vw / 2), w - vw / 2)
        cy = min(max(pos[1], vh / 2), h - vh / 2)
        path.append((cx - vw / 2, cy - vh / 2, vw, vh))
    return path


def captions(events):
    """[(start, end, text, sub)] from the page's caption events."""
    out, cur = [], None
    for t, ev in events:
        if ev.get("kind") != "caption":
            continue
        if cur:
            out.append((cur[0], t, *cur[1:]))
        cur = (t, plain(ev["text"]), plain(ev.get("sub"))) if ev.get("text") else None
    if cur:
        out.append((cur[0], math.inf, *cur[1:]))
    return out


def plain(html):
    """Caption HTML as plain text: tags dropped, the usual entities turned back into characters."""
    if not html:
        return None
    s = re.sub(r"<[^>]+>", "", html)
    return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")


def caption_image(text, sub, out_w, css_w):
    """A caption drawn like the page's own: white on a dark rounded box, sized to the video."""
    from PIL import Image, ImageDraw
    from reshoot.cut import font
    px = out_w / css_w
    size = round(min(max(18, css_w * 0.023), 30) * px)
    big, small = font(size, 600), font(round(size * 0.6), 500)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = d.textlength(text, font=big)
    sw = d.textlength(sub, font=small) if sub else 0
    padx, pady = round(26 * px), round(14 * px)
    w = round(max(tw, sw) + 2 * padx)
    h = round(size * 1.25 + (size * 0.6 * 1.25 + 4 * px if sub else 0) + 2 * pady)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=round(16 * px), fill=(14, 13, 12, 200))
    d.text(((w - tw) / 2, pady), text, font=big, fill=(255, 255, 255, 255))
    if sub:
        d.text(((w - sw) / 2, pady + size * 1.25 + 4 * px), sub, font=small, fill=(255, 255, 255, 190))
    return im


def render(frames, events, out, css_w, css_h, out_w, out_h, z):
    """Writes the video: each output frame is the last frame Chrome painted by then, cropped to the camera, scaled
    to the output size, with the caption drawn on top."""
    from PIL import Image
    end = frames[-1][0] if frames and frames[-1][1] is None else None
    frames = [f for f in frames if f[1] is not None]
    t0 = frames[0][0]
    times = [t - t0 for t, _ in frames]
    total = max((end or 0) - t0, times[-1] + 1 / FPS)
    n = max(1, round(total * FPS))
    events = [(t - t0, ev) for t, ev in events]
    path = camera_path(n, events, css_w, css_h, z)
    caps = [(a, b, caption_image(text, sub, out_w, css_w)) for a, b, text, sub in captions(events)]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{out_w}x{out_h}", "-r", str(FPS), "-i", "-", "-vf", "format=yuv420p", "-color_range", "tv",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-movflags", "+faststart", str(out)],
                          stdin=subprocess.PIPE)
    shown, im = None, None
    try:
        for k in range(n):
            t = k / FPS
            i = max(0, bisect.bisect_right(times, t) - 1)
            if i != shown:
                im, shown = Image.open(io.BytesIO(frames[i][1])).convert("RGB"), i
            sx = im.width / css_w
            x, y, vw, vh = path[k]
            frame = im.resize((out_w, out_h), Image.LANCZOS, box=(x * sx, y * sx, (x + vw) * sx, (y + vh) * sx),
                              reducing_gap=2.0)
            for a, b, cap in caps:  # fades in over 0.35 s, and out over 0.35 s once hidden, as in the page
                fade = 0.0 if t < a else min(1.0, (t - a) / 0.35, 1.0 if t < b else 1 - (t - b) / 0.35)
                if fade > 0:
                    layer = cap if fade >= 1 else cap.copy()
                    if fade < 1:
                        layer.putalpha(layer.getchannel("A").point(lambda v: round(v * fade)))
                    lift = round((1 - fade) * 12 * out_w / css_w)
                    frame.paste(layer, ((out_w - cap.width) // 2, round(out_h * 0.935) - cap.height + lift), layer)
            ff.stdin.write(frame.tobytes())
    finally:
        ff.stdin.close()
        if ff.wait():
            raise RuntimeError("ffmpeg couldn't write the zoomed video")
