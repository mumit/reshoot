"""Records a web page acting out a storyboard, in headless Chrome, so nothing but the page is ever captured.

A storyboard is a Python file with BEATS, a list of (name, JavaScript, seconds to hold afterwards). The JavaScript runs
in the page as the body of an async function, with __demo (overlay.js) for the cursor, typing and captions. A
storyboard may also set:

    URL     the page to open, if not given on the command line
    SIZE    "1280x720@1.5": CSS width x height @ device pixel ratio
    THEME   "dark" or "light", for prefers-color-scheme
    MOBILE  True for a phone layout (touch, mobile viewport)
    SETUP   beats to run before recording, in the same form as BEATS: logging in with a demo account, clearing
            what the last take left behind
    WARM    views (#hashes or URLs) to open before recording, so their data, map tiles and images are loaded
    SETTLE  seconds to wait after the page opens, for fonts and the first images (default 4)
    ASSETS  parts of URLs to list, such as ["/uploads/"]; by default every image and media file the page loads
    ZOOM    True to zoom in on clicks and typing (see zoom.py for the settings)

Every frame Chrome paints is kept with its time, and ffmpeg turns them into a steady 60 fps video. Next to OUT.mp4 it
writes OUT.assets.json (every image and media URL the page loaded, to check before sharing), OUT.beats.json (when
each beat starts in the video) and OUT.events.json (each action and caption, with where and when).
"""
import asyncio, base64, json, os, platform, runpy, shutil, socket, subprocess, tempfile, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAC_CHROMES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "/Applications/Chromium.app/Contents/MacOS/Chromium"]
OTHER_CHROMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


def find_chrome():
    """Chrome or Chromium: $RESHOOT_CHROME if set, or the usual places."""
    if os.environ.get("RESHOOT_CHROME"):
        return os.environ["RESHOOT_CHROME"]
    for c in MAC_CHROMES if platform.system() == "Darwin" else []:
        if Path(c).exists():
            return c
    for c in OTHER_CHROMES:
        if shutil.which(c):
            return shutil.which(c)
    raise SystemExit("can't find Chrome or Chromium: install one, or set RESHOOT_CHROME to its path")


def chrome_flags():
    """Extra flags: $RESHOOT_CHROME_FLAGS, and --no-sandbox as root (in a container), where Chrome won't start
    without it."""
    flags = os.environ.get("RESHOOT_CHROME_FLAGS", "").split()
    if hasattr(os, "geteuid") and os.geteuid() == 0 and "--no-sandbox" not in flags:
        flags.append("--no-sandbox")
    return flags


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Page:
    def __init__(self, ws, frames, assets=()):
        self.ws, self.n, self.waiting, self.frames, self.errors, self.assets = ws, 0, {}, frames, [], set()
        self.want = list(assets)
        self.beats = {}  # name: when the beat started (seconds since epoch, like the frames)
        self.events = []  # (when, what the page reported): actions and captions, for zooming afterwards
        self.loaded = asyncio.Event()  # cleared when the tab starts loading a new page, set when it's loaded
        self.loaded.set()

    async def read(self):
        import websockets
        try:
            await self._read()
        except websockets.ConnectionClosed:
            pass

    async def _read(self):
        async for raw in self.ws:
            m = json.loads(raw)
            if "id" in m and m["id"] in self.waiting:
                self.waiting.pop(m["id"]).set_result(m)
            elif m.get("method") == "Page.screencastFrame":
                p = m["params"]
                self.frames.append((p["metadata"]["timestamp"], base64.b64decode(p["data"])))
                await self.ws.send(json.dumps(dict(id=0, method="Page.screencastFrameAck", params=dict(sessionId=p["sessionId"]))))
            elif m.get("method") == "Network.requestWillBeSent":  # what the video can show
                url, kind = m["params"]["request"]["url"], m["params"].get("type")
                if url.startswith("data:"):
                    continue
                if any(w in url for w in self.want) if self.want else kind in ("Image", "Media"):
                    self.assets.add(url)
            elif m.get("method") == "Page.frameStartedLoading" and "parentId" not in m["params"].get("frame", {}):
                self.loaded.clear()
            elif m.get("method") == "Page.frameStartedNavigating" and m["params"].get("navigationType") != "sameDocument":
                self.loaded.clear()
            elif m.get("method") == "Runtime.bindingCalled" and m["params"]["name"] == "__reshoot":
                self.events.append((time.time(), json.loads(m["params"]["payload"])))
            elif m.get("method") == "Page.loadEventFired":
                self.loaded.set()
            elif m.get("method") == "Runtime.exceptionThrown":
                d = m["params"]["exceptionDetails"]
                self.errors.append(d.get("exception", {}).get("description", d.get("text")))

    async def cmd(self, method, **params):
        self.n += 1
        fut = asyncio.get_running_loop().create_future()
        self.waiting[self.n] = fut
        await self.ws.send(json.dumps(dict(id=self.n, method=method, params=params)))
        m = await fut
        if "error" in m:
            raise RuntimeError(f"{method}: {m['error']}")
        return m.get("result", {})

    async def run(self, js):
        try:
            r = await self.cmd("Runtime.evaluate", expression=f"(async () => {{ {js}\n }})()", awaitPromise=True,
                               returnByValue=True)
        except RuntimeError as e:  # the beat clicked a link and its page went away: that's fine
            if "destroyed" in str(e) or "navigated" in str(e):
                return None
            raise
        if "exceptionDetails" in r:
            d = r["exceptionDetails"]
            raise RuntimeError(d.get("exception", {}).get("description") or d.get("text", "the step failed"))
        return r.get("result", {}).get("value")

    async def go(self, view):
        """Opens a #hash in the same page, or a URL."""
        if view.startswith("#"):
            await self.cmd("Runtime.evaluate", expression=f"location.hash = {json.dumps(view)}")
        else:
            await self.cmd("Page.navigate", url=view)


async def play(page, beats, quiet=False):
    """Runs beats: each one's JavaScript, then a wait for any page it opened, then its hold."""
    for name, js, hold in beats:
        t = page.beats[name] = time.time()
        if js:
            try:
                await page.run(js)
            except RuntimeError as e:
                raise SystemExit(f"beat {name!r} failed: {e}") from None
            await asyncio.sleep(0.05)
            try:  # a beat that opened a new page: the hold starts once it's loaded
                await asyncio.wait_for(page.loaded.wait(), 20)
            except TimeoutError:
                print(f"  note: the page {name!r} opened took over 20 s to load")
        await asyncio.sleep(hold)
        if not quiet:
            print(f"  {name:22} {time.time() - t:5.1f}s", flush=True)


async def record(beats, url, w, h, dpr, frames, theme="dark", warm=(), mobile=False, settle=4, assets=(), setup=(),
                 post_captions=False):
    import websockets
    port, profile = free_port(), tempfile.mkdtemp(prefix="reshoot-")
    chrome = subprocess.Popen([find_chrome(), "--headless", "--hide-scrollbars", "--force-color-profile=srgb",
                               "--mute-audio", "--no-first-run", "--no-default-browser-check", *chrome_flags(),
                               f"--remote-debugging-port={port}", f"--user-data-dir={profile}", f"--window-size={w},{h}",
                               "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tabs = []
        for _ in range(150):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                if any(t["type"] == "page" for t in tabs):
                    break
            except OSError:
                pass
            time.sleep(0.1)
        else:
            raise SystemExit("Chrome didn't start (or has no tab to drive)")
        ws_url = next(t for t in tabs if t["type"] == "page")["webSocketDebuggerUrl"]
        async with websockets.connect(ws_url, max_size=200_000_000) as ws:
            page = Page(ws, frames, assets)
            reader = asyncio.create_task(page.read())
            await page.cmd("Page.enable"); await page.cmd("Runtime.enable"); await page.cmd("Network.enable")
            # The window can't go below 500 px wide; the device metrics can, so phone sizes come out right.
            await page.cmd("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=dpr, mobile=mobile)
            if mobile:
                await page.cmd("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
            await page.cmd("Emulation.setEmulatedMedia", features=[dict(name="prefers-color-scheme", value=theme)])
            # In every document the tab loads, so the overlay is there after a full page load too.
            await page.cmd("Runtime.addBinding", name="__reshoot")
            if post_captions:
                await page.cmd("Page.addScriptToEvaluateOnNewDocument", source="window.__reshootPostCaptions = true")
            await page.cmd("Page.addScriptToEvaluateOnNewDocument", source=(HERE / "overlay.js").read_text())
            await page.cmd("Page.navigate", url=url)
            await asyncio.sleep(settle)
            await page.run("await document.fonts.ready")
            if setup:
                print("  setup (not recorded)")
                await play(page, setup, quiet=True)
                page.beats.clear()
            for view in warm:
                await page.go(view)
                await asyncio.sleep(4)
            if setup or any(not v.startswith("#") for v in warm):  # back to the start page
                await page.go(url)
                await asyncio.sleep(settle)
            elif warm:
                await page.cmd("Runtime.evaluate", expression="location.hash = ''; scrollTo(0, 0)")
                await asyncio.sleep(2)
            got = await page.run("return [typeof __demo, innerWidth]")
            if got[0] != "object":
                raise RuntimeError("the overlay didn't load: " + ("; ".join(page.errors) or "no page errors"))
            if got[1] != w:
                print(f"  note: the page is {got[1]} px wide, not {w}")
            page.events.clear()  # what SETUP and WARM did isn't in the take
            await page.cmd("Page.startScreencast", format="jpeg", quality=92, maxWidth=int(w * dpr), maxHeight=int(h * dpr))
            await play(page, beats)
            frames.append((time.time(), None))  # when recording stopped: the last frame holds until here
            await page.cmd("Page.stopScreencast")
            await asyncio.sleep(0.3)
            reader.cancel()
            return page.errors, page.assets, page.beats, page.events
    finally:
        chrome.kill(); chrome.wait()
        shutil.rmtree(profile, ignore_errors=True)


def encode(frames, out, fps=60, size="1920:1080"):
    """Shows each frame until the next was painted, then resamples to a steady fps. Chrome sends a frame only when
    something changes, so a still page sends none, and the frame rate goes up and down with the motion."""
    end = frames[-1][0] if frames and frames[-1][1] is None else None
    frames = [f for f in frames if f[1] is not None]
    tmp = Path(tempfile.mkdtemp(prefix="reshoot-frames-"))
    try:
        lines = []
        for i, (t, jpg) in enumerate(frames):
            (tmp / f"{i:06}.jpg").write_bytes(jpg)
            nxt = frames[i + 1][0] if i + 1 < len(frames) else max(end or 0, t + 1 / fps)
            lines += [f"file '{tmp / f'{i:06}.jpg'}'", f"duration {max(nxt - t, 1 / 240):.5f}"]
        lines.append(f"file '{tmp / f'{len(frames) - 1:06}.jpg'}'")
        (tmp / "list.txt").write_text("\n".join(lines))
        # The last file is listed twice so its duration counts, and the second copy adds time of its own: -t cuts it.
        total = max(end or 0, frames[-1][0] + 1 / fps) - frames[0][0]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-t", f"{total:.3f}",
                        "-vf", f"fps={fps},scale={size}:flags=lanczos:out_range=tv,format=yuv420p", "-color_range", "tv",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-movflags", "+faststart", str(out)], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def parse_size(s):
    wh, dpr = s.split("@") if "@" in s else (s, "1")
    w, h = map(int, wh.split("x"))
    return w, h, float(dpr)


def main(a):
    """`reshoot web STORYBOARD OUT.mp4`"""
    from reshoot import zoom
    board = runpy.run_path(a.storyboard)
    url = a.url or board.get("URL") or "http://localhost:8000/"
    w, h, dpr = parse_size(a.size or board.get("SIZE", "1280x720@1.5"))
    theme = a.theme or board.get("THEME", "dark")
    z = zoom.settings(a.zoom if a.zoom is not None else board.get("ZOOM"))
    # Zoomed parts are enlarged, so the page is recorded sharper to begin with (up to 2x, and 4 pixels per CSS pixel).
    cap_dpr = min(dpr * min(z["scale"], 2), 4) if z else dpr
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    errors, assets, starts, events = asyncio.run(record(
        board["BEATS"], url, w, h, cap_dpr, frames, theme, board.get("WARM", ()), a.mobile or board.get("MOBILE", False),
        board.get("SETTLE", 4), board.get("ASSETS", ()), board.get("SETUP", ()), post_captions=bool(z)))
    out.with_suffix(".assets.json").write_text(json.dumps(sorted(assets), indent=1))
    if len(frames) < 3:
        raise SystemExit("no frames captured: did the page draw anything?")
    t0 = frames[0][0]
    out.with_suffix(".beats.json").write_text(json.dumps({n: max(0, round(t - t0, 3)) for n, t in starts.items()}, indent=1))
    out.with_suffix(".events.json").write_text(json.dumps([{"t": round(t - t0, 3), **ev} for t, ev in events], indent=1))
    span = frames[-1][0] - frames[0][0]
    gaps = sorted(b[0] - a_[0] for a_, b in zip(frames[:-1], frames[1:-1]))
    print(f"{len(frames)} frames over {span:.1f}s: {len(frames) / span:.0f} fps on average, "
          f"longest gap {gaps[-1] * 1000:.0f} ms, 95% of gaps under {gaps[int(len(gaps) * .95)] * 1000:.0f} ms")
    ow, oh = int(w * dpr) // 2 * 2, int(h * dpr) // 2 * 2
    if z:
        print(f"zooming ({sum(1 for _, e in events if e.get('kind') == 'act') // 2} actions)", flush=True)
        zoom.render(frames, events, out, w, h, ow, oh, z)
    else:
        encode(frames, out, size=f"{ow}:{oh}")
    print("wrote", out, f"| {len(assets)} images and media loaded (listed in {out.with_suffix('.assets.json').name})",
          "| page errors:", errors or "none")
