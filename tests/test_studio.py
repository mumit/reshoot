import json
import threading
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
import pytest
from reshoot import project, studio

BOARD = '''schema_version = 1
url = "http://127.0.0.1:8765/"

# the opening
[[beat]]
id = "intro"
caption = "Find a note"   # short
hold = 1.5

[[beat]]
id = "search"
hold = 2.0
[[beat.action]]
type = "type"
target = {css = "#q"}
text = "bike"
'''


def test_studio_edits_change_one_line_and_keep_the_rest(tmp_path):
    import tomllib
    board = tmp_path / 'storyboard.toml'
    board.write_text(BOARD)
    studio.edit(board, {'beat': 'search', 'caption': 'Every "matching" note', 'sub': 'as you type'})
    studio.edit(board, {'beat': 'intro', 'caption': ''})
    studio.edit(board, {'look': {'position': 'top', 'background': '#1d4ed8e6'}})
    text = board.read_text()
    assert '# the opening' in text and 'hold = 1.5' in text  # comments and other keys stay
    data = tomllib.loads(text)
    assert 'caption' not in data['beat'][0]
    assert data['beat'][1]['caption'] == 'Every "matching" note' and data['beat'][1]['sub'] == 'as you type'
    assert data['beat'][1]['action'][0]['text'] == 'bike'
    assert data['caption'] == {'position': 'top', 'background': '#1d4ed8e6'}
    assert text.index('caption = "Every') < text.index('[[beat.action]]')  # in the beat, not its action
    studio.edit(board, {'look': {'position': 'bottom', 'background': ''}})
    assert tomllib.loads(board.read_text())['caption'] == {'position': 'bottom'}


@pytest.mark.parametrize('change, error', [
    ({'beat': 'missing', 'caption': 'x'}, 'no beat'),
    ({'look': {'background': 'blue'}}, 'colour'),
    ({'look': {'position': 'left'}}, 'top or bottom'),
    ({'look': {'font': 'x.ttf'}}, 'does not change'),
])
def test_studio_refuses_a_change_it_cannot_make_and_keeps_the_file(tmp_path, change, error):
    board = tmp_path / 'storyboard.toml'
    board.write_text(BOARD)
    with pytest.raises(ValueError, match=error):
        studio.edit(board, change)
    assert board.read_text() == BOARD


def test_studio_leaves_a_multiline_caption_to_the_file(tmp_path):
    board = tmp_path / 'storyboard.toml'
    board.write_text(BOARD.replace('caption = "Find a note"   # short', 'caption = """Find\na note"""'))
    with pytest.raises(ValueError, match='multi-line'):
        studio.edit(board, {'beat': 'intro', 'caption': 'One line'})


def test_studio_needs_a_versioned_project_with_a_toml_storyboard(tmp_path):
    with pytest.raises(ValueError, match='no '):
        studio.project(tmp_path)
    (tmp_path / 'reshoot.toml').write_text('[[take]]\nrun = "true"\n')
    with pytest.raises(ValueError, match='versioned'):
        studio.project(tmp_path)


@pytest.mark.browser
def test_the_studio_edits_a_caption_and_recuts_the_run(tmp_path):
    from playwright.sync_api import sync_playwright
    from test_reshoot import free_port
    from reshoot import web
    from reshoot.cli import main
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    port = free_port()
    config = tmp_path / 'reshoot.toml'
    config.write_text(config.read_text().replace('8765', str(port)).replace('scan = true', 'scan = false'))
    board = tmp_path / 'storyboard.toml'
    board.write_text(board.read_text().replace('8765', str(port)))
    with pytest.raises(SystemExit) as result:
        main(['run', str(config)])
    assert result.value.code == 0
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with pytest.raises(urllib.error.HTTPError, match='403'):  # another site's page can't change the story
            urllib.request.urlopen(urllib.request.Request(url + 'edit', data=b'{}', method='POST', headers={
                'Content-Type': 'application/json', 'Origin': 'https://elsewhere.example'}))
        with pytest.raises(urllib.error.HTTPError, match='404'):
            urllib.request.urlopen(url.rsplit('/', 2)[0] + '/guess/')
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page()
            page.goto(url)
            assert page.locator('.beat').count() == 4 and page.locator('.seg').count() >= 3
            assert page.locator('.beat[data-beat=search] .checks').inner_text() == '2 of 2 result checks passed'
            search = page.locator('.beat[data-beat=search]')
            assert search.locator('.pending').is_hidden()
            search.locator('input[name=caption]').fill('A caption from the studio')
            search.locator('input[name=caption]').press('Tab')
            page.wait_for_selector('#toast.on')
            assert search.locator('.pending').is_visible()
            assert 'caption = "A caption from the studio"' in board.read_text()
            page.locator('.look input[name=background]').fill('blue')
            page.locator('.look input[name=background]').press('Tab')
            page.wait_for_function("document.getElementById('toast').textContent.includes('colour')")
            assert 'blue' not in board.read_text()
            search.locator('.play').click()  # plays the beat, from its place in the video
            page.wait_for_function("!document.getElementById('video').paused")
            start = float(search.get_attribute('data-start'))
            assert page.evaluate("document.getElementById('video').currentTime") >= start - .1
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=recut]')
            assert 'a re-cut of' in page.locator('.status').inner_text()
            assert page.locator('.beat[data-beat=search] .pending').is_hidden()
            assert page.locator('#to-accept').count() == 1
            browser.close()
    finally:
        httpd.shutdown()
    newest = max((tmp_path / 'takes/runs').glob('*/run.json'), key=lambda p: json.loads(p.read_text())['finished_at'])
    assert 'A caption from the studio' in (newest.parent / 'takes/demo-final.srt').read_text()
