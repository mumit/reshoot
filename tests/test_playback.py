"""Paired export playback uses only the selected run's media and bound cut maps."""
import json
import threading
import urllib.error
import urllib.request
from types import SimpleNamespace

import pytest
from reshoot import comparison, playback, project, review, studio, timeline
from reshoot.artifacts import digest
from test_comparison import recording, model, rebind


def rendered(run, segments=None, duration=8):
    root, report = run
    video = root / 'takes/final movie.mp4'
    video.write_bytes(b'synthetic exported video bytes')
    if segments is not None:
        timeline.write(video, segments, duration)
    for path in (video, video.with_suffix('.timeline.json')):
        if path.exists():
            report['files'].append({'path': str(path.relative_to(root)), 'sha256': digest(path)})
    rebind(run)
    return video


def segment(run, start=1, end=3, source_start=0, source_end=2):
    return {'source': str(run[0] / 'takes/demo.mp4'), 'source_start': source_start, 'source_end': source_end,
            'start': start, 'end': end}


def test_export_maps_trims_and_repeated_steps_in_each_cut(tmp_path):
    old, new = recording(tmp_path, 1), recording(tmp_path, 2)
    rendered(old, [segment(old, 1, 2, 0, 1), segment(old, 5, 7)])
    rendered(new, [segment(new, 0, 1, 1, 2)])
    result = model(tmp_path, old, new)
    previous, current = result['previous']['videos'][0], result['current']['videos'][0]
    assert previous['beats'] == {'notes/result': [[1, 2], [5, 7]]}
    assert current['beats'] == {'notes/result': [[0, 1]]}
    assert 'final%20movie.mp4' in previous['src'] and old[1]['id'] in previous['src']
    assert review.binding(*new) in current['src']


@pytest.mark.parametrize('bound', [False, True])
def test_missing_or_unbound_timeline_leaves_manual_video_playback_available(tmp_path, bound):
    old, new = recording(tmp_path, 1), recording(tmp_path, 2)
    rendered(old, [segment(old)])
    video = rendered(new)
    if not bound:
        timeline.write(video, [segment(new)], 8)  # exists, but not in the run's file list
    result = model(tmp_path, old, new)['current']['videos'][0]
    assert not result['beats'] and result['duration'] is None and 'no saved export timeline' in result['note']


def test_removed_step_has_no_fabricated_appearance_and_cards_do_not_map_to_steps(tmp_path):
    old, new = recording(tmp_path, 1), recording(tmp_path, 2, beats=('added',))
    rendered(old, [segment(old)])
    rendered(new, [{**segment(new, 0, 1), 'source': str(tmp_path / 'temporary-card.mp4')}, segment(new, 3, 5)])
    result = model(tmp_path, old, new)
    assert 'notes/result' not in result['current']['videos'][0]['beats']
    assert result['current']['videos'][0]['beats']['notes/added'] == [[3, 5]]


def test_invalid_bound_timeline_is_rejected_before_seeking(tmp_path):
    old, new = recording(tmp_path, 1), recording(tmp_path, 2)
    rendered(old, [segment(old)])
    rendered(new, [segment(new, source_start=2, source_end=2)])
    with pytest.raises(ValueError, match='invalid timeline segments'):
        model(tmp_path, old, new)


def test_pinned_video_http_supports_ranges_and_rejects_changed_media_or_scan(tmp_path):
    project.init(SimpleNamespace(directory=str(tmp_path), url=None, quiet=True))
    old, new = recording(tmp_path, 1), recording(tmp_path, 2)
    old_video = rendered(old, [segment(old)])
    rendered(new, [segment(new)])
    httpd, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        result = model(tmp_path, old, new)
        src = result['previous']['videos'][0]['src']
        recording(tmp_path, 3)
        request = urllib.request.Request(url + src, headers={'Range': 'bytes=0-3'})
        with urllib.request.urlopen(request) as response:
            assert response.status == 206 and response.read() == old_video.read_bytes()[:4]
            assert response.headers['Content-Range'].startswith('bytes 0-3/')
        with urllib.request.urlopen(urllib.request.Request(url + src, method='HEAD')) as response:
            assert response.status == 200 and response.read() == b''
        with pytest.raises(ValueError, match='exported video'):
            playback.media(tmp_path, old[1]['id'], review.binding(*old), 'takes/demo.mp4')
        old_video.write_bytes(b'changed export')
        with pytest.raises(urllib.error.HTTPError, match='409'):
            urllib.request.urlopen(url + src)
        scan = new[0] / 'review'
        scan.mkdir()
        (scan / 'report.json').write_text('{"policy":"new scan"}')
        with pytest.raises(urllib.error.HTTPError, match='409'):
            urllib.request.urlopen(url + result['current']['videos'][0]['src'])
    finally:
        httpd.shutdown(); httpd.server_close()
