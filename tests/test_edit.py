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


def test_a_preset_sets_the_shape_and_checks_the_platforms_limits(tmp_path):
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=s=320x180:r=30:d=4', '-c:v', 'libx264', source)
    out = timeline.export(source, {'preset': 'x-square'})
    assert out.name == 'source-x-square.mp4' and cut.probe(out)[:2] == (720, 720)
    out = timeline.export(source, {'preset': 'readme', 'name': 'loop'})  # a field given overrides the preset's
    assert out.name == 'source-loop.gif'
    with pytest.raises(ValueError, match=r'does not fit X: its long side is 1920 px; X takes 32 to 1280'):
        timeline.export(source, {'preset': 'x', 'width': 1920, 'height': 1080})
    with pytest.raises(ValueError, match='unknown export preset'):
        timeline.export(source, {'preset': 'tiktok'})


def test_linkedin_refuses_a_video_shorter_than_three_seconds(tmp_path):
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=s=320x180:r=30:d=2', '-c:v', 'libx264', source)
    with pytest.raises(ValueError, match=r'it is 2\.0 s; LinkedIn takes 3 to 900 s'):
        timeline.export(source, {'preset': 'linkedin'})


def test_a_frame_puts_the_take_in_a_window_on_the_background(tmp_path):
    from PIL import Image
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=c=white:s=640x360:r=30:d=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', source)
    edit = tmp_path / 'edit.toml'
    edit.write_text('schema_version = 1\noutput = "final.mp4"\n[style]\nbackground = "#0000ff"\n[frame]\nshadow = false\n'
                    '[[part]]\ntake = 0\n[[part]]\ncard = "Blue"\nduration = 0.5\n')
    with pytest.raises(SystemExit) as result:
        main(['edit', str(edit), str(source)])
    assert result.value.code == 0
    out = tmp_path / 'final.mp4'
    assert cut.probe(out)[:2] == (640, 360)  # the same size: the page is shrunk into the window
    cut.ff('-ss', 0.5, '-i', out, '-frames:v', 1, tmp_path / 'still.png')
    im = Image.open(tmp_path / 'still.png').convert('RGB')
    r, g, b = im.getpixel((5, 5))
    assert b > 200 and r < 40 and g < 40  # the background from [style]
    assert min(im.getpixel((320, 200))) > 230  # the page, white, in the middle
    r, g, b = im.getpixel((150, 45))  # the window's title bar, above the page
    assert max(r, g, b) < 80 and abs(r - b) < 30
    with pytest.raises(ValueError, match='unknown frame option: shadows'):
        timeline.frame_style({'frame': {'shadows': True}})
