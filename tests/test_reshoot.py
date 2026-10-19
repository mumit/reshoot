"""Fast tests use made-up frames and images. The browser test records the notes example in headless Chrome."""
import http.server, io, json, shutil, threading
from functools import partial
from pathlib import Path

import pytest
from PIL import Image

from reshoot import check, cut, web
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
def test_setup_runs_first_and_beats_can_open_new_pages(tmp_path, notes_app):
    out = tmp_path / "pages.mp4"
    assert record(ROOT / "tests/boards/pages.py", out, notes_app) == 0  # each beat throws if it isn't so
    assert list(cut.beats(out)) == ["home", "about", "check", "back"]  # SETUP's beats aren't in the take
