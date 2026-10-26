"""Demonstrated edits remain separate until reviewed and preserve the task's original checks."""
import json
import threading
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import demonstrate, demonstration, project, story, studio


def setup(folder):
    project.init(SimpleNamespace(directory=str(folder), url=None, quiet=True))
    return folder / 'reshoot.toml', folder / 'storyboard.toml'


def calls(text='bikes'):
    return [(0, {'kind':'page', 'href':'http://127.0.0.1/'}),
            (1, {'kind':'type', 'where':['css', '#q'], 'value':text, 'before':''})]


@pytest.mark.parametrize('mode', ['replace', 'before', 'after'])
def test_draft_preserves_existing_steps_checks_and_words(tmp_path, mode):
    config, path = setup(tmp_path)
    path.write_text(path.read_text().replace('target = {css = "#q"}\ntext = "bike"', 'text = "bike"\n[beat.action.target]\ncss = "#q"') + '# keep this explanation\n')
    original, before = path.read_bytes(), story.load(path)
    data = demonstration.begin(config, 'search', mode)
    ident = demonstration.finish(data, calls())
    assert path.read_bytes() == original
    draft = demonstration.read(config, ident)
    assert demonstration.model(draft)['can_apply']
    demonstration.apply(config, ident, draft['binding'])
    after = story.load(path)
    if mode == 'replace':
        assert after['beat'][2]['action'][0]['text'] == 'bikes'
        assert after['beat'][2]['expect'] == before['beat'][2]['expect']
        assert after['beat'][2]['caption'] == before['beat'][2]['caption']
        assert after['beat'][2]['hold'] == before['beat'][2]['hold']
        assert '[beat.action.target]' not in path.read_text()
    else:
        at = 2 + (mode == 'after')
        assert after['beat'][:at] + after['beat'][at+1:] == before['beat']
    assert '# keep this explanation' in path.read_text()
    assert demonstration.latest(config) is None


def test_draft_rejects_changed_sources_tampered_checks_and_old_review(tmp_path):
    config, path = setup(tmp_path)
    data = demonstration.begin(config, 'search')
    ident = demonstration.finish(data, calls())
    draft = demonstration.read(config, ident)
    after = data['root'] / 'after.toml'
    after.write_text(after.read_text() + '# changed proposal\n')
    with pytest.raises(ValueError, match='changed'):
        demonstration.apply(config, ident, draft['binding'])
    token = demonstration.read(config, ident)['binding']
    path.write_text(path.read_text() + '# external edit\n')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='not ready'):
        demonstration.apply(config, ident, token)
    assert not demonstration.latest(config)['can_apply'] and path.read_bytes() == before
    path.write_bytes((data['root'] / 'before.toml').read_bytes())
    after.write_text(after.read_text().replace('count = 1', 'count = 0'))
    with pytest.raises(ValueError, match='preserve every existing result check'):
        demonstration.read(config, ident)


@pytest.mark.parametrize('extra', [{'kind':'unsupported-drop'}, {'kind':'type', 'where':['css','#q'], 'value':'private', 'secret':True}])
def test_unsupported_or_secret_draft_never_changes_source(tmp_path, extra):
    config, path = setup(tmp_path)
    original = path.read_bytes()
    data = demonstration.begin(config, 'search')
    with pytest.raises(ValueError):
        demonstration.finish(data, calls() + [(2, extra)])
    assert path.read_bytes() == original
    assert 'private' not in (data['root'] / 'recorded.toml').read_text()


def test_failed_group_save_restores_source_and_draft(tmp_path, monkeypatch):
    config, path = setup(tmp_path)
    original = path.read_bytes()
    data = demonstration.begin(config, 'search')
    ident = demonstration.finish(data, calls())
    draft = demonstration.read(config, ident)
    replace = Path.replace
    def fail(source, target):
        if target == data['root'] / 'draft.json':
            raise OSError('simulated disk failure')
        return replace(source, target)
    monkeypatch.setattr(Path, 'replace', fail)
    with pytest.raises(OSError):
        demonstration.apply(config, ident, draft['binding'])
    assert path.read_bytes() == original
    assert demonstration.read(config, ident)['binding'] == draft['binding']
    monkeypatch.setattr(Path, 'replace', replace)
    demonstration.discard(config, ident, draft['binding'])
    assert demonstration.latest(config) is None and path.read_bytes() == original


def test_explicit_new_check_and_caption_keep_the_previous_checks(tmp_path):
    config, path = setup(tmp_path)
    old = story.load(path)['beat'][2]
    data = demonstration.begin(config, 'search')
    check = {'type':'value', 'target':{'css':'#q'}, 'value':'bikes'}
    ident = demonstration.finish(data, calls() + [(2, {'kind':'expect', 'check':check})])
    draft = demonstration.read(config, ident)
    assert draft['after']['beat'][2]['expect'] == old['expect'] + [check]
    with pytest.raises(ValueError, match='review'):
        demonstration.apply(config, ident, None)
    data = demonstration.begin(config, 'search', 'after')
    ident = demonstration.finish(data, calls() + [(2, {'kind':'caption', 'text':'Find the bikes'})])
    assert demonstration.read(config, ident)['after']['beat'][3]['caption'] == 'Find the bikes'


def test_studio_routes_a_guarded_recording_and_refuses_unreviewed_or_stale_drafts(tmp_path, monkeypatch):
    config, path = setup(tmp_path)
    commands = []
    monkeypatch.setattr(studio.Job, 'start', lambda self, *args, **kwargs: commands.append(args))
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    from reshoot.workspace import History
    def post(action, body):
        revision = History(demonstration.context(config)['paths']).revision()
        request = urllib.request.Request(url + action, data=json.dumps({**body, 'revision':revision}).encode(),
                                         headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(request).read())
    try:
        assert post('job', {'kind':'demonstrate', 'beat':'search', 'mode':'replace'})['ok']
        assert commands[0][0] == 'demonstrate'
        command = commands[0][1]
        assert command[3:6] == ['step', 'record', 'search']
        assert command[command.index('--expected-revision') + 1] == History(demonstration.context(config)['paths']).revision()
        data = demonstration.begin(config, 'search')
        ident = demonstration.finish(data, calls())
        draft = demonstration.read(config, ident)
        original = path.read_bytes()
        assert not post('demonstration', {'operation':'apply', 'id':ident})['ok']
        path.write_text(path.read_text() + '# owner edit\n')
        external = path.read_bytes()
        result = post('demonstration', {'operation':'apply', 'id':ident, 'draft_binding':draft['binding']})
        assert not result['ok'] and path.read_bytes() == external
        assert post('demonstration', {'operation':'discard', 'id':ident, 'draft_binding':draft['binding']})['ok']
        assert original != external and path.read_bytes() == external
    finally:
        httpd.shutdown(); httpd.server_close()


@pytest.mark.browser
@pytest.mark.parametrize('anchor,mode', [('search','after'), ('end','before')])
def test_insertion_replays_the_right_prefix_and_records_only_new_actions(tmp_path, monkeypatch, anchor, mode):
    from test_reshoot import free_port
    monkeypatch.setattr(project, 'free_port', free_port)
    config, path = setup(tmp_path)
    before = story.load(path)
    async def drive(page):
        assert await page.locator('#q').input_value() == 'bike'
        assert await page.locator('#list li').count() == 1
        await page.locator('#q').fill('bikes')
        await page.locator('reshoot-recorder [data-do=check]').click()
        await page.locator('#list li').click()
        await page.locator('reshoot-recorder [data-do=done]').click()
    ident = demonstrate.record(config, anchor, mode, headless=True, drive=drive)
    data = demonstration.read(config, ident)
    inserted = data['after']['beat'][3]
    assert len(inserted['action']) == 1 and inserted['action'][0]['text'] == 'bikes'
    assert inserted['expect']
    assert data['after']['beat'][:3] + data['after']['beat'][4:] == before['beat']


@pytest.mark.browser
def test_replay_record_review_undo_then_verify_the_complete_task(tmp_path, monkeypatch):
    from playwright.sync_api import sync_playwright, expect
    from reshoot import review, web
    from reshoot.cli import main
    from test_reshoot import free_port
    monkeypatch.setattr(project, 'free_port', free_port)
    config, path = setup(tmp_path)
    config.write_text(config.read_text().replace('scan = true', 'scan = false'))
    original = path.read_bytes()
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code == 0
    initial_run = review.read(tmp_path / 'latest')[1]['id']
    async def drive(page):
        assert 'Pick up the bikes' in await page.locator('#list').inner_text()
        assert await page.locator('#q').input_value() == ''
        await page.locator('#q').fill('bikes')
        await page.locator('reshoot-recorder [data-do=done]').click()
    ident = demonstrate.record(config, 'search', headless=True, drive=drive)
    assert path.read_bytes() == original
    draft = demonstration.read(config, ident)
    assert len(draft['after']['beat'][2]['action']) == 1
    assert draft['after']['beat'][2]['action'][0]['text'] == 'bikes'
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            chrome = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = chrome.new_page(viewport={'width':1280,'height':900})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            video = page.locator('#video').get_attribute('src')
            assert initial_run in video
            expect(page.locator('#demonstration-panel')).to_contain_text('bikes')
            page.screenshot(path=str(tmp_path / 'review-desktop.png'))
            page.set_viewport_size({'width':390, 'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.locator('#demonstration-panel').scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path / 'review-mobile.png'))
            with page.expect_navigation():
                page.get_by_role('button', name='Use these actions', exact=True).click()
            changed = path.read_bytes()
            assert changed != original
            assert page.locator('#video').get_attribute('src') == video
            with page.expect_navigation():
                page.locator('[data-history=undo]').click()
            assert path.read_bytes() == original
            with page.expect_navigation():
                page.locator('[data-history=redo]').click()
            assert path.read_bytes() == changed
            with page.expect_navigation(timeout=120000):
                page.locator('[data-job=update]').click()
            assert page.locator('#video').get_attribute('src') != video
            page.set_viewport_size({'width':390, 'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert not errors
            chrome.close()
    finally:
        httpd.shutdown(); httpd.server_close()
    _, report = review.read(tmp_path / 'latest')
    assert report['expectations_count'] == 3 and report['expectations_status'] == 'passed'
    async def cancel(page):
        await page.close()
    with pytest.raises(ValueError, match='cancelled'):
        demonstrate.record(config, 'search', headless=True, drive=cancel)
    assert path.read_bytes() == changed
