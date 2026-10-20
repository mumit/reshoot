"""Zoom on clicks, done after recording: the view moves in on what's being clicked or typed, follows the cursor from
one action to the next, and moves back out when things go quiet.

The page reports each action with where its element is (overlay.js). Zooming out and back in for nothing is
distracting, so the view only moves when it has to: when the next action is out of view, after a long quiet spell,
at a new caption, or when something outside the view changes. Since the zoom is worked out afterwards, it
can start before a click and land as the click happens. The page is recorded at a higher pixel density, so text
stays sharp when enlarged. Captions are drawn after the zoom, so they stay in place.

    ZOOM = True                                   # in a storyboard, or `reshoot web --zoom`
    ZOOM = {"scale": 1.8, "lead": 0.7, "hold": 1.0, "quiet": 4.0, "watch": True, "show": 1.0}

scale is the most it enlarges; lead is how many seconds before an action the zoom starts; hold is how long it
stays after the last action. A zoom stays while the next action is already in view, however long the pause; it
widens to take in an action just out of view; it ends after quiet seconds with nothing done, when a new caption
starts, or when the next action is far away. With watch on, it also ends (once the action
under way is done) when something changes outside the view, such as a new item in a list, and stays out for show
seconds, so the change is seen.
"""
import bisect, io, math, re, subprocess, os

DEFAULTS = {"scale": 1.8, "lead": 0.7, "hold": 1.0, "quiet": 4.0, "watch": True, "show": 1.0}
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


def view_of(cam, w, h):
    """The part of the page a camera (cx, cy, s) shows: [x, y, w, h], kept inside the page."""
    cx, cy, s = cam
    vw, vh = w / s, h / s
    cx, cy = min(max(cx, vw / 2), w - vw / 2), min(max(cy, vh / 2), h - vh / 2)
    return [cx - vw / 2, cy - vh / 2, vw, vh]


def inside(rect, view, margin=0.03):
    x, y, rw, rh = rect
    vx, vy, vw, vh = view
    mx, my = vw * margin, vh * margin
    return x >= vx + mx and y >= vy + my and x + rw <= vx + vw - mx and y + rh <= vy + vh - my


def targets(events, w, h, z, changed=None):
    """Where the camera should be over time: [(from, to, (cx, cy, s))], everything else being the whole page.

    A zoom stays while the next action is already in view, however long the pause. It widens to take in the next
    action if that's just out of view and the wider view still enlarges (1.2x or more). It ends after `quiet`
    seconds with nothing done, when a new caption starts, or when the next action is far away. And if
    changed(start, end, view) finds something changing outside the view, it ends once the action under way is done,
    so the change can be seen."""
    acts, out = actions(events), []
    caps = [t for t, ev in events if ev.get("kind") == "caption" and ev.get("text")]
    i, rest = 0, -math.inf  # rest: after zooming out to show a change, stay out until then
    while i < len(acts):
        rects, j = [acts[i][2]], i
        cam = fit(rects[0], w, h, z["scale"])
        start = max(acts[i][0] - z["lead"], rest)
        scanned = acts[i][0] - z["lead"]
        while True:
            nxt = acts[j + 1] if j + 1 < len(acts) else None
            until = nxt[0] if nxt else acts[j][1] + z["hold"]
            tc = changed(scanned, until, view_of(cam, w, h)) if changed and cam[2] > 1 else None
            if tc is not None:  # something outside the view changed: show it once the action under way is done,
                doing = next((a for a in acts[i:j + 1] if a[0] <= tc <= a[1]), None)  # or a moment before it
                end = doing[1] + 0.3 if doing else tc - 0.4  # happens, so a new page appears already zoomed out
                rest = end + z["show"]  # and leave time to see it, such as a new page, before zooming in again
                break
            scanned = until
            end = acts[j][1] + z["hold"]
            if not nxt:
                break
            gap = nxt[0] - acts[j][1]
            if gap > z["quiet"] or any(acts[j][1] < c < nxt[0] for c in caps):
                break
            if inside(nxt[2], view_of(cam, w, h)):
                j += 1  # already in view: stay
                continue
            wider = fit(union(rects + [nxt[2]]), w, h, z["scale"])
            if wider[2] >= 1.2:
                rects.append(nxt[2]); cam = wider; j += 1  # close by: widen to take it in, smoother than out and in
                continue
            break
        if start < end:
            out.append((start, end, cam))
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


def camera_path(n, events, w, h, z, changed=None):
    """The camera for each of n frames at 60 fps: a spring that follows the target, so moves ease in and out."""
    auto, manual = targets(events, w, h, z, changed)
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


def change_finder(frames, w, h):
    """changed(start, end, view): the first time in [start, end) when something sizeable changed outside view on
    the page, or None. Frames are compared small (8 CSS pixels to a cell), so the text caret, the cursor and a click's
    ripple don't count; a new list item or a page load does."""
    from PIL import Image, ImageChops
    gw, gh = max(1, w // 8), max(1, h // 8)
    small, diffs = None, []  # (time, mask of changed cells)
    for t, jpg in frames:
        im = Image.open(io.BytesIO(jpg))
        im.draft("L", (gw * 2, gh * 2))  # JPEG decodes small, quickly
        im = im.convert("L").resize((gw, gh), Image.BILINEAR)
        if small is not None:
            diffs.append((t, ImageChops.difference(im, small).point(lambda v: 255 if v > 24 else 0)))
        small = im
    least = 0.004 * gw * gh  # 0.4% of the page: about a line of text across a third of it
    times = [t for t, _ in diffs]

    def changed(start, end, view):
        x, y, vw, vh = view
        box = (int(x / 8), int(y / 8), int(math.ceil((x + vw) / 8)), int(math.ceil((y + vh) / 8)))
        for k in range(bisect.bisect_left(times, start), bisect.bisect_left(times, end)):
            t, mask = diffs[k]
            total = mask.histogram()[255]
            if total >= least and total - mask.crop(box).histogram()[255] >= least:
                return t
        return None
    return changed


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


def caption_image(text, sub, out_w, css_w, style=None):
    """A caption drawn like the page's own: white on a dark rounded box, sized to the video."""
    from PIL import Image, ImageDraw, ImageFont, ImageColor
    from reshoot.cut import font, wrap_text
    style = style or {}
    px = out_w / css_w
    size = max(1, round(min(max(18, css_w * .023), 30)*px))
    load = (lambda size, weight: ImageFont.truetype(style['font'], size)) if style.get('font') else font
    big, small = load(size, 600), load(max(1, round(size*.6)), 500)
    d = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    padx, pady = round(26*px), round(14*px)
    limit = max(1, out_w*(1-2*max(.1,style.get('margin',.065)))-2*padx)
    lines = wrap_text(text, big, limit, d)
    subs = wrap_text(sub, small, limit, d) if sub else []
    width = max([d.textlength(line, font=big) for line in lines]+[d.textlength(line, font=small) for line in subs]+[0])
    w = min(out_w, round(width+2*padx))
    h = round(len(lines)*size*1.25+len(subs)*size*.6*1.25+2*pady+(4*px if sub else 0))
    im = Image.new('RGBA', (w,h))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,w-1,h-1), radius=round(16*px), fill=ImageColor.getcolor(style.get('background', '#0e0d0cc8'), 'RGBA'))
    y = pady
    for line in lines:
        d.text(((w-d.textlength(line,font=big))/2,y),line,font=big,fill=style.get('foreground','white'))
        y += size*1.25
    y += 4*px if sub else 0
    for line in subs:
        d.text(((w-d.textlength(line,font=small))/2,y),line,font=small,fill=ImageColor.getcolor(style.get('foreground','white'), 'RGBA')[:3]+(190,))
        y += size*.6*1.25
    return im


def render(frames, events, out, css_w, css_h, out_w, out_h, z):
    """Writes the video: each output frame is the last frame Chrome painted by then, cropped to the camera, scaled
    to the output size, with the caption drawn on top."""
    from PIL import Image
    end = frames[-1][0] if frames and frames[-1][1] is None else None
    from reshoot.artifacts import images
    frames = images(frames)
    t0 = frames[0][0]
    times = [t - t0 for t, _ in frames]
    total = max((end or 0) - t0, times[-1] + 1 / FPS)
    n = max(1, round(total * FPS))
    events = [(t - t0, ev) for t, ev in events]
    changed = change_finder(((t - t0, jpg) for t, jpg in frames), css_w, css_h) if z.get("watch", True) else None
    path = camera_path(n, events, css_w, css_h, z, changed)
    caps = [(a, b, caption_image(text, sub, out_w, css_w, z.get('caption_style'))) for a, b, text, sub in captions(events)]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{out_w}x{out_h}", "-r", str(FPS), "-i", "-", "-vf", "format=yuv420p", "-color_range", "tv",
                           "-c:v", "libx264", "-preset", "ultrafast" if os.environ.get("RESHOOT_PREVIEW") else "slow", "-crf", "17", "-movflags", "+faststart", str(out)],
                          stdin=subprocess.PIPE)
    shown, im = None, None
    try:
        for k in range(n):
            t = k / FPS
            i = max(0, bisect.bisect_right(times, t) - 1)
            if i != shown:
                im, shown = Image.open(io.BytesIO(frames[i][1])).convert("RGB"), i
            sx, sy = im.width / css_w, im.height / css_h
            x, y, vw, vh = path[k]
            frame = im.resize((out_w, out_h), Image.LANCZOS, box=(max(0, x * sx), max(0, y * sy), min(im.width, (x + vw) * sx), min(im.height, (y + vh) * sy)),
                              reducing_gap=2.0)
            for a, b, cap in caps:  # fades in over 0.35 s, and out over 0.35 s once hidden, as in the page
                fade = 0.0 if t < a else min(1.0, (t - a) / 0.35, 1.0 if t < b else 1 - (t - b) / 0.35)
                if fade > 0:
                    layer = cap if fade >= 1 else cap.copy()
                    if fade < 1:
                        layer.putalpha(layer.getchannel("A").point(lambda v: round(v * fade)))
                    lift = round((1 - fade) * 12 * out_w / css_w)
                    style = z.get('caption_style', {})
                    margin = round(out_h*style.get('margin', .065))
                    ycap = margin-lift if style.get('position') == 'top' else out_h-margin-cap.height+lift
                    if cap.height > out_h-2*margin:
                        raise ValueError('caption exceeds the safe frame area; shorten it or increase the frame size')
                    frame.paste(layer, ((out_w - cap.width) // 2, ycap), layer)
            ff.stdin.write(frame.tobytes())
    finally:
        ff.stdin.close()
        if ff.wait():
            raise RuntimeError("ffmpeg couldn't write the zoomed video")
