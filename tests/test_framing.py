"""Destination geometry is shared by MP4/GIF, and measured hints retain their limits and artifact binding."""
import json
import threading
import tomllib
from pathlib import Path
from types import SimpleNamespace
import pytest
from PIL import Image
from reshoot import cut, framing, project, readability, review, studio, timeline
from reshoot.artifacts import digest


def test_fit_and_crop_have_explicit_chroma_aligned_geometry():
    fit = framing.geometry((400, 200), 200, 200)
    assert (fit['scaled_width'], fit['scaled_height'], fit['x'], fit['y']) == (200, 100, 0, 50)
    left = framing.geometry((400, 200), 200, 200, 'crop', [0, .5])
    right = framing.geometry((400, 200), 200, 200, 'crop', [1, .5])
    assert left['x'] == 0 and right['x'] == -200
    assert framing.rect([200, 0, 200, 200], right) == [0, 0, 200, 200]


@pytest.mark.parametrize('settings', [
    {'focus': [float('nan'), .5]}, {'focus': [True, .5]}, {'focus': [1.1, .5]},
    {'fit': 'stretch'}, {'display_width': 0}, {'display_width': True}, {'width': 201},
])
def test_invalid_framing_preserves_project_files(tmp_path, settings):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    edit = tmp_path / 'edit.toml'
    before = edit.read_bytes()
    with pytest.raises(ValueError):
        framing.apply(tmp_path, 0, settings)
    assert edit.read_bytes() == before


def test_framing_edits_and_destination_changes_preserve_other_settings(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    edit, config = tmp_path / 'edit.toml', tmp_path / 'reshoot.toml'
    edit.write_text(edit.read_text() + 'min_reading = 0.5\nmax_bytes = 10000000\n')
    original = tomllib.loads(edit.read_text())
    board_before, config_before = (tmp_path / 'storyboard.toml').read_bytes(), config.read_bytes()
    framing.apply(tmp_path, 0, {'fit': 'crop', 'focus': [.3, .6], 'display_width': 390})
    after = tomllib.loads(edit.read_text())
    assert after['part'] == original['part']
    assert after['export'][0]['min_reading'] == .5 and after['export'][0]['max_bytes'] == 10000000
    assert '# an 800x450 GIF' in edit.read_text()
    assert (tmp_path / 'storyboard.toml').read_bytes() == board_before and config.read_bytes() == config_before
    studio.edit_cut(edit, config, {'export': 0, 'preset': 'x-portrait'})
    profile = tomllib.loads(edit.read_text())['export'][0]
    assert profile['fit'] == 'crop' and profile['focus'] == [.3, .6] and profile['display_width'] == 390
    assert profile['max_bytes'] == 10000000


def test_stale_framing_cannot_overwrite_or_capture_external_edits(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    board, edit = tmp_path / 'storyboard.toml', tmp_path / 'edit.toml'
    expected = {board.resolve(): board.read_bytes(), edit.resolve(): edit.read_bytes()}
    external = '# changed in another editor\n' + board.read_text()
    board.write_text(external)
    with pytest.raises(ValueError, match='project changed'):
        framing.apply(tmp_path, 0, {'fit': 'crop'}, expected=expected)
    assert board.read_text() == external and edit.read_bytes() == expected[edit.resolve()]


def test_recording_view_changes_only_the_first_browser_take_setting(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None))
    board, edit, config = tmp_path / 'storyboard.toml', tmp_path / 'edit.toml', tmp_path / 'reshoot.toml'
    before = board.read_bytes(), edit.read_bytes()
    framing.recording(tmp_path, '640x480@2')
    assert tomllib.loads(config.read_text())['take'][0]['size'] == '640x480@2'
    assert (board.read_bytes(), edit.read_bytes()) == before
    assert studio.view(tmp_path, studio.project(tmp_path)[2], config)['recording_size'] == '640x480@2'
    changed = config.read_bytes()
    with pytest.raises(ValueError):
        framing.recording(tmp_path, 'bad size')
    assert config.read_bytes() == changed


def coloured_source(tmp_path):
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=c=red:s=400x200:r=30:d=1', '-vf', 'drawbox=x=200:y=0:w=200:h=200:color=blue:t=fill',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', source)
    source.with_suffix('.take.json').write_text(json.dumps({'capture': {'zoom': False}, 'beats': [{
        'id': 'result', 'start': 0, 'end': 1, 'layout': {'viewport': [400, 200],
        'text': [{'box': [20, 20, 50, 20], 'font_px': 20}, {'box': [300, 20, 50, 20], 'font_px': 20}],
        'checked': [[300, 20, 50, 20]]}}]}))
    source.with_suffix('.captions.json').write_text(json.dumps({'captions': [{'beat': 'result', 'start': 0, 'end': 1,
        'text': 'Read the result', 'sub': None, 'layout': {'box': [100, 160, 200, 30], 'font_px': 20, 'smallest_font_px': 20}}]}))
    return source


def test_mp4_and_gif_use_the_same_crop_and_measured_result_bounds(tmp_path):
    source = coloured_source(tmp_path)
    for kind in ('mp4', 'gif'):
        for side, position in [('left', 0), ('right', 1)]:
            output = timeline.export(source, {'name': kind + side, 'format': kind, 'width': 100, 'height': 100,
                                             'fit': 'crop', 'focus': [position, .5], 'display_width': 160})
            if kind == 'mp4':
                still = tmp_path / (side + '.png')
                cut.ff('-ss', .5, '-i', output, '-frames:v', 1, still)
            else:
                still = output
            with Image.open(still) as image:
                r, g, b = image.convert('RGB').getpixel((50, 50))
            assert (r > 230 and b < 20) if side == 'left' else (b > 230 and r < 20)
            report = json.loads(output.with_suffix('.readability.json').read_text())
            kinds = {item['kind'] for item in report['issues']}
            assert 'caption-crop' in kinds
            assert ('result-crop' in kinds) == (side == 'left')
            assert report['sampled_holds'] == 1


def test_frame_spatial_scale_is_preserved_through_trims_and_exports(tmp_path):
    source = coloured_source(tmp_path)
    framed = cut.frame(source, tmp_path / 'framed.mp4')
    trimmed = cut.trim(framed, .2, 1, tmp_path / 'trimmed.mp4')
    spatial = timeline.read(trimmed)['segments'][0]['spatial']
    output = timeline.export(trimmed, {'name': 'small', 'width': 200, 'height': 100, 'display_width': 200})
    report = json.loads(output.with_suffix('.readability.json').read_text())
    assert report['metrics']['app_font_p10_px'] == pytest.approx(round(20 * spatial['sy'] * .5, 1), abs=.1)
    assert report['metrics']['caption_min_px'] < 10
    assert not {'caption-crop', 'result-crop'} & {item['kind'] for item in report['issues']}


def test_camera_zoom_and_source_clipping_are_reported_without_false_crop_advice(tmp_path):
    source = coloured_source(tmp_path)
    meta = json.loads(source.with_suffix('.take.json').read_text())
    meta['beats'][0]['layout']['checked'] = [[350, 0, 100, 20]]
    source.with_suffix('.take.json').write_text(json.dumps(meta))
    output = timeline.export(source, {'name': 'fit', 'width': 400, 'height': 200})
    report = json.loads(output.with_suffix('.readability.json').read_text())
    assert 'result-source-clip' in {item['kind'] for item in report['issues']}
    assert 'result-crop' not in {item['kind'] for item in report['issues']}
    meta['capture']['zoom'] = True
    source.with_suffix('.take.json').write_text(json.dumps(meta))
    output = timeline.export(source, {'name': 'zoom', 'width': 400, 'height': 200})
    report = json.loads(output.with_suffix('.readability.json').read_text())
    assert report['metrics']['app_font_p10_px'] is None and any('camera zoom' in note for note in report['notes'])


@pytest.mark.browser
def test_studio_destination_crop_undo_inspection_and_bound_measurements(tmp_path):
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
    clean_hash, board_before = digest(baseline / 'takes/demo.clean.mp4'), board.read_bytes()
    meta = json.loads((baseline / 'takes/demo.take.json').read_text())
    assert meta['beats'][0]['layout']['text']
    assert all(set(sample) == {'box', 'font_px'} for sample in meta['beats'][0]['layout']['text'])
    baseline_quality = json.loads((baseline / 'takes/demo-final.readability.json').read_text())
    assert 'result-source-clip' not in {item['kind'] for item in baseline_quality['issues']}
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
            with page.expect_navigation():
                page.select_option('.cut [name=add_export]', 'x-portrait')
            before = edit.read_bytes()
            form = page.locator('.export-framing[data-export="1"]')
            form.locator('[name=fit]').select_option('crop')
            page.click('[data-job=update]')
            page.wait_for_function("document.getElementById('save-error').textContent.includes('unsaved')")
            assert edit.read_bytes() == before
            guide = form.locator('.crop-guide')
            image = guide.locator('img')
            image.wait_for()
            page.wait_for_function("document.querySelector('.export-framing[data-export=\"1\"] img').naturalWidth > 0")
            box = guide.bounding_box()
            guide.click(position={'x': box['width'] * .65, 'y': box['height'] * .5})
            assert float(form.locator('[name=focus_x]').input_value()) > 60
            form.locator('[name=display_width]').fill('390')
            with page.expect_navigation():
                form.locator('button[type=submit]').click()
            saved = tomllib.loads(edit.read_text())['export'][1]
            assert saved['fit'] == 'crop' and saved['display_width'] == 390
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert edit.read_bytes() == before
            with page.expect_navigation():
                page.click('[data-history=redo]')
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            assert page.locator('#video').get_attribute('src').endswith('/takes/demo-final.mp4')
            assert page.locator('.shape').first.locator('a').get_attribute('href').endswith('/takes/demo-final.mp4')
            inspector = page.locator('button[data-inspect$="demo-final-x-portrait.mp4"]').first
            inspector.click()
            video = page.locator('#export-inspector video')
            assert video.evaluate('el => el.getBoundingClientRect().width') == 390
            page.locator('#export-inspector button').click()
            assert page.locator('.readability').count() == 3
            assert not errors
            page.locator('.styling').scroll_into_view_if_needed()
            page.screenshot(path=str(tmp_path / 'framing-studio.png'))
            first_recut = review.read(tmp_path / 'latest')
            with page.expect_navigation():
                page.select_option('.recording-view select', '640x480@2')
                page.locator('.recording-view button[type=submit]').click()
            assert page.locator('.recording-view select').input_value() == '640x480@2'
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert 'size' not in tomllib.loads(config.read_text())['take'][0]
            with page.expect_navigation():
                page.click('[data-history=redo]')
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            assert 'a re-cut of' not in page.locator('.status').inner_text()
            rerecorded, rerecorded_report = review.read(tmp_path / 'latest')
            assert rerecorded_report['expectations_count'] == 3
            assert json.loads((rerecorded / 'takes/demo.take.json').read_text())['capture']['css_width'] == 640
            assert board.read_bytes() == board_before and not errors
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    latest, report = first_recut
    assert report['recut_from'] == baseline.name and report['expectations_count'] == 3
    assert digest(latest / 'takes/demo.clean.mp4') == clean_hash and board.read_bytes() == board_before
    measured = latest / 'takes/demo-final-x-portrait.readability.json'
    quality = json.loads(measured.read_text())
    assert quality['display_width'] == 390 and quality['sampled_holds'] >= 3
    assert 'Framing and readability at 390' in (latest / 'review.html').read_text()
    assert 'caption-crop' in {issue['kind'] for issue in quality['issues']}
    measured.write_text('{}')
    with pytest.raises(ValueError):
        review.read(latest)
