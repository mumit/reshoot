"""First-run recovery uses synthetic data and never installs tools or overwrites a saved story."""
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import create, project, rec, setup, studio, web


def args(folder, **changes):
    return SimpleNamespace(**({'url': None, 'directory': str(folder), 'size': None, 'resume': False,
                               'no_studio': True, 'no_open': True} | changes))


def test_missing_tools_keep_the_project_and_resume_without_reinitializing(tmp_path, monkeypatch, capsys):
    checks, previews = [], []
    monkeypatch.setattr(setup, 'check_project', lambda path: (checks.append(path) or {'ok': len(checks) > 1}))
    monkeypatch.setattr('reshoot.run.preview', lambda a: previews.append(a.config))
    assert create.main(args(tmp_path)) == 2
    original = (tmp_path / 'storyboard.toml').read_bytes()
    assert 'reshoot create --resume --directory' in capsys.readouterr().out
    # Upstream now reopens existing projects; a saved preview can finish there.
    assert create.main(args(tmp_path)) == 0
    assert create.main(args(tmp_path, resume=True)) == 0
    assert (tmp_path / 'storyboard.toml').read_bytes() == original and len(previews) == 1
    assert create.load(tmp_path)['stage'] == 'done'
    monkeypatch.setattr(setup, 'check_project', lambda path: pytest.fail('completed creation needs no new probe'))
    assert create.main(args(tmp_path, resume=True)) == 0 and len(previews) == 1


def test_missing_tools_open_the_setup_studio_without_starting_the_app(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, 'check_project', lambda path: {'ok': False})
    monkeypatch.setattr(rec, 'main', lambda a: pytest.fail('no recorder before tools pass'))
    monkeypatch.setattr('reshoot.run.preview', lambda a: pytest.fail('no app before tools pass'))
    opened = []
    monkeypatch.setattr(studio, 'serve', lambda a: (opened.append(a.project) or 0))
    assert create.main(args(tmp_path, url='http://localhost:3000/', no_studio=False)) == 0
    assert opened == [str(tmp_path)] and create.load(tmp_path)['stage'] == 'record'


def test_resuming_a_saved_task_after_preview_failure_does_not_record_it_again(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, 'check_project', lambda path: {'ok': True})
    recorded, previews = [], []
    def record(a):
        recorded.append(a)
        Path(a.out).write_text('schema_version=1\nurl="http://localhost:3000/"\n[[beat]]\nid="result"\nhold=1\n')
    def preview(a):
        previews.append(a)
        if len(previews) == 1:
            raise ValueError('synthetic preview failure')
    monkeypatch.setattr(rec, 'main', record)
    monkeypatch.setattr('reshoot.run.preview', preview)
    assert create.main(args(tmp_path, url='http://localhost:3000/')) == 2
    saved = (tmp_path / 'storyboard.toml').read_bytes()
    assert create.load(tmp_path)['stage'] == 'preview'
    assert create.main(args(tmp_path, resume=True)) == 0
    assert (tmp_path / 'storyboard.toml').read_bytes() == saved
    assert len(recorded) == 1 and len(previews) == 2


@pytest.mark.parametrize('change', ['draft', 'url', 'size'])
def test_paused_demonstration_refuses_changed_inputs(tmp_path, monkeypatch, change):
    monkeypatch.setattr(setup, 'check_project', lambda path: {'ok': False})
    create.main(args(tmp_path, url='http://localhost:3000/'))
    values = {'resume': True}
    if change == 'draft':
        path = tmp_path / 'storyboard.toml'
        path.write_text(path.read_text() + '# edited outside\n')
    elif change == 'url':
        values['url'] = 'http://localhost:4000/'
    else:
        values['size'] = '640x360@1'
    monkeypatch.setattr(rec, 'main', lambda a: pytest.fail('must preserve the paused draft'))
    with pytest.raises(ValueError, match='changed|differs'):
        create.main(args(tmp_path, **values))


def test_external_edit_during_demonstration_retains_both_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, 'check_project', lambda path: {'ok': True})
    def record(a):
        board = tmp_path / 'storyboard.toml'
        board.write_text(board.read_text() + '# external during demonstration\n')
        Path(a.out).write_text('schema_version=1\nurl="http://localhost:3000/"\n[[beat]]\nid="recorded"\nhold=1\n')
    monkeypatch.setattr(rec, 'main', record)
    with pytest.raises(ValueError, match='External edits were kept'):
        create.main(args(tmp_path, url='http://localhost:3000/'))
    assert 'external during demonstration' in (tmp_path / 'storyboard.toml').read_text()
    assert 'id="recorded"' in next(tmp_path.glob('recorded-*.toml')).read_text()
    assert create.load(tmp_path)['stage'] == 'record'


def test_scan_disabled_does_not_require_or_probe_ocr(tmp_path, monkeypatch):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    config = tmp_path / 'reshoot.toml'
    config.write_text(config.read_text().replace('scan = true', 'scan = false'))
    monkeypatch.setattr(setup, 'text_probe', lambda engine: pytest.fail('scan choice must remain unchanged'))
    monkeypatch.setattr(setup, 'video_probe', lambda: None)
    monkeypatch.setattr(setup, 'browser_probe', lambda: None)
    report = setup.inspect(config, probe=True, versions=False)
    assert not any(row['id'] in ('text', 'ocr') for row in report['checks'])
    assert report['scan_probe'] == 'not run'


def test_probe_failure_blocks_readiness_and_does_not_switch_ocr(tmp_path, monkeypatch):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    config = tmp_path / 'reshoot.toml'
    monkeypatch.setattr(setup, 'video_probe', lambda: None)
    monkeypatch.setattr(setup, 'browser_probe', lambda: None)
    engines = []
    def fail(engine):
        engines.append(engine)
        raise RuntimeError('synthetic OCR failure')
    monkeypatch.setattr(setup, 'text_probe', fail)
    from reshoot import scan
    monkeypatch.setattr(scan, 'can_scan', lambda engine: {'text'})
    report = setup.inspect(config, probe=True, versions=False)
    assert not report['ok'] and report['scan_probe'] == 'failed'
    assert engines == [None] and 'scan = true' in config.read_text()


def test_diagnostics_name_the_bad_override_and_platform_fixes(tmp_path, monkeypatch):
    monkeypatch.setenv('RESHOOT_CHROME', str(tmp_path / 'missing-browser'))
    report = setup.inspect(versions=False)
    assert not report['ok']
    chrome = next(row for row in report['checks'] if row['id'] == 'chrome')
    assert chrome['status'] == 'missing' and 'unset RESHOOT_CHROME' in chrome['action']
    assert setup.action('ffmpeg', 'Darwin') == 'With Homebrew: brew install ffmpeg'
    assert 'apt-get' in setup.action('text', 'Linux')


def test_cached_probe_is_invalidated_by_config_or_environment_changes(tmp_path, monkeypatch):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    config = tmp_path / 'reshoot.toml'
    monkeypatch.setattr(setup, 'video_probe', lambda: None)
    monkeypatch.setattr(setup, 'browser_probe', lambda: None)
    monkeypatch.setattr(setup, 'text_probe', lambda engine: None)
    setup.check_project(config)
    assert setup.current(config)['probed']
    config.write_text(config.read_text() + '# new config revision\n')
    assert not setup.current(config)['probed']
    setup.check_project(config)
    monkeypatch.setenv('RESHOOT_CHROME_FLAGS', '--disable-gpu')
    assert not setup.current(config)['probed']
    (tmp_path / 'takes/setup.json').write_text('{truncated')
    assert not setup.current(config)['probed']


@pytest.mark.parametrize('works', [True, False])
def test_merged_doctor_reports_the_vision_reader_or_its_failure(monkeypatch, works, capsys):
    from reshoot import scan
    monkeypatch.setattr(scan, 'backend', lambda engine: 'vision')
    monkeypatch.setattr(scan, 'can_scan', lambda engine: {'text', 'people'})
    def reader():
        if not works:
            raise RuntimeError('neither Vision reader works')
        return 'fast'
    monkeypatch.setattr(scan, 'vision_level', reader)
    report = setup.inspect(versions=False)
    assert report['text_reader'] == ('fast' if works else None)
    assert report['scan_probe'] == ('fast' if works else 'failed: neither Vision reader works')
    text = next(row for row in report['checks'] if row['id'] == 'text')
    assert text['status'] == ('installed' if works else 'missing')
    assert 'people' in report['detectors']
    setup.print_report(report)
    assert ('fast' if works else 'neither Vision reader works') in capsys.readouterr().out


@pytest.mark.browser
def test_setup_panel_rechecks_and_continues_the_saved_notes_creation(tmp_path, monkeypatch):
    from playwright.sync_api import sync_playwright, expect
    from reshoot import review
    chrome = web.find_chrome()
    monkeypatch.setenv('RESHOOT_CHROME', str(tmp_path / 'missing-browser'))
    assert create.main(args(tmp_path)) == 2
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=chrome, headless=True)
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            expect(page.locator('#setup-panel')).to_contain_text('unset RESHOOT_CHROME')
            expect(page.get_by_role('button', name='Continue creation')).to_be_disabled()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(tmp_path / 'setup-missing-mobile.png'))
            with page.expect_navigation(timeout=60000):
                page.get_by_role('button', name='Check again', exact=True).click()
            expect(page.get_by_role('button', name='Continue creation')).to_be_disabled()
            monkeypatch.delenv('RESHOOT_CHROME')
            with page.expect_navigation(timeout=60000):
                page.get_by_role('button', name='Check again', exact=True).click()
            expect(page.get_by_role('button', name='Continue creation')).to_be_enabled()
            with page.expect_navigation(timeout=120000):
                page.get_by_role('button', name='Continue creation').click()
            expect(page.locator('#setup-panel')).to_have_count(0)
            assert create.load(tmp_path)['stage'] == 'done'
            root, report = review.read(tmp_path / 'latest')
            assert report['ok'] and report['mode'] == 'preview' and report['expectations_count'] == 3
            assert report['review_status'] == 'pending' and not errors
            assert json.loads((tmp_path / 'takes/setup.json').read_text())['scan_probe'] == 'passed'
            browser.close()
    finally:
        httpd.reshoot_job.cancel()
        httpd.shutdown(); httpd.server_close()
