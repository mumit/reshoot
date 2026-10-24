import json
import http.server
import threading
from functools import partial
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import story
from reshoot.cli import main


def board(path, url, action='', expectation=''):
    path.write_text(f'''schema_version = 1
url = "{url}"
size = "640x360@1"
[[beat]]
id = "result"
hold = 0.3
{action}
{expectation}
''')
    return path


@pytest.fixture
def native_page(tmp_path):
    from PIL import Image
    Image.new('RGB', (20,20), 'red').save(tmp_path / 'asset.png')
    (tmp_path / 'frame.html').write_text('<input id=inside>')
    (tmp_path / 'next.html').write_text('<h1 id=next>Next page</h1>')
    (tmp_path / 'index.html').write_text('''<html><body>
<button id="good" onclick="this.textContent = event.isTrusted ? 'native click' : 'fake click'">Run</button>
<button class="duplicate">One</button><button class="duplicate">Two</button>
<div style="position:relative;width:200px;height:80px"><button id="covered">Covered</button>
<div style="position:absolute;inset:0;background:#ccc">Cover</div></div>
<button disabled id="disabled">Disabled</button><button id="hidden" style="display:none">Hidden</button>
<input id="controlled" oninput="if(!event.isTrusted)this.value=''">
<input id="field"><div id="result">Expected result</div>
<img src="asset.png" alt="Synthetic square"><iframe id="frame" src="frame.html"></iframe>
<div id="host"></div><script>document.querySelector('#host').attachShadow({mode:'open'}).innerHTML='<input id="shadow">'</script>
<input id="upload" type="file" onchange="document.querySelector('#result').textContent=this.files[0].name">
<a id="next-link" href="next.html">Next</a>
<select id="label"><option value="b">bug</option><option value="f">feature</option></select>
</body></html>''')
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{server.server_port}/'
    server.shutdown()


def test_story_rejects_duplicate_beats_and_unknown_operations(tmp_path):
    p = board(tmp_path / 'story.toml', 'http://localhost/')
    p.write_text(p.read_text() + '\n[[beat]]\nid="result"\n')
    with pytest.raises(ValueError, match='unique'):
        story.load(p)
    p = board(p, 'http://localhost/', '[[beat.action]]\ntype="force-click"')
    with pytest.raises(ValueError, match='unsupported'):
        story.load(p)


@pytest.mark.browser
def test_native_click_is_trusted_and_result_is_verified(tmp_path, native_page):
    p = board(tmp_path / 'story.toml', native_page, '''[[beat.action]]
type = "click"
target = {css = "#good"}''', '''[[beat.expect]]
type = "text"
target = {css = "#good"}
contains = "native click"''')
    with pytest.raises(SystemExit) as result:
        main(['web', str(p), str(tmp_path / 'take.mp4')])
    assert result.value.code == 0
    report = json.loads((tmp_path / 'take.take.json').read_text())
    assert report['status'] == 'completed'
    assert any(resource['status'] == 'saved' for resource in report['resources'])
    assert report['beats'][0]['status'] == 'passed'
    assert report['beats'][0]['expectations'][0]['actual'] == 'native click'


@pytest.mark.browser
@pytest.mark.parametrize('selector', ['#covered', '#disabled', '.duplicate', '#absent', '#hidden'])
def test_native_action_does_not_bypass_actionability(tmp_path, native_page, selector):
    p = board(tmp_path / 'story.toml', native_page, f'''[[beat.action]]
type = "click"
target = {{css = "{selector}"}}
timeout = 500''')
    with pytest.raises(SystemExit) as result:
        main(['web', str(p), str(tmp_path / 'take.mp4')])
    assert result.value.code == 2
    report = json.loads((tmp_path / 'take.take.json').read_text())
    assert report['status'] == 'failed' and report['beats'][0]['status'] == 'failed'
    assert (tmp_path / report['failure_screenshot']).exists()
    assert not (tmp_path / 'take.mp4').exists()


@pytest.mark.browser
def test_wrong_result_fails_even_after_successful_action(tmp_path, native_page):
    p = board(tmp_path / 'story.toml', native_page, '', '''[[beat.expect]]
type = "text"
target = {css = "#result"}
contains = "wrong result"
timeout = 500''')
    with pytest.raises(SystemExit) as result:
        main(['web', str(p), str(tmp_path / 'take.mp4')])
    assert result.value.code == 2
    assert json.loads((tmp_path / 'take.take.json').read_text())['beats'][0]['status'] == 'failed'


def test_story_errors_name_the_beat_and_operation(tmp_path):
    p = board(tmp_path / 'story.toml', 'http://localhost/', '[[beat.action]]\ntype="key"\nkey="Tab"')
    with pytest.raises(ValueError, match=r"beat 'result', action 1 \(key\): target needs exactly one"):
        story.load(p)
    p = board(p, 'http://localhost/', '[[beat.action]]\ntype="select"\ntarget={css="#label"}')
    with pytest.raises(ValueError, match='select needs option'):
        story.load(p)


@pytest.mark.browser
def test_select_chooses_a_dropdown_option_by_its_label(tmp_path, native_page):
    p = board(tmp_path / 'story.toml', native_page, '''[[beat.action]]
type = "select"
target = {css = "#label"}
option = "feature"''', '''[[beat.expect]]
type = "value"
target = {css = "#label"}
value = "f"''')
    with pytest.raises(SystemExit) as result:
        main(['web', str(p), str(tmp_path / 'take.mp4')])
    assert result.value.code == 0
    assert json.loads((tmp_path / 'take.take.json').read_text())['beats'][0]['status'] == 'passed'


def test_rec_toml_writes_dropdown_choices_as_select_actions(tmp_path):
    from reshoot import rec
    path = tmp_path / 'recorded.toml'
    rec.write_toml(path, 'http://localhost/', '640x360@1', [
        (0, {'kind': 'click', 'where': ['css', '#label']}),
        (1, {'kind': 'select', 'where': ['css', '#label'], 'option': 'feature'})])
    actions = [a for beat in story.load(path)['beat'] for a in beat['action']]
    assert actions == [{'type': 'select', 'target': {'css': '#label'}, 'option': 'feature'}]


def test_rec_toml_keeps_target_and_replaces_password(tmp_path):
    from reshoot import rec
    path = tmp_path / 'recorded.toml'
    calls = [(0, {'kind': 'type', 'where': ['css', '#pw'], 'value': 'secret-pass', 'secret': True}),
             (1, {'kind': 'key', 'where': ['css', '#pw'], 'key': 'Enter'})]
    rec.write_toml(path, 'http://localhost/', '640x360@1', calls)
    data = story.load(path)
    assert data['beat'][0]['action'][0]['text'] == 'demo-password'
    assert data['beat'][1]['action'][0]['target'] == {'css': '#pw'}
    assert 'secret-pass' not in path.read_text()
    with pytest.raises(ValueError, match='unsupported'):
        rec.write_toml(path, 'http://localhost/', '640x360@1', [(0, {'kind': 'unsupported-change'})])


@pytest.mark.browser
def test_partial_capture_replays_previous_actions(tmp_path, native_page):
    path = tmp_path / 'partial.toml'
    path.write_text(f'''schema_version=1
url="{native_page}"
size="640x360@1"
[[beat]]
id="prepare"
hold=0
[[beat.action]]
type="type"
target={{css="#field"}}
text="Ready"
[[beat]]
id="result"
hold=0.1
[[beat.expect]]
type="value"
target={{css="#field"}}
value="Ready"
''')
    with pytest.raises(SystemExit) as result:
        main(['web', str(path), str(tmp_path/'partial.mp4'), '--from-beat', 'result'])
    assert result.value.code == 0
    data = json.loads((tmp_path/'partial.take.json').read_text())
    assert data['replayed_before'] == ['prepare']
    assert [b['id'] for b in data['beats']] == ['result']


@pytest.mark.browser
def test_native_iframe_shadow_upload_and_navigation(tmp_path, native_page):
    fixture = tmp_path / 'demo.txt'
    fixture.write_text('made-up fixture')
    path = tmp_path / 'complex.toml'
    path.write_text(f'''schema_version=1
url="{native_page}"
size="800x600@1"
[[beat]]
id="fields"
hold=0.1
[[beat.action]]
type="type"
target={{css="#controlled"}}
text="Controlled"
[[beat.expect]]
type="value"
target={{css="#controlled"}}
value="Controlled"
[[beat.action]]
type="type"
target={{frame="#frame",css="#inside"}}
text="Inside"
[[beat.expect]]
type="value"
target={{frame="#frame",css="#inside"}}
value="Inside"
[[beat.action]]
type="type"
target={{css="#shadow"}}
text="Shadow"
[[beat.expect]]
type="value"
target={{css="#shadow"}}
value="Shadow"
[[beat.action]]
type="upload"
target={{css="#upload"}}
file="demo.txt"
[[beat.expect]]
type="text"
target={{css="#result"}}
contains="demo.txt"
[[beat]]
id="navigate"
hold=0.1
[[beat.action]]
type="click"
target={{css="#next-link"}}
[[beat.expect]]
type="text"
target={{css="#next"}}
contains="Next page"
''')
    with pytest.raises(SystemExit) as result:
        main(['web',str(path),str(tmp_path/'complex.mp4')])
    assert result.value.code == 0
    data = json.loads((tmp_path/'complex.take.json').read_text())
    assert all(beat['status'] == 'passed' for beat in data['beats'])


@pytest.mark.browser
@pytest.mark.parametrize('zoomed', [False, True, 'styled'])
@pytest.mark.parametrize('navigate', [False, True])
def test_native_caption_is_visible_with_and_without_zoom(tmp_path, native_page, zoomed, navigate):
    from reshoot import cut
    from PIL import Image
    target = '#next-link' if navigate else '#good'
    p = board(tmp_path / 'caption.toml', native_page,
              f'[[beat.action]]\ntype="click"\ntarget={{css="{target}"}}')
    text = p.read_text().replace('schema_version = 1\n', f'schema_version = 1\nzoom = {str(zoomed is True).lower()}\n')
    if zoomed == 'styled':
        text = text.replace('[[beat]]', '[caption]\nposition="top"\nmargin=0.05\n[[beat]]', 1)
    p.write_text(text.replace('id = "result"\n', 'id = "result"\ncaption = "Expected result"\n'))
    output = tmp_path / 'caption.mp4'
    with pytest.raises(SystemExit) as result:
        main(['web', str(p), str(output)])
    assert result.value.code == 0
    cut.ff('-ss', max(0,cut.duration(output)-.12), '-i', output, '-frames:v', 1, tmp_path/'frame.png')
    im = Image.open(tmp_path/'frame.png').convert('RGB')
    ys = range(30,65) if zoomed == 'styled' else range(298,327)
    pixels = [im.getpixel((x, y)) for x in range(240,400) for y in ys]
    assert sum(max(pixel) < 150 for pixel in pixels) / len(pixels) > .6  # caption background, allowing white letters


@pytest.mark.browser
def test_native_recording_includes_the_bottom_of_a_tall_viewport(tmp_path, native_page):
    index = tmp_path/'index.html'
    index.write_text(index.read_text()+'<div style="position:fixed;bottom:0;left:0;right:0;height:30px;background:rgb(255,0,0)"></div>')
    p = board(tmp_path/'edges.toml', native_page)
    p.write_text(p.read_text().replace('640x360','1280x720').replace('hold = 0.3','hold = 0.6'))
    output = tmp_path/'edges.mp4'
    with pytest.raises(SystemExit) as result:
        main(['web', str(p), str(output)])
    assert result.value.code == 0
    from reshoot import cut
    from PIL import Image
    cut.ff('-ss', .3, '-i', output, '-frames:v', 1, tmp_path/'edges.png')
    im = Image.open(tmp_path/'edges.png').convert('RGB')
    r,g,b = im.getpixel((640,710))
    assert r > 200 and g < 30 and b < 30


@pytest.mark.browser
def test_a_port_chrome_refuses_is_explained(tmp_path):
    p = board(tmp_path / 'story.toml', 'http://127.0.0.1:5060/')
    with pytest.raises(SystemExit) as result:
        main(['web', str(p), str(tmp_path / 'take.mp4')])
    assert result.value.code == 2
    error = json.loads((tmp_path / 'take.take.json').read_text())['error']
    assert error.startswith('opening the storyboard url failed') and '--explicitly-allowed-ports' in error


@pytest.mark.browser
def test_the_video_shows_a_result_through_its_hold(tmp_path):
    """The beat's evidence used to be a screenshot, which could take the frame showing the result: a still page sends
    no other, so the video showed the old page for the whole hold. A React app at a pixel ratio of 2 did this on every
    take; this page doesn't trigger it, so it checks the behavior rather than reproducing the race."""
    import subprocess
    from PIL import Image
    cards = ''.join(f'<div style="display:inline-block;width:90px;height:40px;margin:4px;border-radius:8px;'
                    f'box-shadow:0 2px 8px rgba(0,0,0,.3);background:#fff">Card {i}</div>' for i in range(300))
    (tmp_path / 'index.html').write_text('<body style="margin:0;background:#fff"><button id="go" '
                                         'onclick="document.body.style.background=\'#e00\';this.textContent=\'Done\'">Go</button>'
                                         + cards + '</body>')
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        p = tmp_path / 'story.toml'
        p.write_text(f'''schema_version = 1
url = "http://127.0.0.1:{server.server_port}/"
size = "960x540@2"
[[beat]]
id = "go"
hold = 1.5
[[beat.action]]
type = "click"
target = {{css = "#go"}}
[[beat.expect]]
type = "text"
target = {{css = "#go"}}
contains = "Done"
[[beat]]
id = "end"
hold = 0.3
''')
        with pytest.raises(SystemExit) as result:
            main(['web', str(p), str(tmp_path / 'take.mp4')])
        assert result.value.code == 0
    finally:
        server.shutdown()
    beats = json.loads((tmp_path / 'take.beats.json').read_text())
    at = beats['go'] + 1.2  # well after the click, still inside the hold
    frame = tmp_path / 'frame.png'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(tmp_path / 'take.mp4'), '-vf', f"select='gte(t,{at})'",
                    '-frames:v', '1', '-y', str(frame)], check=True)
    def red(path):  # most of the page's background shows between the cards, whatever the image size
        data = Image.open(path).convert('RGB').resize((96, 54)).tobytes()
        pixels = [data[i:i + 3] for i in range(0, len(data), 3)]
        return sum(r > 180 and g < 80 for r, g, b in pixels) > len(pixels) * .2
    assert red(frame), 'the video still shows the page before the click'
    assert red(tmp_path / 'take.evidence/go.png'), 'the evidence frame is not the result'
