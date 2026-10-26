"""Workshop editing may shorten generation waits, never the demonstrated inputs."""
import importlib.util
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('tutorial_media',Path(__file__).resolve().parents[1]/'examples/tutorial/media.py')
media=importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


def test_long_actions_are_retained_when_there_is_no_generation_wait():
    assert media.ranges({'seconds':60,'wait':None},20)==[(0,60)]


@pytest.mark.parametrize('voice_seconds',[15,30,55])
def test_wait_edits_keep_the_original_action_intervals_and_capture_offset(voice_seconds):
    meta={'seconds':60,'wait':[11,56],'capture_offset':1}
    selected=media.ranges(meta,voice_seconds)
    assert selected[0][0]==0 and selected[-1][1]==60
    assert all(end>start for start,end in selected)
    if len(selected)==2:
        removed_start,removed_end=selected[0][1],selected[1][0]
        assert 10<removed_start<removed_end<55
        assert sum(end-start for start,end in selected)>=voice_seconds


def test_caption_rounding_carries_across_minute_boundaries():
    assert media.stamp(59.9998,True)=='00:01:00,000'
