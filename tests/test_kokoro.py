"""Local neural voices use the existing audition and beat cache, without shell execution."""
import json
import wave

import pytest
from reshoot import audio, kokoro, voice
from test_audio import setup


@pytest.mark.parametrize('engine', ['kokoro --speed nan', 'kokoro --speed 0', 'kokoro --speed fast',
                                   'kokoro --voice ../../voice.pt', 'kokoro --voice',
                                   'kokoro --unknown 1', 'kokoro --speed 1 --speed 2'])
def test_bad_neural_settings_do_not_change_project(tmp_path, engine):
    board, edit, _ = setup(tmp_path)
    before = board.read_bytes(), edit.read_bytes()
    with pytest.raises(ValueError):
        audio.apply(tmp_path, {'beat': 'search', 'text': 'Keep this unsaved.', 'engine': engine})
    assert (board.read_bytes(), edit.read_bytes()) == before


def test_neural_audition_normalizes_audio_preserves_timings_and_reuses_cache(tmp_path, monkeypatch):
    setup(tmp_path)
    calls = []
    def render(text, out, engine):
        calls.append((text, engine))
        with wave.open(str(out), 'wb') as file:
            file.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
            file.writeframes(b'\x01\x00' * 24000)
        return [{'text': text, 'start': .1, 'end': .9}]
    monkeypatch.setattr(kokoro, 'render', render)
    audio.apply(tmp_path, {'beat': 'search', 'text': 'Find the matching note. Then hold the result.', 'engine': 'kokoro'})
    path, seconds = audio.audition(tmp_path, 'search')
    assert seconds == pytest.approx(1)
    with wave.open(str(path)) as file:
        assert (file.getframerate(), file.getnchannels()) == (48000, 1)
    assert json.loads(path.with_suffix('.words.json').read_text())[0]['start'] == .1
    assert audio.audition(tmp_path, 'search') == (path, seconds)
    assert len(calls) == 1 and 'Then hold' in calls[0][0]
    assert voice.cache_key(calls[0][0], 'kokoro') == voice.cache_key(calls[0][0], 'kokoro --voice af_heart --speed 1.0')
    assert voice.cache_key(calls[0][0], 'kokoro --voice af_bella') != path.stem
    assert voice.cache_key(calls[0][0], 'kokoro --speed 0.9') != path.stem
