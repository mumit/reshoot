"""Project setup and dependency checks using packaged demo data."""
import json
import platform
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
        for name, path in found.items():
            print(f'{name}: ' + ('available' if path else 'missing; install reshoot[browser]' if name == 'playwright' else 'missing; install it before recording'))
        print('Text scan: ' + ('installed, not probed' if 'text' in detectors else 'install Tesseract or Vision'))
        print('Face scan: ' + ('installed, not probed' if 'people' in detectors else 'unavailable'))
    return 0 if result['ok'] else 2


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
        if port:
            text = text.replace('8765', str(port))
        if a.url:
            if name == 'storyboard.toml':
                text = 'schema_version = 1\nurl = ' + json.dumps(a.url) + '\n[[beat]]\nid = "intro"\ncaption = "Replace this with one useful task"\nhold = 2\n'
            elif name == 'reshoot.toml':
                text = text[text.index('[[take]]'):]
                text = 'schema_version = 1\n' + text
        (root / name).write_text(text)
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
    selected = a.file or []
    if not selected and not getattr(a, 'record', None):
        raise ValueError('choose at least one --file from run.json files, or --record')
    if selected and not a.directory:
        raise ValueError('--file needs --directory')
    if getattr(a, 'record', None):
        print(record(root, report, a.record))
    if not selected:
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
    if any(p.suffix not in ('.mp4', '.gif', '.srt', '.mov', '.png') for p in targets):
        raise ValueError('export accepts final media and subtitle files')
    destination.mkdir(parents=True, exist_ok=True)
    for source, target in zip(selected, targets):
        shutil.copyfile(root / source, target)
        print(target)
    print('Copied locally. Review and publishing decisions are unchanged.')
    return 0
