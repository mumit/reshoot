"""Starting recipes tune presentation while preserving the task and reversible source edits."""
import json
import threading
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import create, project, recipes, story, studio
from reshoot.workspace import History


def setup(folder):
    project.init(SimpleNamespace(directory=str(folder), url=None, quiet=True))
    return [folder / name for name in ('reshoot.toml', 'storyboard.toml', 'edit.toml')]


@pytest.mark.parametrize('key', list(recipes.CATALOG))
def test_recipe_changes_presentation_but_preserves_task_and_undo(tmp_path, key):
    config, board, edit = setup(tmp_path)
    board.write_text(board.read_text() + '\n# keep the task explanation\n')
    original = {p: p.read_bytes() for p in (config, board, edit)}
    task = story.load(board)
    history = History(original)
    history.change(lambda: recipes.apply(config, key, 'A useful notes task', expected=history.snapshot()))
    changed = story.load(board)
    assert [b['id'] for b in changed['beat']] == [b['id'] for b in task['beat']]
    for before, after in zip(task['beat'], changed['beat']):
        assert {k:v for k,v in before.items() if k != 'hold'} == {k:v for k,v in after.items() if k != 'hold'}
    assert '# keep the task explanation' in board.read_text()
    cut = tomllib.loads(edit.read_text())
    assert cut['part'][1 if key != 'feature' else 0]['take'] == 0
    assert cut.get('export', []) == recipes.CATALOG[key]['exports']
    if key == 'walkthrough':
        assert tomllib.loads(config.read_text())['check']['sources'] == ['takes/demo-final.mp4']
    history.move('undo')
    assert all(p.read_bytes() == value for p, value in original.items())
    history.move('redo')
    assert story.load(board) == changed


def test_recipe_preserves_existing_cards_and_cut_ranges(tmp_path):
    config, board, edit = setup(tmp_path)
    studio.edit_cut(edit, config, {'add_card': 'start', 'text': 'The existing opening'})
    before = tomllib.loads(edit.read_text())['part']
    result = recipes.apply(config, 'release', 'A different proposed opening')
    assert not result['cards_added']
    assert tomllib.loads(edit.read_text())['part'] == before


def test_recipe_dry_run_and_invalid_or_stale_changes_keep_all_sources(tmp_path, capsys):
    paths = setup(tmp_path)
    original = {p: p.read_bytes() for p in paths}
    assert recipes.main(SimpleNamespace(operation='apply', recipe='release', project=str(tmp_path), title=None, dry_run=True)) == 0
    assert 'Would apply Release update' in capsys.readouterr().out
    with pytest.raises(ValueError):
        recipes.apply(tmp_path, {'invalid': 'key'})
    paths[1].write_text(paths[1].read_text() + '# external edit\n')
    external = paths[1].read_bytes()
    with pytest.raises(ValueError, match='project changed'):
        recipes.apply(tmp_path, 'feature', expected=original)
    assert paths[1].read_bytes() == external
    assert paths[0].read_bytes() == original[paths[0]] and paths[2].read_bytes() == original[paths[2]]


def test_recipe_rolls_back_its_writes_if_the_config_cannot_be_replaced(tmp_path, monkeypatch):
    paths = setup(tmp_path)
    original = {p: p.read_bytes() for p in paths}
    replace = Path.replace
    def fail(path, target):
        if target == paths[0]:
            raise OSError('simulated full disk')
        return replace(path, target)
    monkeypatch.setattr(Path, 'replace', fail)
    with pytest.raises(OSError, match='full disk'):
        recipes.apply(tmp_path, 'walkthrough')
    assert all(p.read_bytes() == value for p, value in original.items())


def test_recipe_cannot_remove_an_export_used_by_keep(tmp_path):
    config, _, _ = setup(tmp_path)
    config.write_text(config.read_text() + '\n[keep]\n"takes/demo-final-readme.gif" = "docs/demo.gif"\n')
    before = config.read_bytes()
    with pytest.raises(ValueError, match='used by .keep.'):
        recipes.apply(config, 'walkthrough')
    assert config.read_bytes() == before


def test_create_applies_recipe_once_then_preserves_edits_after_failure(tmp_path, monkeypatch):
    monkeypatch.setattr('reshoot.setup.check_project', lambda config, **_: {'ok': True})
    calls = []
    def preview(a):
        calls.append(a.config)
        if len(calls) == 1:
            raise ValueError('synthetic preview needs attention')
    monkeypatch.setattr('reshoot.run.preview', preview)
    args = SimpleNamespace(url=None, directory=str(tmp_path), recipe='walkthrough', title='Find a note',
                           size=None, no_studio=True, no_open=True, resume=False)
    assert create.main(args) == 2
    assert create.load(tmp_path)['recipe_applied']
    board = tmp_path / 'storyboard.toml'
    studio.edit(board, {'beat':'search', 'caption':'Keep these words', 'hold':3.2})
    args.resume, args.recipe, args.title = True, None, None
    assert create.main(args) == 0
    saved = story.load(board)['beat'][2]
    assert saved['caption'] == 'Keep these words' and saved['hold'] == 3.2
    assert create.load(tmp_path)['stage'] == 'done'
    assert len(tomllib.loads((tmp_path / 'edit.toml').read_text())['part']) == 3


@pytest.mark.browser
def test_create_with_recipe_then_apply_undo_and_record_another_in_the_studio(tmp_path, monkeypatch):
    from playwright.sync_api import sync_playwright, expect
    from reshoot import review, web
    from reshoot.cli import main
    from test_reshoot import free_port
    monkeypatch.setattr(project, 'free_port', free_port)
    with pytest.raises(SystemExit) as result:
        main(['create', '--directory', str(tmp_path), '--recipe', 'feature', '--no-studio'])
    assert result.value.code == 0
    first = review.read(tmp_path / 'latest')
    assert first[1]['expectations_count'] == 3
    paths = [tmp_path / name for name in ('reshoot.toml', 'storyboard.toml', 'edit.toml')]
    original = {p:p.read_bytes() for p in paths}
    task = story.load(paths[1])
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page(viewport={'width':1280, 'height':900})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.locator('.more-tools > summary').click()
            page.locator('[data-jump=recipe-panel]').click()
            page.check('#apply-recipe [value=walkthrough]')
            page.locator('#apply-recipe [name=title]').fill('Find the saved note')
            with page.expect_navigation():
                page.get_by_role('button', name='Apply recipe', exact=True).click()
            expect(page.locator('#journey')).to_have_attribute('data-phase', 'pending')
            expect(page.locator('#still-image')).to_be_visible(timeout=15000)
            assert not tomllib.loads(paths[2].read_text()).get('export')
            with page.expect_navigation():
                page.locator('[data-history=undo]').click()
            assert all(p.read_bytes() == value for p, value in original.items())
            with page.expect_navigation():
                page.locator('[data-history=redo]').click()
            with page.expect_navigation(timeout=120000):
                page.locator('[data-job=update]').click()
            second = review.read(tmp_path / 'latest')
            assert second[1]['id'] != first[1]['id'] and second[1]['expectations_count'] == 3
            assert second[1]['expectations_status'] == 'passed' and second[1]['review_status'] == 'pending'
            assert not any(name.endswith('.gif') for name in review.exports(*second))
            changed = story.load(paths[1])
            for before, after in zip(task['beat'], changed['beat']):
                assert before.get('action') == after.get('action') and before.get('expect') == after.get('expect')
            page.set_viewport_size({'width':390, 'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert not errors
            browser.close()
    finally:
        httpd.shutdown(); httpd.server_close()
