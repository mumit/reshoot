"""Beat cuts change the video, preserve the task, and map every repeated appearance."""
import json
import threading
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import cut, project, review, sequence, story, studio, timeline
from reshoot.artifacts import digest


def recorded_project(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    edit = tmp_path / 'edit.toml'
    edit.write_text(edit.read_text().replace('[[part]]', '# keep the clip reason\n[[part]] # main clip', 1))
    root = tmp_path / 'takes/runs' / ('1' * 32)
    root.mkdir(parents=True)
    source = root / 'takes/demo.mp4'
    source.parent.mkdir()
    source.write_bytes(b'synthetic media; timing comes from its map')
    timeline.write(source, [{'source': str(source), 'source_start': 0, 'source_end': 9, 'start': 0, 'end': 9}], 9)
    bounds = [('intro', 0, 2), ('add', 2, 5), ('search', 5, 8), ('end', 8, 9)]
    source.with_suffix('.beats.json').write_text(json.dumps({name: start for name, start, _ in bounds}))
    source.with_suffix('.take.json').write_text(json.dumps({'beats': [
        {'id': name, 'start': start, 'end': end, 'status': 'passed'} for name, start, end in bounds]}))
    report = {'id': root.name, 'ok': True, 'mode': 'preview', 'files': [], 'inputs': {'edit_sha256': digest(edit)}}
    report['files'] = [{'path': str(file.relative_to(root)), 'sha256': digest(file)} for file in root.rglob('*') if file.is_file()]
    (root / 'run.json').write_text(json.dumps(report))
    return tmp_path / 'reshoot.toml', edit, source


def test_ranges_and_order_preserve_the_recorded_task_and_comments(tmp_path):
    config, edit, _ = recorded_project(tmp_path)
    board = tmp_path / 'storyboard.toml'
    unchanged = config.read_bytes(), board.read_bytes()
    sequence.apply(sequence.load(config), {'operation': 'range', 'part': 0, 'start': 'add', 'through': 'search'})
    data = tomllib.loads(edit.read_text())
    assert data['part'] == [{'take': 0, 'start': 'add', 'through': 'search'}]
    assert '# main clip' in edit.read_text() and '# keep the clip reason' in edit.read_text()
    original_export = data['export']
    sequence.apply(sequence.load(config), {'operation': 'add', 'take': 0, 'start': 'intro', 'through': 'intro'})
    sequence.apply(sequence.load(config), {'operation': 'move', 'part': 1, 'to': 0})
    sequence.apply(sequence.load(config), {'operation': 'duplicate', 'part': 0})
    assert [p['start'] for p in tomllib.loads(edit.read_text())['part']] == ['intro', 'intro', 'add']
    sequence.apply(sequence.load(config), {'operation': 'remove', 'part': 1})
    assert [p['start'] for p in tomllib.loads(edit.read_text())['part']] == ['intro', 'add']
    assert tomllib.loads(edit.read_text())['export'] == original_export
    assert (config.read_bytes(), board.read_bytes()) == unchanged


def test_through_includes_the_last_hold_and_protects_spoken_lines(tmp_path):
    _, _, source = recorded_project(tmp_path)
    assert timeline.part_range({'start': 'add', 'end': 'search'}, source) == (2, 5, 1)
    assert timeline.part_range({'start': 'add', 'through': 'search'}, source) == (2, 8, 1)
    source.with_suffix('.voice.json').write_text(json.dumps([{'t': 4, 'seconds': 2, 'text': 'Complete sentence', 'file': 'synthetic.wav'}]))
    with pytest.raises(ValueError, match='narration line'):
        timeline.part_range({'start': 'search', 'through': 'search'}, source)
    with pytest.raises(ValueError, match='narration line'):
        timeline.part_range({'start': 'add', 'through': 'add'}, source)
    assert timeline.part_range({'start': 'add', 'through': 'search'}, source) == (2, 8, 1)
    with pytest.raises(ValueError, match='either end'):
        timeline.part_range({'end': 'search', 'through': 'search'}, source)


@pytest.mark.parametrize('change', [
    {'operation': 'range', 'part': 0, 'start': 'search', 'through': 'intro'},
    {'operation': 'range', 'part': 0, 'start': 'missing', 'through': 'search'},
    {'operation': 'move', 'part': 0, 'to': 3}, {'operation': 'remove', 'part': 0},
    {'operation': 'duplicate', 'part': True}, {'operation': 'add', 'take': 2, 'start': 'intro', 'through': 'search'},
])
def test_invalid_sequence_edit_keeps_the_file(tmp_path, change):
    config, edit, _ = recorded_project(tmp_path)
    before = edit.read_bytes()
    with pytest.raises(ValueError):
        sequence.apply(sequence.load(config), change)
    assert edit.read_bytes() == before


def test_external_edit_and_changed_evidence_are_preserved(tmp_path):
    config, edit, source = recorded_project(tmp_path)
    data = sequence.load(config)
    external = edit.read_text() + '# an editor changed the cut\n'
    edit.write_text(external)
    with pytest.raises(ValueError, match='project changed'):
        sequence.apply(data, {'operation': 'duplicate', 'part': 0})
    assert edit.read_text() == external
    data = sequence.load(config)
    source.write_bytes(b'changed evidence')
    with pytest.raises(ValueError, match='recording changed'):
        sequence.apply(data, {'operation': 'duplicate', 'part': 0})
    assert edit.read_text() == external
    with pytest.raises(ValueError):
        sequence.load(config)


def test_default_run_skips_partial_previews_and_keeps_external_story_edits(tmp_path):
    config, edit, _ = recorded_project(tmp_path)
    partial = tmp_path / 'takes/runs' / ('2' * 32)
    partial.mkdir()
    (partial / 'run.json').write_text(json.dumps({'id': partial.name, 'ok': True, 'mode': 'partial-preview', 'files': []}))
    data = sequence.load(config)
    assert data['root'].name == '1' * 32
    with pytest.raises(ValueError, match='complete successful'):
        sequence.load(config, partial)
    board = tmp_path / 'storyboard.toml'
    external = '# a new caption from another editor\n' + board.read_text()
    board.write_text(external)
    before = edit.read_bytes()
    with pytest.raises(ValueError, match='project changed'):
        sequence.apply(data, {'operation': 'duplicate', 'part': 0})
    assert edit.read_bytes() == before and board.read_text() == external


def test_occurrences_include_repeats_and_exclude_omitted_beats(tmp_path):
    source = tmp_path / 'source.mp4'
    rows = [{'source': str(source), 'source_start': a, 'source_end': b, 'start': start, 'end': end}
            for a, b, start, end in [(5, 8, 0, 3), (0, 5, 3, 8), (5, 8, 8, 11)]]
    assert timeline.occurrences(rows, source, 5, 8) == [[0, 3], [8, 11]]
    assert timeline.occurrences(rows, source, 0, 2) == [[3, 5]]
    assert timeline.occurrences(rows, source, 8, 9) == []
    assert timeline.occurrences(rows, source, 4, 6) == [[0, 1], [7, 9]]


def test_rendered_sequence_preserves_ranges_cards_repeated_cues_and_export_map(tmp_path):
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=c=red:s=160x90:r=60:d=1',
           '-f', 'lavfi', '-i', 'color=c=green:s=160x90:r=60:d=1',
           '-f', 'lavfi', '-i', 'color=c=blue:s=160x90:r=60:d=1',
           '-filter_complex', '[0:v][1:v][2:v]concat=n=3:v=1:a=0', '-c:v', 'libx264', source)
    source.with_suffix('.beats.json').write_text(json.dumps({'intro': 0, 'add': 1, 'search': 2}))
    source.with_suffix('.take.json').write_text(json.dumps({'beats': [
        {'id': name, 'start': i, 'end': i + 1} for i, name in enumerate(['intro', 'add', 'search'])]}))
    source.with_suffix('.events.json').write_text(json.dumps([
        {'t': 0, 'kind': 'caption', 'text': 'Intro'}, {'t': 1, 'kind': 'caption', 'text': 'Add'},
        {'t': 2, 'kind': 'caption', 'text': 'Search'}, {'t': 3, 'kind': 'caption', 'text': None}]))
    edit = tmp_path / 'edit.toml'
    edit.write_text('''schema_version = 1
[[part]]
start = "search"
through = "search"
[[part]]
card = "Middle"
duration = 1
[[part]]
start = "intro"
through = "add"
[[part]]
start = "search"
through = "search"
[[export]]
name = "small"
width = 160
height = 90
''')
    timeline.edit(SimpleNamespace(script=str(edit), args=[str(source)]))
    movie = tmp_path / 'demo-final.mp4'
    assert cut.duration(movie) == pytest.approx(5, abs=.03)
    assert timeline.cues(movie) == [(0, 1, 'Search'), (2, 3, 'Intro'), (3, 4, 'Add'), (4, 5, 'Search')]
    mapping = timeline.read(movie)
    assert [(row['start'], row['end']) for row in mapping['parts']] == [(0, 1), (1, 2), (2, 4), (4, 5)]
    assert timeline.read(tmp_path / 'demo-final-small.mp4')['parts'] == mapping['parts']


@pytest.mark.browser
def test_studio_trims_repeats_reorders_and_undoes_without_changing_the_task(tmp_path):
    from playwright.sync_api import sync_playwright
    from reshoot import web
    from reshoot.cli import main
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    config, board, edit = tmp_path / 'reshoot.toml', tmp_path / 'storyboard.toml', tmp_path / 'edit.toml'
    board.write_text(board.read_text().replace('1280x720@1', '960x540@1'))
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code == 0
    baseline, _ = review.read(tmp_path / 'latest')
    clean_hash, original_board, original_edit = digest(baseline / 'takes/demo.clean.mp4'), board.read_bytes(), edit.read_bytes()
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            stale = browser.new_page()
            stale.goto(url)
            form = page.locator('.sequence-part[data-part="0"] .range-form')
            form.locator('[name=start]').select_option('search')
            page.click('[data-job=update]')
            page.wait_for_function("document.getElementById('save-error').textContent.includes('unsaved')")
            assert edit.read_bytes() == original_edit
            with page.expect_navigation():
                form.locator('button[type=submit]').click()
            assert tomllib.loads(edit.read_text())['part'][0]['through'] == 'search'
            stale.click('[data-sequence=duplicate]')
            stale.wait_for_function("document.getElementById('save-error').textContent.includes('another tab')")
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert edit.read_bytes() == original_edit
            with page.expect_navigation():
                page.click('[data-history=redo]')
            form = page.locator('.sequence-part[data-part="0"] .range-form')
            form.locator('[name=through]').select_option('intro')
            form.locator('button[type=submit]').click()
            page.wait_for_function("document.getElementById('save-error').textContent.includes('end after')")
            form.locator('button[type=reset]').click()
            assert form.locator('[name=through]').input_value() == 'search'
            add = page.locator('#add-clip')
            add.locator('[name=start]').select_option('intro')
            add.locator('[name=through]').select_option('add')
            with page.expect_navigation():
                add.locator('button[type=submit]').click()
            with page.expect_navigation():
                page.locator('.sequence-part[data-part="0"] [data-sequence=duplicate]').click()
            with page.expect_navigation():
                page.locator('.sequence-part[data-part="2"] [data-sequence=move][data-to="1"]').click()
            assert [part['start'] for part in tomllib.loads(edit.read_text())['part']] == ['search', 'intro', 'search']
            assert page.locator('[data-part-play]:enabled').count() == 0
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            assert 'a re-cut of' in page.locator('.status').inner_text()
            assert page.locator('[data-part-play]:enabled').count() == 3
            assert page.locator('.seg[data-beat=search]').count() == 2
            assert page.locator('.beat[data-beat=end] .when').inner_text() == 'not in this cut'
            assert '2 appearances' in page.locator('.beat[data-beat=search] .when').inner_text()
            second = page.locator('.seg[data-beat=search]').nth(1)
            second.click()
            page.wait_for_function("document.getElementById('video').currentTime > 4")
            page.locator('.sequence').scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path / 'sequence-studio.png'))
            assert not errors
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    latest, report = review.read(tmp_path / 'latest')
    assert report['recut_from'] == baseline.name and report['expectations_count'] == 3
    assert digest(latest / 'takes/demo.clean.mp4') == clean_hash
    assert board.read_bytes() == original_board
