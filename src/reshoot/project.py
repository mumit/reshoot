"""Project setup and dependency checks using packaged demo data."""
import json
import os
import platform
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path
from reshoot import config, scan, web


def doctor(a):
    shoot = config.read(a.config)[0] if a.config else {'take': [{'web': ''}]}
    names = ['ffmpeg', 'ffprobe']
    if any('tape' in t for t in shoot.get('take', [])):
        names.append('vhs')
    found = {name: shutil.which(name) for name in names}
    if any('web' in t for t in shoot.get('take', [])):
        try:
            found['chrome'] = shutil.which(web.find_chrome())
        except SystemExit:
            found['chrome'] = None
    required_text = 'check' in shoot and shoot['check'].get('scan', True)
    engine = shoot.get('check', {}).get('ocr')
    detectors = sorted(scan.can_scan(engine))
    if any(str(t.get('web', '')).endswith('.toml') for t in shoot.get('take', [])):
        import importlib.util
        found['playwright'] = 'installed' if importlib.util.find_spec('playwright') else None
    result = {'ok': all(found.values()) and (not required_text or 'text' in detectors),
              'platform': platform.system(), 'ocr_backend': scan.backend(engine), 'scan_probe': 'not run', 'tools': found, 'detectors': detectors,
              'window_capture': platform.system() == 'Darwin', 'versions': {}}
    from importlib.metadata import version
    result['reshoot'] = {'version': version('reshoot'), 'latest': latest_release()}
    from reshoot.cut import FONTS
    result['fonts'] = [Path(f).name for f in FONTS if Path(f).exists()]
    for name, path in found.items():
        if path and name != 'playwright':
            try:
                result['versions'][name] = subprocess.run([path, '-version' if name in ('ffmpeg', 'ffprobe') else '--version' if name != 'vhs' else '-v'], capture_output=True, text=True, timeout=5).stdout.splitlines()[0]
            except (OSError, IndexError, subprocess.TimeoutExpired):
                result['versions'][name] = 'unknown'
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        installed, latest = result['reshoot']['version'], result['reshoot']['latest']
        newer = latest and release(latest) > release(installed)
        print(f'reshoot: {installed}' + (f"; {latest} is out: uv tool install --upgrade 'reshoot[browser]'" if newer else ''))
        for name, path in found.items():
            print(f'{name}: ' + ('available' if path else 'missing; install reshoot[browser]' if name == 'playwright' else 'missing; install it before recording'))
        print('Text scan: ' + ('installed, not probed' if 'text' in detectors else 'install Tesseract or Vision'))
        print('Face scan: ' + ('installed, not probed' if 'people' in detectors else 'unavailable'))
    return 0 if result['ok'] else 2


def latest_release():
    """The newest reshoot on PyPI, or None when it can't be reached quickly. RESHOOT_OFFLINE=1 skips the check."""
    if os.environ.get('RESHOOT_OFFLINE'):
        return None
    import urllib.request
    try:
        with urllib.request.urlopen('https://pypi.org/pypi/reshoot/json', timeout=3) as response:
            return json.loads(response.read())['info']['version']
    except Exception:
        return None


def release(text):
    """A version such as 0.3.2 as a comparable tuple; anything unusual compares as oldest."""
    try:
        return tuple(int(part) for part in text.split('.')[:3])
    except (AttributeError, ValueError):
        return ()


def init(a):
    root = Path(a.directory)
    template = files('reshoot').joinpath('templates')
    names = ['storyboard.toml', 'edit.toml', 'BRIEF.md', 'reshoot.toml']
    if not a.url:
        names += ['index.html', 'about.html']
    conflicts = [name for name in names if (root / name).exists()]
    if conflicts:
        raise ValueError('existing files would be overwritten: ' + ', '.join(conflicts))
    root.mkdir(parents=True, exist_ok=True)
    port = None if a.url else free_port()
    for name in names:
        text = template.joinpath(name).read_text()
        if name == 'storyboard.toml' and getattr(a, 'size', None):
            text = re.sub(r'(?m)^size\s*=.*$', lambda m: 'size = ' + json.dumps(a.size), text)
        if port:
            text = text.replace('8765', str(port))
        if a.url:
            if name == 'storyboard.toml':
                text = ('schema_version = 1\nurl = ' + json.dumps(a.url) + '\n[[beat]]\nid = "intro"\n'
                        'caption = "Replace this with one useful task"\nhold = 2\n\n[[beat]]\nid = "end"\nhold = 0.5\n')
            elif name == 'reshoot.toml':
                text = text[text.index('[[take]]'):]
                text = 'schema_version = 1\n' + text
        if name == 'BRIEF.md':
            text = text.replace('demo/', f'{root.as_posix().rstrip("/")}/')
        (root / name).write_text(text)
    if not (root / '.gitignore').exists():  # recordings are remade from the source; demo/accepted/ is what to keep
        (root / '.gitignore').write_text('/takes/\n')
    if not getattr(a, 'quiet', False):
        print(f'Created {root}. Read BRIEF.md, then run reshoot doctor --config {root / "reshoot.toml"}.')
    return 0


def free_port():
    """8765 if nothing is using it, otherwise any free local port, so the notes example doesn't collide with another app."""
    import socket
    for port in (8765, 0):
        with socket.socket() as s:
            try:
                s.bind(('127.0.0.1', port))
            except OSError:
                continue
            return s.getsockname()[1]


def export(a):
    from reshoot.review import read, record
    root, report = read(a.run_path)
    from reshoot.review import exports
    selected = a.file or []
    if not selected and a.directory:  # the run's videos and GIFs, with the videos' subtitles
        selected = exports(root, report)
        selected += [srt for f in selected if Path(f).suffix != '.gif' and
                     (srt := str(Path(f).with_suffix('.srt'))) in {item['path'] for item in report.get('files', [])}]
    if not selected and not getattr(a, 'record', None):
        raise ValueError('give --directory to copy the run\'s exports, or --record')
    if selected and not a.directory:
        raise ValueError('--file needs --directory')
    if not selected:
        if getattr(a, 'record', None):
            print(record(root, report, a.record))
        return 0
    known = {item['path'] for item in report.get('files', [])}
    if not set(selected) <= known:
        raise ValueError('export names an artifact not recorded in this run')
    destination = Path(a.directory).resolve()
    targets = [destination / Path(name).name for name in selected]
    if len(set(targets)) != len(targets):
        raise ValueError('export would collide with another selected name')
    if not getattr(a, 'replace', False) and any(p.exists() for p in targets):
        raise ValueError('export would overwrite a file; pass --replace to update media already there')
    from reshoot.tours import listing as tour_listing
    tours = {row['path'] for row in tour_listing(root, report)}
    if any(Path(name).suffix == '.html' and name not in tours for name in selected):
        raise ValueError('Only a bound tour HTML file can be exported.')
    if any(p.suffix not in ('.mp4', '.gif', '.srt', '.mov', '.png', '.html') for p in targets):
        raise ValueError('export accepts final media and subtitle files')
    if getattr(a, 'record', None):
        print(record(root, report, a.record, shared=selected))
    destination.mkdir(parents=True, exist_ok=True)
    from reshoot.run import shown
    for source, target in zip(selected, targets):
        shutil.copyfile(root / source, target)
        print(shown(target))
    print('Copied locally; nothing is published.')
    if getattr(a, 'markdown', None):
        from reshoot.review import shared
        findings = Path(a.record) / 'findings' if getattr(a, 'record', None) else None
        Path(a.markdown).write_text(shared(root, report, targets, findings, getattr(a, 'link', None)))
        print('Wrote ' + shown(a.markdown))
        return 0
    gifs, videos = [shown(t) for t in targets if t.suffix == '.gif'], [shown(t) for t in targets if t.suffix == '.mp4']
    if gifs:
        image = f'![Describe what the demo shows]({gifs[0]})'
        print('To show it in a README at the top of this folder:\n  ' + (f'[{image}]({videos[0]})' if videos else image))
    from reshoot.screenshots import listing
    from urllib.parse import quote
    shots = {Path(row['path']).name: row for row in listing(root, report)}
    for target in targets:
        if target.name in shots:
            alt = re.sub(r'([\\\[\]`*_<>])', r'\\\1', shots[target.name]['alt'])
            print(f'![{alt}]({quote(shown(target))})')
        if target.suffix == '.html':
            print(f'[Explore the walkthrough]({quote(shown(target))})')
    return 0
