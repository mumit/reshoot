"""Documentation images are checked result frames, bound and refreshed with their run."""
import json
import threading
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from reshoot import config, project, review, screenshots, studio
from reshoot.artifacts import digest
from reshoot.workspace import History

SPEC = {'name': 'search-result', 'beat': 'search', 'alt': 'Search shows the matching note'}
TAKES = [{'web': 'storyboard.toml', 'out': 'takes/demo.mp4'}]


def source(root, colour='red'):
    folder = root / 'takes'
    folder.mkdir(parents=True)
    (folder / 'demo.mp4').write_bytes(b'fixture video placeholder')
    shot = folder / 'demo.evidence/search.png'
    shot.parent.mkdir()
    image = Image.new('RGB', (800, 400), colour)
    image.paste(Image.new('RGB', (400, 400), 'blue'), (400, 0))
    image.save(shot)
    (folder / 'demo.take.json').write_text(json.dumps({'status': 'completed', 'mode': 'final', 'video': 'demo.mp4',
        'story_id': 'notes', 'beats': [{'id': 'search', 'status': 'passed', 'screenshot': 'demo.evidence/search.png',
        'expectations': [{'status': 'passed', 'type': 'text'}]}]}))
    return shot


def bind(root, name='run'):
    report = {'schema_version': 1, 'id': name, 'ok': True, 'mode': 'final', 'review_status': 'pending',
              'expectations_status': 'passed', 'expectations_count': 1,
              'files': [{'path': str(p.relative_to(root)), 'sha256': digest(p)} for p in root.rglob('*') if p.is_file() and p.name != 'run.json']}
    (root / 'run.json').write_text(json.dumps(report))
    return report


@pytest.mark.parametrize('change', [
    {'name': '../escape'}, {'name': ''}, {'alt': ''}, {'alt': 'two\nlines'}, {'alt': 'a' * 301},
    {'take': True}, {'take': 2}, {'width': True}, {'width': 0}, {'crop': [0, 0, 0, 1]},
    {'crop': [.5, 0, .6, 1]}, {'crop': [float('nan'), 0, 1, 1]}, {'unknown': True},
])
def test_invalid_screenshot_specs_do_not_change_project(tmp_path, change):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    path = tmp_path / 'reshoot.toml'
    before = path.read_bytes()
    spec = {**SPEC, **change}
    with pytest.raises(ValueError):
        screenshots.apply(tmp_path, 'set', spec['name'], {k: v for k, v in spec.items() if k != 'name'})
    assert path.read_bytes() == before


def test_screenshot_edits_preserve_task_sources_comments_and_undo(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    path, board = tmp_path / 'reshoot.toml', tmp_path / 'storyboard.toml'
    original, task = config.read(path)[0], board.read_bytes()
    history = History([path, board])
    before = history.snapshot()
    screenshots.apply(tmp_path, 'add', SPEC['name'], {k: v for k, v in SPEC.items() if k != 'name'}, expected=before)
    history.remember(before, history.snapshot())
    with pytest.raises(ValueError, match='already exists'):
        screenshots.apply(tmp_path, 'add', SPEC['name'], {'beat': 'add', 'alt': 'Duplicate name'})
    path.write_text(path.read_text().replace('alt = ', '# descriptive text\nalt = '))
    screenshots.apply(tmp_path, 'set', SPEC['name'], {'width': 640, 'crop': [.5, 0, .5, 1]})
    data = config.read(path)[0]
    assert data['take'] == original['take'] and data['check'] == original['check']
    assert board.read_bytes() == task and '# descriptive text' in path.read_text()
    assert data['screenshot'][0]['crop'] == [.5, 0, .5, 1]
    with pytest.raises(ValueError, match='result checks'):
        screenshots.apply(tmp_path, 'set', 'unchecked', {'beat': 'intro', 'alt': 'No checks'})
    history.restore(before)
    screenshots.apply(tmp_path, 'set', 'checked', {'beat': 'search', 'alt': 'Found'})
    after = history.snapshot()
    history.remember(before, after)
    history.move('undo'); assert history.snapshot() == before
    history.move('redo'); assert history.snapshot() == after
    path.write_text(path.read_text() + '# external\n')
    with pytest.raises(ValueError, match='project changed'):
        screenshots.apply(tmp_path, 'remove', 'checked', expected=after)
    assert path.read_text().endswith('# external\n')


def test_render_crops_actual_pixels_downsizes_and_binds_provenance(tmp_path):
    shot = source(tmp_path)
    rows = screenshots.render(tmp_path, [{**SPEC, 'crop': [.5, 0, .5, 1], 'width': 200}], TAKES)
    assert rows[0]['pixels'] == [200, 200] and rows[0]['source_pixels'] == [800, 400]
    assert Image.open(tmp_path / rows[0]['path']).getpixel((50, 50)) == (0, 0, 255)
    assert rows[0]['source_sha256'] == digest(shot) and rows[0]['result_checks'] == 1
    report = bind(tmp_path)
    assert screenshots.listing(*review.read(tmp_path)) == rows
    assert review.exports(tmp_path, report) == ['screenshots/search-result.png']
    assert 'screenshot/search-result' in review.decision_names(tmp_path)
    assert review.main(SimpleNamespace(run_path=str(tmp_path), previous=None, import_decisions=None, quiet=True)) == 0
    page = (tmp_path / 'review.html').read_text()
    assert 'alt="Search shows the matching note"' in page and 'Documentation screenshot from a checked result frame' in page
    (tmp_path / rows[0]['path']).write_bytes(b'changed after scan')
    with pytest.raises(ValueError, match='changed'):
        review.read(tmp_path)


@pytest.mark.parametrize('fault', ['unchecked', 'failed', 'partial', 'missing', 'outside'])
def test_screenshot_refuses_unverified_or_missing_evidence(tmp_path, fault):
    shot = source(tmp_path)
    metadata = tmp_path / 'takes/demo.take.json'
    data = json.loads(metadata.read_text())
    if fault == 'unchecked':
        data['beats'][0]['expectations'] = []
    elif fault == 'failed':
        data['beats'][0]['expectations'][0]['status'] = 'failed'
    elif fault == 'partial':
        data['mode'] = 'partial'
    elif fault == 'missing':
        shot.unlink()
    else:
        data['beats'][0]['screenshot'] = '../../outside.png'
    metadata.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        screenshots.render(tmp_path, [SPEC], TAKES)
    assert not (tmp_path / 'screenshots.json').exists()


def test_local_export_record_and_refresh_comparison_include_screenshots(tmp_path, monkeypatch, capsys):
    old, new = tmp_path / 'old', tmp_path / 'new'
    for root, colour in [(old, 'red'), (new, 'green')]:
        source(root, colour)
        screenshots.render(root, [{**SPEC, 'width': 160}], TAKES)
        bind(root, root.name)
    monkeypatch.chdir(tmp_path)
    destination, record = tmp_path / 'docs', tmp_path / 'record'
    args = SimpleNamespace(run_path=str(new), directory=str(destination), record=str(record), file=None,
                           replace=False, markdown=str(tmp_path / 'media.md'), link=None)
    assert project.export(args) == 0
    assert (destination / 'search-result.png').exists()
    assert '![Search shows the matching note](docs/search-result.png)' in (tmp_path / 'media.md').read_text()
    assert screenshots.listing(*review.read(record))[0]['name'] == 'search-result'
    with pytest.raises(ValueError, match='overwrite'):
        project.export(args)
    result = review.compare(SimpleNamespace(previous=str(old), current=str(new), out=None))
    assert result['screenshots'][0]['change'] == 'changed'
    assert 'Documentation screenshot' in review.summary(result, review.read(new)[1], new)
    # Resizing never enlarges the source; identical re-cuts retain screenshot pixels.
    screenshots.render(new, [{**SPEC, 'width': 3840}], TAKES)
    assert Image.open(new / 'screenshots/search-result.png').size == (800, 400)


def test_manifest_cannot_promote_unbound_pixels_or_provenance(tmp_path):
    source(tmp_path)
    screenshots.render(tmp_path, [SPEC], TAKES)
    report = bind(tmp_path)
    for missing in ('screenshots/search-result.png', 'takes/demo.take.json', 'takes/demo.evidence/search.png'):
        partial = {**report, 'files': [item for item in report['files'] if item['path'] != missing]}
        with pytest.raises(ValueError, match='Unbound'):
            screenshots.listing(tmp_path, partial)


def test_alt_text_is_scanned_directly_without_ocr(tmp_path):
    from reshoot.check import text_findings
    source(tmp_path)
    screenshots.render(tmp_path, [{**SPEC, 'alt': 'PrivateMarker is visible'}], TAKES)
    key, flags = text_findings([str(tmp_path / 'screenshots.json')], ['PrivateMarker'], {}, 'test-policy')
    assert len(key) == len(flags) == 1
    assert 'search-result' in next(iter(key.values()))[0]


@pytest.mark.browser
def test_studio_selects_checked_docs_frame_and_recuts_with_scan_and_review(tmp_path):
    from playwright.sync_api import sync_playwright
    from reshoot import web
    from reshoot.cli import main
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    path, board = tmp_path / 'reshoot.toml', tmp_path / 'storyboard.toml'
    path.write_text(path.read_text().replace('scan = true', 'scan = false'))
    task = board.read_bytes()
    with pytest.raises(SystemExit) as result:
        main(['preview', str(path)])
    assert result.value.code == 0
    baseline, report = review.read(tmp_path / 'latest')
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
            assert page.locator('.beat[data-beat=intro] [data-shot-beat]').count() == 0
            page.locator('[data-shot-beat=search]').click()
            form = page.locator('#add-screenshot')
            assert form.locator('[name=name]').input_value() == 'search-result'
            form.locator('[name=alt]').fill('Search shows the saved bike note')
            form.locator('[name=width]').fill('640')
            page.click('[data-job=update]')
            assert 'unsaved' in page.locator('#save-error').inner_text()
            with page.expect_navigation():
                form.locator('[type=submit]').click()
            assert config.read(path)[0]['screenshot'][0]['alt'] == 'Search shows the saved bike note'
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert not config.read(path)[0].get('screenshot')
            with page.expect_navigation():
                page.click('[data-history=redo]')
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            current, current_report = review.read(tmp_path / 'latest')
            assert current_report['recut_from'] == baseline.name and current_report['expectations_count'] == 3
            assert digest(current / 'takes/demo.clean.mp4') == clean and board.read_bytes() == task
            assert page.locator('.docs-shots img').get_attribute('alt') == 'Search shows the saved bike note'
            assert 'runs/' + current.name + '/screenshots/search-result.png' in page.locator('.docs-shots img').get_attribute('src')
            row = screenshots.listing(current, current_report)[0]
            assert row['pixels'][0] == 640 and row['result_checks'] == 2
            page.locator('[data-shot-beat=search]').click()
            assert page.locator('#add-screenshot [name=name]').input_value() == ''
            assert page.locator('.screenshot-form[data-name=search-result] [name=alt]').evaluate('el => el === document.activeElement')
            page.locator('.docs-shots [data-inspect]').click()
            image = page.locator('#export-inspector img')
            assert image.get_attribute('alt') == row['alt']
            assert image.evaluate('el => el.getBoundingClientRect().width') == row['pixels'][0]
            page.locator('#export-inspector button').click()
            from reshoot.safety import describe
            source_name = describe(str(current / row['path']))
            key = json.loads((current / 'review/key.json').read_text())
            assert any(value[0] == source_name for value in key.values())
            assert 'screenshots/search-result.png' in (current / 'review.html').read_text()
            existing = page.locator('.screenshot-form[data-name=search-result]')
            existing.locator('.shot-crop > summary').click()
            guide = existing.locator('.shot-crop-guide')
            box = guide.bounding_box()
            page.mouse.move(box['x'] + box['width'] * .1, box['y'] + box['height'] * .1)
            page.mouse.down()
            page.mouse.move(box['x'] + box['width'] * .9, box['y'] + box['height'] * .7, steps=8)
            page.mouse.up()
            assert float(existing.locator('[name=crop_w]').input_value()) == pytest.approx(80, abs=.1)
            with page.expect_navigation():
                existing.locator('[type=submit]').click()
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            cropped, cropped_report = review.read(tmp_path / 'latest')
            cropped_row = screenshots.listing(cropped, cropped_report)[0]
            assert cropped_row['pixels'][0] < row['pixels'][0] and cropped_row['pixels'][1] < row['pixels'][1]
            assert digest(cropped / 'takes/demo.clean.mp4') == clean
            existing.locator('[name=alt]').fill('   ')
            existing.locator('[type=submit]').click()
            page.wait_for_function("document.getElementById('save-error').textContent.includes('alt text')")
            assert config.read(path)[0]['screenshot'][0]['alt'] == 'Search shows the saved bike note'
            existing.locator('[type=reset]').click()
            with page.expect_navigation():
                page.click('[data-remove-shot=search-result]')
            assert not config.read(path)[0].get('screenshot')
            assert page.locator('.docs-shots img').count() == 1  # displayed run still bound to its image
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert not errors
            page.screenshot(path=str(tmp_path / 'screenshots-studio.png'))
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
