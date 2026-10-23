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


def sheets_fixture(root, flags=None):
    (root / 'review').mkdir()
    (root / 'review/key.json').write_text(json.dumps({'1-1': ['demo.mp4@0s', 'aaaa'], '1-2': ['demo.mp4@3s', 'bbbb']}))
    (root / 'review/flags.json').write_text(json.dumps(flags or {}))
    (root / 'review/report.json').write_text(json.dumps({'status': 'completed', 'policy': 'p', 'review': 'pending'}))


def accept_args(root, **options):
    return SimpleNamespace(**{'run_path': str(root), 'flagged': None, 'reject': None, 'yes': True, **options})


def test_accept_records_every_decision_and_scan_item_in_one_step(tmp_path):
    root = run_fixture(tmp_path / 'run')
    sheets_fixture(root)
    assert review.accept(accept_args(root)) == 0
    assert review.read(root)[1]['review_status'] == 'completed'
    assert json.loads((root / 'review/report.json').read_text())['review'] == 'completed'
    assert set(json.loads((root / 'review/checked.json').read_text())) == {'aaaa', 'bbbb'}
    decisions = json.loads((root / 'decisions.json').read_text())
    assert decisions['decisions'] == {'video': 'accepted'}
    assert decisions['binding'] == review.binding(root, review.read(root)[1])
    args = SimpleNamespace(run_path=str(root), previous=None, import_decisions=str(root / 'decisions.json'))
    assert review.main(args) == 0


def test_accept_requires_each_flagged_item_by_name(tmp_path, capsys):
    root = run_fixture(tmp_path / 'run')
    sheets_fixture(root, {'1-2': [['email', 'priv•••']]})
    assert review.accept(accept_args(root)) == 1
    assert '1-2' in capsys.readouterr().out
    assert not (root / 'decisions.json').exists() and not (root / 'review/checked.json').exists()
    with pytest.raises(ValueError, match='not on the current sheets'):
        review.accept(accept_args(root, flagged=['9-9']))
    assert review.accept(accept_args(root, flagged=['1-2'])) == 0
    assert json.loads((root / 'decisions.json').read_text())['decisions']['finding/1-2'] == 'accepted'


def test_rejected_item_fails_the_run_and_blocks_acceptance(tmp_path):
    root = run_fixture(tmp_path / 'run')
    sheets_fixture(root, {'1-2': [['email', 'priv•••']]})
    assert review.accept(accept_args(root, reject=['1-2'])) == 1
    assert review.read(root)[1]['review_status'] == 'failed'
    assert json.loads((root / 'decisions.json').read_text())['decisions']['finding/1-2'] == 'rejected'
    with pytest.raises(ValueError, match='rejected'):
        review.accept(accept_args(root, flagged=['1-2']))


def test_accept_needs_the_owner_and_a_passing_run(tmp_path, monkeypatch):
    root = run_fixture(tmp_path / 'run')
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
    with pytest.raises(ValueError, match='owner'):
        review.accept(accept_args(root, yes=False))
    assert not (root / 'decisions.json').exists()
    report = review.read(root)[1]
    report['ok'] = False
    (root / 'run.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='failed run'):
        review.accept(accept_args(root))


def test_run_aliases_pick_the_newest_matching_run(tmp_path, capsys):
    runs = tmp_path / 'demo/takes/runs'
    runs.mkdir(parents=True)
    for name, finished, ok, status in [('old', '2026-01-01T00:00:00+00:00', True, 'completed'),
                                       ('new', '2026-01-02T00:00:00+00:00', True, 'pending'),
                                       ('broken', '2026-01-03T00:00:00+00:00', False, 'pending')]:
        root = run_fixture(runs / name, name)
        report = review.read(root)[1]
        report.update(finished_at=finished, ok=ok, review_status=status)
        (root / 'run.json').write_text(json.dumps(report))
    assert review.read(tmp_path / 'demo/latest')[1]['id'] == 'new'
    assert review.read(runs / 'accepted')[1]['id'] == 'old'
    assert 'latest is run new' in capsys.readouterr().err
    assert review.listing(SimpleNamespace(project=str(tmp_path / 'demo/reshoot.toml'))) == 0
    rows = capsys.readouterr().out.splitlines()[1:]
    assert [row.split()[0] for row in rows] == ['broken', 'new', 'old']
    assert rows[1].endswith('latest') and rows[2].endswith('accepted')
    with pytest.raises(ValueError, match='no accepted run'):
        review.read(tmp_path / 'elsewhere/accepted')


def project_run(tmp_path, name='run'):
    """A run inside a project, as `reshoot run` lays it out, with one beat and its evidence frame."""
    root = tmp_path / 'demo/takes/runs' / name
    root.mkdir(parents=True)
    (root / 'takes/demo.evidence').mkdir(parents=True)
    Image.new('RGB', (8, 8), 'blue').save(root / 'takes/demo.evidence/search.png')
    (root / 'takes/demo.take.json').write_text(json.dumps({'story_id': 'notes', 'video': 'demo.mp4', 'beats': [
        {'id': 'search', 'status': 'passed', 'start': 0, 'end': 1, 'screenshot': 'demo.evidence/search.png'}]}))
    (root / 'takes/demo-final.mp4').write_bytes(b'synthetic media placeholder')
    files = [{'path': p, 'sha256': digest(root / p)} for p in
             ('takes/demo-final.mp4', 'takes/demo.take.json', 'takes/demo.evidence/search.png')]
    (root / 'run.json').write_text(json.dumps({'schema_version': 1, 'id': name, 'ok': True, 'files': files,
                                               'expectations_status': 'passed', 'expectations_count': 1}))
    return root


def test_accept_writes_a_record_that_later_runs_compare_against(tmp_path):
    root = project_run(tmp_path)
    assert review.accept(accept_args(root)) == 0
    record = tmp_path / 'demo/accepted'
    assert {str(p.relative_to(record)) for p in record.rglob('*') if p.is_file()} == {
        'run.json', 'decisions.json', 'takes/demo.take.json', 'takes/demo.evidence/search.png'}
    assert review.read(record)[0] == root.resolve()  # the run itself, with its media, while it is here
    __import__('shutil').rmtree(root)  # as in CI or a fresh clone
    assert review.read(record)[1]['record'] is True
    with pytest.raises(ValueError, match='record'):
        review.accept(accept_args(record))
    newer = project_run(tmp_path, 'newer')
    out = tmp_path / 'summary.md'
    review.compare(SimpleNamespace(previous=str(record), current=str(newer), out=str(tmp_path / 'c.json'), markdown=str(out)))
    text = out.read_text()
    assert '`notes/search` | matched | same | 0 | same | same |' in text and 'Result checks: passed (1)' in text


def test_export_replaces_media_and_writes_records_only_over_records(tmp_path):
    from reshoot import project
    root = project_run(tmp_path)
    media = tmp_path / 'docs/demo'
    args = SimpleNamespace(run_path=str(root), directory=str(media), file=['takes/demo-final.mp4'], replace=False,
                           record=str(tmp_path / 'demo/accepted'))
    assert project.export(args) == 0
    with pytest.raises(ValueError, match='--replace'):
        project.export(args)
    args.replace = True
    assert project.export(args) == 0 and (media / 'demo-final.mp4').exists()
    args.record = str(media)
    with pytest.raises(ValueError, match='not a run record'):
        project.export(args)


def test_run_writes_a_github_job_summary_with_the_failed_beat(tmp_path, monkeypatch):
    from reshoot import run
    summary = tmp_path / 'summary.md'
    monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(summary))
    monkeypatch.delenv('GITHUB_OUTPUT', raising=False)
    run.save({'ok': False, 'expectations_status': 'unverified', 'scan_status': 'skipped', 'review_status': 'pending',
              'errors': ["beat 'search' failed: type target {css = '#q'} matched 0 elements"]}, tmp_path / 'run.json')
    text = summary.read_text()
    assert '### reshoot: failed' in text and "beat 'search' failed" in text
