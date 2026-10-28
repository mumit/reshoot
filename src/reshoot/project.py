"""Project setup and dependency checks using packaged demo data."""
import json
import os
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path
from reshoot import config


def doctor(a):
    from reshoot import setup
    result = setup.inspect(a.config, probe=getattr(a, 'probe', False))
    result['reshoot']['latest'] = latest_release()
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        installed, latest = result['reshoot']['version'], result['reshoot']['latest']
        newer = latest and release(latest) > release(installed)
        print(f'reshoot: {installed}' + (f'; {latest} is out: reshoot upgrade' if newer else ''))
        setup.print_report(result)
        if not getattr(a, 'probe', False):
            import shlex
            print('Test the tools with synthetic data: reshoot doctor --probe' +
                  (' --config ' + shlex.quote(a.config) if a.config else ''))
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


CHANGELOG = 'https://github.com/mumit/reshoot/blob/main/CHANGELOG.md'


def installation():
    """How this reshoot was installed: ('uv', extras), ('pipx', extras), ('source', None) or ('pip', None)."""
    import sys
    import tomllib
    from importlib.metadata import distribution
    try:
        origin = json.loads(distribution('reshoot').read_text('direct_url.json') or '{}')
    except Exception:
        origin = {}
    if 'dir_info' in origin:  # installed from a folder, editable or not
        return 'source', None
    prefix = Path(sys.prefix)
    if (prefix / 'uv-receipt.toml').is_file():
        wanted = tomllib.loads((prefix / 'uv-receipt.toml').read_text())['tool']['requirements']
        return 'uv', next((item.get('extras', []) for item in wanted if item.get('name') == 'reshoot'), [])
    if (prefix / 'pipx_metadata.json').is_file():
        spec = json.loads((prefix / 'pipx_metadata.json').read_text())['main_package'].get('package_or_url', '')
        return 'pipx', re.findall(r'[\w-]+', spec.partition('[')[2].partition(']')[0])
    return 'pip', None


def upgrade(a):
    """Install the newest reshoot, or the one asked for, the way this one was installed."""
    import sys
    from importlib.metadata import version
    installed, target = version('reshoot'), a.version or latest_release()
    if not target:
        raise ValueError(f"PyPI couldn't be reached to find the newest reshoot. To choose one: reshoot upgrade {installed}")
    if target == installed:
        print(f'reshoot {installed} is already ' + ('installed.' if a.version else 'the newest.'))
        return 0
    how, extras = installation()
    package = 'reshoot' + (f"[{','.join(extras)}]" if extras else '') + (f'=={a.version}' if a.version else '')
    command = {'uv': ['uv', 'tool', 'install', '--force' if a.version else '--upgrade', package],
               'pipx': ['pipx', 'install', '--force', package] if a.version else ['pipx', 'upgrade', 'reshoot']}.get(how)
    if how == 'source':
        print('This reshoot runs from a source checkout. Update it there: git pull, then uv sync --extra browser.')
        return 2
    if command is None:
        print(f"Upgrade this installation yourself: python -m pip install --upgrade '{package}'")
        return 2
    if not shutil.which(command[0]):
        print(f'{command[0]} is not on PATH. Run this where it is: {" ".join(command)}')
        return 2
    print(f'reshoot {installed} to {target}, with: {" ".join(command)}\nWhat changed: {CHANGELOG}')
    if release(target)[:2] != release(installed)[:2]:
        print('A minor version before 1.0 may change project files or commands, so read what changed first.')
    if not a.yes:
        if not sys.stdin.isatty():
            raise ValueError('pass --yes to upgrade without a question')
        if input('Upgrade? [y/N] ').strip().lower() not in ('y', 'yes'):
            print('Not upgraded.')
            return 0
    if subprocess.run(command).returncode:
        print(f'The upgrade failed, so reshoot {installed} is still installed.')
        return 2
    found = subprocess.run([str(Path(sys.prefix) / 'bin' / 'reshoot'), '--version'], capture_output=True, text=True)
    if found.returncode or found.stdout.strip() != target:
        print(f'The upgrade finished, but reshoot --version says {found.stdout.strip() or found.stderr.strip()!r}, '
              f'not {target}. Run reshoot doctor.')
        return 2
    print(f'reshoot {target} is installed. Restart any open studio to use it.')
    for harness, folder in (('claude', '.claude'), ('codex', '.agents')):
        if (Path.cwd() / folder / 'skills' / 'reshoot-demo').is_dir():
            print(f'This project has reshoot skills; update them to match: reshoot skills {harness} --directory . --replace')
    return 0


NOTES_DATA = '''Use made-up data only. The bundled notes app resets when the page reloads.
For another app, document its separate demo account or database, reset command,
and expected result before changing the storyboard. Log mocked responses explicitly.'''
URL_DATA = '''The app is at {url}. reshoot records it there but doesn't start it, so start
it first, or add an `[app]` table to reshoot.toml with the command that starts it
and one that resets its data. Use made-up data only: write down its demo account,
how its data is reset, and the result each recording should show. Log mocked
responses explicitly.'''


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
            if a.url:
                text = text.replace(NOTES_DATA, URL_DATA.format(url=a.url))
            here = os.path.relpath(root)  # as the reader types it, not the absolute path create resolved
            text = text.replace('demo/', f'{(root.as_posix() if here.startswith("..") else Path(here).as_posix()).rstrip("/")}/')
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


def task(root):
    """The brief's task, such as "Save a note, then find it", for a README image's alt text."""
    for folder in (root.parent, *root.parents[1:3]):
        brief = folder / 'BRIEF.md'
        if brief.is_file():
            found = re.search(r'(?m)^- One task to show:[ \t]*(\S.*)$', brief.read_text())
            return found[1].strip() if found else None
    return None


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
        alt = re.sub(r'([\\\[\]`*_<>])', r'\\\1', task(root) or 'Describe what the demo shows')
        image = f'![{alt}]({gifs[0]})'
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
