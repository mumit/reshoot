"""Narration auditions preserve the story; mix changes use the same verified recording."""
import array
import json
import math
import subprocess
import threading
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from reshoot import audio, cut, project, review, story, studio, voice
from reshoot.artifacts import digest
from reshoot.workspace import History

TONE = 'ffmpeg -loglevel error -y -f lavfi -i sine=frequency=800:duration=2.5 -f wav {out} && cat > /dev/null'


def setup(folder):
    project.init(SimpleNamespace(directory=str(folder), url=None, quiet=True))
    return folder / 'storyboard.toml', folder / 'edit.toml', folder / 'reshoot.toml'


@pytest.mark.parametrize('mix', [
    {'voice_volume': -1}, {'voice_volume': 2.1}, {'music_volume': 1.1}, {'music_volume': True},
    {'voice_volume': float('nan')}, {'duck': 'yes'}, {'unknown': .5},
])
def test_invalid_mix_is_not_saved(tmp_path, mix):
    board, edit, _ = setup(tmp_path)
    original = board.read_bytes(), edit.read_bytes()
    with pytest.raises(ValueError):
        audio.apply(tmp_path, {'beat': 'search', 'text': 'Do not partially save this.', 'mix': mix})
    assert (board.read_bytes(), edit.read_bytes()) == original


def test_narration_mix_and_undo_preserve_story_comments_and_checks(tmp_path):
    board, edit, config = setup(tmp_path)
    original_board, original_cut, original_config = story.load(board), tomllib.loads(edit.read_text()), config.read_bytes()
    board.write_text(board.read_text() + '\n[voice]\n"intro" = "Original line." # keep\n')
    history = History([board, edit, config])
    before = history.snapshot()
    audio.apply(tmp_path, {'beat': 'intro', 'text': '  A revised line.\n', 'engine': TONE,
                          'mix': {'voice_volume': .8, 'music_volume': .15, 'duck': False}}, expected=before)
    history.remember(before, history.snapshot())
    data = story.load(board)
    assert data['beat'] == original_board['beat'] and data['voice'] == {'intro': 'A revised line.'}
    assert '"intro" = "A revised line."  # keep' in board.read_text()
    assert data['voice_engine'] == TONE
    assert tomllib.loads(edit.read_text())['part'] == original_cut['part'] and config.read_bytes() == original_config
    assert audio.settings(tomllib.loads(edit.read_text())['audio']) == {'voice_volume': .8, 'music_volume': .15, 'duck': False}
    history.move('undo')
    assert history.snapshot() == before
    history.move('redo')
    audio.apply(tmp_path, {'beat': 'intro', 'text': ''})
    assert story.load(board)['voice'] == {}


def test_inline_voice_and_audio_tables_and_stale_edits(tmp_path):
    board, edit, _ = setup(tmp_path)
    board.write_text('voice = {intro = "Keep this."}\n' + board.read_text())
    edit.write_text('audio = {music_volume = 0.2}\n' + edit.read_text())
    audio.apply(tmp_path, {'beat': 'search', 'text': 'Find the note.', 'mix': {'voice_volume': .7}})
    assert story.load(board)['voice'] == {'intro': 'Keep this.', 'search': 'Find the note.'}
    assert tomllib.loads(edit.read_text())['audio'] == {'music_volume': .2, 'voice_volume': .7}
    before = {board.resolve(): board.read_bytes(), edit.resolve(): edit.read_bytes()}
    edit.write_text(edit.read_text() + '# external\n')
    with pytest.raises(ValueError, match='project changed'):
        audio.apply(tmp_path, {'beat': 'search', 'text': 'Stale change.'}, expected=before)
    assert board.read_bytes() == before[board.resolve()] and edit.read_text().endswith('# external\n')


def test_audition_reuses_the_recording_cache_without_launching_the_app(tmp_path, capsys):
    board, edit, config = setup(tmp_path)
    # Relative engine paths resolve from the project, as they do during a run.
    (tmp_path / 'tone.sh').write_text('#!/bin/sh\n' + TONE.replace('{out}', '"$1"') + '\n')
    audio.apply(tmp_path, {'beat': 'search', 'text': 'Find a note.', 'engine': 'sh tone.sh {out}'})
    originals = board.read_bytes(), edit.read_bytes(), config.read_bytes()
    path, seconds = audio.audition(tmp_path, 'search')
    assert seconds == pytest.approx(2.5, abs=.05) and path.parent == tmp_path / 'takes/voice-cache'
    assert 'speaking' in capsys.readouterr().out
    assert audio.audition(tmp_path, 'search') == (path, seconds)
    assert 'speaking' not in capsys.readouterr().out
    assert (board.read_bytes(), edit.read_bytes(), config.read_bytes()) == originals
    assert not (tmp_path / 'latest').exists()
    old_key = audio.audition_spec(tmp_path, 'search')['key']
    audio.apply(tmp_path, {'beat': 'search', 'text': 'A different line.'})
    with pytest.raises(ValueError, match='changed'):
        audio.audition(tmp_path, 'search', expected_key=old_key)
    assert audio.audition_spec(tmp_path, 'search')['key'] != old_key
    with pytest.raises(ValueError, match='Save a narration'):
        audio.audition(tmp_path, 'intro')


def test_studio_voice_selection_rejects_unlisted_commands_and_bad_types(tmp_path):
    import urllib.request
    board, edit, _ = setup(tmp_path)
    originals = board.read_bytes(), edit.read_bytes()
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        for engine in ([], 'touch unexpected {out}'):
            data = {'revision': History([tmp_path / 'reshoot.toml', board, tmp_path / 'styles.toml', edit]).revision(),
                    'change': {'engine': engine}}
            request = urllib.request.Request(url + 'audio', data=json.dumps(data).encode(),
                                             headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request) as response:
                result = json.load(response)
            assert result['ok'] is False and 'installed voice' in result['error']
        assert (board.read_bytes(), edit.read_bytes()) == originals
    finally:
        httpd.shutdown()
        httpd.server_close()


def amplitude(file, hz, start=1.3, seconds=.5):
    raw = subprocess.check_output(['ffmpeg', '-loglevel', 'error', '-ss', str(start), '-i', str(file), '-t', str(seconds),
                                   '-f', 'f32le', '-ac', '1', '-ar', '48000', '-'])
    values = array.array('f', raw)
    return 2 * abs(sum(value * complex(math.cos(i * 2 * math.pi * hz / 48000),
                                      math.sin(i * 2 * math.pi * hz / 48000)) for i, value in enumerate(values))) / len(values)


def test_encoded_mix_gains_ducking_mute_and_timing(tmp_path):
    video, line, music = [tmp_path / name for name in ['source.mp4', 'line.wav', 'music.wav']]
    cut.ff('-f', 'lavfi', '-i', 'color=size=160x90:rate=60:duration=6', *cut.ENC, video)
    cut.ff('-f', 'lavfi', '-i', 'sine=frequency=800:duration=1', line)
    cut.ff('-f', 'lavfi', '-i', 'sine=frequency=220:duration=2', music)
    track = cut.voice_track([(1, 1, 'Synthetic tone.', str(line))], tmp_path / 'track.wav', 6)
    flat = cut.add_audio(video, tmp_path / 'flat.mp4', voice=track, music=music, music_volume=1, duck=False)
    ducked = cut.add_audio(video, tmp_path / 'ducked.mp4', voice=track, music=music, music_volume=1)
    quiet = cut.add_audio(video, tmp_path / 'quiet.mp4', voice=track, music=music, music_volume=0, voice_volume=.5)
    assert amplitude(ducked, 220) < amplitude(flat, 220) * .5
    assert amplitude(quiet, 800) == pytest.approx(amplitude(flat, 800) * .5, rel=.08)
    assert amplitude(quiet, 220) < .001
    assert amplitude(quiet, 800, start=.3) < .001
    assert cut.duration(quiet) == pytest.approx(6, abs=.05)
    muted = cut.add_audio(video, tmp_path / 'muted.mp4', voice=track, voice_volume=0)
    assert amplitude(muted, 800) < .0001
    loud = tmp_path / 'loud.wav'
    cut.ff('-f', 'lavfi', '-i', 'sine=frequency=800:duration=6', '-af', 'volume=6', loud)
    limited = cut.add_audio(video, tmp_path / 'limited.mp4', voice=loud, voice_volume=2)
    decoded = subprocess.check_output(['ffmpeg', '-loglevel', 'error', '-i', str(limited), '-f', 'f32le', '-ac', '1', '-'])
    peak = max(abs(value) for value in array.array('f', decoded))
    assert .9 < peak < 1.05  # AAC can slightly overshoot the pre-encoding limiter ceiling.


@pytest.mark.browser
def test_studio_narration_audition_capture_and_mix_recut(tmp_path):
    from playwright.sync_api import sync_playwright
    from reshoot import web
    from reshoot.cli import main
    board, edit, config = setup(tmp_path)
    config.write_text(config.read_text().replace('scan = true', 'scan = false'))
    audio.apply(tmp_path, {'engine': TONE})
    original_beats = story.load(board)['beat']
    with pytest.raises(SystemExit) as result:
        main(['preview', str(config)])
    assert result.value.code == 0
    baseline, baseline_report = review.read(tmp_path / 'latest')
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            search = page.locator('.beat[data-beat=search]')
            page.locator('[data-select-step=search]').click()
            search.locator('.narration summary').click()
            search.locator('textarea').fill('Find the matching note.')
            page.click('[data-job=update]')
            assert 'unsaved' in page.locator('#save-error').inner_text()
            with page.expect_navigation():
                search.locator('.narration-form [type=submit]').click()
            assert story.load(board)['voice']['search'] == 'Find the matching note.'
            assert search.locator('.narration-pending').is_visible()
            with page.expect_navigation():
                page.click('[data-history=undo]')
            assert not story.load(board).get('voice')
            with page.expect_navigation():
                page.click('[data-history=redo]')
            assert search.locator('.narration').evaluate('el => el.open')
            search.locator('[data-audition]').click()
            page.wait_for_selector('#audition-player:not([hidden])', timeout=30000)
            assert 'Listen before updating' in page.locator('#job-title').inner_text()
            assert page.locator('body').get_attribute('data-run') == baseline_report['id']
            audition_url = page.locator('#audition-player').get_attribute('src')
            assert page.request.get(url + audition_url).status == 200
            assert page.request.get(url + 'auditions/../../reshoot.toml').status == 404
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            narrated, narrated_report = review.read(tmp_path / 'latest')
            assert 'recut_from' not in narrated_report and narrated_report['expectations_count'] == 3
            said = json.loads((narrated / 'takes/demo.voice.json').read_text())
            assert said[0]['seconds'] == pytest.approx(2.5, abs=.05)
            assert Path(said[0]['file']).name == Path(audition_url).name
            assert 'Find the matching note.' in (narrated / 'takes/demo-final.srt').read_text()
            assert search.locator('.narration-pending').count() == 0
            clean_hash = digest(narrated / 'takes/demo.clean.mp4')
            page.click('#video-tab')
            page.locator('.audio-controls > summary').click()
            mix = page.locator('.audio-mix')
            mix.locator('[name=voice_volume]').fill('50')
            mix.locator('[name=music_volume]').fill('10')
            mix.locator('[name=duck]').uncheck()
            with page.expect_navigation():
                mix.locator('[type=submit]').click()
            assert tomllib.loads(edit.read_text())['audio'] == {'voice_volume': .5, 'music_volume': .1, 'duck': False}
            with page.expect_navigation(timeout=120000):
                page.click('[data-job=update]')
            mixed, mixed_report = review.read(tmp_path / 'latest')
            assert mixed_report['recut_from'] == narrated.name and mixed_report['expectations_count'] == 3
            assert digest(mixed / 'takes/demo.clean.mp4') == clean_hash
            assert story.load(board)['beat'] == original_beats
            assert not errors
            page.screenshot(path=str(tmp_path / 'audio-studio.png'))
            # A failed or cancelled audition never replaces the displayed successful video.
            audio.apply(tmp_path, {'engine': 'false {out}'})
            page.reload()
            with page.expect_navigation():
                page.locator('[data-session=fresh]').click()
            page.click('#step-tab')
            search.locator('[data-audition]').click()
            page.wait_for_function("document.getElementById('job-title').textContent.includes('audition failed')", timeout=30000)
            assert page.locator('body').get_attribute('data-run') == mixed.name
            assert page.locator('#audition-player').is_hidden()
            audio.apply(tmp_path, {'engine': 'sleep 30; ' + TONE})
            page.reload()
            search.locator('[data-audition]').click()
            page.wait_for_selector('#cancel:visible')
            page.click('#cancel')
            page.wait_for_function("document.getElementById('job-title').textContent.includes('audition cancelled')", timeout=30000)
            assert page.locator('body').get_attribute('data-run') == mixed.name
            assert story.load(board)['voice']['search'] == 'Find the matching note.' and not errors
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
