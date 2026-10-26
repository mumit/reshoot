import json
import tomllib
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
    with pytest.raises(ValueError, match='more than one line'):
        studio.edit(board, {'beat': 'intro', 'caption': 'One line'})


def test_studio_needs_a_versioned_project_with_a_toml_storyboard(tmp_path):
    with pytest.raises(ValueError, match='no '):
        studio.project(tmp_path)
    (tmp_path / 'reshoot.toml').write_text('[[take]]\nrun = "true"\n')
    with pytest.raises(ValueError, match='versioned'):
        studio.project(tmp_path)


CUT = """schema_version = 1
output = "demo-final.mp4"

[[part]]
take = 0
start = 0
end = "end"

[[export]]
preset = "readme"   # an 800x450 GIF
"""

CONFIG = """schema_version = 1

[[take]]
web = "storyboard.toml"
out = "takes/demo.mp4"

[edit]
file = "edit.toml"
args = ["takes/demo.mp4"]

[check]
sources = ["takes/demo-final.mp4", "takes/demo-final-readme.gif"]
"""


def test_studio_edits_cards_frame_music_and_exports_in_the_edit_file(tmp_path):
    import tomllib
    cut, config = tmp_path / 'edit.toml', tmp_path / 'reshoot.toml'
    cut.write_text(CUT)
    config.write_text(CONFIG)
    (tmp_path / 'storyboard.toml').write_text(BOARD)
    (tmp_path / 'music').mkdir()
    (tmp_path / 'music/calm.mp3').write_bytes(b'')
    studio.edit_cut(cut, config, {'add_card': 'start', 'text': 'Notes'})
    studio.edit_cut(cut, config, {'add_card': 'end', 'text': 'Try it'})
    studio.edit_cut(cut, config, {'card': 0, 'text': 'Notes, found fast', 'duration': 1.5})
    studio.edit_cut(cut, config, {'frame': True})
    studio.edit_cut(cut, config, {'background': '#2a3f5f'})
    studio.edit_cut(cut, config, {'music': 'music/calm.mp3'})
    studio.edit_cut(cut, config, {'export': 0, 'preset': 'x-square'})
    studio.edit_cut(cut, config, {'add_export': 'linkedin'})
    data = tomllib.loads(cut.read_text())
    assert [p.get('card') for p in data['part']] == ['Notes, found fast', None, 'Try it']
    assert data['part'][0]['duration'] == 1.5 and data['part'][1]['end'] == 'end'
    assert data['frame'] == {'padding': 0.06} and data['style'] == {'background': '#2a3f5f'}
    assert data['music'] == 'music/calm.mp3' and [x['preset'] for x in data['export']] == ['x-square', 'linkedin']
    # The scan follows the exports: the renamed one and the new one
    assert tomllib.loads(config.read_text())['check']['sources'] == [
        'takes/demo-final.mp4', 'takes/demo-final-x-square.mp4', 'takes/demo-final-linkedin.mp4']
    studio.edit_cut(cut, config, {'card': 2, 'remove': True})
    studio.edit_cut(cut, config, {'export': 1, 'remove': True})
    studio.edit_cut(cut, config, {'frame': False})
    studio.edit_cut(cut, config, {'music': ''})
    data = tomllib.loads(cut.read_text())
    assert len(data['part']) == 2 and 'frame' not in data and 'music' not in data and len(data['export']) == 1
    assert tomllib.loads(config.read_text())['check']['sources'] == ['takes/demo-final.mp4', 'takes/demo-final-x-square.mp4']
    before = cut.read_text()
    for change, error in (({'card': 1, 'text': 'x'}, 'a take'), ({'add_export': 'x-square'}, 'same file'),
                          ({'music': 'gone.mp3'}, 'no music'), ({'export': 0, 'preset': 'tiktok'}, 'unknown preset'),
                          ({'card': 0, 'duration': 0}, 'seconds'), ({'background': 'navy'}, 'colour'),
                          ({'background': '#00000080'}, 'opaque'), ({'foreground': '#ffffff80'}, 'opaque')):
        with pytest.raises(ValueError, match=error):
            studio.edit_cut(cut, config, change)
        assert cut.read_text() == before


def test_a_beat_counts_as_changed_only_when_more_than_its_caption_changed():
    import hashlib
    beat = {'id': 'search', 'caption': 'Old words', 'hold': 2.0}
    recorded = hashlib.sha256(json.dumps(beat, sort_keys=True).encode()).hexdigest()
    row = {'recorded': 'Old words', 'recorded_sub': None}
    assert studio.recorded_as({**beat, 'caption': 'New words', 'sub': 'and more'}, row) == recorded
    assert studio.recorded_as({**beat, 'hold': 3.0}, row) != recorded


def test_fits_says_where_an_export_is_going_and_its_limits():
    from reshoot import timeline
    assert studio.fits(timeline.PRESETS['x'][1], 12.4, 300_000) == ('X takes 0.5 to 1200 s and up to 8 GB; this is '
                                                                    '12.4 s and 0.3 MB')
    assert studio.fits(None, 1, 1) is None


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
            assert f'/runs/{page.locator("body").get_attribute("data-run")}/' in page.locator('#video').evaluate('video => video.src')
            assert page.locator('.scan img').count() >= 1
            assert page.locator('.beat').count() == 4 and page.locator('.seg').count() >= 3
            assert page.locator('.beat[data-beat=search] .checks').inner_text() == '2 of 2 result checks passed'
            search = page.locator('.beat[data-beat=search]')
            assert search.locator('.pending').is_hidden()
            search.locator('input[name=caption]').fill('A caption from the studio')
            search.locator('input[name=caption]').press('Tab')
            page.wait_for_selector('#toast.on')
            assert search.locator('.pending').is_visible()
            assert 'caption = "A caption from the studio"' in board.read_text()
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert 'A caption from the studio' not in board.read_text()
            with page.expect_navigation():
                page.click('[data-history=redo]')
            assert 'A caption from the studio' in board.read_text()
            page.locator('.styling > summary').click()
            page.locator('.look input[name=background]').fill('blue')
            page.locator('.look input[name=background]').press('Tab')
            page.wait_for_function("document.getElementById('toast').textContent.includes('colour')")
            assert 'blue' not in board.read_text()
            page.click('[data-job=update]')
            page.wait_for_function("document.getElementById('save-error').textContent.includes('unsaved')")
            page.locator('.look input[name=background]').fill('#1d4ed8')
            page.locator('.look input[name=background]').press('Tab')
            page.wait_for_function("!document.querySelector('[data-unsaved]')")
            search.locator('.play').click()  # plays the beat, from its place in the video
            page.wait_for_function("!document.getElementById('video').paused")
            start = float(search.get_attribute('data-start'))
            assert page.evaluate("document.getElementById('video').currentTime") >= start - .1
            assert page.locator('.shape').count() == 2  # the MP4 and the README GIF, with the GIF's limits
            assert 'GitHub takes up to 10 MB' in page.locator('.shape').nth(1).inner_text()
            assert page.locator('.redo.changed').count() == 0  # a new caption needs a re-cut, not a recording
            with page.expect_navigation():
                page.click('[data-add-card=start]')
            page.locator('.card input[name=text]').fill('Notes, found fast')
            page.locator('.card input[name=text]').press('Tab')
            page.wait_for_selector('#toast.on')
            page.check('.cut [name=frame]')
            page.wait_for_function("document.querySelector('.cut .pending').hidden === false")
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            assert 'a re-cut of' in page.locator('.status').inner_text()
            assert page.locator('.beat[data-beat=search] .pending').is_hidden()
            assert page.locator('.cut .pending').is_hidden()
            assert page.locator('#to-accept').count() == 1
            hold = page.locator('.beat[data-beat=search] input[name=hold]')
            hold.fill('2.5')
            hold.press('Tab')
            page.wait_for_function("!document.querySelector('[data-unsaved]')")
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            assert 'a re-cut of' not in page.locator('.status').inner_text()  # timing replays the app
            # A beat whose hold changed is recorded again from that beat, and its take shown on the page
            board.write_text(board.read_text().replace('hold = 2.5', 'hold = 3.0'))
            page.reload()
            assert page.locator('.redo.changed').count() == 1
            assert page.locator('#session-recovery').is_visible()
            with page.expect_navigation():
                page.locator('[data-session=fresh]').click()
            page.locator('.beat[data-beat=search] [data-from]').click()
            page.wait_for_selector('#job-take:not([hidden])', timeout=120000)
            assert 'Recording from search worked' in page.locator('#job-title').inner_text()
            assert 'a re-cut of' not in page.locator('.status').inner_text()  # still the run, not the partial take
            previous = page.locator('.status').inner_text()
            page.click('[data-job=update]')
            page.wait_for_selector('#cancel:visible')
            page.click('#cancel')
            page.wait_for_function("document.getElementById('job-title').textContent.includes('cancelled')", timeout=30000)
            assert page.locator('.status').inner_text() == previous
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    recut = [p.parent for p in (tmp_path / 'takes/runs').glob('*/run.json') if json.loads(p.read_text()).get('recut_from')]
    assert 'A caption from the studio' in (recut[0] / 'takes/demo-final.srt').read_text()
    assert any(json.loads(p.read_text())['mode'] == 'partial-preview' for p in (tmp_path / 'takes/runs').glob('*/run.json'))
    import tomllib
    assert tomllib.loads((tmp_path / 'edit.toml').read_text())['part'][0]['card'] == 'Notes, found fast'


def test_the_studio_removes_only_the_result_check_it_showed(tmp_path):
    board = tmp_path / 'storyboard.toml'
    board.write_text('schema_version = 1\nurl = "http://localhost:8000/"\n\n[[beat]]\nid = "open"\n[[beat.action]]\n'
                     'type = "click"\ntarget = {css = "#tab"}\n[[beat.expect]]  # suggested\ntype = "count"\n'
                     'target = {css = "#hero > div"}\ncount = 0\n[[beat.expect]]\ntype = "visible"\ntarget = {css = "#list"}\n\n'
                     '[[beat]]\nid = "end"\nhold = 0.5\n')
    shown = {'type': 'count', 'target': {'css': '#hero > div'}, 'count': 0}
    with pytest.raises(ValueError, match='changed since the page loaded'):
        studio.edit(board, {'beat': 'open', 'remove_expect': 0, 'expect': {**shown, 'count': 1}})
    studio.edit(board, {'beat': 'open', 'remove_expect': 0, 'expect': shown})
    beat = tomllib.loads(board.read_text())['beat'][0]
    assert beat['expect'] == [{'type': 'visible', 'target': {'css': '#list'}}] and beat['action']
    with pytest.raises(ValueError, match='no longer in the storyboard'):
        studio.edit(board, {'beat': 'end', 'remove_expect': 0, 'expect': shown})


def test_a_failed_result_check_is_said_plainly():
    error = "Locator expected to have count '0'\nActual value: 4 \nCall log:\n  - waiting for locator(\"#hero > div\")"
    assert studio.explain(5, 'action-5', {'type': 'count', 'target': {'css': '#hero > div'}, 'count': 0}, error) == \
        'Step 5 (action-5) expected no elements matching `#hero > div`, but the page had 4.'
    assert studio.explain(2, 'search', {'type': 'text', 'target': {'css': '#list li'}, 'contains': 'bikes'},
                          'Actual value: "Buy stamps"') == 'Step 2 (search) expected `#list li` to contain "bikes", but it showed "Buy stamps".'


@pytest.mark.browser
@pytest.mark.parametrize('creating', [False, True])
def test_a_first_preview_that_stopped_on_a_wrong_check_can_be_fixed_in_the_studio(tmp_path, creating):
    from playwright.sync_api import sync_playwright
    from test_reshoot import free_port
    from reshoot import web
    from reshoot.cli import main
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    port = free_port()
    config = tmp_path / 'reshoot.toml'
    config.write_text(config.read_text().replace('8765', str(port)).replace('scan = true', 'scan = false'))
    board = tmp_path / 'storyboard.toml'
    text = board.read_text().replace('8765', str(port))
    assert 'count = 1' in text
    board.write_text(text.replace('count = 1', 'count = 0', 1))  # a wrong suggestion, as a tab once made
    if creating:
        from reshoot import create
        create.save(tmp_path, {'schema_version': 1, 'stage': 'preview', 'url': None, 'size': '960x540@1.5'})
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code != 0
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page()
            page.goto(url)
            assert page.locator('body').get_attribute('data-first') == '1'
            assert set(page.locator('.section-nav a').all_inner_texts()) <= {'Tools', 'Preview', 'Story'}
            assert not page.locator('#review-panel').is_visible() and not page.locator('#look-panel').is_visible()
            assert 'expected no elements matching' in page.locator('.failure').inner_text()
            assert page.locator('.beat[data-beat=search] .checks').inner_text().endswith('not run yet')
            page.locator('[data-remove-check]').click()
            page.wait_for_load_state('load')
            page.wait_for_function('!document.querySelector("[data-remove-check]")')
            again = 'Continue creation' if creating else 'Update preview'
            assert again in page.locator('.failure').inner_text()
            assert page.get_by_role('button', name=again, exact=True).is_enabled()
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    assert 'count = 0' not in board.read_text()
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code == 0
