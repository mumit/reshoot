"""Style reuse preserves the story and verified recordings; invalid or stale groups do not partially apply."""
import copy
import json
import threading
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import project, story, studio, styles
from reshoot.artifacts import digest


def demo(folder):
    project.init(SimpleNamespace(directory=str(folder), url=None))
    return folder / 'reshoot.toml', folder / 'storyboard.toml', folder / 'edit.toml'


def test_style_preserves_the_task_fonts_and_exports_across_takes(tmp_path):
    config, board, edit = demo(tmp_path)
    board.write_text(board.read_text().replace('seed = 1', 'seed = 1\n[caption]\nfont = "brand.ttf"\nmin_seconds = 2'))
    second = tmp_path / 'second.toml'
    second.write_bytes(board.read_bytes())
    config.write_text(config.read_text().replace('[edit]', '[[take]]\nweb = "second.toml"\nout = "takes/second.mp4"\n\n[edit]'))
    edit.write_text(edit.read_text().replace('[[part]]', '[style]\nfont = "titles.ttf"\nlogo = "mark.png"\n\n[[part]]', 1))
    before_board, before_edit, before_config = story.load(board), tomllib.loads(edit.read_text()), config.read_bytes()
    styles.apply(config, styles.BUILTINS['midnight'])
    after = story.load(board)
    assert after['beat'] == before_board['beat']
    assert story.recording_settings(after) == story.recording_settings(before_board)
    assert after['caption']['font'] == 'brand.ttf' and after['caption']['min_seconds'] == 2
    assert story.load(second)['caption'] == after['caption']
    cut = tomllib.loads(edit.read_text())
    assert cut['part'] == before_edit['part'] and cut['export'] == before_edit['export']
    assert cut['style']['font'] == 'titles.ttf' and cut['style']['logo'] == 'mark.png'
    assert config.read_bytes() == before_config
    assert styles.selected(config, styles.choices(tmp_path)) == 'midnight'
    studio.edit(second, {'look': {'position': 'top'}})
    assert styles.selected(config, styles.choices(tmp_path)) is None
    styles.apply(config, styles.BUILTINS['focus'])
    assert 'frame' not in tomllib.loads(edit.read_text())


def test_saved_style_and_portable_file_round_trip_without_overwriting(tmp_path):
    config, _, _ = demo(tmp_path / 'one')
    styles.apply(config, styles.BUILTINS['paper'])
    library = styles.save(config, 'My launch')
    assert styles.library(library)['my-launch']['caption'] == styles.BUILTINS['paper']['caption']
    before = library.read_bytes()
    with pytest.raises(ValueError, match='already'):
        styles.save(config, 'My launch')
    assert library.read_bytes() == before
    portable = tmp_path / 'launch.toml'
    styles.save(config, 'Portable launch', output=portable)
    second, _, _ = demo(tmp_path / 'two')
    styles.apply(second, styles.resolve(str(portable), second.parent))
    assert styles.signature(styles.snapshot(second)) == styles.signature(styles.snapshot(config))
    with pytest.raises(ValueError, match='exists'):
        styles.save(config, 'Launch', output=portable)
    with pytest.raises(ValueError, match='source file'):
        styles.save(config, 'Launch', output=config, replace=True)
    with pytest.raises(ValueError, match='project style library'):
        styles.save(config, 'Launch', output=library, replace=True)
    assert library.read_bytes() == before


@pytest.mark.parametrize('change', [
    {'frame_enabled': 'yes'}, {'caption': {'margin': float('nan')}}, {'caption': {'font': '../font.ttf'}},
    {'card': {'background': ['red']}}, {'frame': {'padding': True}}, {'frame': {'bar': 1}},
    {'frame': {'bar_color': '#00000000'}}, {'caption': {'background': 'not-a-colour'}},
    {'beat': [{'caption': 'replace the story'}]},
])
def test_invalid_or_out_of_scope_style_changes_nothing(tmp_path, change):
    config, board, edit = demo(tmp_path)
    before = board.read_bytes(), edit.read_bytes()
    with pytest.raises(ValueError):
        styles.apply(config, {**copy.deepcopy(styles.BUILTINS['focus']), **change})
    assert (board.read_bytes(), edit.read_bytes()) == before


def test_validation_happens_before_any_file_is_replaced(tmp_path):
    config, board, edit = demo(tmp_path)
    edit.write_text('schema_version = 1\n')
    before = board.read_bytes(), edit.read_bytes()
    with pytest.raises(ValueError, match='at least one part'):
        styles.apply(config, styles.BUILTINS['paper'])
    assert (board.read_bytes(), edit.read_bytes()) == before
    assert not list(tmp_path.glob('*.studio'))


def test_later_write_failure_rolls_back_only_our_own_changes(tmp_path, monkeypatch):
    config, board, edit = demo(tmp_path)
    before = board.read_bytes(), edit.read_bytes()
    original = Path.replace
    def fail(self, target):
        if target == edit:
            raise OSError('simulated edit replacement failure')
        return original(self, target)
    monkeypatch.setattr(Path, 'replace', fail)
    with pytest.raises(OSError, match='simulated'):
        styles.apply(config, styles.BUILTINS['midnight'])
    assert (board.read_bytes(), edit.read_bytes()) == before


def test_concurrent_editor_change_is_preserved(tmp_path, monkeypatch):
    config, board, edit = demo(tmp_path)
    original, edit_before = styles.save_many, edit.read_bytes()
    external = '# an external edit\n' + board.read_text()
    def change_then_save(changes, before):
        board.write_text(external)
        return original(changes, before)
    monkeypatch.setattr(styles, 'save_many', change_then_save)
    with pytest.raises(ValueError, match='project changed'):
        styles.apply(config, styles.BUILTINS['paper'])
    assert board.read_text() == external and edit.read_bytes() == edit_before


def test_an_external_edit_during_replacement_survives_rollback(tmp_path, monkeypatch):
    config, board, edit = demo(tmp_path)
    original, edit_before = Path.replace, edit.read_bytes()
    external = '# edited while the style was being applied\n'
    def edit_after_first_replace(self, target):
        result = original(self, target)
        if target == board:
            board.write_text(external)
        return result
    monkeypatch.setattr(Path, 'replace', edit_after_first_replace)
    with pytest.raises(ValueError, match='project changed'):
        styles.apply(config, styles.BUILTINS['paper'])
    assert board.read_text() == external and edit.read_bytes() == edit_before


@pytest.mark.browser
def test_studio_styles_save_import_undo_and_recut_the_verified_recording(tmp_path):
    from playwright.sync_api import sync_playwright
    from reshoot import review, web
    from reshoot.cli import main
    config, board, edit = demo(tmp_path)
    board.write_text(board.read_text().replace('1280x720@1', '960x540@1'))
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code == 0
    baseline, _ = review.read(tmp_path / 'latest')
    original_board, original_edit = board.read_bytes(), edit.read_bytes()
    original_checks = [b.get('expect') for b in story.load(board)['beat']]
    clean_hash = digest(baseline / 'takes/demo.clean.mp4')
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.locator('.styling > summary').click()
            stale = browser.new_page()
            stale.goto(url)
            with page.expect_navigation():
                page.click('[data-style=midnight]')
            assert page.locator('[data-style=midnight]').get_attribute('aria-pressed') == 'true'
            assert story.load(board)['beat'] == tomllib.loads(original_board.decode())['beat']
            stale.locator('.styling > summary').click()
            stale.click('[data-style=paper]')
            stale.wait_for_function("document.getElementById('save-error').textContent.includes('another tab')")
            assert styles.selected(config, styles.choices(tmp_path)) == 'midnight'
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert (board.read_bytes(), edit.read_bytes()) == (original_board, original_edit)
            with page.expect_navigation():
                page.click('[data-history=redo]')
            assert styles.selected(config, styles.choices(tmp_path)) == 'midnight'
            page.fill('#save-style input', 'My launch')
            with page.expect_navigation():
                page.click('#save-style button')
            assert page.locator('[data-style=my-launch]').count() == 1
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert not (tmp_path / 'styles.toml').exists()
            with page.expect_navigation():
                page.click('[data-history=redo]')
            assert (tmp_path / 'styles.toml').exists()
            library_before = (tmp_path / 'styles.toml').read_bytes()
            page.fill('#save-style input', 'My launch')
            page.click('#save-style button')
            page.wait_for_function("document.getElementById('save-error').textContent.includes('already')")
            assert (tmp_path / 'styles.toml').read_bytes() == library_before
            page.set_input_files('#import-style', {'name': 'bad.toml', 'mimeType': 'application/toml', 'buffer': b'caption = ['})
            page.wait_for_function("document.getElementById('save-error').textContent.includes('Invalid')")
            assert styles.selected(config, styles.choices(tmp_path)) == 'midnight'
            portable = styles.dumps({**styles.BUILTINS['paper'], 'name': 'Imported paper'}).encode()
            with page.expect_navigation():
                page.set_input_files('#import-style', {'name': 'paper.toml', 'mimeType': 'application/toml', 'buffer': portable})
            assert styles.selected(config, styles.choices(tmp_path)) == 'paper'
            page.fill('.look [name=background]', 'nope')
            page.locator('.look [name=background]').press('Tab')
            page.wait_for_selector('[data-unsaved]')
            page.click('[data-style=focus]')
            page.wait_for_function("document.getElementById('save-error').textContent.includes('unsaved')")
            assert styles.selected(config, styles.choices(tmp_path)) == 'paper'
            page.fill('.look [name=background]', '#f4f1eaf2')
            page.locator('.look [name=background]').press('Tab')
            page.wait_for_function("!document.querySelector('[data-unsaved]')")
            with page.expect_navigation():
                page.click('[data-add-card=start]')
            # Frame and card backgrounds remain independently editable after applying a style.
            page.fill('.cut [name=frame_background]', '#d8d2c6')
            page.locator('.cut [name=frame_background]').press('Tab')
            page.wait_for_function("document.getElementById('current-style').textContent.includes('Custom')")
            assert tomllib.loads(edit.read_text())['style']['background'] == '#f4f1ea'
            assert tomllib.loads(edit.read_text())['frame']['background'] == '#d8d2c6'
            page.fill('.cut [name=frame_background]', '#e5dfd3')
            page.locator('.cut [name=frame_background]').press('Tab')
            page.wait_for_function("!document.querySelector('[data-unsaved]')")
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            assert 'a re-cut of' in page.locator('.status').inner_text()
            assert page.locator('#video').get_attribute('poster').endswith('/takes/demo-final.poster.png')
            assert page.locator('.cut .pending').is_hidden()
            assert page.locator('[data-style=paper]').get_attribute('aria-pressed') == 'true'
            page.locator('.styling').scroll_into_view_if_needed()
            video_box = page.locator('#video').bounding_box()
            assert video_box['y'] >= 0 and video_box['y'] + video_box['height'] <= 1000
            page.screenshot(path=str(tmp_path / 'styles-studio.png'))
            page.set_viewport_size({'width': 780, 'height': 900})
            assert page.locator('.watch').evaluate("el => getComputedStyle(el).position") == 'static'
            assert not errors
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    latest, report = review.read(tmp_path / 'latest')
    assert report['recut_from'] == baseline.name
    assert digest(latest / 'takes/demo.clean.mp4') == clean_hash
    assert [b.get('expect') for b in story.load(board)['beat']] == original_checks
    assert len(json.loads((latest / 'takes/demo.take.json').read_text())['beats']) == 4
    from PIL import Image
    with Image.open(latest / 'takes/demo-final.poster.png') as poster:
        assert all(abs(actual - expected) < 5 for actual, expected in zip(poster.convert('RGB').getpixel((0, 0)), (229, 223, 211)))
