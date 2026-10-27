"""Actionable dependency checks and synthetic capture/scan probes for first-run setup."""
import hashlib
import importlib.util
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def action(name, system):
    if name == 'playwright':
        return "For a uv tool install: uv tool install --upgrade 'reshoot[browser]'. For a source checkout: uv sync --extra browser. Restart reshoot afterwards."
    if name == 'chrome' and os.environ.get('RESHOOT_CHROME'):
        return 'Correct RESHOOT_CHROME to an executable browser, or run unset RESHOOT_CHROME and restart reshoot to use automatic discovery.'
    if system == 'Darwin':
        return {'ffmpeg': 'With Homebrew: brew install ffmpeg', 'ffprobe': 'With Homebrew: brew install ffmpeg',
                'chrome': 'Use installed Chrome/Chromium, or with Homebrew: brew install --cask google-chrome',
                'vhs': 'With Homebrew: brew install vhs', 'python3': 'With Homebrew: brew install python',
                'text': "If Vision failed inside an agent's sandbox, such as Codex's, run reshoot outside it. Otherwise repair "
                        'the configured OCR backend. For Tesseract with Homebrew: brew install tesseract'}.get(name, 'Check the tool installation and PATH, then check again.')
    return {'ffmpeg': 'On Debian: sudo apt-get install -y ffmpeg', 'ffprobe': 'On Debian: sudo apt-get install -y ffmpeg',
            'chrome': 'Use installed Chrome/Chromium, or on Debian: sudo apt-get install -y chromium',
            'python3': 'On Debian: sudo apt-get install -y python3',
            'text': 'For Tesseract on Debian: sudo apt-get install -y tesseract-ocr',
            'vhs': 'Install VHS using https://github.com/charmbracelet/vhs#installation'}.get(name, 'Check the tool installation and PATH, then check again.')


def inspect(config=None, probe=False, versions=True):
    from reshoot import scan, web
    from reshoot.config import read
    shoot = read(config)[0] if config else {'take': [{'web': 'storyboard.toml'}], 'check': {'scan': True}}
    system = platform.system()
    tools, checks = {}, []
    def row(name, label, installed, detail=''):
        checks.append({'id': name, 'label': label, 'status': 'installed' if installed else 'missing',
                       'required': True, 'detail': detail, 'action': action(name, system)})
    names = ['ffmpeg', 'ffprobe']
    if any('tape' in take for take in shoot.get('take', [])):
        names.append('vhs')
    if shlex.split(shoot.get('app', {}).get('run', '') or '')[:1] == ['python3']:
        names.append('python3')
    for name in names:
        tools[name] = shutil.which(name)
        row(name, name, tools[name])
    browser = any('web' in take for take in shoot.get('take', []))
    declarative = any(str(take.get('web', '')).endswith('.toml') for take in shoot.get('take', []))
    if browser:
        try:
            tools['chrome'] = shutil.which(web.find_chrome())
        except SystemExit:
            tools['chrome'] = None
        row('chrome', 'Chrome or Chromium', tools['chrome'])
    if declarative:
        importlib.invalidate_caches()
        tools['playwright'] = 'installed' if importlib.util.find_spec('playwright') else None
        row('playwright', 'Browser recording support', tools['playwright'])
    required_text = 'check' in shoot and shoot['check'].get('scan', True)
    engine = shoot.get('check', {}).get('ocr')
    engine_error, reader = '', None
    try:
        backend, detectors = scan.backend(engine), sorted(scan.can_scan(engine))
        if required_text and backend == 'vision' and 'text' in detectors:
            try:
                reader = scan.vision_level()
            except RuntimeError as error:
                engine_error = str(error)
                detectors = [name for name in detectors if name != 'text']
    except (ValueError, ImportError) as error:
        backend, detectors, engine_error = 'unavailable', [], str(error)
    if required_text:
        row('text', 'Text scan', 'text' in detectors, engine_error or f'Configured OCR: {backend}')
    from reshoot.cut import FONTS
    from importlib.metadata import version
    report = {'schema_version': 1, 'platform': system, 'tools': tools, 'checks': checks, 'versions': {},
              'ocr_backend': backend, 'scan_probe': reader or ('failed: ' + engine_error if engine_error else 'not run'),
              'text_reader': reader, 'detectors': detectors,
              'window_capture': system == 'Darwin', 'fonts': [Path(f).name for f in FONTS if Path(f).exists()],
              'reshoot': {'version': version('reshoot'), 'latest': None}, 'probed': probe}
    if versions:
        for name, path in tools.items():
            if not path or name == 'playwright':
                continue
            flag = '-version' if name in ('ffmpeg', 'ffprobe') else '-v' if name == 'vhs' else '--version'
            try:
                result = subprocess.run([path, flag], capture_output=True, text=True, timeout=5)
                output = (result.stdout or result.stderr).splitlines()
                if result.returncode or not output:
                    raise RuntimeError('The version command failed.')
                report['versions'][name] = output[0][:300]
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                report['versions'][name] = 'unknown'
                item = next(item for item in checks if item['id'] == name)
                item.update(status='failed', detail='The executable was found, but its version command failed. Check its installation and runtime libraries.')
    if probe:
        def attempt(name, label, operation, fix):
            item = {'id': name, 'label': label, 'required': True, 'action': fix}
            try:
                operation()
                item.update(status='passed', detail='Synthetic check passed.')
            except Exception as error:
                from reshoot.safety import redact
                item.update(status='failed', detail=redact(str(error))[:1200])
            checks.append(item)
        if tools.get('ffmpeg') and tools.get('ffprobe'):
            attempt('video', 'Video encoding and inspection', video_probe, action('ffmpeg', system))
        if declarative and tools.get('chrome') and tools.get('playwright'):
            attempt('browser', 'Headless browser capture', browser_probe,
                    'Check Chrome permissions, shared libraries and RESHOOT_CHROME/RESHOOT_CHROME_FLAGS. Restart reshoot after shell changes.')
        if required_text and 'text' in detectors:
            attempt('ocr', 'Text recognition', lambda: text_probe(engine), action('text', system))
            report['scan_probe'] = 'passed' if checks[-1]['status'] == 'passed' else 'failed'
            if backend == 'vision':
                report['text_reader'] = scan.vision_level()
    report['ok'] = all(item['status'] not in ('missing', 'failed') for item in checks if item['required'])
    return report


def video_probe():
    with tempfile.TemporaryDirectory(prefix='reshoot-setup-') as folder:
        video = str(Path(folder) / 'synthetic.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=64x64:r=10:d=0.2',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', video], check=True, capture_output=True, timeout=15)
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'json', video],
                                check=True, capture_output=True, timeout=10)
        if json.loads(result.stdout)['streams'][0] != {'width': 64, 'height': 64}:
            raise RuntimeError('The synthetic MP4 has unexpected dimensions.')


def browser_probe():
    from playwright.sync_api import sync_playwright
    from reshoot import web
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=web.find_chrome(), headless=True,
                                             args=web.chrome_flags(), timeout=10000)
        try:
            page = browser.new_page(viewport={'width': 320, 'height': 180})
            page.set_content('<title>reshoot setup</title><h1>Made-up notes</h1><button>Save a note</button>', timeout=5000)
            page.get_by_role('button', name='Save a note').click(timeout=5000)
            if not page.screenshot(timeout=5000).startswith(b'\x89PNG'):
                raise RuntimeError('The synthetic page did not produce a PNG.')
        finally:
            browser.close()


def text_probe(engine):
    from PIL import Image, ImageDraw, ImageFont
    from reshoot import scan
    image = Image.new('RGB', (800, 180), 'white')
    ImageDraw.Draw(image).text((30, 50), 'Reshoot setup check', font=ImageFont.load_default(size=40), fill='black')
    flags = scan.scan(image, watch=['Reshoot'], engine=engine)
    if not any('reshoot' in value.lower() for _, _, value in flags):
        raise RuntimeError('OCR ran but did not recognize the synthetic test word.')


def fingerprint(config, report):
    stats = {}
    for name, path in report['tools'].items():
        if not path or path == 'installed':
            stats[name] = path
            continue
        try:
            st = Path(path).stat()
            stats[name] = [path, st.st_size, st.st_mtime_ns, st.st_ctime_ns]
        except OSError:
            stats[name] = None
    values = {'config': Path(config).read_text(), 'tools': stats, 'python': sys.executable,
              'env': {name: os.environ.get(name) for name in ('PATH', 'RESHOOT_CHROME', 'RESHOOT_CHROME_FLAGS', 'RESHOOT_OCR')},
              'ocr': report['ocr_backend'], 'detectors': report['detectors'], 'text_reader': report.get('text_reader')}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def current(config):
    report = inspect(config, versions=False)
    cached = Path(config).parent / 'takes/setup.json'
    try:
        if cached.stat().st_size < 128 * 1024:
            previous = json.loads(cached.read_text())
            if (previous.get('schema_version') == 1 and isinstance(previous.get('checks'), list)
                    and all(isinstance(item, dict) and {'id', 'label', 'status', 'required', 'detail', 'action'} <= item.keys()
                            for item in previous['checks'])
                    and previous.get('fingerprint') == fingerprint(config, report)):
                return previous
    except (OSError, ValueError, TypeError):
        pass
    return report


def print_report(report, brief=False):
    if brief and report['ok']:  # a working setup needs one line; problems still list every check
        print(f'Recording tools: ready ({len(report["checks"])} checks passed).' +
              (" Vision's accurate text reader failed on this Mac, so the scan uses its fast one." if report.get('text_reader') == 'fast' else ''), flush=True)
        return
    print('Recording tools: ' + ('ready' if report['ok'] else 'need attention'), flush=True)
    for item in report['checks']:
        print(f'  {item["label"]}: {item["status"]}' + (f' · {item["detail"]}' if item['detail'] else ''), flush=True)
    fixes = dict.fromkeys(item['action'] for item in report['checks'] if item['status'] in ('missing', 'failed'))
    for fix in fixes:
        print('  Fix: ' + fix, flush=True)
    if report.get('text_reader'):
        print('Vision text reader: ' + report['text_reader'] +
              ('; the accurate reader failed on this Mac.' if report['text_reader'] == 'fast' else '.'), flush=True)


def check_project(config, brief=False):
    report = inspect(config, probe=True)
    report.update(fingerprint=fingerprint(config, report), checked_at=datetime.now(timezone.utc).isoformat())
    target = Path(config).parent / 'takes/setup.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, prefix='.setup-', delete=False) as out:
            temp = Path(out.name)
            json.dump(report, out)
        temp.replace(target)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    print_report(report, brief)
    return report


if __name__ == '__main__':
    raise SystemExit(0 if check_project(Path(sys.argv[1]).resolve())['ok'] else 2)
