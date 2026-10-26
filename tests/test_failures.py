"""Regression cases use generated files and a local synthetic server only."""
import asyncio
import json
from pathlib import Path

import pytest
from PIL import Image
from reshoot import check, scan, web
from reshoot.cli import main as cli
from reshoot.safety import describe, redact


def invoke(*args):
    with pytest.raises(SystemExit) as result:
        cli(list(args))
    return result.value.code


@pytest.mark.parametrize('kind', ['missing.png', 'bad.png', 'missing.json'])
def test_unreadable_source_is_error_not_reviewed(tmp_path, kind):
    source = tmp_path / kind
    if kind == 'bad.png':
        source.write_text('not an image')
    review = tmp_path / 'review'
    assert invoke('check', str(source), '--no-scan', '--review', str(review)) == 2
    report = json.loads((review / 'report.json').read_text())
    assert report['status'] == 'error' and report['unchecked'] is None
    assert report['review'] == 'pending'


def test_no_inputs_and_invalid_interval_are_errors(tmp_path):
    review = str(tmp_path / 'review')
    assert invoke('check', '--no-scan', '--review', review) == 2
    assert invoke('check', 'missing', '--every', '0', '--no-scan', '--review', review) == 2


def test_missing_detector_is_not_a_clean_scan(tmp_path, monkeypatch):
    image = tmp_path / 'demo.png'
    Image.new('RGB', (20, 20), 'red').save(image)
    monkeypatch.setattr(scan, 'can_scan', lambda: set())
    assert invoke('check', str(image), '--review', str(tmp_path / 'review')) == 2


def test_sources_and_errors_do_not_print_fake_credentials():
    fake = 'https://demo:password@localhost/private/user@example.com?token=abc123'
    assert 'password' not in describe(fake) and 'abc123' not in redact(fake)
    assert 'abc123' not in redact('token=abc123')
    assert 'sk-fake123456789' not in redact('key sk-fake123456789')


def test_email_prefix_does_not_exempt_real_domains():
    assert ('email', 'user@realcompany.com') in scan.reasons('user@realcompany.com')
    assert scan.reasons('demo@example.com') == []


def test_run_does_not_reuse_a_previous_check_report(tmp_path):
    review = tmp_path / 'review'
    review.mkdir()
    (review / 'report.json').write_text(json.dumps({'status': 'completed', 'unchecked': 0}))
    config = tmp_path / 'reshoot.toml'
    config.write_text(f'report="{tmp_path}/run.json"\n[check]\nsources=["{tmp_path}/missing.json"]\nreview="{review}"\nscan=false\n')
    assert 'failed' in invoke('run', str(config))
    report = json.loads((tmp_path / 'run.json').read_text())
    assert report['ok'] is False and report['unchecked'] is None


@pytest.mark.parametrize('failure', ['action', 'assertion', 'missing-metadata', None])
def test_run_expectations_cannot_pass_from_only_an_earlier_result(tmp_path, monkeypatch, failure):
    from reshoot import run
    board = tmp_path / 'story.toml'
    board.write_text('schema_version=1\nurl="http://localhost/"\n[[beat]]\nid="result"\n')
    config = tmp_path / 'reshoot.toml'
    config.write_text('schema_version=1\n[[take]]\nweb="story.toml"\nout="takes/first.mp4"\n'
                      '[[take]]\nweb="story.toml"\nout="takes/second.mp4"\n')

    def execute(cmd, *args):
        out = Path(cmd[5])
        second = out.stem == 'second'
        if not (second and failure == 'missing-metadata'):
            out.parent.mkdir(exist_ok=True)
            status = 'failed' if second and failure else 'completed'
            assertions = [{'status': 'failed' if second and failure == 'assertion' else 'passed'}]
            if second and failure == 'action':
                assertions = []
            out.with_suffix('.take.json').write_text(json.dumps({'status': status, 'beats': [
                {'status': 'failed' if second and failure else 'passed', 'expectations': assertions}]}))
        return 2 if second and failure else 0

    monkeypatch.setattr(run, 'execute', execute)
    result = invoke('run', str(config))
    if failure:
        assert 'failed' in result
    else:
        assert result == 0
    report = json.loads(next((tmp_path / 'takes/runs').glob('*/run.json')).read_text())
    expected = 'failed' if failure == 'assertion' else 'unverified' if failure else 'passed'
    assert report['expectations_status'] == expected
    assert report['ok'] is (failure is None)
    assert report['expectations_count'] == (2 if failure in (None, 'assertion') else 1)


def test_url_checks_run_before_server_shutdown(tmp_path):
    from test_reshoot import free_port
    port = free_port()
    Image.new('RGB', (20, 20), 'red').save(tmp_path / 'demo.png')
    config = tmp_path / 'reshoot.toml'
    config.write_text(f'''report="{tmp_path}/run.json"
[app]
run="python3 -m http.server {port} --bind 127.0.0.1 --directory {tmp_path}"
url="http://127.0.0.1:{port}/"
[check]
sources=["http://127.0.0.1:{port}/demo.png"]
review="{tmp_path}/review"
scan=false
''')
    assert invoke('run', str(config)) == 0
    report = json.loads((tmp_path / 'run.json').read_text())
    assert report['ok'] and report['unchecked'] == 1 and report['review_status'] == 'pending'


def test_browser_disconnect_releases_waiters():
    class Connection:
        def __aiter__(self):
            return self
        async def __anext__(self):
            raise StopAsyncIteration
    async def exercise():
        page = web.Page(Connection(), [])
        pending = asyncio.get_running_loop().create_future()
        page.waiting[1] = pending
        await page.read()
        with pytest.raises(RuntimeError, match='closed'):
            await pending
    asyncio.run(exercise())


def test_explicit_ocr_backend_does_not_silently_fall_back(monkeypatch):
    monkeypatch.setenv('RESHOOT_OCR', 'tesseract')
    assert scan.backend() == 'tesseract'
    assert scan.backend('vision') == 'vision'
    monkeypatch.setattr(scan, '_vision', lambda *a: (_ for _ in ()).throw(RuntimeError('detector failed')))
    with pytest.raises(RuntimeError, match='detector failed'):
        scan.scan(Image.new('RGB', (20,20)), engine='vision')


def test_vision_reads_text_with_its_fast_reader_where_the_accurate_one_fails(monkeypatch):
    monkeypatch.setattr(scan, '_level', {})
    tried = []

    def text(im, level):
        tried.append(level)
        if level == 'accurate':
            raise RuntimeError('Vision failed (TextRecognition.CRImageReaderError 1)')
        return []
    monkeypatch.setattr(scan, '_text', text)
    assert scan.vision_level() == 'fast'
    assert scan.vision_level() == 'fast' and tried == ['accurate', 'fast']  # found once


def test_vision_fails_when_neither_text_reader_works(monkeypatch):
    monkeypatch.setattr(scan, '_level', {})
    monkeypatch.setattr(scan, '_text', lambda im, level: (_ for _ in ()).throw(RuntimeError(f'{level} failed')))
    with pytest.raises(RuntimeError, match='fast failed'):
        scan.vision_level()


def test_a_vision_failure_names_an_agent_sandbox_as_the_usual_cause(monkeypatch):
    monkeypatch.setattr(scan, '_level', {})
    monkeypatch.setattr(scan, '_text', lambda im, level: (_ for _ in ()).throw(RuntimeError('Vision failed (com.apple.Vision 8)')))
    with pytest.raises(RuntimeError, match="com.apple.Vision 8.*agent's sandbox"):
        scan.vision_level()


def test_a_stalled_chrome_call_fails_quickly_and_says_what_it_was(monkeypatch):
    from reshoot import browser
    async def stalls():
        await asyncio.sleep(10)
    with pytest.raises(RuntimeError, match='Chrome did not respond to showing the caption within 0.05 s'):
        asyncio.run(browser.bounded(stalls(), 'showing the caption', 0.05))
