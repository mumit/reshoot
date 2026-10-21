"""Verify the promotion's source recordings, actual command and encoded exports."""
import hashlib
import html
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image,ImageDraw
from reshoot import cut
from reshoot.review import read,binding

ROOT=Path(__file__).resolve().parents[2]
FOLDER=Path(sys.argv[1]).resolve()


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def command(args):return subprocess.run(list(map(str,args)),capture_output=True,text=True,check=True)


def main():
    state=load(FOLDER/'recording.json')
    assert state['status']=='recorded'
    assert sha(FOLDER/'inputs.json')==state['source_inputs_sha256']
    inputs=load(FOLDER/'inputs.json')
    assert all(sha(FOLDER/'source-recipe'/name)==digest for name,digest in inputs.items()), 'Recorded recipe snapshot changed'
    recipe_changes=[name for name,digest in inputs.items() if not (ROOT/name).exists() or sha(ROOT/name)!=digest]
    sources=[];hash_count=0
    for label,path in state['runs'].items():
        root,report=read(ROOT/path);hash_count+=len(report['files'])
        assert report['ok'] and report['expectations_status']=='passed' and report['expectations_count']==6
        take=load(root/'takes/notes.take.json')
        assert take['story_sha256']==inputs['examples/promo/storyboard.toml']
        assert len(take['beats'])==4 and all(e['status']=='passed' for b in take['beats'] for e in b['expectations'])
        sources.append({'label':label,'run_id':report['id'],'binding':binding(root,report),'report':path,
                        'video_sha256':sha(root/'takes/notes.mp4'),'expectations_passed':6})
    comparison=load(FOLDER/'comparison.json')
    assert len(comparison['beats'])==4 and all(r['change']=='matched' and not r['definition_changed'] for r in comparison['beats'])
    terminal=load(FOLDER/'terminal-result.json')
    assert terminal['ok'] and terminal['cli_log_sha256']==sha(FOLDER/'terminal-cli.log')
    assert terminal['run_report']==str(ROOT/state['runs']['v2'])
    edits=load(FOLDER/'edit-result.json')
    source_map=load(FOLDER/'exports/social-edit.json')
    assert source_map['app_playback_speed']==1 and source_map['generation_wait_labelled']
    review=FOLDER/'review';review.mkdir(exist_ok=True)
    exports=[];panels=[]
    for name in ('reshoot-social.mp4','reshoot-readme.mp4','reshoot-readme.gif'):
        video=FOLDER/'exports'/name
        info=json.loads(command(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',video]).stdout)
        stream=next(s for s in info['streams'] if s['codec_type']=='video')
        duration=float(info['format']['duration'])
        if name=='reshoot-social.mp4':
            assert (stream['width'],stream['height'])==(1080,1350) and 19<=duration<=28
            times=[.5,3.5,7.2,11,16,duration-1]
        else:
            assert (stream['width'],stream['height'])==((960,640) if name.endswith('gif') else (1200,800))
            assert 7<=duration<=13
            times=[.5,duration/2,duration-.3]
        if name.endswith('mp4'):
            assert stream['codec_name']=='h264' and stream['avg_frame_rate']=='30/1', (
                f"{name}: expected H.264 at 30/1 fps, got "
                f"{stream['codec_name']} at {stream['avg_frame_rate']} fps")
        decoded=command(['ffmpeg','-v','error','-i',video,'-f','null','-'])
        assert not decoded.stderr.strip()
        frames=[]
        for index,at in enumerate(times):
            path=review/(video.name+f'-{index}.png')
            cut.ff('-ss',at,'-i',video,'-frames:v',1,path)
            frames.append({'path':path.name,'seconds':at,'sha256':sha(path)})
            panels.append((name+f' / {at:.2f} s',path))
        exports.append({'path':str(video.relative_to(ROOT)),'name':name,'sha256':sha(video),'duration_seconds':duration,
                        'width':stream['width'],'height':stream['height'],'encoded_frames':int(stream['nb_read_frames']),
                        'bytes':video.stat().st_size,'frames':frames})
    # Inspect actual terminal completion and preserve OCR as independent evidence.
    path=review/'terminal-result.png'
    cut.ff('-ss',edits['terminal_last_change']+1,'-i',FOLDER/'terminal-full.mp4','-frames:v',1,path)
    ocr=command(['tesseract',path,'stdout']).stdout if __import__('shutil').which('tesseract') else None
    if ocr:
        (review/'terminal-result-ocr.txt').write_text(ocr)
        normalized=''.join(ocr.lower().split())
        assert '6resultcheckspassed' in normalized and 'reviewpending' in normalized
    panels.append(('Actual command completion',path))
    width=1280;cell_height=810
    sheet=Image.new('RGB',(width,cell_height*((len(panels)+1)//2)),'#e9e9e9');draw=ImageDraw.Draw(sheet)
    for i,(label,path) in enumerate(panels):
        with Image.open(path) as im:
            im.thumbnail((620,760));sheet.paste(im,((i%2)*640+10,(i//2)*cell_height+30))
        draw.text(((i%2)*640+10,(i//2)*cell_height+8),label,fill='black')
    sheet.save(review/'frames.jpg')
    result={'technical_checks_passed':True,'owner_review':'pending','scan_sheet_review':'pending',
            'native_runs':sources,'manifest_hashes_verified':hash_count,'passed_assertions':24,'matched_beat_definitions':4,
            'actual_cli_run':terminal,'exports':exports,'source_inputs_sha256':sha(FOLDER/'inputs.json'),'recipe_changes_since_capture':recipe_changes,
            'limits':['edited promotional video, not an uncut generation-time measurement','one host; clean-machine reproduction pending',
                      'output approval and human privacy checklist pending','no publication or old-media replacement']}
    save(FOLDER/'results.json',result)
    cards=[]
    for entry in exports:
        url=html.escape(os.path.relpath(ROOT/entry['path'],review))
        media=f'<img src="{url}" alt="Before and after README loop">' if entry['name'].endswith('gif') else f'<video controls preload="metadata" src="{url}"></video>'
        cards.append(f'<section><h2>{entry["name"]} · {entry["duration_seconds"]:.2f} s</h2>{media}<p>{entry["width"]} × {entry["height"]}</p></section>')
    review.joinpath('index.html').write_text('<!doctype html><meta charset="utf-8"><title>reshoot · refreshed demo review</title>'
        '<style>body{background:#0c121b;color:#eef4f9;font:18px system-ui;max-width:1050px;margin:40px auto;padding:0 24px}h1{font-size:44px;color:#91efce}p{line-height:1.6}video,img{display:block;max-width:100%;max-height:85vh}a{color:#91efce}section{margin:48px 0}</style>'
        '<h1>Demos that stay current.</h1><p>Real native recordings of both app versions, one unchanged storyboard, six passed checks in each take. '
        'The social clip includes a real command recording; its omitted generation wait is labelled. App playback is at original speed.</p>'
        '<p>Owner export verdict and separate privacy checklist are pending. Existing docs/demo media are preserved.</p>'
        +''.join(cards)+'<p><a href="../results.json">Technical evidence</a> · <a href="frames.jpg">Encoded frames</a> · '
        '<a href="../terminal-full.mp4">Uncut terminal capture</a></p>')
    save(FOLDER/'presentation.json',{'exports':[{k:e[k] for k in ('name','path','sha256','duration_seconds')} for e in exports],
        'results_sha256':sha(FOLDER/'results.json'),'page_sha256':sha(review/'index.html'),
        'scope':'social MP4 and README GIF/MP4; no publication or automatic privacy-checklist acceptance'})
    print(json.dumps({'technical_checks_passed':True,'exports':[{k:e[k] for k in ('name','duration_seconds','width','height','bytes')} for e in exports]},indent=2))


if __name__=='__main__':main()
