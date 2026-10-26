"""Read-only, exact-run studio comparisons with synthetic evidence and notes."""
import hashlib
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from reshoot import comparison, project, review, studio
from reshoot.artifacts import digest


def recording(project, number, beats=('result',), colour='blue', accepted=False, mode='preview'):
    root = project / 'takes/runs' / (f'{number:032x}')
    evidence = root / 'takes/demo.evidence'
    evidence.mkdir(parents=True)
    rows = []
    for name in beats:
        Image.new('RGB', (160, 100), colour).save(evidence / (name + '.png'))
        rows.append({'id': name, 'purpose': 'Synthetic result ' + name, 'status': 'passed', 'start': 0, 'end': 2,
                     'screenshot': f'demo.evidence/{name}.png', 'definition_sha256': hashlib.sha256(name.encode()).hexdigest(),
                     'expectations': [{'type': 'text', 'status': 'passed', 'actual': 'A saved note', 'at': 1}]})
    (root / 'takes/demo.take.json').write_text(json.dumps({'status': 'completed', 'mode': 'preview',
                                                         'story_id': 'notes', 'video': 'demo.mp4', 'beats': rows}))
    (root / 'takes/demo.mp4').write_bytes(b'synthetic video placeholder')
    (root / 'review.html').write_text('<h1>Review evidence</h1><img src="takes/demo.evidence/result.png">')
    report = {'id': root.name, 'ok': True, 'mode': mode, 'review_status': 'completed' if accepted else 'pending',
              'finished_at': f'2026-10-25T12:{number:02}:00+00:00', 'expectations_status': 'passed', 'expectations_count': len(rows),
              'files': [{'path': str(path.relative_to(root)), 'sha256': digest(path)} for path in sorted(root.rglob('*'))
                        if path.is_file() and path.name != 'review.html']}
    (root / 'run.json').write_text(json.dumps(report))
    return root, report


def rebind(run):
    root, report = run
    for item in report['files']:
        item['sha256'] = digest(root / item['path'])
    (root / 'run.json').write_text(json.dumps(report))


def model(folder, old, new):
    return comparison.model(folder, new[1]['id'], review.binding(*new), old[1]['id'], review.binding(*old))


def test_default_prefers_an_earlier_accepted_run_and_excludes_partial_or_future_runs(tmp_path):
    old = recording(tmp_path, 1, accepted=True)
    recent = recording(tmp_path, 2)
    recording(tmp_path, 3, mode='partial-preview')
    current = recording(tmp_path, 4)
    recording(tmp_path, 5)
    choices = comparison.choices(tmp_path, current)
    assert choices['default'] == old[1]['id']
    assert [row['id'] for row in choices['choices']] == [recent[1]['id'], old[1]['id']]


def test_comparison_matches_ids_and_exposes_added_removed_and_changed_frames_without_writing(tmp_path):
    old = recording(tmp_path, 1, ('removed', 'result'))
    new = recording(tmp_path, 2, ('result', 'added'), colour='orange')
    before = {path: path.read_bytes() for path in tmp_path.rglob('*') if path.is_file()}
    result = model(tmp_path, old, new)
    assert [(row['beat'], row['change']) for row in result['beats']] == [
        ('notes/removed', 'removed'), ('notes/result', 'matched'), ('notes/added', 'added')]
    row = result['beats'][1]
    assert row['frame_changed'] and not row['definition_changed'] and not row['results_changed']
    for side, run in [('previous', old), ('current', new)]:
        frame = row[side]['frame']
        raw = comparison.frame(tmp_path, run[1]['id'], review.binding(*run), frame['sha256'])
        assert hashlib.sha256(raw).hexdigest() == frame['sha256']
        assert run[1]['id'] in frame['src'] and review.binding(*run) in frame['src']
    assert {path: path.read_bytes() for path in tmp_path.rglob('*') if path.is_file()} == before


@pytest.mark.parametrize('kind', ['unchecked', 'outside', 'unbound', 'partial'])
def test_only_bound_complete_checked_frames_can_be_shown(tmp_path, kind):
    old, new = recording(tmp_path, 1), recording(tmp_path, 2)
    path = new[0] / 'takes/demo.take.json'
    data = json.loads(path.read_text())
    if kind == 'unchecked':
        data['beats'][0]['status'] = 'unverified'
    elif kind == 'outside':
        data['beats'][0]['screenshot'] = '../../../outside.png'
        Image.new('RGB', (10, 10)).save(tmp_path / 'outside.png')
    elif kind == 'unbound':
        new[1]['files'] = [item for item in new[1]['files'] if not item['path'].endswith('.png')]
    else:
        data['mode'] = 'partial'
    path.write_text(json.dumps(data)); rebind(new)
    result = model(tmp_path, old, new)
    assert result['beats'][0]['current']['frame'] is None
    sha = digest(new[0] / 'takes/demo.evidence/result.png')
    with pytest.raises(ValueError, match='No checked frame'):
        comparison.frame(tmp_path, new[1]['id'], review.binding(*new), sha)


def test_tampered_artifacts_and_scan_bindings_invalidate_cached_comparisons(tmp_path):
    old, new = recording(tmp_path, 1), recording(tmp_path, 2)
    result = model(tmp_path, old, new)
    token = review.binding(*old)
    frame = result['beats'][0]['previous']['frame']
    (old[0] / frame['path']).write_bytes(b'tampered')
    with pytest.raises(ValueError, match='changed'):
        comparison.frame(tmp_path, old[1]['id'], token, frame['sha256'])
    root, _ = new
    (root / 'review').mkdir()
    (root / 'review/report.json').write_text('{"policy":"changed scan"}')
    with pytest.raises(ValueError, match='scan changed'):
        comparison.read(tmp_path, new[1]['id'], result['current']['binding'])


def test_duplicate_stable_ids_are_not_arbitrarily_paired(tmp_path):
    old, new = recording(tmp_path, 1), recording(tmp_path, 2)
    original = new[0] / 'takes/demo.take.json'
    duplicate = new[0] / 'takes/duplicate.take.json'
    duplicate.write_bytes(original.read_bytes())
    new[1]['files'].append({'path': 'takes/duplicate.take.json', 'sha256': digest(duplicate)})
    rebind(new)
    with pytest.raises(ValueError, match='share a story/beat ID'):
        model(tmp_path, old, new)


def test_http_comparison_and_review_assets_remain_bound_to_the_displayed_pair(tmp_path, monkeypatch):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    old, current = recording(tmp_path, 1), recording(tmp_path, 2)
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        query = urllib.parse.urlencode({'run_id': current[1]['id'], 'binding': review.binding(*current),
                                       'previous_id': old[1]['id'], 'previous_binding': review.binding(*old)})
        result = json.load(urllib.request.urlopen(url + 'comparison.json?' + query))
        recording(tmp_path, 3)
        same = json.load(urllib.request.urlopen(url + 'comparison.json?' + query))
        assert same == result and same['current']['id'] == current[1]['id']
        frame = result['beats'][0]['previous']['frame']
        with urllib.request.urlopen(url + frame['src']) as response:
            assert hashlib.sha256(response.read()).hexdigest() == frame['sha256']
        review_url = url + result['previous']['review']
        assert b'Review evidence' in urllib.request.urlopen(review_url).read()
        assert urllib.request.urlopen(review_url.replace('review.html', frame['path'])).read() == (old[0] / frame['path']).read_bytes()
        with pytest.raises(urllib.error.HTTPError, match='409'):
            urllib.request.urlopen(url + 'comparison.json?' + query.replace(review.binding(*old), '0' * 64))
        assert (old[0] / 'run.json').read_text() and current[1]['review_status'] == 'pending'
        verified_read = comparison.read
        def change_after_verification(*args):
            run = verified_read(*args)
            (run[0] / 'takes/demo.mp4').write_bytes(b'changed during request')
            return run
        monkeypatch.setattr(comparison, 'read', change_after_verification)
        with pytest.raises(urllib.error.HTTPError, match='409'):
            urllib.request.urlopen(review_url.replace('review.html', 'takes/demo.mp4'))
    finally:
        httpd.shutdown(); httpd.server_close()


@pytest.mark.browser
def test_studio_compares_two_captures_with_mobile_layout_and_pinned_current_run(tmp_path):
    from playwright.sync_api import sync_playwright, expect
    from reshoot import web
    from reshoot.cli import main
    import shutil
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    config = tmp_path / 'reshoot.toml'
    config.write_text(config.read_text().replace('scan = true', 'scan = false'))
    def preview():
        with pytest.raises(SystemExit) as result:
            main(['preview', str(config)])
        assert result.value.code == 0
        return review.read(tmp_path / 'latest')
    old = preview()
    page_source = tmp_path / 'index.html'
    page_source.write_text(page_source.read_text().replace('#0e0d0c', '#123852'))
    current = preview()
    source_hashes = {path: digest(path) for path in (config, tmp_path / 'storyboard.toml', tmp_path / 'edit.toml')}
    old_report, new_report = (old[0] / 'run.json').read_bytes(), (current[0] / 'run.json').read_bytes()
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.locator('.more-tools > summary').click()
            page.locator('.section-nav [data-jump=compare-panel]').click()
            expect(page.locator('#comparison-status')).to_have_text('Compared 2 result-check steps.')
            expect(page.locator('.compare-pair img')).to_have_count(4)
            assert page.locator('#comparison-source').input_value() == old[1]['id']
            assert all(old[1]['id'] in src or current[1]['id'] in src for src in page.locator('.compare-pair img').evaluate_all('els => els.map(el => el.src)'))
            # A new successful run must not change the two revisions on this page.
            later = tmp_path / 'takes/runs' / ('f' * 32)
            shutil.copytree(current[0], later)
            data = json.loads((later / 'run.json').read_text())
            data.update(id=later.name, finished_at='2099-01-01T00:00:00+00:00')
            (later / 'run.json').write_text(json.dumps(data))
            page.locator('#compare-refresh').click()
            expect(page.locator('#comparison-results')).to_have_attribute('aria-busy', 'false')
            assert page.locator('body').get_attribute('data-run') == current[1]['id']
            assert later.name not in page.locator('#comparison-results').inner_text()
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator('.section-nav [data-jump=compare-panel]').click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(tmp_path / 'comparison-mobile.png'))
            assert not errors
            browser.close()
    finally:
        httpd.shutdown(); httpd.server_close()
    assert all(digest(path) == sha for path, sha in source_hashes.items())
    assert (old[0] / 'run.json').read_bytes() == old_report and (current[0] / 'run.json').read_bytes() == new_report
