"""Creation and revision regressions, using synthetic projects only."""
import asyncio
import hashlib
import json
import threading
import time
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import create, project, rec, review, story, studio
from reshoot.artifacts import digest
from reshoot.workspace import History


def test_undo_preserves_external_changes_and_failed_edits(tmp_path):
    board, config = tmp_path / 'story.toml', tmp_path / 'reshoot.toml'
    board.write_text('before')
    config.write_text('settings')
    history = History([board, config])
    initial = history.revision()
    history.change(lambda: board.write_text('after'))
    with pytest.raises(ValueError, match='another tab'):
        history.check(initial)
    history.move('undo')
    assert board.read_text() == 'before'
    history.move('redo')
    assert board.read_text() == 'after'
    def fail():
        board.write_text('partial')
        config.write_text('partial settings')
        raise ValueError('bad export')
    with pytest.raises(ValueError):
        history.change(fail)
    assert board.read_text() == 'after' and config.read_text() == 'settings'
    board.write_text('from an editor')
    with pytest.raises(ValueError, match='editor'):
        history.move('undo')
    assert board.read_text() == 'from an editor'


def test_recorder_keeps_incomplete_steps_and_explicit_checks(tmp_path):
    board = tmp_path / 'storyboard.toml'
    calls = [(0, {'kind': 'type', 'where': ['css', '#q'], 'value': 'stamps', 'label': 'Find a note'}),
             (1, {'kind': 'caption', 'text': 'Find the matching note'}),
             (2, {'kind': 'expect', 'check': {'type': 'text', 'target': {'css': '#list'}, 'contains': 'Buy stamps'}}),
             (3, {'kind': 'blur', 'selector': '#avatar'}),
             (4, {'kind': 'click', 'where': ['css', '#choice']}),
             (5, {'kind': 'check', 'where': ['css', '#choice'], 'checked': True}),
             (6, {'kind': 'unsupported-drop'}), (7, {'kind': 'finish'})]
    rec.write_toml(board, 'http://localhost/', '640x360@1', calls)
    data = story.load(board)
    assert data['blur'] == ['#avatar']
    assert data['beat'][0]['caption'] == 'Find the matching note'
    assert data['beat'][0]['expect'][0]['contains'] == 'Buy stamps'
    assert data['beat'][1]['action'] == [{'type': 'check', 'target': {'css': '#choice'}, 'checked': True}]
    assert 'recording_issue' in data['beat'][2]
    assert data['beat'][-1]['id'] == 'end'


def test_create_keeps_an_incomplete_story_without_attempting_a_preview(tmp_path, monkeypatch):
    monkeypatch.setattr('reshoot.setup.check_project', lambda config: {'ok': True})
    monkeypatch.setattr(rec, 'main', lambda a: rec.write_toml(a.out, a.url, a.size,
        [(0, {'kind': 'unsupported-drop'})]))
    monkeypatch.setattr('reshoot.run.preview', lambda a: pytest.fail('an incomplete draft must not render'))
    assert create.main(SimpleNamespace(url='http://localhost:3000/', directory=str(tmp_path),
                                     size='640x360@1', no_studio=True, no_open=True)) == 2
    assert story.load(tmp_path / 'storyboard.toml')['beat'][0]['recording_issue']


def test_create_applies_the_viewport_to_the_notes_example(tmp_path, monkeypatch):
    monkeypatch.setattr('reshoot.setup.check_project', lambda config: {'ok': True})
    seen = []
    monkeypatch.setattr('reshoot.run.preview', lambda a: seen.append(story.load(tmp_path / 'storyboard.toml')['size']))
    create.main(SimpleNamespace(url=None, directory=str(tmp_path), size='960x540@1.5', no_studio=True, no_open=True))
    assert seen == ['960x540@1.5']


def test_update_reuses_only_matching_recordings(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    config, folder, take = studio.project(tmp_path)
    board = story.load(tmp_path / 'storyboard.toml')
    shoot = __import__('tomllib').loads(config.read_text())
    root = tmp_path / 'run'
    source = root / take['out']
    source.parent.mkdir(parents=True)
    signature = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    meta = {'beats': [{'id': b['id'], 'definition_sha256': signature(b)} for b in board['beat']],
            'recording_settings_sha256': signature({k: v for k, v in board.items() if k not in ('beat', 'caption')})}
    source.with_suffix('.take.json').write_text(json.dumps(meta))
    source.with_suffix('.captions.json').write_text(json.dumps({'captions': [
        {'beat': b['id'], 'recorded': b.get('caption'), 'recorded_sub': b.get('sub')} for b in board['beat']]}))
    report = {'inputs': {'recording_config_sha256': signature({k: v for k, v in shoot.items() if k in ('app', 'take', 'inputs')}),
                        'fixtures': [{'sha256': digest(tmp_path / p)} for p in shoot['inputs']]}}
    run = root, report
    studio.edit(tmp_path / 'storyboard.toml', {'beat': 'search', 'caption': 'New words'})
    assert studio.update_kind(folder, config, take, run)[0] == 'recut'
    studio.edit(tmp_path / 'storyboard.toml', {'beat': 'search', 'hold': 3})
    assert studio.update_kind(folder, config, take, run)[0] == 'preview'
    studio.edit(tmp_path / 'storyboard.toml', {'beat': 'search', 'hold': 2})
    (tmp_path / 'index.html').write_text('changed app')
    assert studio.update_kind(folder, config, take, run)[0] == 'preview'


@pytest.mark.browser
def test_an_unresolved_recording_cannot_produce_a_successful_take(tmp_path):
    from reshoot.cli import main
    board = tmp_path / 'unresolved.toml'
    board.write_text('schema_version=1\nurl="about:blank"\n[[beat]]\nid="missing"\n'
                     'recording_issue="Add the dropped demo file action"\n')
    with pytest.raises(SystemExit) as result:
        main(['web', str(board), str(tmp_path / 'take.mp4')])
    assert result.value.code == 2
    meta = json.loads((tmp_path / 'take.take.json').read_text())
    assert meta['status'] == 'failed' and 'Unresolved step missing' in meta['error']
    assert not (tmp_path / 'take.mp4').exists()


def test_studio_media_and_decisions_keep_the_displayed_run(tmp_path, monkeypatch):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    roots = []
    for n in (1, 2):
        root = tmp_path / 'takes/runs' / (str(n) * 32)
        root.mkdir(parents=True)
        (root / 'clip.mp4').write_bytes(f'run {n}'.encode())
        report = {'id': root.name, 'ok': True, 'finished_at': f'2026-10-24T00:00:0{n}+00:00',
                  'files': [{'path': 'clip.mp4', 'sha256': digest(root / 'clip.mp4')}]}
        (root / 'run.json').write_text(json.dumps(report))
        roots.append(root)
    chosen = review.read(roots[0])
    routed = []
    monkeypatch.setattr(review, 'accept_from_page', lambda path, body: (routed.append(path) or 2, 'test interception'))
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        # Run 2 is already newest; an old tab's exact run 1 media still returns run 1.
        assert urllib.request.urlopen(url + f'runs/{roots[0].name}/clip.mp4').read() == b'run 1'
        config, folder, take = studio.project(tmp_path)
        rev = History([config, folder / take['web'], folder / 'styles.toml', folder / 'edit.toml']).revision()
        body = {'run_id': chosen[1]['id'], 'binding': review.binding(*chosen), 'revision': rev}
        def post(data):
            return json.loads(urllib.request.urlopen(urllib.request.Request(url + 'accept',
                data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})).read())
        assert post(body)['code'] == 2
        assert routed == [str(roots[0])]
        assert post({**body, 'binding': 'stale'})['ok'] is False
        assert len(routed) == 1
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_changed_scan_rejects_a_served_decision(tmp_path):
    root = tmp_path / 'run'
    root.mkdir()
    (root / 'run.json').write_text(json.dumps({'id': 'synthetic', 'ok': True, 'files': []}))
    body = {'run_id': 'synthetic', 'binding': review.binding(*review.read(root))}
    (root / 'review').mkdir()
    (root / 'review/flags.json').write_text('{"1-1": [["email", "demo…"]]}')
    code, message = review.accept_from_page(str(root), body)
    assert code == 2 and 'changed' in message
    assert not (root / 'decisions.json').exists()


def test_cancel_stops_a_job_and_allows_another(tmp_path):
    import sys
    job = studio.Job()
    job.start('preview', [sys.executable, '-c', 'import time; time.sleep(60)'], tmp_path)
    job.cancel()  # also covers cancellation before Popen publishes its handle
    deadline = time.monotonic() + 5
    while job.running() and time.monotonic() < deadline:
        time.sleep(.02)
    assert not job.running() and job.code == 130
    job.start('recut', [sys.executable, '-c', 'print("done")'], tmp_path)
    while job.running() and time.monotonic() < deadline:
        time.sleep(.02)
    assert job.code == 0 and job.lines == ['done']


@pytest.mark.browser
def test_create_from_demonstration_replays_toolbar_captions_and_checks(tmp_path, monkeypatch):
    import http.server
    from functools import partial
    from test_reshoot import ROOT
    import person
    app = tmp_path / 'app'
    app.mkdir()
    text = (ROOT / 'src/reshoot/templates/index.html').read_text()
    (app / 'index.html').write_text(text.replace('<form id="add">',
        '<label><input type="checkbox" id="pin"> Pin a note</label><form id="add">'))
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(http.server.SimpleHTTPRequestHandler, directory=str(app)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    original = rec.session
    async def toolbar(page, selector):
        coords = await page.run('const r = document.querySelector("reshoot-recorder").shadowRoot.querySelector('
                                + json.dumps(selector) + ').getBoundingClientRect(); return [r.x+r.width/2,r.y+r.height/2]')
        await person.click_at(page, *coords)
    async def tour(page):
        for _ in range(50):
            if await page.run('return !!document.querySelector("reshoot-recorder")'):
                break
            await asyncio.sleep(.1)
        await person.click(page, '#pin')
        await person.click(page, '#text')
        await person.type(page, 'Buy stamps')
        await person.enter(page)
        await toolbar(page, '[data-do=caption]')
        await page.run('document.querySelector("reshoot-recorder").shadowRoot.querySelector("input").focus()')
        await person.type(page, 'Save the note')
        await toolbar(page, 'form button')
        await toolbar(page, '[data-do=check]')
        await person.click(page, '#list li')
        await toolbar(page, '[data-do=blur]')
        await person.click(page, '#about')  # selection must not navigate
        assert (await page.run('return location.pathname')) == '/'
        await toolbar(page, '[data-do=pause]')
        await person.click(page, '#text')  # ignored, with no change to app state
        await toolbar(page, '[data-do=pause]')
        await person.click(page, '#q')
        await person.type(page, 'stamps')
        await toolbar(page, '[data-do=check]')
        await person.click(page, '#list')
        await toolbar(page, '[data-do=done]')
    async def driven(url, w, h, calls, **kwargs):
        await original(url, w, h, calls, headless=True, toolbar=True, drive=tour)
        assert calls[-1][1]['kind'] == 'finish'
    monkeypatch.setattr(rec, 'session', driven)
    try:
        folder = tmp_path / 'created'
        assert create.main(SimpleNamespace(url=f'http://127.0.0.1:{httpd.server_port}/', directory=str(folder),
                                         size='960x540@1', no_studio=True, no_open=True)) == 0
    finally:
        httpd.shutdown()
        httpd.server_close()
    data = story.load(folder / 'storyboard.toml')
    assert data['blur'] == ['#about']
    assert any(b.get('caption') == 'Save the note' for b in data['beat'])
    assert any(a['type'] == 'check' for b in data['beat'] for a in b.get('action', []))
    root, report = review.read(folder / 'latest')
    assert report['ok'] and report['expectations_status'] == 'passed'
    assert set(Path(p).suffix for p in review.exports(root, report)) == {'.mp4', '.gif'}
    from reshoot import cut
    from PIL import Image, ImageStat
    first = tmp_path / 'first.png'
    cut.ff('-i', root / 'takes/demo-final.mp4', '-frames:v', 1, first)
    assert max(ImageStat.Stat(Image.open(first).convert('RGB')).stddev) > 5  # an app, not a blank opening
