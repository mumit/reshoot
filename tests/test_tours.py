"""Offline tours retain checked frames, bounded text, provenance and normal run review."""
import base64
import json
import re
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import check, config, project, review, studio, tours
from reshoot.artifacts import digest
from reshoot.workspace import History
from test_screenshots import source, bind

STEP = {'beat': 'search', 'title': 'Find the note', 'text': 'Only the matching note remains.', 'alt': 'Search shows the matching note'}
SPEC = {'name': 'notes-tour', 'title': 'Save and find a note', 'step': [STEP, {**STEP, 'title': 'Explore the result', 'hotspot': [.5, .4]}]}
TAKES = [{'web': 'storyboard.toml', 'out': 'takes/demo.mp4'}]


@pytest.mark.parametrize('change', [
    {'name': '../outside'}, {'title': ''}, {'step': []}, {'step': [STEP] * 31},
    {'step': [{**STEP, 'alt': ''}]}, {'step': [{**STEP, 'title': 'x' * 121}]},
    {'step': [{**STEP, 'text': 'x' * 1001}]}, {'step': [{**STEP, 'take': True}]},
    {'step': [{**STEP, 'hotspot': [.5, float('nan')]}]}, {'step': [{**STEP, 'hotspot': [-.1, .5]}]},
    {'step': [{**STEP, 'hotspot': [True, .5]}]}, {'unknown': True},
])
def test_tour_validation_rejects_unsupported_settings(change):
    with pytest.raises(ValueError):
        tours.validate({**SPEC, **change}, 1)


def test_tour_edits_preserve_story_comments_and_revisions(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    path, board = tmp_path / 'reshoot.toml', tmp_path / 'storyboard.toml'
    task, original = board.read_bytes(), path.read_bytes()
    history = History([path, board])
    before = history.snapshot()
    tours.apply(tmp_path, {'operation': 'create', 'title': SPEC['title']}, expected=before)
    history.remember(before, history.snapshot())
    data = config.read(path)[0]['tour']
    assert [step['beat'] for step in data['step']] == ['add', 'search']
    assert board.read_bytes() == task
    with pytest.raises(ValueError, match='already exists'):
        tours.apply(tmp_path, {'operation': 'create'})
    path.write_text(path.read_text().replace('title = "Save', '# keep title comment\ntitle = "Save', 1))
    tours.apply(tmp_path, {'operation': 'set', 'step': 0, 'settings': {'text': 'Saved.', 'hotspot': [.3, .4]}})
    tours.apply(tmp_path, {'operation': 'move', 'step': 0, 'to': 1})
    assert config.read(path)[0]['tour']['step'][1]['text'] == 'Saved.'
    assert '# keep title comment' in path.read_text()
    tours.apply(tmp_path, {'operation': 'remove', 'step': 0})
    tours.apply(tmp_path, {'operation': 'move', 'step': 0, 'to': 0})
    saved = path.read_bytes()
    with pytest.raises(ValueError, match='at least one'):
        tours.apply(tmp_path, {'operation': 'remove', 'step': 0})
    with pytest.raises(ValueError, match='result checks'):
        tours.apply(tmp_path, {'operation': 'set', 'step': 0, 'settings': {'beat': 'intro'}})
    assert path.read_bytes() == saved
    tours.apply(tmp_path, {'operation': 'add', 'beat': 'search', 'settings': {'title': 'Again'}})
    assert config.read(path)[0]['tour']['step'][-1]['title'] == 'Again'
    tours.apply(tmp_path, {'operation': 'disable'})
    assert not config.read(path)[0].get('tour')
    assert board.read_bytes() == task
    history.restore(before)
    tours.apply(tmp_path, {'operation': 'create'})
    after = history.snapshot(); history.remember(before, after)
    history.move('undo'); assert path.read_bytes() == original
    history.move('redo'); assert history.snapshot() == after
    path.write_text(path.read_text() + '# external edit\n')
    with pytest.raises(ValueError, match='project changed'):
        tours.apply(tmp_path, {'operation': 'title', 'title': 'Stale'}, expected=after)
    assert path.read_text().endswith('# external edit\n')


def test_tour_embeds_checked_pixels_and_rejects_unbound_artifacts(tmp_path):
    shot = source(tmp_path)
    row = tours.render(tmp_path, SPEC, TAKES)
    report = bind(tmp_path)
    assert tours.listing(*review.read(tmp_path)) == [row]
    assert row['steps'][0]['source_sha256'] == digest(shot)
    assert review.exports(tmp_path, report) == ['tours/notes-tour.html']
    html = (tmp_path / row['path']).read_text()
    images = re.findall(r'data:image/png;base64,([^"\s]+)', html)
    assert len(images) == 2
    assert base64.b64decode(images[0]) == (tmp_path / row['steps'][0]['image']).read_bytes()
    assert 'connect-src \'none\'' in html and 'sha256-' in html
    for missing in [row['path'], row['steps'][0]['image'], row['steps'][0]['metadata'], row['steps'][0]['source']]:
        partial = {**report, 'files': [item for item in report['files'] if item['path'] != missing]}
        with pytest.raises(ValueError, match='Unbound'):
            tours.listing(tmp_path, partial)
    assert 'tour/notes-tour' in review.decision_names(tmp_path)
    (tmp_path / row['path']).write_text(html + 'tampered')
    with pytest.raises(ValueError, match='changed'):
        review.read(tmp_path)


def test_tour_text_scan_export_record_and_refresh_comparison(tmp_path, monkeypatch):
    old, new = tmp_path / 'old', tmp_path / 'new'
    for root, text in [(old, 'First explanation'), (new, 'PrivateMarker in the explanation')]:
        source(root)
        tours.render(root, {**SPEC, 'step': [{**STEP, 'text': text}]}, TAKES)
        bind(root, root.name)
    key, flags = check.text_findings([str(new / 'tours.json')], ['PrivateMarker'], {}, 'policy')
    assert len(key) == len(flags) == 1
    monkeypatch.chdir(tmp_path)
    args = SimpleNamespace(run_path=str(new), directory='docs', file=None, record='record', replace=False,
                           markdown='media.md', link=None)
    project.export(args)
    assert (tmp_path / 'docs/notes-tour.html').exists()
    assert 'Explore the walkthrough' in (tmp_path / 'media.md').read_text()
    assert tours.listing(*review.read(tmp_path / 'record'))[0]['name'] == SPEC['name']
    with pytest.raises(ValueError, match='overwrite'):
        project.export(args)
    compared = review.compare(SimpleNamespace(previous=str(old), current=str(new), out=None))
    assert compared['tours'][0]['change'] == 'changed'
    assert 'Walkthrough' in review.summary(compared, review.read(new)[1], new)
    assert review.main(SimpleNamespace(run_path=str(new), previous=None, import_decisions=None, quiet=True)) == 0
    assert 'sandbox="allow-scripts"' in (new / 'review.html').read_text()


def test_unbound_html_export_does_not_replace_record_or_copy_files(tmp_path):
    source(tmp_path / 'run')
    (tmp_path / 'run/arbitrary.html').write_text('<script>not a generated tour</script>')
    bind(tmp_path / 'run')
    args = SimpleNamespace(run_path=str(tmp_path / 'run'), directory=str(tmp_path / 'docs'),
                           file=['arbitrary.html'], record=str(tmp_path / 'record'), replace=False)
    with pytest.raises(ValueError, match='bound tour'):
        project.export(args)
    assert not (tmp_path / 'record').exists() and not (tmp_path / 'docs').exists()


@pytest.mark.browser
def test_offline_tour_navigation_escape_and_no_network(tmp_path):
    from playwright.sync_api import sync_playwright
    from reshoot import web
    source(tmp_path)
    hostile = '</script><img src="https://invalid.example/track" onerror="alert(1)">'
    spec = {**SPEC, 'title': hostile, 'step': [{**STEP, 'title': hostile, 'text': hostile}, SPEC['step'][1]]}
    row = tours.render(tmp_path, spec, TAKES)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844}, offline=True)
        errors, requests = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
        page.goto((tmp_path / row['path']).as_uri())
        assert page.locator('h1').inner_text() == hostile
        assert page.locator('.step:visible').count() == 1 and page.locator('.step:visible').get_attribute('id') == 'step-1'
        assert page.locator('img').count() == 2 and page.locator('img').first.evaluate('el => el.complete && el.naturalWidth > 0')
        page.get_by_role('link', name='Next', exact=True).click()
        assert page.locator('.step:visible').get_attribute('id') == 'step-2'
        assert page.locator('[aria-current=step]').inner_text() == '2'
        assert page.locator('.step:visible h2').evaluate('el => el === document.activeElement')
        page.locator('.marker').click()
        assert page.locator('.step:visible').get_attribute('id') == 'step-1'
        page.keyboard.press('End')
        assert page.locator('.step:visible').get_attribute('id') == 'step-2'
        page.keyboard.press('ArrowLeft')
        assert page.locator('.step:visible').get_attribute('id') == 'step-1'
        assert not requests and not errors
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(tmp_path / 'offline-tour.png'))
        plain = browser.new_page(viewport={'width': 390, 'height': 844}, java_script_enabled=False, offline=True)
        plain.goto((tmp_path / row['path']).as_uri())
        assert plain.locator('.step:visible').count() == 2
        assert plain.locator('img').first.evaluate('el => el.complete && el.naturalWidth > 0')
        plain.close()
        browser.close()


@pytest.mark.browser
def test_studio_builds_edits_and_recuts_checked_tour(tmp_path):
    from playwright.sync_api import expect, sync_playwright
    from reshoot import web
    from reshoot.cli import main
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    path, board = tmp_path / 'reshoot.toml', tmp_path / 'storyboard.toml'
    path.write_text(path.read_text().replace('scan = true', 'scan = false'))
    task = board.read_bytes()
    with pytest.raises(SystemExit) as result:
        main(['preview', str(path)])
    assert result.value.code == 0
    baseline, _ = review.read(tmp_path / 'latest')
    clean = digest(baseline / 'takes/demo.clean.mp4')
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.click('#video-tab')
            page.locator('.tour-controls > summary').click()
            page.locator('#tour-create [name=title]').fill(SPEC['title'])
            page.click('[data-job=update]')
            assert 'unsaved' in page.locator('#save-error').inner_text()
            with page.expect_navigation():
                page.locator('#tour-create [type=submit]').click()
            assert [s['beat'] for s in config.read(path)[0]['tour']['step']] == ['add', 'search']
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert 'tour' not in config.read(path)[0]
            with page.expect_navigation():
                page.click('[data-history=redo]')
            first = page.locator('.tour-form[data-step="0"]')
            first.locator('[name=text]').fill('The saved note appears in the list.')
            first.locator('.tour-marker > summary').click()
            first.locator('.tour-point').click(position={'x': 100, 'y': 60})
            with page.expect_navigation():
                first.locator('[type=submit]').click()
            assert 'hotspot' in config.read(path)[0]['tour']['step'][0]
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            current, report = review.read(tmp_path / 'latest')
            assert report['recut_from'] == baseline.name and report['expectations_count'] == 3
            assert digest(current / 'takes/demo.clean.mp4') == clean and board.read_bytes() == task
            row = tours.listing(current, report)[0]
            assert len(row['steps']) == 2 and all(s['result_checks'] for s in row['steps'])
            frame = page.frame_locator('.tour-previews iframe')
            assert frame.get_by_role('link', name='Next', exact=True).evaluate('el => el.getBoundingClientRect().bottom <= innerHeight')
            frame.get_by_role('link', name='Next', exact=True).click()
            expect(frame.locator('.step:visible')).to_have_attribute('id', 'step-2')  # waits for the step to change
            assert 'tours/demo-tour.html' in review.exports(current, report)
            key = json.loads((current / 'review/key.json').read_text())
            from reshoot.safety import describe
            assert any(value[0] == describe(str(current / row['steps'][0]['image'])) for value in key.values())
            with page.expect_navigation():
                page.locator('.tour-step[data-step="1"] [data-tour-op=move][data-to="0"]').click()
            assert config.read(path)[0]['tour']['step'][0]['beat'] == 'search'
            with page.expect_navigation():
                page.locator('[data-history=undo]').click()
            assert config.read(path)[0]['tour']['step'][0]['beat'] == 'add'
            assert not errors
            page.screenshot(path=str(tmp_path / 'tour-studio.png'))
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
