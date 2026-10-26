"""Representative feedback preserves source, media, review and the production drawing geometry."""
import io
import hashlib
import json
import shutil
import threading
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageChops, ImageStat
from reshoot import captions, comparison, cut, framing, project, review, stills, story, studio
from reshoot.artifacts import digest
from reshoot.workspace import History


def fixture(folder):
    project.init(SimpleNamespace(directory=str(folder), url=None, quiet=True))
    config = folder / 'reshoot.toml'
    root = folder / 'takes/runs' / ('a' * 32)
    take = root / 'takes/demo.mp4'
    take.parent.mkdir(parents=True)
    clean = take.with_suffix('.clean.mp4')
    cut.ff('-f', 'lavfi', '-i', 'color=c=0x123852:s=320x180:r=60:d=1.5', *cut.ENC, clean)
    shutil.copyfile(clean, take)
    take.with_suffix('.take.json').write_text(json.dumps({'status': 'completed', 'mode': 'preview', 'beats': [
        {'id': 'search', 'start': 0, 'end': 1.5, 'status': 'passed'}]}))
    take.with_suffix('.captions.json').write_text(json.dumps({'css_width': 320, 'captions': [
        {'beat': 'search', 'start': 0, 'end': 1.5, 'recorded': 'Find the matching note', 'recorded_sub': None}]}))
    report = {'id': root.name, 'ok': True, 'mode': 'preview', 'review_status': 'pending',
              'files': [{'path': str(path.relative_to(root)), 'sha256': digest(path)} for path in root.rglob('*') if path.is_file()]}
    (root / 'run.json').write_text(json.dumps(report))
    take_config = studio.project(config)[2]
    body = {'run_id': root.name, 'binding': review.binding(root, report), 'beat': 'search', 'export': -1,
            'revision': History([config, folder / 'storyboard.toml', folder / 'styles.toml', folder / 'edit.toml']).revision()}
    return config, take_config, (root, report), body


def decoded(video, at=1.4):
    raw = stills._ff(['-ss', at, '-i', video, '-frames:v', 1, '-f', 'image2pipe', '-c:v', 'png', '-'])
    return Image.open(io.BytesIO(raw)).convert('RGB')


@pytest.mark.parametrize('window', [False, True])
def test_still_matches_the_encoded_caption_and_window_renderers(tmp_path, window):
    config, take, run, body = fixture(tmp_path)
    board = story.load(tmp_path / 'storyboard.toml')
    board['beat'][2]['caption'] = 'A clear result'
    body['draft'] = {'caption': 'A clear result', 'frame': {'enabled': window, 'background': ['#172554', '#0e0d0c']}}
    if window:
        body['export'] = 0
        body['draft']['framing'] = {'fit': 'crop', 'focus': [.25, .5]}
    before = {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    request = stills.prepare(config, take, run, body)
    actual = Image.open(io.BytesIO(stills.Renderer().render(request))).convert('RGB')
    assert all(p.read_bytes() == value for p, value in before.items())
    expected = tmp_path / 'expected.mp4'
    shutil.copyfile(run[0] / 'takes/demo.clean.mp4', expected.with_suffix('.clean.mp4'))
    shutil.copyfile(run[0] / 'takes/demo.captions.json', expected.with_suffix('.captions.json'))
    captions.draw(expected, board, tmp_path / 'storyboard.toml', quiet=True)
    if window:
        expected = cut.frame(expected, tmp_path / 'framed.mp4', **request['window'])
        plan = framing.geometry((320, 180), 800, 450, 'crop', [.25, .5])
        cut.ff('-i', expected, '-vf', framing.filter_for(plan), *cut.ENC, tmp_path / 'export.mp4')
        expected = tmp_path / 'export.mp4'
    reference = decoded(expected)
    assert actual.size == reference.size
    # PNG feedback precedes H.264 compression; geometry/colour must agree within encoding noise.
    assert max(ImageStat.Stat(ImageChops.difference(actual, reference)).mean) < 4


def test_caption_edits_reuse_the_clean_frame_and_identical_feedback(tmp_path, monkeypatch):
    config, take, run, body = fixture(tmp_path)
    render = stills.Renderer()
    decode, calls = stills._ff, []
    def counted(args):
        if args[0] == '-ss':
            calls.append(args)
        return decode(args)
    monkeypatch.setattr(stills, '_ff', counted)
    request = stills.prepare(config, take, run, body)
    first = render.render(request)
    assert render.render(request) == first
    newer = render.render({**request, 'text': {'caption': 'New words', 'sub': ''}})
    assert newer != first and len(calls) == 1
    render.slot.acquire()
    try:
        with pytest.raises(ValueError, match='busy'):
            render.render({**request, 'text': {'caption': 'Another edit', 'sub': ''}})
    finally:
        render.slot.release()


@pytest.mark.parametrize('draft', [{'look': {'font': '/arbitrary/file'}}, {'frame': {'enabled': 'yes'}},
                                  {'framing': {'focus': [2, .5]}}, {'caption': 7}])
def test_invalid_still_settings_are_rejected(tmp_path, draft):
    config, take, run, body = fixture(tmp_path)
    with pytest.raises(ValueError):
        stills.prepare(config, take, run, {**body, 'export': 0, 'draft': draft})


def test_http_still_rejects_changed_sources_and_a_revision_change_during_render(tmp_path, monkeypatch):
    config, take, run, body = fixture(tmp_path)
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    def get():
        return urllib.request.urlopen(urllib.request.Request(url + 'still', data=json.dumps(body).encode(),
                                      headers={'Content-Type': 'application/json'}))
    try:
        with get() as response:
            assert response.headers['Content-Type'] == 'image/png'
            assert response.headers['X-Reshoot-Revision'] == body['revision']
            assert Image.open(io.BytesIO(response.read())).size == (320, 180)
        renderer = stills.Renderer.render
        board = tmp_path / 'storyboard.toml'
        def external_change(self, request):
            result = renderer(self, request)
            board.write_text(board.read_text() + '# external change during preview\n')
            return result
        monkeypatch.setattr(stills.Renderer, 'render', external_change)
        with pytest.raises(urllib.error.HTTPError, match='409'):
            get()
        assert '# external change during preview' in board.read_text()
        assert run[1]['review_status'] == 'pending'
    finally:
        httpd.shutdown(); httpd.server_close()


@pytest.mark.browser
def test_live_caption_and_crop_feedback_ignores_old_results_and_keeps_the_recording(tmp_path, monkeypatch):
    from playwright.sync_api import sync_playwright, expect
    from reshoot import web
    from reshoot.cli import main
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    config = tmp_path / 'reshoot.toml'
    config.write_text(config.read_text().replace('scan = true', 'scan = false'))
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code == 0
    run = review.read(tmp_path / 'latest')
    report_before = (run[0] / 'run.json').read_bytes()
    board = tmp_path / 'storyboard.toml'
    before = board.read_bytes()
    old_entered, release_old, old_finished = threading.Event(), threading.Event(), threading.Event()
    rendered = {}
    renderer = stills.Renderer.render
    def delayed(self, request):
        old = request['text']['caption'] == 'Older draft'
        if old:
            old_entered.set(); release_old.wait(5)
        png = renderer(self, request)
        rendered[request['text']['caption']] = hashlib.sha256(png).hexdigest()
        if old:
            old_finished.set()
        return png
    monkeypatch.setattr(stills.Renderer, 'render', delayed)
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.locator('[data-select-step=search]').click()
            image = page.locator('#still-image')
            expect(image).to_have_attribute('data-beat', 'search', timeout=15000)
            expect(image).to_be_visible()
            caption = page.locator('.beat[data-beat=search] input[name=caption]')
            caption.fill('Older draft')
            assert old_entered.wait(5)
            caption.fill('Latest result')
            page.wait_for_function('document.getElementById("still-status").textContent.startsWith("Unsaved layout still")')
            assert image.get_attribute('data-sha256') == rendered['Latest result']
            assert board.read_bytes() == before
            release_old.set()
            assert old_finished.wait(5)
            page.wait_for_timeout(250)  # allow the deliberately late response to reach the browser
            assert image.get_attribute('data-sha256') == rendered['Latest result']
            caption.press('Tab')
            page.wait_for_function('!document.querySelector("[data-unsaved]")')
            assert story.load(board)['beat'][2]['caption'] == 'Latest result'
            page.locator('.section-nav [data-jump=look-panel]').click()
            form = page.locator('.export-framing').first
            form.locator('[name=fit]').select_option('crop')
            form.locator('[name=focus_x]').fill('25')
            page.wait_for_function('document.getElementById("still-image").naturalWidth === 800')
            assert page.locator('#still-export').input_value() == '0'
            assert page.locator('body').get_attribute('data-run') == run[1]['id']
            assert (run[0] / 'run.json').read_bytes() == report_before
            page.locator('#toggle-still').click()
            expect(page.locator('#video')).to_be_visible()
            assert run[1]['id'] in page.locator('#video').get_attribute('src')
            assert not errors
            browser.close()
    finally:
        release_old.set()
        httpd.shutdown(); httpd.server_close()
