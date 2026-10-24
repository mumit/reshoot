import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from reshoot import config, project
from reshoot.artifacts import Frames


def test_init_is_packaged_and_refuses_overwrites(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    assert (tmp_path / 'index.html').exists()
    assert config.read(tmp_path / 'reshoot.toml')[0]['schema_version'] == 1
    with pytest.raises(ValueError, match='overwritten'):
        project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    assert (tmp_path / '.gitignore').read_text() == '/takes/\n'  # not demo/accepted/takes/
    assert f'{tmp_path.as_posix()}/reshoot.toml' in (tmp_path / 'BRIEF.md').read_text()


def test_export_without_files_copies_the_exports_and_offers_markdown(tmp_path, capsys, monkeypatch):
    from test_review import project_run
    root = project_run(tmp_path)
    gif = root / 'takes/demo-final-readme.gif'
    gif.write_bytes(b'GIF89a')
    report = __import__('reshoot.review', fromlist=['read']).read(root)[1]
    report['files'].append({'path': 'takes/demo-final-readme.gif', 'sha256': __import__('reshoot.artifacts', fromlist=['digest']).digest(gif)})
    (root / 'run.json').write_text(__import__('json').dumps(report))
    monkeypatch.chdir(tmp_path)
    args = SimpleNamespace(run_path=str(root), directory='docs/demo', file=None, record=None, replace=False)
    assert project.export(args) == 0
    assert sorted(p.name for p in (tmp_path / 'docs/demo').iterdir()) == ['demo-final-readme.gif', 'demo-final.mp4']
    assert '[![Describe what the demo shows](docs/demo/demo-final-readme.gif)](docs/demo/demo-final.mp4)' in capsys.readouterr().out


def test_init_moves_the_notes_app_off_a_busy_port(tmp_path):
    import socket
    with socket.socket() as busy:
        try:
            busy.bind(('127.0.0.1', 8765))
            busy.listen()
        except OSError:
            pass  # something else already holds it, which is the case under test
        project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    data = config.read(tmp_path / 'reshoot.toml')[0]
    port = data['app']['url'].rsplit(':', 1)[1].strip('/')
    assert port != '8765' and port in data['app']['run']
    assert f'127.0.0.1:{port}/' in (tmp_path / 'storyboard.toml').read_text()


def test_busy_app_port_is_named_without_exposing_remote_urls(monkeypatch):
    from reshoot import run
    monkeypatch.setattr(run, 'answers', lambda url, ready=False: True)
    with pytest.raises(SystemExit, match='port 8765 on 127.0.0.1'):
        run.start_app({'url': 'http://127.0.0.1:8765/', 'run': 'true'})
    with pytest.raises(SystemExit) as remote:
        run.start_app({'url': 'https://demo.example.com/app', 'run': 'true'})
    assert 'https://' in str(remote.value)  # the run reports it through redact(), which hides it


def test_the_app_log_stays_out_of_the_output_and_shows_when_the_app_stops(tmp_path, capfd, monkeypatch):
    from reshoot import run
    monkeypatch.setattr(run, 'answers', lambda url, ready=False: False)
    log = tmp_path / 'app.log'
    with pytest.raises(SystemExit) as stopped:
        run.start_app({'url': 'http://127.0.0.1:9/', 'run': 'echo GET /favicon.ico 404; exit 3'}, log)
    assert 'exit 3' in str(stopped.value) and 'GET /favicon.ico 404' in str(stopped.value)
    assert 'favicon' not in capfd.readouterr().out
    assert 'favicon' in log.read_text()


def test_doctor_says_when_a_newer_release_is_out(monkeypatch, capsys):
    monkeypatch.setattr(project, 'latest_release', lambda: '99.0.0')
    project.doctor(SimpleNamespace(config=None, json=False))
    assert "99.0.0 is out: uv tool install --upgrade 'reshoot[browser]'" in capsys.readouterr().out
    monkeypatch.setattr(project, 'latest_release', lambda: None)
    project.doctor(SimpleNamespace(config=None, json=False))
    assert 'is out' not in capsys.readouterr().out
    assert project.release('0.10.0') > project.release('0.9.9') and project.release('weird') == ()


def test_external_app_scaffold_is_valid_python(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url='http://localhost:1234/'))
    __import__('tomllib').loads((tmp_path / 'storyboard.toml').read_text())
    assert 'app' not in config.read(tmp_path / 'reshoot.toml')[0]


@pytest.mark.parametrize('exists', [False, True])
def test_doctor_rejects_missing_or_nonexecutable_browser(tmp_path, monkeypatch, capsys, exists):
    browser = tmp_path / 'chrome'
    if exists:
        browser.write_text('not an executable browser')
        browser.chmod(0o644)
    monkeypatch.setenv('RESHOOT_CHROME', str(browser))
    assert project.doctor(SimpleNamespace(config=None, json=True)) == 2
    report = json.loads(capsys.readouterr().out)
    assert not report['ok']
    assert report['tools']['chrome'] is None
    assert 'chrome' not in report['versions']


def test_versioned_outputs_are_isolated_and_paths_are_explicit(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    a = config.prepare(tmp_path / 'reshoot.toml')
    b = config.prepare(tmp_path / 'reshoot.toml')
    assert a['_run_id'] != b['_run_id']
    assert a['take'][0]['out'] != b['take'][0]['out']
    assert a['take'][0]['web'] == str(tmp_path / 'storyboard.toml')
    assert a['edit']['args'][0] == a['take'][0]['out']
    assert a['app']['cwd'] == str(tmp_path)


def test_disk_frames_support_encoding_access(tmp_path):
    with Frames() as frames:
        frames.append((0, b'first'))
        frames.append((1, b'second'))
        frames.append((2, None))
        assert frames[0] == (0, b'first')
        assert list(frames[1:]) == [(1, b'second'), (2, None)]
        assert list(frames.without_end()) == [(0, b'first'), (1, b'second')]
        folder = Path(frames.temp.name)
    assert not folder.exists()


@pytest.mark.browser
def test_generated_project_records_an_isolated_preview(tmp_path):
    from test_reshoot import free_port
    from reshoot.cli import main
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    port = free_port()
    path = tmp_path / 'reshoot.toml'
    path.write_text(path.read_text().replace('8765', str(port)).replace('scan = true', 'scan = false'))
    board = tmp_path / 'storyboard.toml'
    board.write_text(board.read_text().replace('8765', str(port)))
    with pytest.raises(SystemExit) as result:
        main(['preview', str(path)])
    assert result.value.code == 0
    reports = list((tmp_path / 'takes/runs').glob('*/run.json'))
    report = json.loads(reports[0].read_text())
    assert report['ok'] and report['mode'] == 'preview'
    assert report['expectations_status'] == 'passed'
    assert (reports[0].parent / 'takes/demo-final.mp4').exists()
    assert (reports[0].parent / 'takes/demo-final-readme.gif').exists()
    from reshoot import review
    review.main(SimpleNamespace(run_path=str(reports[0]), previous=None, import_decisions=None))
    assert (reports[0].parent / 'review.html').exists()
    metadata = json.loads((reports[0].parent / 'takes/demo.take.json').read_text())
    assert [b['status'] for b in metadata['beats']] == ['unverified', 'passed', 'passed', 'unverified']
    assert report['files'] and all('sha256' in f for f in report['files'])


@pytest.mark.browser
def test_mixed_preview_can_join_web_and_terminal_takes(tmp_path, monkeypatch):
    import re
    from test_reshoot import free_port
    from reshoot import cut, run
    from reshoot.cli import main
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    port = free_port()
    config_path = tmp_path / 'reshoot.toml'
    text = config_path.read_text().replace('8765', str(port))
    text = text.replace('[edit]', '[[take]]\ntape = "terminal.tape"\n[edit]')
    text = text.replace('args = ["takes/demo.mp4"]', 'args = ["takes/demo.mp4", "takes/terminal.mp4"]')
    text = text.replace(', "takes/demo-final-readme.gif"', '')
    config_path.write_text(text.replace('scan = true', 'scan = false'))
    board = tmp_path / 'storyboard.toml'
    board.write_text(board.read_text().replace('8765', str(port)))
    (tmp_path / 'terminal.tape').write_text('Output "takes/terminal.mp4"\n')
    edit = tmp_path / 'edit.toml'
    edit.write_text(edit.read_text().split('[[export]]')[0] + '\n[[part]]\ntake = 1\n')
    execute = run.execute

    def capture(cmd, *args):
        if cmd[0] == 'vhs':
            output = re.search(r'Output "([^"]+)"', Path(cmd[1]).read_text())[1]
            # Stand in for VHS with its fixed-size encoded terminal output.
            cut.ff('-f', 'lavfi', '-i', 'color=s=1280x720:r=10:d=1', '-c:v', 'libx264', output)
            return 0
        return execute(cmd, *args)

    monkeypatch.setattr(run, 'execute', capture)
    monkeypatch.setenv('RESHOOT_PREVIEW', 'previous-value')
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config_path)])
    assert result.value.code == 0
    assert __import__('os').environ['RESHOOT_PREVIEW'] == 'previous-value'
    report_path = next((tmp_path / 'takes/runs').glob('*/run.json'))
    report = json.loads(report_path.read_text())
    assert report['ok'] and report['mode'] == 'preview'
    assert report['expectations_status'] == 'passed'
    assert cut.probe(report_path.parent / 'takes/demo-final.mp4')[:2] == (1280, 720)


def test_harness_bundle_is_self_contained_and_replaces_only_when_asked(tmp_path):
    from reshoot import skills
    for harness in ('codex', 'claude'):
        args = SimpleNamespace(directory=str(tmp_path), harness=harness, replace=False)
        skills.install(args)
        folder = tmp_path / ('.agents' if harness == 'codex' else '.claude') / 'skills'
        assert sorted(p.name for p in folder.iterdir()) == sorted(skills.NAMES)
        for name in skills.NAMES:
            assert '../../examples' not in (folder / name / 'SKILL.md').read_text()
        with pytest.raises(ValueError, match='overwrite'):
            skills.install(args)
        stale = folder / 'reshoot-demo' / 'SKILL.md'
        stale.write_text('Requires reshoot CLI 0.2')
        skills.install(SimpleNamespace(directory=str(tmp_path), harness=harness, replace=True))
        assert 'Requires reshoot CLI 0.2' not in stale.read_text()


def test_export_requires_explicit_files_and_preserves_existing(tmp_path):
    from test_review import run_fixture
    root = run_fixture(tmp_path / 'run')
    args = SimpleNamespace(run_path=str(root), directory=str(tmp_path / 'export'), file=['demo.mp4'])
    assert project.export(args) == 0
    with pytest.raises(ValueError, match='overwrite'):
        project.export(args)
