"""Verify the tutorial's media and sources and make a local owner-review player."""
import html
import json
from pathlib import Path
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageStat
from reshoot import cut, review
from reshoot.artifacts import digest
from media import draw_text, save, stamp

ROOT=Path(__file__).resolve().parents[2]


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_chapters','-show_format','-of','json',str(path)]))


def player(folder, lesson, timeline, report):
    target=folder/'review';target.mkdir(exist_ok=True)
    chapters=json.loads((folder/'exports/tutorial-chapters.json').read_text())
    e=lambda value:html.escape(str(value),quote=True)
    buttons=''.join(f'<li><button data-at="{row["start"]:.3f}"><time>{stamp(row["start"])[:-4]}</time> {e(row["title"])}</button></li>' for row in chapters)
    transcript=[]
    previous=None
    scenes={row['id']:row for row in lesson['scene']}
    markdown=['# '+lesson['title'],'','Local synthetic narration. Synthetic notes data. Owner review pending.','']
    for row in timeline:
        scene=scenes[row['id']]
        if row['chapter']!=previous:
            transcript.append(f'<h2>{e(row["chapter"])}</h2>');markdown+=['## '+row['chapter'],''];previous=row['chapter']
        transcript.append(f'<article><h3><button data-at="{row["start"]:.3f}">{stamp(row["start"])[:-4]} · {e(row["title"])}</button></h3><p>{e(scene["text"])}</p></article>')
        markdown+=['### '+stamp(row['start'])[:-4]+' '+row['title'],'',scene['text'],'']
        if scene.get('command'):markdown+=['```text',scene['command'],'```','']
    (folder/'exports/transcript.md').write_text('\n'.join(markdown))
    sheets=''.join(f'<a href="{path.name}"><img src="{path.name}" alt="Encoded scene contact sheet {i+1}" loading="lazy"></a>' for i,path in enumerate(sorted(target.glob('contact-*.jpg'))))
    scan_links=''.join(f'<li><a href="../scan/{path.name}">Scan sheet {i+1}</a></li>' for i,path in enumerate(sorted((folder/'scan').glob('[0-9]*.jpg'))))
    waits=', '.join(e(row['title']) for row in timeline if row['wait_shortened'] or row.get('generation_wait_omitted')) or 'No recording waits were shortened.'
    native=folder/'demo/takes/runs'/report['native_run']
    for name in ('tutorial','first-demo'):
        (target/(name+'-player.html')).write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(name)} · reshoot</title><style>body{{margin:0;background:#101a29;color:white;font:16px system-ui}}video{{width:100%;max-height:100vh}}</style><video controls preload="metadata" src="../exports/{name}.mp4"><track default kind="captions" srclang="en" label="English" src="../exports/{name}.vtt"></video></html>''')
    native_exports=review.exports(native,json.loads((native/'run.json').read_text()))
    samplelinks=''.join(f'<li><a href="../demo/takes/runs/{native.name}/{e(path)}">{e(Path(path).name)}</a></li>' for path in native_exports)
    page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(lesson['title'])}</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#101a29;color:#eef4fc;font:17px/1.6 system-ui}}main{{max-width:1500px;margin:auto;padding:28px}}h1{{font-size:clamp(26px,4vw,46px);line-height:1.2}}a{{color:#8ee9cc}}button{{font:inherit;text-align:left;background:#1b2b43;color:#eef4fc;border:1px solid #39516f;border-radius:8px;padding:10px;cursor:pointer}}button:focus-visible,a:focus-visible{{outline:3px solid #8ee9cc}}.watch{{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:22px;align-items:start}}video{{width:100%;background:#060a12;border-radius:12px}}ol{{list-style:none;padding:0;margin:0;display:grid;gap:8px}}ol button{{width:100%}}time{{font-variant-numeric:tabular-nums;color:#8ee9cc}}.note{{border-left:4px solid #8ee9cc;padding:14px 18px;background:#1b2b43}}.sheets{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.sheets img{{width:100%}}article{{max-width:1000px}}article h3{{margin-bottom:4px}}article p{{margin-top:6px}}.links{{display:flex;gap:18px;flex-wrap:wrap}}@media(max-width:900px){{.watch,.sheets{{grid-template-columns:1fr}}main{{padding:16px}}}}</style></head><body><main>
<h1>{e(lesson['title'])}</h1><p>{e(lesson['subtitle'])} · {stamp(report['seconds'])[:-4]} · English synthetic narration · Pending owner review</p>
<p class="links"><a href="../exports/tutorial.mp4" download>Download workshop MP4</a><a href="first-demo-player.html">Watch the first-demo excerpt</a><a href="../exports/transcript.md">Written transcript</a><a href="../exports/tutorial.srt">SRT captions</a><a href="../exports/notes-demo-exports.zip">Download the demonstrated notes exports</a></p>
<div class="watch"><video id="video" controls preload="metadata" src="../exports/tutorial.mp4"><track default kind="captions" srclang="en" label="English" src="../exports/tutorial.vtt"></video><nav aria-label="Chapters"><ol>{buttons}</ol></nav></div>
<p class="note">This is a local review copy. The recorder and Studio use native automated input on real headless pages. All notes are synthetic. Speech uses the installed local voice. Command graphics are instructions. Detail views crop the original page. Browser audio is kept out of the workshop voice; the sample demo exports below contain their own narration. Nothing is accepted or published.</p>
<h2>Edits and verification</h2><p>Shortened or omitted recording waits: {waits}</p><p>The opening plays the finished native demo export made later in this workshop. The scan samples every 3 seconds, plus exact subtitle text. It does not inspect every video frame or approve the media. Read <a href="../scan/report.json">the scan report</a> and <a href="../audit.json">the mechanical audit</a>. Inspect all findings and watch both edits before deciding on acceptance.</p>
<details><summary>Scan sheets ({len(list((folder/'scan').glob('[0-9]*.jpg')))})</summary><ul>{scan_links}</ul></details>
<h2>Native demo files</h2><ul>{samplelinks}</ul><p>The final native run has {report['native_checks']} passing result checks and remains pending review.</p>
<h2>Encoded scene contact sheets</h2><div class="sheets">{sheets}</div>
<details><summary>Full chaptered transcript</summary>{''.join(transcript)}</details>
<script>const video=document.getElementById('video');document.querySelectorAll('[data-at]').forEach(button=>button.onclick=()=>{{video.currentTime=Number(button.dataset.at);video.play();video.scrollIntoView({{behavior:'smooth',block:'center'}});}});</script></main></body></html>'''
    (target/'index.html').write_text(page)


def audit(folder):
    timeline=json.loads((folder/'timeline.json').read_text());lesson=json.loads((folder/'lesson.json').read_text())
    recording=json.loads((folder/'recording.json').read_text())
    assert recording['status']=='recorded'
    assert recording.get('mode')!='rehearsal','A rehearsal is not a candidate video.'
    for path,value in recording['accepted_media'].items():assert digest(ROOT/path)==value,('Accepted media changed',path)
    assert len(timeline)==len(lesson['scene'])==len({row['id'] for row in timeline})
    result={'review_status':'pending','capture':'headless browser pages only','narration':'local synthetic speech',
            'scene_count':len(timeline),'native_run':recording['native_run'],'scan_coverage':'every 3 seconds plus exact subtitle text',
            'accepted_repository_media_unchanged':True,'exports':{},'scenes':[]}
    for name in ('tutorial','first-demo'):
        file=folder/'exports'/(name+'.mp4');info=probe(file)
        video=next(row for row in info['streams'] if row['codec_type']=='video')
        audio=next(row for row in info['streams'] if row['codec_type']=='audio')
        assert (video['width'],video['height'])==(1920,1080)
        assert any(row['codec_type']=='subtitle' for row in info['streams'])
        seconds=float(info['format']['duration'])
        av_delta=abs(float(video['duration'])-float(audio['duration']))
        assert av_delta<.25,(name,av_delta)
        cues=json.loads((folder/'exports'/(name+'-captions.json')).read_text())
        previous=0
        for cue in cues:
            assert previous<=cue['start']<cue['end']<=seconds+.1,(name,cue)
            previous=cue['end']-.002
        chapters=json.loads((folder/'exports'/(name+'-chapters.json')).read_text())
        assert len(info['chapters'])==len(chapters)
        assert abs(chapters[-1]['end']-seconds)<.3,(name,chapters[-1],seconds)
        loudness=subprocess.run(['ffmpeg','-v','info','-i',str(file),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True).stderr
        mean=float(re.search(r'mean_volume: ([-.\d]+)',loudness)[1]);peak=float(re.search(r'max_volume: ([-.\d]+)',loudness)[1])
        assert -35<mean<-5 and peak<0,(name,mean,peak)
        result['exports'][name]={'seconds':seconds,'sha256':digest(file),'bytes':file.stat().st_size,
            'chapters':len(chapters),'captions':len(cues),'av_delta_seconds':av_delta,'mean_dbfs':mean,'peak_dbfs':peak}
    result['seconds']=result['exports']['tutorial']['seconds']
    target=folder/'review';target.mkdir(exist_ok=True)
    for group in range((len(timeline)+5)//6):
        sheet=Image.new('RGB',(1600,1530),'#e7edf5');draw=ImageDraw.Draw(sheet)
        for n,row in enumerate(timeline[group*6:group*6+6]):
            x,y=(n%2)*800,(n//2)*510
            at=min(row['end']-.2,row['start']+(row['end']-row['start'])*.55)
            frame=target/(row['id']+'.png')
            cut.ff('-ss',at,'-i',folder/'exports/tutorial.mp4','-frames:v','1',frame)
            image=Image.open(frame).convert('RGB')
            assert max(ImageStat.Stat(image).stddev)>12,('Blank frame',row['id'])
            sheet.paste(image.resize((760,428),Image.Resampling.LANCZOS),(x+20,y+12))
            # A compact overview; per-scene PNGs above retain the original 1080p geometry.
            draw_text(draw,(x+20,y+456),row['title'],22,'#101a29',width=760)
            result['scenes'].append({'id':row['id'],'frame_at':at,'wait_shortened':row['wait_shortened']})
        sheet.save(target/f'contact-{group+1:02}.jpg',quality=94)
    native,native_report=review.read(folder/'demo/latest')
    assert native_report['mode']=='final' and native_report['ok'] and native_report['expectations_status']=='passed'
    assert native_report['review_status']=='pending'
    result['native_checks']=native_report['expectations_count']
    successful=[];failed=[]
    for path in (folder/'demo/takes/runs').glob('*/run.json'):
        report=json.loads(path.read_text())
        assert report.get('review_status')!='accepted'
        (successful if report['ok'] else failed).append(report['id'])
    assert failed,'The lesson must preserve its actual failed refresh.'
    result.update(native_successful_runs=successful,native_failed_runs=failed)
    command=[sys.executable,'-m','reshoot.cli','check',str(folder/'exports/tutorial.mp4'),str(folder/'exports/first-demo.mp4'),
             '--review',str(folder/'scan'),'--every','3','--text-file',str(folder/'exports/tutorial.srt'),'--text-file',str(folder/'exports/first-demo.srt')]
    with (folder/'privacy-scan.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
    result['scan']=json.loads((folder/'scan/report.json').read_text())
    save(folder/'audit.json',result)
    player(folder,lesson,timeline,result)
    print('Audit passed. Owner review remains pending:',folder/'review/index.html',flush=True)
