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
