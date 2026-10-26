"""Recovery of saved studio edits, using synthetic source files and notes only."""
import json
import threading
import urllib.error
import urllib.request
import zipfile
from html import unescape
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import project, studio
from reshoot.session import Session


def files(folder):
    project.init(SimpleNamespace(directory=str(folder), url=None, quiet=True))
    config = folder / 'reshoot.toml'
    return config, [config, folder / 'storyboard.toml', folder / 'styles.toml', folder / 'edit.toml']


def change(session, operation):
    with session.transaction():
        session.check(session.revision())
        session.change(operation)


def recover(session, choice='resume'):
    with session.transaction(recovery=True):
        session.recover(choice, session.token)


def test_restart_recovers_grouped_undo_redo_and_absent_files(tmp_path):
    config, paths = files(tmp_path)
    initial = {path: path.read_bytes() if path.exists() else None for path in paths}
    session = Session(config, paths)
    def operation():
        paths[1].write_text(paths[1].read_text() + '# preserved comment\n')
        paths[2].write_text('# a saved style library\n')
        paths[3].write_text(paths[3].read_text() + '# same Undo step\n')
    change(session, operation)
    saved = session.snapshot()
    checkpoint = session.file.read_bytes()
    restarted = Session(config, paths)
    assert restarted.info() is None and len(restarted.undo) == 1
    assert restarted.snapshot() == saved and restarted.file.read_bytes() == checkpoint
    with restarted.transaction():
        restarted.move('undo')
    assert restarted.snapshot() == initial and not paths[2].exists()
    again = Session(config, paths)
    assert again.info() is None and len(again.redo) == 1
    with again.transaction():
        again.move('redo')
    assert again.snapshot() == saved
    assert again.file.stat().st_mode & 0o777 == 0o600


def test_external_changes_offer_copy_and_fresh_start_without_replacing_files(tmp_path):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    change(session, lambda: paths[1].write_text(paths[1].read_text() + '# saved caption\n'))
    checkpoint = session.file.read_bytes()
    saved = paths[1].read_bytes()
    paths[1].write_text(paths[1].read_text() + '# external change\n')
    actual = paths[1].read_bytes()
    restarted = Session(config, paths)
    assert not restarted.info()['resume'] and restarted.info()['changed'] == ['storyboard.toml']
    with pytest.raises(ValueError, match='project changed'):
        recover(restarted)
    with restarted.source_copy(restarted.token) as file, zipfile.ZipFile(file) as archive:
        assert archive.read('sources/2/storyboard.toml') == saved
        assert all(not name.startswith('/') and '..' not in name.split('/') for name in archive.namelist())
    recover(restarted, 'fresh')
    assert paths[1].read_bytes() == actual and not restarted.undo and not restarted.redo
    assert next(restarted.file.parent.glob('*-archived-*.json')).read_bytes() == checkpoint
    change(restarted, lambda: paths[1].write_text(paths[1].read_text() + '# new session\n'))
    with restarted.transaction():
        restarted.move('undo')
    assert paths[1].read_bytes() == actual


def test_empty_history_does_not_interrupt_external_edits(tmp_path):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    with session.transaction():
        session.checkpoint()
    paths[1].write_text(paths[1].read_text() + '# external editor, no history to recover\n')
    actual = paths[1].read_bytes()
    restarted = Session(config, paths)
    assert restarted.info() is None and not restarted.undo and not restarted.redo
    change(restarted, lambda: paths[1].write_text(paths[1].read_text() + '# new change\n'))
    with restarted.transaction():
        restarted.move('undo')
    assert paths[1].read_bytes() == actual


@pytest.mark.parametrize('raw', [b'{"schema_version":999}', b'{truncated', b'[]'])
def test_bad_checkpoints_require_explicit_start_and_preserve_original(tmp_path, raw):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    original = session.snapshot()
    session.file.write_bytes(raw)
    restarted = Session(config, paths)
    assert restarted.info()['problem'] and not restarted.info()['download']
    recover(restarted, 'fresh')
    assert restarted.snapshot() == original and not restarted.pending
    assert next(restarted.file.parent.glob('*-archived-*.json')).read_bytes() == raw


def test_source_paths_are_matched_before_saved_history_can_be_used(tmp_path):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    change(session, lambda: paths[1].write_text(paths[1].read_text() + '# saved\n'))
    outside = tmp_path / 'untracked.txt'
    outside.write_text('keep me')
    data = json.loads(session.file.read_text())
    data['paths'][1] = str(outside)
    session.file.write_text(json.dumps(data))
    restarted = Session(config, paths)
    with pytest.raises(ValueError, match='project changed'):
        recover(restarted)
    assert outside.read_text() == 'keep me'


def test_saved_source_download_cannot_make_unsafe_zip_paths(tmp_path):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    change(session, lambda: paths[1].write_text(paths[1].read_text() + '# saved\n'))
    data = json.loads(session.file.read_text())
    data['paths'] = ['../..', r'..\..\story.toml', 'styles.toml', '/']
    session.file.write_text(json.dumps(data))
    restarted = Session(config, paths)
    with restarted.source_copy(restarted.token) as file, zipfile.ZipFile(file) as archive:
        for name in archive.namelist():
            assert not name.startswith('/') and '..' not in name.split('/') and '\\' not in name


def test_competing_studios_cannot_overwrite_a_newer_checkpoint(tmp_path):
    config, paths = files(tmp_path)
    first, second = Session(config, paths), Session(config, paths)
    change(first, lambda: paths[1].write_text(paths[1].read_text() + '# first studio\n'))
    checkpoint = first.file.read_bytes()
    with pytest.raises(ValueError, match='another studio'):
        change(second, lambda: paths[1].write_text('must not run'))
    assert first.file.read_bytes() == checkpoint and 'first studio' in paths[1].read_text()
    second.refresh(paths)
    assert second.info() is None and second.file.read_bytes() == checkpoint
    change(second, lambda: paths[1].write_text(paths[1].read_text() + '# second studio\n'))
    with pytest.raises(ValueError, match='another studio'):
        change(first, lambda: paths[1].write_text('must not run either'))


def test_change_during_resume_is_not_adopted_into_the_old_undo_stack(tmp_path, monkeypatch):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    change(session, lambda: paths[1].write_text(paths[1].read_text() + '# saved\n'))
    matches = Session.can_resume
    def concurrent_edit(self):
        result = matches(self)
        if result:
            paths[1].write_text(paths[1].read_text() + '# concurrent editor\n')
        return result
    with monkeypatch.context() as patch:
        patch.setattr(Session, 'can_resume', concurrent_edit)
        restarted = Session(config, paths)
    with pytest.raises(ValueError, match='editor'):
        with restarted.transaction():
            restarted.move('undo')
    assert 'concurrent editor' in paths[1].read_text()
    assert not Session(config, paths).info()['resume']


def test_checkpoint_replacement_failure_keeps_saved_source_and_previous_history(tmp_path, monkeypatch):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    change(session, lambda: paths[1].write_text(paths[1].read_text() + '# saved first\n'))
    checkpoint = session.file.read_bytes()
    replace = Path.replace
    def fail(path, target):
        if path.name.startswith('.history-'):
            raise OSError('simulated full disk')
        return replace(path, target)
    with monkeypatch.context() as patch:
        patch.setattr(Path, 'replace', fail)
        with pytest.raises(OSError, match='Project files are saved'):
            change(session, lambda: paths[1].write_text(paths[1].read_text() + '# saved second\n'))
    assert 'saved second' in paths[1].read_text() and session.file.read_bytes() == checkpoint
    assert session.info()['download'] and not session.info()['resume']
    assert session.pending and not list(session.file.parent.glob('.history-*'))
    restarted = Session(config, paths)
    assert not restarted.info()['resume']
    recover(restarted, 'fresh')
    assert 'saved second' in paths[1].read_text()


def test_history_remains_bounded_and_blob_storage_deduplicates(tmp_path):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    for i in range(55):
        change(session, lambda: paths[1].write_text(f'# synthetic revision {i}\n'))
    restarted = Session(config, paths)
    assert len(restarted.undo) == 50 and restarted.info() is None
    data = json.loads(restarted.file.read_text())
    assert len(data['blobs']) == 53  # 51 story versions, one config and one cut


def serve(folder):
    httpd, url, _ = studio.server(SimpleNamespace(project=str(folder), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, url


def stop(httpd):
    httpd.shutdown(); httpd.server_close()


def test_http_recovery_blocks_edits_jobs_and_decisions_until_resolved(tmp_path, monkeypatch):
    config, paths = files(tmp_path)
    session = Session(config, paths)
    change(session, lambda: paths[1].write_text(paths[1].read_text() + '# checkpoint\n'))
    paths[1].write_text(paths[1].read_text() + '# external change\n')
    expected = session.snapshot()
    launched = []
    monkeypatch.setattr(studio.Job, 'start', lambda *args, **kwargs: launched.append(args))
    httpd, url = serve(tmp_path)
    try:
        import re
        html = urllib.request.urlopen(url).read().decode()
        revision = unescape(re.search(r'data-revision="([^"]+)"', html)[1])
        def post(action, **body):
            request = urllib.request.Request(url + action, data=json.dumps({'revision': revision, **body}).encode(),
                                             headers={'Content-Type': 'application/json'})
            return json.load(urllib.request.urlopen(request))
        for action in ('edit', 'cut', 'undo', 'redo', 'job', 'accept'):
            assert 'Choose how to resume' in post(action, beat='search', caption='must not save', kind='preview')['error']
        assert not launched and session.snapshot() == expected
        assert 'saved session changed' in post('session', choice='fresh', session_token='stale')['error']
        with pytest.raises(urllib.error.HTTPError, match='409'):
            urllib.request.urlopen(url + 'session.zip?token=stale')
        assert post('session', choice='fresh', session_token=session.token)['ok']
        assert post('edit', beat='search', caption='Recovered edit')['ok']
        assert 'Recovered edit' in paths[1].read_text()
    finally:
        stop(httpd)


@pytest.mark.browser
def test_studio_restarts_resume_redo_and_external_recovery_download(tmp_path):
    from playwright.sync_api import sync_playwright, expect
    from reshoot import web
    config, paths = files(tmp_path)
    httpd, url = serve(tmp_path)
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            original = paths[1].read_bytes()
            caption = page.locator('.beat[data-beat=search] input[name=caption]')
            caption.fill('Resume this caption'); caption.press('Tab')
            page.wait_for_function("!document.querySelector('[data-unsaved]')")
            assert b'Resume this caption' in paths[1].read_bytes()
            stop(httpd); httpd, url = serve(tmp_path)
            page.goto(url)
            expect(page.locator('#session-recovery')).to_have_count(0)
            expect(caption).to_be_enabled()
            with page.expect_navigation():
                page.locator('[data-history=undo]').click()
            assert paths[1].read_bytes() == original
            stop(httpd); httpd, url = serve(tmp_path)
            page.goto(url)
            expect(page.locator('#session-recovery')).to_have_count(0)
            expect(page.locator('[data-history=redo]')).to_be_enabled()
            with page.expect_navigation():
                page.locator('[data-history=redo]').click()
            saved = paths[1].read_bytes()
            stop(httpd)
            paths[1].write_bytes(saved + b'# external editor\n')
            external = paths[1].read_bytes()
            httpd, url = serve(tmp_path)
            page.goto(url)
            expect(page.locator('[data-session=resume]')).to_have_count(0)
            with page.expect_download() as event:
                page.get_by_role('link', name='Download saved source copy').click()
            with zipfile.ZipFile(event.value.path()) as archive:
                assert archive.read('sources/2/storyboard.toml') == saved
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(tmp_path / 'recovery-mobile.png'))
            with page.expect_navigation():
                page.locator('[data-session=fresh]').click()
            assert paths[1].read_bytes() == external
            expect(page.locator('[data-history=undo]')).to_be_disabled()
            assert not errors
            browser.close()
    finally:
        stop(httpd)
