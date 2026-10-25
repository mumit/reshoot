"""Locator repair preserves the task and checks, and never silently heals a recording."""
import asyncio
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import project, repair, review, story, studio
from reshoot.artifacts import digest


def source(tmp_path):
    board = tmp_path / 'storyboard.toml'
    board.write_text('''schema_version = 1
url = "about:blank"
[[beat]] # keep this comment
id = "save"
caption = "Save the note"
[[beat.action]]
type = "click"
target = {css = "#old"} # keep the reason for this identifier
fallbacks = [{role = "button", name = "Save"}]
[[beat.expect]]
type = "text"
target = {css = "#result"}
contains = "Saved the note"
[[beat]]
id = "end"
hold = 0.5
''')
    root = tmp_path / 'failed'
    root.mkdir()
    return {'board_path': board, 'board': story.load(board), 'root': root,
            'meta': {'story_sha256': digest(board)},
            'failure': {'beat': 'save', 'section': 'action', 'index': 1},
            'entry': story.load(board)['beat'][0]['action'][0]}


def test_repair_changes_one_target_and_keeps_checks_and_comments(tmp_path):
    data = source(tmp_path)
    before = story.load(data['board_path'])
    repair.apply(data, {'css': '#new'})
    after = story.load(data['board_path'])
    assert after['beat'][0]['expect'] == before['beat'][0]['expect']
    assert after['beat'][0]['action'][0]['type'] == 'click'
    assert after['beat'][0]['action'][0]['target'] == {'css': '#new'}
    assert after['beat'][1] == before['beat'][1]
    assert '# keep this comment' in data['board_path'].read_text()
    assert '# keep the reason for this identifier' in data['board_path'].read_text()
    assert json.loads((data['root'] / 'repair.json').read_text())['before'] == data['meta']['story_sha256']


def test_stale_source_cannot_be_overwritten_by_a_repair(tmp_path):
    data = source(tmp_path)
    data['board_path'].write_text('# an external edit\n')
    with pytest.raises(ValueError, match='changed'):
        repair.apply(data, {'css': '#new'})
    assert data['board_path'].read_text() == '# an external edit\n'
    assert not (data['root'] / 'repair.json').exists()


def test_unwritable_repair_evidence_does_not_change_source(tmp_path):
    data = source(tmp_path)
    before = data['board_path'].read_bytes()
    data['root'] = tmp_path / 'missing-run'
    with pytest.raises(OSError):
        repair.apply(data, {'css': '#new'})
    assert data['board_path'].read_bytes() == before


def test_repair_preserves_a_multiline_fallback_list(tmp_path):
    data = source(tmp_path)
    board = data['board_path']
    board.write_text(board.read_text().replace('fallbacks = [{role = "button", name = "Save"}]',
                                             'fallbacks = [\n  # keep the accessible name\n  {role = "button", name = "Save"},\n]'))
    data.update(board=story.load(board), meta={'story_sha256': digest(board)}, entry=story.load(board)['beat'][0]['action'][0])
    repair.apply(data, {'css': '#new'})
    assert '# keep the accessible name' in board.read_text()
    assert story.load(board)['beat'][0]['action'][0]['target'] == {'css': '#new'}


@pytest.mark.parametrize('section', ['expect', 'setup'])
def test_repair_updates_the_exact_check_or_setup_slot(tmp_path, section):
    data = source(tmp_path)
    board = data['board_path']
    if section == 'setup':
        board.write_text(board.read_text().replace('url = "about:blank"',
            'url = "about:blank"\n[[setup]]\ntype = "wait"\ntarget = {css = "#login"}'))
    before = story.load(board)
    entry = before['setup'][0] if section == 'setup' else before['beat'][0]['expect'][0]
    data.update(board=before, meta={'story_sha256': digest(board)}, entry=entry,
                failure={'beat': 'save', 'section': section, 'index': 1})
    repair.apply(data, {'css': '#replacement'})
    after = story.load(board)
    assert after['beat'][0]['action'] == before['beat'][0]['action']
    if section == 'setup':
        assert after['setup'][0]['target'] == {'css': '#replacement'}
        assert after['setup'][0]['type'] == 'wait'
        assert after['beat'] == before['beat']
    else:
        assert after['beat'][0]['expect'][0]['target'] == {'css': '#replacement'}
        assert after['beat'][0]['expect'][0]['contains'] == 'Saved the note'


def test_fallbacks_must_be_bounded_valid_targets(tmp_path):
    data = source(tmp_path)
    entry = data['entry']
    for alternatives in ([{'css': '#a', 'role': 'button'}], 'button', [{'css': '#a'}] * 13):
        with pytest.raises(ValueError):
            story.validate({**entry, 'fallbacks': alternatives}, story.ACTIONS)


@pytest.mark.browser
def test_alternatives_must_agree_and_never_mask_a_wrong_result():
    from playwright.async_api import async_playwright
    from reshoot import web
    async def check():
        async with async_playwright() as pw:
            chrome = await pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            try:
                page = await chrome.new_page()
                await page.set_content('<button id="new">Save</button><button id="cancel">Cancel</button><input id="field" placeholder="New note">')
                entry = {'type': 'click', 'target': {'css': '#old'}, 'fallbacks': [{'css': '#new'}, {'role': 'button', 'name': 'Save'}]}
                found = await repair.diagnose(page, entry)
                assert found['candidates'] == [{'css': '#new'}]
                found = await repair.diagnose(page, {**entry, 'fallbacks': [{'css': '#new'}, {'css': '#cancel'}]})
                assert found['ambiguous'] and not found['candidates']
                assert await repair.diagnose(page, {'type': 'text', 'target': {'css': '#new'}, 'contains': 'Wrong'}) is None
                ambiguous = await repair.diagnose(page, {**entry, 'target': {'css': 'button'}})
                assert ambiguous['kind'] == 'ambiguous-target' and not ambiguous['candidates']
                found = await repair.diagnose(page, {**entry, 'type': 'type'})
                assert not found['candidates']  # a button cannot replace a text field
                await page.evaluate('''() => {
                  for (const id of ['one', 'two']) {
                    const host = document.createElement('div'); host.id = id;
                    host.attachShadow({mode: 'open'}).innerHTML = '<button>Save</button>';
                    document.body.append(host);
                  }
                }''')
                found = await repair.diagnose(page, {**entry, 'fallbacks': [{'css': '#one button'}, {'css': '#two button'}]})
                assert found['ambiguous'] and not found['candidates']
                found = await asyncio.wait_for(repair.diagnose(page, {**entry,
                    'fallbacks': [{'frame': '#absent-frame', 'css': 'button'}]}), timeout=5)
                assert not found['candidates']
            finally:
                await chrome.close()
    asyncio.run(check())


def broken_project(tmp_path):
    from test_reshoot import free_port
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    port = free_port()
    for name in ('reshoot.toml', 'storyboard.toml'):
        path = tmp_path / name
        path.write_text(path.read_text().replace('8765', str(port)))
    config, board = tmp_path / 'reshoot.toml', tmp_path / 'storyboard.toml'
    config.write_text(config.read_text().replace('scan = true', 'scan = false'))
    board.write_text(board.read_text().replace('target = {css = "#q"}',
        'target = {css = "#old-search"}\nfallbacks = [{css = "input[placeholder=\'Search notes\']"}]'))
    return config, board


def fail(config):
    from reshoot.cli import main
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code != 0
    return review.runs(config)[0][0]


@pytest.mark.browser
def test_failed_run_suggests_repair_and_new_preview_keeps_original_checks(tmp_path):
    from reshoot.cli import main
    config, board = broken_project(tmp_path)
    root = fail(config)
    before = story.load(board)
    data = repair.load(root)
    assert data['failure']['candidates'] == [{'css': "input[placeholder='Search notes']"}]
    repair.main(SimpleNamespace(run_path=str(root), config=None, apply=True, pick=False))
    after = story.load(board)
    assert [b.get('expect') for b in before['beat']] == [b.get('expect') for b in after['beat']]
    assert review.read(root)[1]['ok'] is False
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code == 0
    latest = review.read(tmp_path / 'latest')[1]
    assert latest['expectations_status'] == 'passed' and latest['expectations_count'] == 3


@pytest.mark.browser
def test_visual_selection_does_not_activate_the_app_and_cancel_keeps_source(tmp_path):
    from reshoot import run
    config, board = broken_project(tmp_path)
    root = fail(config)
    data = repair.load(root)
    before = board.read_bytes()
    app = run.start_app({**__import__('tomllib').loads(config.read_text())['app'], 'cwd': str(tmp_path)}, tmp_path / 'picker-app.log')
    async def select(page):
        await page.evaluate("window.activated = 0; document.querySelector('#q').addEventListener('pointerdown', () => window.activated++); document.querySelector('#q').addEventListener('click', () => window.activated++)")
        await page.locator('#q').click()
        assert await page.evaluate('window.activated') == 0
        await page.wait_for_function("document.getAnimations().every(animation => animation.playState === 'finished')")
        await page.screenshot(path=str(tmp_path / 'picker.png'))
        await page.locator('reshoot-repair').get_by_role('button', name='Use this control').click()
    async def cancel(page):
        await page.locator('reshoot-repair').get_by_role('button', name='Cancel repair').click()
    try:
        target, alternatives = asyncio.run(repair.choose(data, pick=True, headless=True, drive=select))
        assert target == {'css': '#q'} and alternatives
        assert board.read_bytes() == before  # selecting alone does not write the source
        with pytest.raises(ValueError, match='cancelled'):
            asyncio.run(repair.choose(data, pick=True, headless=True, drive=cancel))
        assert board.read_bytes() == before
    finally:
        run.stop_app(app)


@pytest.mark.browser
def test_changed_app_refuses_a_stale_suggestion(tmp_path):
    config, board = broken_project(tmp_path)
    root = fail(config)
    before = board.read_bytes()
    app = tmp_path / 'index.html'
    app.write_text(app.read_text().replace('Search notes', 'Find notes'))
    with pytest.raises(ValueError, match='changed or is ambiguous'):
        repair.main(SimpleNamespace(run_path=str(root), config=None, apply=True, pick=False))
    assert board.read_bytes() == before and not (root / 'repair.json').exists()


@pytest.mark.browser
def test_studio_repairs_undoes_and_verifies_the_same_task(tmp_path):
    from playwright.sync_api import sync_playwright
    from reshoot import web
    config, board = broken_project(tmp_path)
    fail(config)
    checks = [b.get('expect') for b in story.load(board)['beat']]
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            chrome = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            try:
                page = chrome.new_page()
                page.goto(url)
                assert page.locator('.failure img').count() == 1
                with page.expect_navigation(timeout=60000):
                    page.click('[data-repair=apply]')
                assert 'Repair ready to verify' in page.locator('.failure').inner_text()
                assert page.locator('[data-history=undo]').is_enabled()
                with page.expect_navigation():
                    page.click('[data-history=undo]')
                assert page.locator('[data-repair=apply]').is_visible()
                with page.expect_navigation():
                    page.click('[data-history=redo]')
                assert page.locator('[data-repair]').count() == 0
                with page.expect_navigation(timeout=120000):
                    page.click('[data-job=update]')
                assert page.locator('.failure').count() == 0
                assert '3 of 3 result checks passed' in page.locator('.status').inner_text()
            finally:
                chrome.close()
    finally:
        httpd.reshoot_job.cancel()
        httpd.shutdown()
        httpd.server_close()
    assert checks == [b.get('expect') for b in story.load(board)['beat']]
