"""Saved edits, rendered files and captured task provenance remain distinct throughout the studio."""
import hashlib
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import delivery, journey, project, review, story, studio
from reshoot.artifacts import digest
from reshoot.workspace import History


def setup(folder):
    project.init(SimpleNamespace(directory=str(folder), url=None, quiet=True))
    return folder / 'reshoot.toml', folder / 'storyboard.toml', folder / 'edit.toml'


def recording(folder, config, board, edit, mode='preview'):
    from reshoot.config import read
    data, _ = read(config)
    root = folder / 'takes/runs' / ('a' * 32)
    (root / 'takes').mkdir(parents=True)
    (root / 'final.mp4').write_bytes(b'synthetic fixture final video')
    board_data = story.load(board)
    metadata = {'status': 'completed', 'mode': 'preview', 'story_id': 'notes', 'beats': [
        {'id': beat['id'], 'definition_sha256': hashlib.sha256(json.dumps(beat, sort_keys=True).encode()).hexdigest()}
        for beat in board_data['beat']],
        'recording_settings_sha256': hashlib.sha256(json.dumps(story.recording_settings(board_data), sort_keys=True).encode()).hexdigest()}
    (root / 'takes/demo.take.json').write_text(json.dumps(metadata))
    (root / 'takes/demo.captions.json').write_text(json.dumps({'style': board_data.get('caption', {}), 'captions': [
        {'beat': beat['id'], 'recorded': beat.get('caption'), 'recorded_sub': beat.get('sub'), 'text': beat.get('caption'), 'sub': beat.get('sub')}
        for beat in board_data['beat']]}))
    state = journey.snapshot(config)
    report = {'id': root.name, 'ok': True, 'mode': mode, 'review_status': 'pending', 'scan_status': 'skipped',
              'inputs': {'render_state': state, 'capture_state': state, 'config_sha256': digest(config), 'edit_sha256': digest(edit),
              'recording_config_sha256': hashlib.sha256(json.dumps({k: v for k, v in data.items() if k in ('app', 'take', 'inputs')}, sort_keys=True).encode()).hexdigest(),
              'fixtures': [{'sha256': digest(folder / name)} for name in data.get('inputs', [])]},
              'files': [{'path': str(path.relative_to(root)), 'sha256': digest(path)} for path in root.rglob('*') if path.is_file()]}
    (root / 'run.json').write_text(json.dumps(report))
    return root, report


def test_caption_recut_is_current_but_ignored_capture_changes_are_not(tmp_path):
    config, board, edit = setup(tmp_path)
    run = recording(tmp_path, config, board, edit)
    assert journey.state(config, run)['phase'] == 'preview'
    studio.edit(board, {'beat': 'search', 'caption': 'New caption'})
    assert journey.state(config, run)['pending']
    assert studio.update_kind(tmp_path, config, studio.project(tmp_path)[2], run)[0] == 'recut'
    run[1]['inputs']['render_state'] = journey.snapshot(config)  # a re-cut redraws these words
    assert not journey.state(config, run)['pending']
    studio.edit(board, {'beat': 'search', 'hold': 8})
    run[1]['inputs']['render_state'] = journey.snapshot(config)  # an explicit re-cut still uses the older hold
    assert journey.state(config, run)['pending']
    assert 'Story' in journey.state(config, run)['changes']
    assert studio.update_kind(tmp_path, config, studio.project(tmp_path)[2], run)[0] == 'preview'


@pytest.mark.parametrize('kind', ['input', 'upload'])
def test_recut_retains_original_demo_data_and_upload_fingerprints(tmp_path, kind):
    config, board, edit = setup(tmp_path)
    asset = tmp_path / 'seed.txt'
    asset.write_text('old data')
    if kind == 'input':
        import re
        config.write_text(re.sub(r'(?m)^inputs\s*=.*$', 'inputs = ["seed.txt"]', config.read_text()))
    else:
        board.write_text('setup = [{type="upload",target={css="#upload"},file="seed.txt"}]\n' + board.read_text())
    run = recording(tmp_path, config, board, edit)
    asset.write_text('new data')  # same-size overwrite also invalidates the stat-keyed hash cache
    run[1]['inputs']['render_state'] = journey.snapshot(config)
    assert journey.state(config, run)['pending']
    assert studio.update_kind(tmp_path, config, studio.project(tmp_path)[2], run)[0] == 'preview'


def test_changed_music_requires_recut_and_style_library_alone_does_not(tmp_path):
    config, board, edit = setup(tmp_path)
    music = tmp_path / 'music.wav'
    music.write_bytes(b'old tone')
    edit.write_text('music = "music.wav"\n' + edit.read_text())
    run = recording(tmp_path, config, board, edit)
    (tmp_path / 'styles.toml').write_text('# saved library only\n')
    assert not journey.state(config, run)['pending']
    music.write_bytes(b'new tone')
    assert journey.state(config, run)['changes'] == ['Music']
    assert studio.update_kind(tmp_path, config, studio.project(tmp_path)[2], run)[0] == 'recut'


def test_earlier_runs_do_not_claim_full_source_freshness(tmp_path):
    config, board, edit = setup(tmp_path)
    run = recording(tmp_path, config, board, edit)
    run[1]['inputs'].pop('render_state')
    state = journey.state(config, run)
    assert not state['known'] and not state['pending'] and state['phase'] == 'unknown'
    studio.edit_cut(edit, config, {'add_card': 'start'})
    assert journey.state(config, run)['pending']


@pytest.mark.parametrize('creating', [False, True])
@pytest.mark.parametrize('failure', [{'stale': False, 'repaired': False}, {'stale': True, 'repaired': False},
                                   {'stale': False, 'repaired': True}])
def test_recovery_instruction_and_available_continuation_agree(creating, failure):
    base = {'next': 'run', 'phase': 'preview', 'title': 'Preview', 'detail': '', 'pending': False}
    state = journey.workflow(base, creating=creating, tools={'ok': True}, failure=failure)
    continuation = state['continuation']
    assert continuation['enabled'] and continuation['label'] in state['detail']
    assert state['action'] == continuation
    assert state['actions']['update']['enabled'] is not creating
    assert base['phase'] == 'preview'


def test_tool_and_history_blocks_take_precedence_over_recording_actions():
    base = {'next': 'update', 'phase': 'empty', 'title': 'Preview', 'detail': '', 'pending': False}
    stopped = journey.workflow(base, creating=True, tools={'ok': False}, failure={'stale': True})
    assert stopped['action']['kind'] == 'setup'
    assert all(not action['enabled'] and action['reason'] for action in stopped['actions'].values())
    recovery = journey.workflow(base, creating=True, tools={'ok': True},
                                session={'title': 'Changed files', 'detail': 'Compare the files.'})
    assert recovery['action']['kind'] == 'session' and recovery['title'] == 'Changed files'
    assert all(not action['enabled'] and action['reason'] for action in recovery['actions'].values())


def test_bundle_contains_only_exports_and_hashes_the_actual_archived_bytes(tmp_path):
    from test_screenshots import source, bind, SPEC as SHOT, TAKES
    from test_tours import SPEC as TOUR
    from reshoot import screenshots, tours
    source(tmp_path)
    screenshots.render(tmp_path, [SHOT], TAKES)
    tours.render(tmp_path, TOUR, TAKES)
    (tmp_path / 'final.mp4').write_bytes(b'final video')
    (tmp_path / 'final.srt').write_text('1\n00:00:00,000 --> 00:00:01,000\nResult\n')
    (tmp_path / 'app.log').write_text('not part of the download')
    report = bind(tmp_path)
    with delivery.bundle(tmp_path, report) as file, zipfile.ZipFile(file) as archive:
        assert set(archive.namelist()) == {'final.mp4', 'final.srt', 'search-result.png', 'notes-tour.html', 'README.md', 'manifest.json'}
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['review_status'] == 'pending'
        for item in manifest['files']:
            assert hashlib.sha256(archive.read(item['name'])).hexdigest() == item['sha256']
        assert 'Search shows the matching note' in archive.read('README.md').decode()
    (tmp_path / 'final.mp4').write_bytes(b'changed after review')
    with pytest.raises(ValueError, match='changed while'):
        delivery.bundle(tmp_path, report)


def test_studio_rejects_pending_acceptance_and_stale_bundle_bindings(tmp_path, monkeypatch):
    config, board, edit = setup(tmp_path)
    root, report = recording(tmp_path, config, board, edit, mode='final')
    intercepted = []
    monkeypatch.setattr(review, 'accept_from_page', lambda path, body: (intercepted.append(path) or 2, 'intercepted'))
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        history = History([config, board, tmp_path / 'styles.toml', edit])
        body = {'run_id': root.name, 'binding': review.binding(root, report), 'revision': history.revision()}
        def post():
            request = urllib.request.Request(url + 'accept', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
            return json.load(urllib.request.urlopen(request))
        assert post()['output'] == 'intercepted' and len(intercepted) == 1
        studio.edit(board, {'beat': 'search', 'caption': 'Saved but not rendered'})
        body['revision'] = history.revision()
        assert 'not in this recording' in post()['error'] and len(intercepted) == 1
        assert json.loads((root / 'run.json').read_text())['review_status'] == 'pending'
        link = url + f'download/{root.name}/{body["binding"]}/exports.zip'
        with urllib.request.urlopen(link) as response:
            assert response.headers['Content-Type'] == 'application/zip'
            assert 'reshoot-final-' in response.headers['Content-Disposition']
        with pytest.raises(urllib.error.HTTPError, match='409'):
            urllib.request.urlopen(url + f'download/{root.name}/{"0" * 64}/exports.zip')
    finally:
        httpd.shutdown(); httpd.server_close()


@pytest.mark.browser
def test_creation_journey_shows_saved_state_navigates_and_downloads_bound_exports(tmp_path):
    from playwright.sync_api import sync_playwright
    from reshoot import web
    from reshoot.cli import main
    config, board, edit = setup(tmp_path)
    config.write_text(config.read_text().replace('scan = true', 'scan = false'))
    from reshoot.workspace import block, first_header, put, read_lines, save
    from reshoot.config import read
    seed = tmp_path / 'reset-seed.txt'
    seed.write_text('before reset')
    lines = read_lines(config)
    put(lines, (0, first_header(lines)), 'inputs', ['index.html', 'about.html', 'reset-seed.txt'])
    put(lines, block(lines, '[app]'), 'reset', 'python3 -c "from pathlib import Path; Path(\'reset-seed.txt\').write_text(\'after reset\')"')
    save(config, lines, read)
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code == 0
    baseline, baseline_report = review.read(tmp_path / 'latest')
    assert seed.read_text() == 'after reset'
    assert baseline_report['inputs']['fixtures'][-1]['sha256'] == digest(seed)
    clean = digest(baseline / 'takes/demo.clean.mp4')
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            assert page.locator('#journey').get_attribute('data-phase') == 'preview'
            assert page.locator('[data-job=run]').evaluate('el => el.classList.contains("primary")')
            page.locator('.section-nav [data-jump=look-panel]').click()
            assert page.locator('.styling').evaluate('el => el.open')
            colour = page.locator('.look input[name=background]')
            colour.fill('invalid colour'); colour.press('Tab')
            page.wait_for_function("document.getElementById('save-error').textContent.includes('colour')")
            assert page.locator('[data-reset-drafts]').is_visible()
            with page.expect_navigation():
                page.locator('[data-reset-drafts]').click()
            assert 'invalid colour' not in board.read_text()
            page.locator('.section-nav [data-jump=story-panel]').click()
            page.locator('[data-select-step=search]').click()
            caption = page.locator('.beat[data-beat=search] input[name=caption]')
            caption.fill('A clearer result'); caption.press('Tab')
            page.wait_for_function("!document.querySelector('[data-unsaved]')")
            assert page.locator('#journey').get_attribute('data-phase') == 'pending'
            assert 'existing recording' in page.locator('#journey-plan').inner_text()
            assert page.locator('body').get_attribute('data-run') == baseline.name
            with page.expect_download() as event:
                page.locator('.section-nav [data-jump=download-panel]').click()
                page.locator('[data-bundle]').click()
            download = event.value
            assert download.suggested_filename.startswith('reshoot-preview-')
            with zipfile.ZipFile(download.path()) as archive:
                manifest = json.loads(archive.read('manifest.json'))
                assert manifest['run_id'] == baseline_report['id'] and manifest['review_status'] == 'pending'
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            current, current_report = review.read(tmp_path / 'latest')
            assert current_report['recut_from'] == baseline.name and digest(current / 'takes/demo.clean.mp4') == clean
            assert page.locator('#journey').get_attribute('data-phase') == 'preview'
            page.locator('.more-tools > summary').click()
            page.locator('.section-nav [data-jump=tour-panel]').click()
            assert page.locator('.tour-controls').evaluate('el => el.open')
            # Returning from an editor detects external changes without advancing this tab's revision.
            revision = page.locator('body').get_attribute('data-revision')
            board.write_text(board.read_text() + '# external edit\n')
            page.evaluate('window.dispatchEvent(new Event("focus"))')
            page.wait_for_function("document.getElementById('journey').dataset.phase === 'external'")
            assert page.locator('body').get_attribute('data-revision') == revision
            with page.expect_navigation():
                page.locator('[data-reload-project]').click()
            assert board.read_text().endswith('# external edit\n')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator('.section-nav [data-jump=story-panel]').click()
            top = page.locator('#story-panel').bounding_box()['y']
            assert top >= page.locator('header').bounding_box()['height'] - 2
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert not errors
            page.screenshot(path=str(tmp_path / 'journey-mobile.png'))
            browser.close()
    finally:
        httpd.shutdown(); httpd.server_close()


def test_external_storyboard_replacement_requires_reload_and_rebinds_undo(tmp_path):
    config, board, _ = setup(tmp_path)
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        from html import unescape
        import re
        def revision():
            html = urllib.request.urlopen(url).read().decode()
            return unescape(re.search(r'data-revision="([^"]+)"', html)[1])
        old = revision()
        replacement = tmp_path / 'replacement.toml'
        replacement.write_text(board.read_text())
        original = board.read_bytes()
        config.write_text(config.read_text().replace('web = "storyboard.toml"', 'web = "replacement.toml"'))
        def post(action, revision):
            request = urllib.request.Request(url + action, data=json.dumps(
                {'revision': revision, 'beat': 'search', 'caption': 'Edited replacement'}).encode(),
                headers={'Content-Type': 'application/json'})
            return json.load(urllib.request.urlopen(request))
        assert 'error' in post('edit', old)
        new = revision()
        assert new != old
        saved = post('edit', new)
        assert saved['ok'] and 'Edited replacement' in replacement.read_text()
        assert post('undo', saved['revision'])['ok']
        assert replacement.read_bytes() == original and board.read_bytes() == original
        assert 'replacement.toml' in config.read_text()
    finally:
        httpd.shutdown(); httpd.server_close()
