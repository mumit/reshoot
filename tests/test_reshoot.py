"""Fast tests use made-up frames and images. The browser test records the notes example in headless Chrome."""
import http.server, io, json, shutil, threading
from functools import partial
from pathlib import Path

import pytest
from PIL import Image

from reshoot import check, cut, rec, web, zoom
from reshoot.cli import main as cli

ROOT = Path(__file__).resolve().parents[1]
needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")


def jpg(colour, size=(320, 180)):
    b = io.BytesIO()
    Image.new("RGB", size, colour).save(b, "JPEG")
    return b.getvalue()


@needs_ffmpeg
def test_encode_holds_each_frame_until_the_next_and_the_last_until_the_end(tmp_path):
    frames = [(10.0, jpg("red")), (10.5, jpg("green")), (12.0, jpg("blue")), (13.0, None)]
    out = tmp_path / "t.mp4"
    web.encode(frames, out, size="320:180")
    assert cut.duration(out) == pytest.approx(3.0, abs=0.05)
    cut.ff("-ss", 1.0, "-i", out, "-frames:v", 1, tmp_path / "f.png")  # inside the green frame's 1.5 s
    r, g, b = Image.open(tmp_path / "f.png").convert("RGB").getpixel((160, 90))
    assert g > 100 and r < 60 and b < 60


def test_bold_text_uses_dejavus_bold_file_where_theres_no_weight_axis(tmp_path, monkeypatch):
    regular = tmp_path / "DejaVuSans.ttf"
    bold = tmp_path / "DejaVuSans-Bold.ttf"
    regular.touch(); bold.touch()
    monkeypatch.setattr(cut, "FONTS", [str(regular)])
    opened = []

    class Font:  # stands in for a font file with no weight axis
        def set_variation_by_axes(self, axes):
            raise OSError("no axes")

    monkeypatch.setattr("PIL.ImageFont.truetype", lambda path, size: opened.append(Path(path).name) or Font())
    cut.font(40, 700); cut.font(40, 450)
    assert opened == ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]


def act(t0, t1, rect):
    return [(t0, {"kind": "act", "phase": "start", "rect": rect}), (t1, {"kind": "act", "phase": "end", "rect": rect})]


def test_zoom_frames_nearby_actions_together_and_moves_out_when_quiet():
    z = zoom.settings(True)
    events = act(1, 2, [100, 100, 200, 40]) + act(2.5, 3, [320, 100, 60, 40]) + act(8, 9, [500, 500, 100, 40])
    auto, manual = zoom.targets(events, 1280, 720, z)
    assert len(auto) == 2 and not manual  # the first two are 0.5 s apart, so they share one view
    (a, b, (cx, cy, s)), second = auto
    assert a == pytest.approx(1 - z["lead"]) and b == pytest.approx(3 + z["hold"])
    assert (cx, cy) == (240, 120) and s == pytest.approx(1.8)  # the middle of both, enlarged as far as allowed
    path = zoom.camera_path(12 * 60, events, 1280, 720, z)
    assert path[0] == (0, 0, 1280, 720)  # starts with the whole page
    assert path[int(2.8 * 60)][2] < 1280 / 1.6  # zoomed in by the end of the second action
    assert path[int(6.5 * 60)][2] > 1280 * 0.95  # back out while nothing happens
    xs = [p[0] for p in path]
    assert max(abs(b - a) for a, b in zip(xs, xs[1:])) < 20  # moves smoothly, no jumps
    assert all(0 <= x and x + w <= 1280 + 1e-6 for x, _, w, _ in path)  # never looks past the page


def test_zoom_wont_crop_a_big_target_and_manual_zoom_wins():
    z = zoom.settings(2.5)
    assert zoom.fit([0, 0, 1200, 600], 1280, 720, z["scale"])[2] == 1.0
    events = act(1, 2, [100, 100, 50, 20]) + [(1.5, {"kind": "zoom", "rect": [900, 500, 100, 50], "scale": 2}),
                                               (5, {"kind": "zoom-out"})]
    auto, manual = zoom.targets(events, 1280, 720, z)
    assert manual == [(1.5 - z["lead"], 5, (950, 525, 2))]


def test_captions_come_from_the_pages_reports_as_plain_text():
    events = [(0.5, {"kind": "caption", "text": "Search by what&rsquo;s <i>in</i> them", "sub": "on &amp; off"}),
              (2.0, {"kind": "caption", "text": None}), (3.0, {"kind": "caption", "text": "The end", "sub": None})]
    assert zoom.captions(events) == [(0.5, 2.0, "Search by what&rsquo;s in them", "on & off"), (3.0, zoom.math.inf, "The end", None)]


@needs_ffmpeg
def test_zoom_render_enlarges_the_target_and_draws_the_caption(tmp_path):
    from PIL import ImageDraw
    im = Image.new("RGB", (640, 360), "black")
    ImageDraw.Draw(im).rectangle((300, 160, 340, 200), fill="red")  # the thing clicked
    b = io.BytesIO(); im.save(b, "JPEG")
    frames = [(0.0, b.getvalue()), (4.0, None)]
    events = act(1.5, 2.5, [300, 160, 40, 40]) + [(0.2, {"kind": "caption", "text": "Hello", "sub": None})]
    out = tmp_path / "z.mp4"
    zoom.render(frames, events, out, 640, 360, 640, 360, zoom.settings(2))
    assert cut.duration(out) == pytest.approx(4, abs=0.05)
    cut.ff("-ss", 0.1, "-i", out, "-frames:v", 1, tmp_path / "a.png")
    cut.ff("-ss", 2.8, "-i", out, "-frames:v", 1, tmp_path / "b.png")

    def red(p):
        b = Image.open(p).convert("RGB").tobytes()
        return sum(1 for i in range(0, len(b), 3) if b[i] > 150 and b[i + 1] < 80)

    assert red(tmp_path / "b.png") > 3 * red(tmp_path / "a.png")  # about 4 times the area at 2x
    bottom = Image.open(tmp_path / "b.png").convert("L").crop((200, 300, 440, 340))
    assert bottom.getextrema()[1] > 200  # the caption's white text


def test_rec_joins_typing_drops_the_focusing_click_and_hides_passwords(tmp_path):
    calls = [(1.0, {"kind": "click", "where": ["css", "#email"], "field": True})]
    calls += [(1.1 + i / 10, {"kind": "type", "where": ["css", "#email"], "value": "demo@example.com"[:i + 1]}) for i in range(16)]
    calls += [(4.0, {"kind": "click", "where": ["css", "#pw"], "field": True}),
              (4.2, {"kind": "type", "where": ["css", "#pw"], "value": "hunter2", "secret": True}),
              (5.0, {"kind": "key", "key": "Enter", "where": ["css", "#pw"]}),
              (5.1, {"kind": "key", "key": "Tab", "where": ["css", "#pw"]}),
              (7.0, {"kind": "scroll", "dy": 400}),
              (9.0, {"kind": "click", "where": ["text", ["button", "Save"]], "field": False})]
    beats = rec.beats_from(calls)
    assert [b[0] for b in beats] == ["type-email", "type-pw", "press-enter", "scroll", "click-save"]
    assert beats[0][1] == 'await __demo.type("#email", "demo@example.com")'
    assert "hunter2" not in repr(beats) and beats[1][1].endswith('"demo-password")') and "password" in beats[1][3]
    assert beats[3][1] == "await __demo.scroll(400)"
    assert beats[4][1] == 'await __demo.click(__demo.byText("button", "Save"))'
    assert all(0.4 <= b[2] <= 3.0 for b in beats[:-1]) and beats[-1][2] == 2.5
    out = tmp_path / "board.py"
    rec.write(out, "http://localhost:8000/", "1280x720@1.5", beats)
    board = __import__("runpy").run_path(str(out))
    assert board["URL"] == "http://localhost:8000/" and board["BEATS"][-1][0] == "end" and len(board["BEATS"]) == 6
    assert "put the demo account's password here" in out.read_text()


def test_size_parsing():
    assert web.parse_size("390x844@3") == (390, 844, 3.0)
    assert web.parse_size("1280x720") == (1280, 720, 1.0)


@needs_ffmpeg
def test_cut_pieces_join_and_make_gifs(tmp_path):
    src = tmp_path / "src.mp4"
    cut.ff("-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=4", *cut.ENC, src)
    a = cut.trim(src, 0.5, 2.5, tmp_path / "a.mp4", fade_out=0.3)
    card = cut.Card(640, 360).text(None, 150, "The end", 48).save(tmp_path / "end.png")
    b = cut.still(card, 1.5, tmp_path / "b.mp4")
    joined = cut.concat([a, b], tmp_path / "j.mp4")
    assert cut.duration(joined) == pytest.approx(3.5, abs=0.1)
    assert cut.probe(cut.speed(src, 0, 4, 4, tmp_path / "s.mp4"))[2] == pytest.approx(1.0, abs=0.1)
    gif = cut.gif(src, 1, 2, tmp_path / "g.gif", fps=10, width=320)
    assert Image.open(gif).n_frames == pytest.approx(10, abs=1)
    small = tmp_path / "small.mp4"
    cut.ff("-f", "lavfi", "-i", "color=size=320x180:duration=1", *cut.ENC, small)
    with pytest.raises(ValueError, match="different sizes"):
        cut.concat([a, small], tmp_path / "bad.mp4")


@needs_ffmpeg
def test_joined_cards_keep_their_colour_after_a_web_take(tmp_path):
    web.encode([(0.0, jpg((14, 13, 12))), (1.0, None)], tmp_path / "web.mp4", size="320:180")  # full-range JPEGs
    card = cut.still(cut.Card(320, 180, (14, 13, 12)).save(tmp_path / "c.png"), 1, tmp_path / "card.mp4", fade_in=0)
    cut.concat([tmp_path / "web.mp4", card], tmp_path / "j.mp4")
    cut.ff("-ss", 1.5, "-i", tmp_path / "j.mp4", "-frames:v", 1, tmp_path / "f.png")
    assert max(Image.open(tmp_path / "f.png").convert("RGB").getpixel((160, 90))) < 20  # not lifted to grey
    full = tmp_path / "full.mp4"
    cut.ff("-f", "lavfi", "-i", "color=size=320x180:duration=1", "-pix_fmt", "yuvj420p", "-color_range", "pc", full)
    with pytest.raises(ValueError, match="colour ranges"):
        cut.concat([full, card], tmp_path / "bad.mp4")


@needs_ffmpeg
def test_last_change_finds_where_the_picture_stops_changing(tmp_path):
    src = tmp_path / "s.mp4"
    cut.ff("-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=2", "-f", "lavfi", "-i",
           "color=size=320x180:rate=30:duration=2", "-filter_complex", "[0][1]concat=n=2:v=1", *cut.ENC, src)
    assert cut.last_change(src) == pytest.approx(2.0, abs=0.1)


@needs_ffmpeg
def test_window_clip_finds_the_window_and_rounds_its_corners(tmp_path):
    from PIL import ImageDraw
    frame = Image.new("RGB", (400, 300), "black")  # like a `reshoot window` recording: a window on black
    ImageDraw.Draw(frame).rounded_rectangle((50, 40, 349, 259), radius=30, fill=(200, 60, 60))
    frame.save(tmp_path / "f.png")
    mov = tmp_path / "w.mp4"
    cut.ff("-loop", 1, "-i", tmp_path / "f.png", "-t", 1, *cut.ENC, mov)
    assert cut.window_box(mov) == (300, 220, 50, 40)
    assert cut.corner_radius(mov) == pytest.approx(30, abs=3)
    bg = cut.Card(640, 360, (240, 240, 240)).save(tmp_path / "bg.png")
    cut.window_clip(mov, bg, 100, 50, tmp_path / "clip.mp4")
    cut.ff("-ss", 0.5, "-i", tmp_path / "clip.mp4", "-frames:v", 1, tmp_path / "out.png")
    out = Image.open(tmp_path / "out.png").convert("RGB")
    assert min(out.getpixel((103, 53))) > 200  # the corner shows the card, not the black around the window
    assert out.getpixel((250, 160))[0] > 150  # the window itself


def test_check_shows_only_whats_new_and_remembers_what_passed(tmp_path, capsys):
    shots, review = tmp_path / "shots", tmp_path / "review"
    shots.mkdir()
    for i, c in enumerate(["red", "green", "blue", "white", "black"]):
        (shots / f"{i}.jpg").write_bytes(jpg(c))
    (shots / "copy.jpg").write_bytes((shots / "0.jpg").read_bytes())  # the same image twice is shown once
    run = lambda *a: pytest.raises(SystemExit, cli, ["check", "--review", str(review), *a]).value.code
    assert run(str(shots)) == 1
    key = json.loads((review / "key.json").read_text())
    assert len(key) == 5 and sorted(p.name for p in review.glob("*.jpg")) == ["01.jpg", "02.jpg"]
    assert run("--fail", "1-2") == 0
    assert "1.jpg" in capsys.readouterr().out
    assert run("--ok") == 0
    assert len(json.loads((review / "checked.json").read_text())) == 4
    assert run(str(shots)) == 1  # only the one that failed is left, until it's taken out of the demo
    assert list(json.loads((review / "key.json").read_text()).values())[0][0].endswith("1.jpg")
    (shots / "1.jpg").unlink()
    assert run(str(shots)) == 0


def test_check_reads_asset_lists(tmp_path):
    (tmp_path / "a.jpg").write_bytes(jpg("red"))
    (tmp_path / "take.assets.json").write_text(json.dumps([str(tmp_path / "a.jpg")]))
    assert [s for s, _ in check.items([str(tmp_path / "take.assets.json")])] == [str(tmp_path / "a.jpg")]


@pytest.fixture
def notes_app():
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "examples/notes"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()


def record(board, out, url):
    with pytest.raises(SystemExit) as e:
        cli(["web", str(board), str(out), "--url", url, "--size", "640x360@1"])
    return e.value.code


def shoot(tmp_path, takes, port):
    """A reshoot.toml with a little web server as the app, and the given [[take]] lines."""
    app = f'python3 -m http.server {port} --bind 127.0.0.1 --directory {tmp_path}'
    (tmp_path / "reshoot.toml").write_text(f"""
report = "{tmp_path}/run.json"
[app]
run = "{app}"
url = "http://127.0.0.1:{port}/"
{takes}
[keep]
"{tmp_path}/a.jpg" = "{tmp_path}/docs/a.jpg"
[check]
sources = ["{tmp_path}/a.jpg"]
review = "{tmp_path}/review"
""")
    return tmp_path / "reshoot.toml"


def free_port():
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_run_does_every_step_keeps_the_files_and_stops_the_app(tmp_path, monkeypatch):
    port, out = free_port(), tmp_path / "gh-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    (tmp_path / "a.jpg").write_bytes(jpg("red"))
    take = f'[[take]]\nrun = "python3 -c \'open(\\"{tmp_path}/took\\", \\"w\\")\'"'
    with pytest.raises(SystemExit) as e:
        cli(["run", str(shoot(tmp_path, take, port))])
    assert e.value.code == 0
    r = json.loads((tmp_path / "run.json").read_text())
    assert r["ok"] and r["unchecked"] == 1 and (tmp_path / "took").exists() and (tmp_path / "docs/a.jpg").exists()
    assert "ok=true" in out.read_text() and "unchecked=1" in out.read_text()
    with pytest.raises(OSError):  # the app was stopped
        __import__("urllib.request").request.urlopen(f"http://127.0.0.1:{port}/", timeout=2)


def test_run_stops_at_a_failed_take_and_says_so(tmp_path, monkeypatch):
    port, out = free_port(), tmp_path / "gh-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    (tmp_path / "a.jpg").write_bytes(jpg("red"))
    takes = '[[take]]\nrun = "false"\n[[take]]\nrun = "touch never"'
    with pytest.raises(SystemExit) as e:
        cli(["run", str(shoot(tmp_path, takes, port))])
    assert "failed" in str(e.value.code)
    r = json.loads((tmp_path / "run.json").read_text())
    assert not r["ok"] and [s["ok"] for s in r["steps"]] == [False] and not (tmp_path / "docs").exists()
    assert "ok=false" in out.read_text()


@pytest.mark.browser
@needs_ffmpeg
def test_records_the_notes_example(tmp_path, notes_app):
    out = tmp_path / "notes.mp4"
    assert record(ROOT / "examples/notes/storyboard.py", out, notes_app) == 0
    beats = cut.beats(out)
    assert list(beats) == ["home", "type", "add", "search", "end"] and beats["home"] == 0
    assert cut.probe(out)[:2] == (640, 360)
    assert cut.duration(out) == pytest.approx(beats["end"] + 2.5, abs=0.5)


@pytest.mark.browser
@needs_ffmpeg
def test_zoomed_take_reports_its_actions(tmp_path, notes_app):
    out = tmp_path / "zoom.mp4"
    with pytest.raises(SystemExit) as e:
        cli(["web", str(ROOT / "examples/notes/storyboard.py"), str(out), "--url", notes_app, "--size", "640x360@1",
             "--zoom"])
    assert e.value.code == 0
    events = json.loads(out.with_suffix(".events.json").read_text())
    assert [e["phase"] for e in events if e["kind"] == "act"] == ["start", "end"] * 3  # type, click Add, type
    assert any(e["kind"] == "caption" and e["text"] for e in events)
    assert cut.probe(out)[:2] == (640, 360)


def test_rec_clears_a_field_that_was_emptied_or_changed():
    w = ["css", "#q"]
    calls = [(1.0, {"kind": "type", "where": w, "value": "bread", "before": ""}),
             (3.0, {"kind": "click", "where": ["css", "#other"], "field": False}),
             (4.0, {"kind": "type", "where": w, "value": "brea", "before": "bread"}),
             (4.1, {"kind": "type", "where": w, "value": "", "before": "bread"}),
             (6.0, {"kind": "click", "where": ["css", "#other"], "field": False}),
             (7.0, {"kind": "type", "where": w, "value": "tap water", "before": "tap"})]
    js = [b[1] for b in rec.beats_from(calls)]
    assert js[0] == 'await __demo.type("#q", "bread")'
    assert js[2] == 'await __demo.type("#q", "", { clear: true })'  # emptied: cleared on replay, not left alone
    assert js[4] == 'await __demo.type("#q", " water")'  # added to what was there: only the new words


@pytest.mark.browser
@needs_ffmpeg
def test_rec_replays_clearing_a_field_and_skips_background_clicks(tmp_path, notes_app):
    import asyncio, sys
    sys.path.insert(0, str(ROOT / "tests"))
    import person
    calls = []
    asyncio.run(rec.session(notes_app, 1280, 720, calls, headless=True, drive=person.clearing_tour))
    beats = rec.beats_from(calls)
    js = [b[1] for b in beats]
    assert js == ['await __demo.type("#q", "bread")', 'await __demo.click("#text")',
                  'await __demo.type("#q", "", { clear: true })', 'await __demo.click("#text")',
                  'await __demo.type("#q", "tap")'], js  # no beat for the background click
    board = tmp_path / "board.py"
    rec.write(board, notes_app, "640x360@1", beats)
    board.write_text(board.read_text().replace('    ("end", "__demo.hide()", 2.5),', """    ("check", "if (document.querySelector('#q').value !== 'tap') throw new Error('search is ' + document.querySelector('#q').value)", 0),"""))
    assert record(board, tmp_path / "replay.mp4", notes_app) == 0


@pytest.mark.browser
def test_rec_picks_stable_selectors(tmp_path):
    import asyncio, sys
    sys.path.insert(0, str(ROOT / "tests"))
    import person
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "tests/boards"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    async def tour(page):
        await asyncio.sleep(1)
        for sel in ["[data-testid=save]", "#css-8f3k2z", "input[name=email]", ".toolbar button:nth-of-type(2)", "nav a"]:
            await person.click(page, sel)
        await person.click(page, "#pw"); await person.type(page, "secret1")

    calls = []
    try:
        asyncio.run(rec.session(f"http://127.0.0.1:{server.server_port}/selectors.html", 800, 600, calls, headless=True, drive=tour))
    finally:
        server.shutdown()
    found = [c["where"] for _, c in calls if c["kind"] == "click"]
    assert found[0] == ["css", '[data-testid="save"]']  # a test id first
    assert found[1] == ["text", ["button", "Generated id"]]  # a made-up id is skipped for its words
    assert found[2] == ["css", 'input[name="email"]']
    assert found[3] == ["css", "body > div > button:nth-of-type(2)"]  # two buttons say Share: found by place
    assert found[4] == ["text", ["a", "One"]]
    assert [c.get("secret") for _, c in calls if c["kind"] == "type"][-1] is True


@pytest.mark.browser
@needs_ffmpeg
def test_rec_writes_a_storyboard_that_replays(tmp_path, notes_app):
    import asyncio, sys
    sys.path.insert(0, str(ROOT / "tests"))
    import person
    calls = []
    asyncio.run(rec.session(notes_app, 1280, 720, calls, headless=True, drive=person.notes_tour))
    beats = rec.beats_from(calls)
    assert [b[0] for b in beats] == ["click-about", "click-back", "type-text", "press-enter", "type-q"]
    board = tmp_path / "board.py"
    rec.write(board, notes_app, "640x360@1", beats)
    text = board.read_text().replace('    ("end", "__demo.hide()", 2.5),', """    ("check", "const n = [...document.querySelectorAll('#list li')].filter(li => li.textContent.includes('Buy stamps')).length; if (n !== 1) throw new Error(n + ' notes')", 0),""")
    board.write_text(text)  # the note was added once: Enter's own click on Add wasn't recorded too
    assert record(board, tmp_path / "replay.mp4", notes_app) == 0


@pytest.mark.browser
@needs_ffmpeg
def test_setup_runs_first_and_beats_can_open_new_pages(tmp_path, notes_app):
    out = tmp_path / "pages.mp4"
    assert record(ROOT / "tests/boards/pages.py", out, notes_app) == 0  # each beat throws if it isn't so
    assert list(cut.beats(out)) == ["home", "about", "check", "back"]  # SETUP's beats aren't in the take
