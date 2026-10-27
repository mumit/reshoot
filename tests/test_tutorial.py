"""Workshop editing may shorten generation waits, never the demonstrated inputs."""
import importlib.util
import json
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('tutorial_media',Path(__file__).resolve().parents[1]/'examples/tutorial/media.py')
media=importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


def test_new_narration_preserves_original_capture_and_uses_recorded_commands(tmp_path):
    source=tmp_path/'original';source.mkdir()
    for name in ('raw','demo','exports'):(source/name).mkdir()
    (source/'raw/step.mp4').write_bytes(b'original synthetic footage')
    (source/'demo/run.json').write_text('{"review_status":"pending"}')
    (source/'exports/notes-demo-exports.zip').write_bytes(b'original local bundle')
    original={'voice':'say','scene':[{'id':'step','text':'Old words.','command':'reshoot create http://localhost:8765'}]}
    (source/'lesson.json').write_text(json.dumps(original))
    (source/'recording.json').write_text(json.dumps({'status':'recorded','native_run':'original-run','commit':'capture-commit'}))
    before={str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}
    lesson={'voice':'kokoro --voice af_heart','scene':[{'id':'step','text':'New words.','command':'different port'}]}
    target=tmp_path/'heart'
    edition=media.renarrate(source,target,lesson)
    assert edition['voice']==lesson['voice'] and edition['scene'][0]['text']=='New words.'
    assert edition['scene'][0]['command']==original['scene'][0]['command']
    assert (target/'raw/step.mp4').read_bytes()==before['raw/step.mp4']
    state=json.loads((target/'recording.json').read_text())
    assert state['native_run']=='original-run' and state['commit']=='capture-commit'
    assert state['renarrated_from']==str(source)
    assert {str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}==before
    with pytest.raises(ValueError,match='Scene order changed'):
        media.renarrate(source,tmp_path/'invalid',{'voice':'kokoro','scene':[{'id':'new'}]})
    assert not (tmp_path/'invalid').exists()


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


def test_neural_passage_uses_word_timing_without_detaching_punctuation(tmp_path, monkeypatch):
    from reshoot import cut, voice
    calls = []
    text = 'A connected explanation with enough words to reach the caption break before its punctuation.'
    def speak(passage, path, engine):
        calls.append(passage)
        cut.ff('-f','lavfi','-i','anullsrc=r=48000:cl=mono','-t','2',path)
        words = [{'text':text[:-1], 'start':.1,'end':1.6}, {'text':'.','start':1.6,'end':1.7}]
        path.with_suffix('.words.json').write_text(json.dumps(words))
        return 2
    monkeypatch.setattr(voice, 'speak', speak)
    lesson = {'voice':'kokoro','scene':[{'id':'sample','text':text}]}
    spoken = media.speech(tmp_path,lesson)['sample']
    assert calls == [text]
    assert len(spoken['cues']) == 1 and spoken['cues'][0]['text'] == text
    assert spoken['cues'][0]['start'] == pytest.approx(.3)
    assert spoken['cues'][0]['end'] == pytest.approx(1.9)
    media.speech(tmp_path,lesson)
    assert calls == [text]


def test_local_review_serves_seek_ranges_and_keeps_symlinks_inside_its_root(tmp_path):
    import http.server
    import threading
    import urllib.error
    import urllib.request
    from functools import partial
    module_spec=importlib.util.spec_from_file_location('tutorial_serve',Path(__file__).resolve().parents[1]/'examples/tutorial/serve.py')
    server_module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(server_module)
    root=tmp_path/'site';root.mkdir();(root/'clip.mp4').write_bytes(b'0123456789')
    outside=tmp_path/'outside.txt';outside.write_text('synthetic outside-root fixture')
    (root/'link.txt').symlink_to(outside)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),partial(server_module.MediaHandler,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/'
    try:
        for requested,content,interval in [('bytes=0-2',b'012','bytes 0-2/10'),('bytes=6-99',b'6789','bytes 6-9/10'),('bytes=-3',b'789','bytes 7-9/10')]:
            with urllib.request.urlopen(urllib.request.Request(url+'clip.mp4',headers={'Range':requested})) as response:
                assert response.status==206 and response.read()==content
                assert response.headers['Content-Range']==interval
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(urllib.request.Request(url+'clip.mp4',headers={'Range':'bytes=10-'}))
        assert error.value.code==416 and error.value.headers['Content-Range']=='bytes */10'
        with urllib.request.urlopen(url+'clip.mp4') as response:
            assert response.status==200 and response.read()==b'0123456789'
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(url+'link.txt')
        assert error.value.code==403
    finally:server.shutdown();server.server_close()


def test_long_chapters_keep_their_quicktime_track_with_subtitles_and_audio(tmp_path):
    import subprocess
    from reshoot.cut import ff
    (tmp_path/'edit').mkdir();(tmp_path/'exports').mkdir()
    # FFmpeg 9's automatic movie timescale can overflow a long chapter packet
    # while Nero metadata still makes ffprobe appear to have valid chapters.
    ff('-f','lavfi','-i','color=c=blue:s=16x16:r=1:d=150','-f','lavfi','-i','anullsrc=r=48000:cl=mono',
       '-t','150','-c:v','libx264','-preset','ultrafast','-c:a','aac',tmp_path/'edit/long.mp4')
    row={'id':'long','chapter':'A long chapter','start':0,'end':150}
    media.export(tmp_path,{'title':'Synthetic chapter fixture'},[row],
                 [{'start':1,'end':3,'text':'A synthetic chapter fixture.'}],'fixture',[row])
    result=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_chapters','-of','json',
                                              str(tmp_path/'exports/fixture.mp4')]))
    track=next(s for s in result['streams'] if s['codec_type']=='data' and s.get('codec_tag_string')=='text')
    assert float(track['duration'])>=149.9
    assert len(result['chapters'])==1 and float(result['chapters'][0]['end_time'])>=149.9


def test_workshop_export_brings_quiet_audio_to_a_listenable_level(tmp_path):
    import subprocess,re
    from reshoot.cut import ff
    (tmp_path/'edit').mkdir();(tmp_path/'exports').mkdir()
    ff('-f','lavfi','-i','color=c=blue:s=16x16:r=30:d=3',
       '-f','lavfi','-i','sine=frequency=440:duration=3',
       '-af','volume=0.01','-c:v','libx264','-preset','ultrafast','-c:a','aac',tmp_path/'edit/quiet.mp4')
    row={'id':'quiet','chapter':'Synthetic audio','start':0,'end':3}
    media.export(tmp_path,{'title':'Synthetic quiet tone'},[row],
                 [{'start':.5,'end':2,'text':'Synthetic quiet tone.'}],'fixture',[row])
    measured=subprocess.run(['ffmpeg','-v','info','-i',str(tmp_path/'exports/fixture.mp4'),
                             '-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True).stderr
    mean=float(re.search(r'mean_volume: ([-.\d]+)',measured)[1])
    assert -21<mean<-16
    cues=json.loads((tmp_path/'exports/fixture-captions.json').read_text())
    assert cues==[{'start':.5,'end':2,'text':'Synthetic quiet tone.'}]


@pytest.mark.browser
def test_filming_camera_keeps_controls_at_the_bottom_of_the_page(tmp_path):
    import asyncio
    from PIL import Image
    from playwright.async_api import async_playwright
    from reshoot import cut,web
    async def capture():
        async with async_playwright() as pw:
            chrome=await pw.chromium.launch(executable_path=web.find_chrome(),headless=True,
                     args=web.chrome_flags()+['--force-device-scale-factor=1','--window-size=1440,810'])
            try:
                context=await chrome.new_context(viewport={'width':1440,'height':810})
                page=await context.new_page()
                await page.set_content('<button style="position:fixed;left:0;bottom:0;width:200px;height:40px;background:red" '
                                       'onclick="this.style.background=\'rgb(0,255,0)\'">Bottom control</button>')
                camera=media.Camera(page);await camera.start()
                await page.locator('button').click();await asyncio.sleep(.5)
                await camera.stop(tmp_path/'page.mp4')
            finally:await chrome.close()
    asyncio.run(capture())
    cut.ff('-sseof','-0.1','-i',tmp_path/'page.mp4','-frames:v','1',tmp_path/'last.png')
    image=Image.open(tmp_path/'last.png').convert('RGB')
    assert image.size==(1440,810)
    red,green,blue=image.getpixel((10,790))
    assert green>200 and red<50 and blue<50


def test_long_cues_break_at_a_comma_that_still_fits(tmp_path, monkeypatch):
    from reshoot import cut, voice
    text = 'In this workshop, we turn one task in a web app into a short video, and a GIF you can put in the readme file.'
    def speak(passage, path, engine):
        cut.ff('-f','lavfi','-i','anullsrc=r=48000:cl=mono','-t','2',path)
        words = [{'text':word + ' ', 'start':n*.1, 'end':n*.1+.08} for n, word in enumerate(text.split())]
        path.with_suffix('.words.json').write_text(json.dumps(words))
        return 2
    monkeypatch.setattr(voice, 'speak', speak)
    cues = media.speech(tmp_path, {'voice':'kokoro','scene':[{'id':'opening','text':text}]})['opening']['cues']
    assert [cue['text'] for cue in cues] == ['In this workshop, we turn one task in a web app into a short video,',
                                             'and a GIF you can put in the readme file.']
