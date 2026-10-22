import io
import json
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from reshoot import check, cut, review
from reshoot.artifacts import digest
from reshoot.cli import main


def run_fixture(root, name='run'):
    root.mkdir()
    media = root / 'demo.mp4'
    media.write_bytes(b'synthetic media placeholder')
    report = {'schema_version': 1, 'id': name, 'ok': True,
              'files': [{'path': 'demo.mp4', 'sha256': digest(media)}]}
    (root / 'run.json').write_text(json.dumps(report))
    return root


def test_review_rejects_changed_files_and_foreign_decisions(tmp_path):
    root = run_fixture(tmp_path / 'one')
    report = review.read(root)[1]
    decisions = {'run_id': report['id'], 'binding': review.binding(root, report), 'decisions': {'video': 'accepted'}}
    path = tmp_path / 'decisions.json'
    path.write_text(json.dumps(decisions))
    args = SimpleNamespace(run_path=str(root), previous=None, import_decisions=str(path))
    assert review.main(args) == 0
    assert review.read(root)[1]['review_status'] == 'completed'
    (root / 'demo.mp4').write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        review.main(args)


def test_policy_change_invalidates_decisions(tmp_path):
    root = run_fixture(tmp_path / 'one')
    report = review.read(root)[1]
    token = review.binding(root, report)
    (root / 'review').mkdir()
    (root / 'review/report.json').write_text(json.dumps({'policy': 'new', 'status': 'completed'}))
    assert review.binding(root, report) != token


def test_review_escapes_capture_text_and_compares_stable_ids(tmp_path):
    old = run_fixture(tmp_path / 'old', 'old')
    new = run_fixture(tmp_path / 'new', 'new')
    for root, actual in [(old, 'before'), (new, '</script><img src=x onerror=alert(1)>')]:
        (root / 'web.take.json').write_text(json.dumps({'story_id': 'search', 'beats': [{'id': 'result', 'status': 'passed', 'expectations': [{'actual': actual}]}]}))
    result = review.compare(SimpleNamespace(previous=str(old), current=str(new), out=None))
    assert result['beats'][0]['beat'] == 'search/result'
    assert result['beats'][0]['current']['expectations'][0]['actual'].startswith('</script>')
    assert review.main(SimpleNamespace(run_path=str(new), previous=str(old), import_decisions=None)) == 0
    text = (new / 'review.html').read_text()
    assert '</script><img' not in text
    assert '&lt;/script&gt;' in text


def test_review_comparison_displays_baseline_gifs_as_images(tmp_path):
    old = run_fixture(tmp_path / 'old', 'old')
    new = run_fixture(tmp_path / 'new', 'new')
    for root in (old, new):
        gif = root / 'demo loop.gif'
        Image.new('RGB', (16, 16), 'blue').save(
            gif, save_all=True, append_images=[Image.new('RGB', (16, 16), 'orange')],
            duration=100, loop=0)
        report = review.read(root)[1]
        report['files'].append({'path': gif.name, 'sha256': digest(gif)})
        (root / 'run.json').write_text(json.dumps(report))
    original_baseline = {p.name: digest(p) for p in old.iterdir()}
    original_report = (new / 'run.json').read_bytes()
    original_binding = review.binding(new, review.read(new)[1])

    assert review.main(SimpleNamespace(run_path=str(new), previous=str(old), import_decisions=None)) == 0

    class MediaElements(HTMLParser):
        def __init__(self):
            super().__init__()
            self.sources = {}

        def handle_starttag(self, tag, attrs):
            if tag in ('img', 'video'):
                self.sources[dict(attrs)['src']] = tag

    page = MediaElements()
    page.feed((new / 'review.html').read_text())
    assert page.sources['baseline/demo%20loop.gif'] == 'img'
    assert page.sources['demo%20loop.gif'] == 'img'
    assert page.sources['baseline/demo.mp4'] == 'video'
    assert page.sources['demo.mp4'] == 'video'
    assert digest(new / 'baseline/demo loop.gif') == digest(old / 'demo loop.gif')
    with Image.open(new / 'baseline/demo loop.gif') as copied:
        assert copied.n_frames == 2
    assert {p.name: digest(p) for p in old.iterdir()} == original_baseline
    assert (new / 'run.json').read_bytes() == original_report
    assert review.binding(new, review.read(new)[1]) == original_binding


@pytest.mark.skipif(not __import__('shutil').which('ffmpeg'), reason='needs ffmpeg')
def test_full_frames_preserve_brief_content_and_sample_times(tmp_path):
    video = tmp_path / 'flash.mp4'
    cut.ff('-f', 'lavfi', '-i', "color=black:s=160x100:r=10:d=4,drawbox=x=0:y=0:w=160:h=100:color=red:t=fill:enable=between(t\\,2.0\\,2.2)", '-c:v', 'libx264', video)
    quick = list(check.items([str(video)], every=3))
    full = list(check.items([str(video)], full=True))
    def red(frame):
        return Image.open(io.BytesIO(frame[1])).getpixel((80, 50))[0] > 150
    assert not any(red(f) for f in quick)
    assert any(red(f) for f in full)
    assert len(full) == 40
    assert quick[0][0].endswith('@0.000000s') and quick[1][0].endswith('@3.000000s')


def test_empty_manifest_is_not_completed_review(tmp_path):
    p = tmp_path / 'assets.json'
    p.write_text('[]')
    with pytest.raises(SystemExit) as result:
        main(['check', str(p), '--no-scan', '--review', str(tmp_path / 'review')])
    assert result.value.code == 2


def test_edit_map_tracks_trim_and_speed_and_subtitles(tmp_path):
    from reshoot import timeline
    source = tmp_path / 'source.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=s=160x100:r=10:d=4', '-c:v', 'libx264', source)
    source.with_suffix('.events.json').write_text(json.dumps([{'t': 1, 'kind': 'caption', 'text': 'Read the result'}, {'t': 3, 'kind': 'caption', 'text': None}]))
    trimmed = cut.trim(source, 1, 4, tmp_path / 'trim.mp4')
    fast = cut.speed(trimmed, 0, 2, 2, tmp_path / 'fast.mp4')
    mapping = timeline.read(fast)
    assert mapping['segments'][0]['source_start'] == 1
    assert mapping['segments'][0]['source_end'] == 3
    assert timeline.cues(fast) == [(0, 1, 'Read the result')]


@pytest.mark.skipif(not __import__('reshoot.scan', fromlist=['can_scan']).can_scan(), reason='needs OCR')
def test_full_scan_flags_brief_synthetic_email(tmp_path):
    from test_reshoot import text_image
    marker = tmp_path / 'marker.png'
    text_image(marker, 'Write to private.person@gmail.com')
    video = tmp_path / 'brief.mp4'
    cut.ff('-f', 'lavfi', '-i', 'color=black:s=1600x400:r=10:d=4', '-loop', 1, '-i', marker,
           '-filter_complex', "[0:v][1:v]overlay=enable='between(t,2,2.1)'", '-t', 4, '-c:v', 'libx264', video)
    with pytest.raises(SystemExit) as result:
        main(['check', str(video), '--full', '--review', str(tmp_path / 'review')])
    assert result.value.code == 1
    report = json.loads((tmp_path / 'review/report.json').read_text())
    assert report['samples'] == 40 and report['flagged'] > 0
    assert report['scan']['mode'] == 'full'


def test_review_requires_decisions_for_each_finding(tmp_path):
    root = run_fixture(tmp_path / 'run')
    (root / 'review').mkdir()
    (root / 'review/flags.json').write_text(json.dumps({'1-1': [['email', '•••']]}))
    report = review.read(root)[1]
    decisions = {'run_id': report['id'], 'binding': review.binding(root, report), 'decisions': {'video': 'accepted'}}
    path = tmp_path / 'decisions.json'
    path.write_text(json.dumps(decisions))
    args = SimpleNamespace(run_path=str(root), previous=None, import_decisions=str(path))
    review.main(args)
    assert review.read(root)[1]['review_status'] == 'pending'
    decisions['decisions']['finding/1-1'] = 'accepted'
    path.write_text(json.dumps(decisions))
    review.main(args)
    assert review.read(root)[1]['review_status'] == 'completed'


def test_subtitles_are_scanned_as_exact_text_without_exposing_words(tmp_path):
    path = tmp_path / 'final.srt'
    path.write_text('1\n00:00:01,000 --> 00:00:02,000\nprivate.person@gmail.com\n')
    key, flags = check.text_findings([str(path)], [], {}, 'policy')
    assert '00:00:01,000' in key['text-1'][0]
    assert flags['text-1'][0][0] == 'email'
    assert 'private.person@gmail.com' not in json.dumps(flags)
