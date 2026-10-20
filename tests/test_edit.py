import json
from pathlib import Path
import pytest
from reshoot import cut, timeline
from reshoot.cli import main


def test_edit_file_renders_profiles_and_remaps_subtitles(tmp_path):
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=s=160x100:r=10:d=2', '-c:v', 'libx264', source)
    source.with_suffix('.events.json').write_text(json.dumps([{'t': 0, 'kind': 'caption', 'text': 'A visible result'}, {'t': 2, 'kind': 'caption', 'text': None}]))
    edit = tmp_path / 'edit.toml'
    edit.write_text('''schema_version=1
output="final.mp4"
[[part]]
take=0
start=0.5
end=1.5
[[export]]
name="portrait"
width=100
height=160
fit="crop"
''')
    with pytest.raises(SystemExit) as result:
        main(['edit', str(edit), str(source)])
    assert result.value.code == 0
    assert cut.probe(tmp_path / 'final-portrait.mp4')[:2] == (100, 160)
    assert '00:00:00,000 --> 00:00:01,000' in (tmp_path / 'final.srt').read_text()
    assert (tmp_path / 'final-portrait.poster.png').exists()
    assert timeline.read(tmp_path / 'final.mp4')['segments'][0]['source_start'] == .5


def test_phone_caption_wraps_within_frame_width():
    from reshoot.zoom import caption_image
    image = caption_image('A longer caption that needs to wrap on a narrow phone screen', 'Read the result', 390, 390)
    assert image.width <= 390
    assert image.height > caption_image('Short', None, 390, 390).height


def test_declarative_cards_have_no_fake_source_and_shift_cues(tmp_path):
    from types import SimpleNamespace
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=s=320x180:r=10:d=1', '-c:v', 'libx264', source)
    source.with_suffix('.events.json').write_text(json.dumps([{'t': 0, 'kind': 'caption', 'text': 'Result'}, {'t': 1, 'kind': 'caption', 'text': None}]))
    spec = tmp_path / 'edit.toml'
    spec.write_text('schema_version=1\n[[part]]\ncard="Title"\nduration=1\n[[part]]\ntake=0\n')
    timeline.edit(SimpleNamespace(script=str(spec), args=[str(source)]))
    mapping = timeline.read(tmp_path / 'demo-final.mp4')
    assert mapping['segments'][0]['start'] == 1
    assert timeline.cues(tmp_path / 'demo-final.mp4') == [(1, 2, 'Result')]


def test_gif_profile_honours_both_dimensions(tmp_path):
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=s=160x100:r=10:d=1', '-c:v', 'libx264', source)
    result = timeline.export(source, {'name': 'portrait', 'format': 'gif', 'width': 100, 'height': 160})
    from PIL import Image
    assert Image.open(result).size == (100, 160)


def test_only_marked_verified_waits_are_trimmed_and_reading_is_kept(tmp_path):
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=s=320x180:r=10:d=4', '-c:v', 'libx264', source)
    metadata = {'beats': [{'id': 'result', 'status': 'passed', 'trim_wait': True, 'verified_at': 1, 'end': 4, 'min_reading': 1.5}]}
    source.with_suffix('.take.json').write_text(json.dumps(metadata))
    assert timeline.waiting_ranges(source, 0, 4) == [(2.5, 4)]
    source.with_suffix('.voice.json').write_text(json.dumps([{'t': 1.5, 'seconds': 1, 'text': 'Result', 'file': 'unused.wav'}]))
    assert timeline.waiting_ranges(source, 0, 4) == []
    source.with_suffix('.voice.json').unlink()
    spec = tmp_path / 'edit.toml'
    spec.write_text('schema_version=1\ntrim_waits=true\n[[part]]\ntake=0\n')
    from types import SimpleNamespace
    timeline.edit(SimpleNamespace(script=str(spec), args=[str(source)]))
    assert abs(cut.duration(tmp_path / 'demo-final.mp4')-2.5) < .1


def test_export_refuses_unreadably_short_caption(tmp_path):
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=s=160x100:r=10:d=1', '-c:v', 'libx264', source)
    source.with_suffix('.events.json').write_text(json.dumps([{'t': 0, 'kind': 'caption', 'text': 'Read this'}]))
    with pytest.raises(ValueError, match='min_reading'):
        timeline.export(source, {'name': 'short', 'min_reading': 2})
