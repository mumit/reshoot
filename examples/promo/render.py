"""Compose actual recorded pages and terminal footage into two distinct edits."""
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image,ImageDraw
from reshoot import cut

ROOT=Path(__file__).resolve().parents[2]
FOLDER=Path(sys.argv[1]).resolve()
OUT=FOLDER/'exports';OUT.mkdir(exist_ok=True)
WORK=FOLDER/'edit';WORK.mkdir(exist_ok=True)
STATE=json.loads((FOLDER/'recording.json').read_text())
BG='#0c121b';FG='#f4f6f8';MUTED='#b5c1d0';MINT='#91efce'
ENC=['-r','30','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-color_range','tv','-an']


def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n')


def text(draw,xy,words,size=40,fill=FG,weight=650):
    draw.text(xy,words,font=cut.font(size,weight),fill=fill,spacing=8)


def background(size=(1080,1350)):
    image=Image.new('RGB',size,BG);draw=ImageDraw.Draw(image)
    draw.line((60,108,size[0]-60,108),fill='#2b3949',width=2)
    text(draw,(60,42),'reshoot',34,MINT,800)
    return image,draw


def stage(first,second,number):
    image,draw=background()
    text(draw,(60,150),first,74)
    text(draw,(60,242),second,74,MINT)
    text(draw,(920,50),number,24,MUTED)
    return image,draw


def frame(video,at,name):
    path=WORK/(name+'.png')
    cut.ff('-ss',at,'-i',video,'-frames:v',1,path)
    return path


def still(image,name,seconds):
    png=WORK/(name+'.png');image.save(png)
    video=WORK/(name+'.mp4')
    cut.ff('-loop',1,'-i',png,'-t',seconds,'-vf','fps=30',*ENC,video)
    return video


def trim(video,start,end,name):
    path=WORK/(name+'.mp4')
    cut.ff('-ss',start,'-i',video,'-t',end-start,'-vf','fps=30',*ENC,path)
    return path


def place(image,video,x,y,width,name):
    png=WORK/(name+'-bg.png');image.save(png)
    path=WORK/(name+'.mp4')
    cut.ff('-loop',1,'-i',png,'-i',video,'-filter_complex',f'[1:v]scale={width}:-2:flags=lanczos,fps=30[v];[0:v][v]overlay={x}:{y}:shortest=1,format=yuv420p',*ENC,path)
    return path


def paste(image,path,box):
    with Image.open(path) as original:
        piece=original.convert('RGB').resize((box[2],box[3]),Image.Resampling.LANCZOS)
        image.paste(piece,(box[0],box[1]))


def main():
    old_root=(ROOT/STATE['runs']['v1']).parent
    new_root=(ROOT/STATE['runs']['v2']).parent
    old=old_root/'takes/notes.mp4';new=new_root/'takes/notes.mp4'
    old_duration,new_duration=cut.duration(old),cut.duration(new)
    openings=[frame(old,.5,'old-opening'),frame(new,.5,'new-opening')]
    endings=[frame(old,old_duration-.3,'old-ending'),frame(new,new_duration-.3,'new-ending')]
    for path in openings+endings:
        with Image.open(path) as im: assert im.size==(960,828)

    hook,draw=stage('Your UI changed.','Update your demo.','01')
    initial_hook=None
    for index,(path,label,ink) in enumerate(zip(openings,['BEFORE','AFTER UI UPDATE'],[MUTED,MINT])):
        y=390+index*470
        text(draw,(60,y),label,25,ink)
        if index==1:initial_hook=hook.copy()
        with Image.open(path) as im:hook.paste(im.crop((0,0,960,390)),(60,y+47))
    initial_hook.save(WORK/'01-hook-before.png');hook.save(WORK/'01-hook-after.png')
    hook_clip=WORK/'01-hook.mp4'
    cut.ff('-loop',1,'-i',WORK/'01-hook-before.png','-loop',1,'-i',WORK/'01-hook-after.png',
           '-filter_complex','[1:v]format=rgba,fade=t=in:st=0.35:d=0.45:alpha=1[reveal];[0:v][reveal]overlay=0:0,format=yuv420p',
           '-t',2.8,*ENC,hook_clip)
    parts=[hook_clip]
    mapping=[{'section':'hook','seconds':2.8,'sources':[str(p.relative_to(ROOT)) for p in openings],'kind':'encoded-frame crops'}]

    terminal=FOLDER/'terminal-full.mp4'
    last=cut.last_change(terminal)
    assert 4<last<cut.duration(terminal)-1, 'Inspect terminal completion before choosing cut'
    # The typing is intact. Skip the actual generation wait and show its real result.
    first_end=3.0;tail_start=max(first_end,last-.25);tail_end=min(cut.duration(terminal),last+1.5)
    first=trim(terminal,0,first_end,'command-typing')
    tail=trim(terminal,tail_start,tail_end,'command-result')
    command_clip=WORK/'command-cut.mp4';cut.concat([first,tail],command_clip)
    command,draw=stage('One command.','A fresh recording.','02')
    text(draw,(60,433),'ACTUAL CLI RUN',25,MUTED)
    text(draw,(60,965),'Generation wait omitted',32,MUTED)
    text(draw,(60,1040),'Same storyboard. Result checks passed.',31)
    parts.append(place(command,command_clip,60,510,960,'02-command'))
    command_seconds=cut.duration(parts[-1])
    mapping.append({'section':'command','seconds':command_seconds,'source':str(terminal.relative_to(ROOT)),
                    'ranges':[[0,first_end],[tail_start,tail_end]],'generation_wait_omitted':True,'speed':1})

    app,draw=stage('Same task.','Updated UI.','03')
    text(draw,(60,1260),'Save a note. Find it again.',32,MUTED)
    parts.append(place(app,new,60,380,960,'03-updated-app'))
    mapping.append({'section':'updated-task','seconds':cut.duration(parts[-1]),'source':str(new.relative_to(ROOT)),
                    'range':[0,new_duration],'speed':1})

    comparison,draw=stage('Same story.','Fresh recording.','04')
    for index,(path,label,ink) in enumerate(zip(endings,['BEFORE','AFTER UI UPDATE'],[MUTED,MINT])):
        x=60+index*500
        text(draw,(x,470),label,23,ink)
        paste(comparison,path,(x,525,460,397))
    text(draw,(60,1040),'Same note saved.',48)
    text(draw,(60,1110),'Same search result.',48,MINT)
    text(draw,(60,1230),'Verified in both recordings.',29,MUTED)
    parts.append(still(comparison,'04-comparison',3.5))
    mapping.append({'section':'comparison','seconds':3.5,'sources':[str(p.relative_to(ROOT)) for p in endings],'kind':'encoded-frame stills'})

    end,draw=background()
    text(draw,(60,400),'reshoot',140,MINT,850)
    text(draw,(60,610),'Demos that',72)
    text(draw,(60,700),'stay current.',72)
    draw.line((60,865,1020,865),fill='#2b3949',width=2)
    text(draw,(60,925),'github.com/mumit/reshoot',42)
    text(draw,(60,1030),'Try the notes example.',36,MUTED)
    parts.append(still(end,'05-end',2.7))
    mapping.append({'section':'end','seconds':2.7,'kind':'authored end card'})
    social=OUT/'reshoot-social.mp4';cut.concat(parts,social)
    cues=[];cursor=0
    words=['Your UI changed. Update your demo.','One command. A fresh recording. Generation wait omitted.',
           'Same task. Updated UI. Save a note. Find it again.','Same story. Fresh recording.',
           'reshoot. Demos that stay current. github.com/mumit/reshoot']
    for row,phrase in zip(mapping,words):
        cues.append((cursor,cursor+row['seconds'],phrase));row['output_start']=cursor;cursor+=row['seconds']
    cut.write_srt(cues,social.with_suffix('.srt'))
    save(OUT/'social-edit.json',{'segments':mapping,'audio':'none','app_playback_speed':1,'generation_wait_labelled':True})

    # Align beat boundaries by holding the earlier completed beat's last frame.
    # Every action retains its original speed, and both source movies stay intact.
    native=[json.loads((r/'takes/notes.take.json').read_text()) for r in (old_root,new_root)]
    aligned=[[],[]];beat_alignment=[]
    for index,(before,after) in enumerate(zip(native[0]['beats'],native[1]['beats'])):
        assert before['id']==after['id']
        ranges=[(before['start'],before['end']),(after['start'],after['end'])]
        frames=[max(1,round((b-a)*30)) for a,b in ranges]
        target_frames=max(frames)
        beat_alignment.append({'beat':before['id'],'source_ranges':ranges,'output_frames':target_frames,'hold_frames':[target_frames-n for n in frames]})
        for side,source in enumerate((old,new)):
            a,b=ranges[side];target=WORK/f'readme-{side}-beat-{index}.mp4'
            cut.ff('-ss',a,'-i',source,
                   '-vf',f'trim=duration={b-a},setpts=PTS-STARTPTS,fps=30,tpad=stop_mode=clone:stop_duration=2',
                   '-frames:v',target_frames,*ENC,target)
            aligned[side].append(target)
    aligned_paths=[WORK/'readme-old-aligned.mp4',WORK/'readme-new-aligned.mp4']
    for clips,path in zip(aligned,aligned_paths):cut.concat(clips,path)
    span=sum(b['output_frames'] for b in beat_alignment)/30+1.2
    readme=OUT/'reshoot-readme.mp4'
    image,draw=background((1200,800))
    text(draw,(60,138),'Your app changed. Your demo can too.',46)
    text(draw,(40,217),'BEFORE',23,MUTED);text(draw,(620,217),'AFTER UI UPDATE',23,MINT)
    text(draw,(40,744),'Same storyboard. Fresh recording.',27,MUTED)
    image.save(WORK/'readme-bg.png')
    cut.ff('-loop',1,'-i',WORK/'readme-bg.png','-i',aligned_paths[0],'-i',aligned_paths[1],'-filter_complex',
           '[1:v]scale=540:466:flags=lanczos,fps=30,tpad=stop_mode=clone:stop_duration=2[a];'
           '[2:v]scale=540:466:flags=lanczos,fps=30,tpad=stop_mode=clone:stop_duration=2[b];'
           '[0:v][a]overlay=40:255:shortest=1[x];[x][b]overlay=620:255:shortest=1,format=yuv420p',
           '-t',span,*ENC,readme)
    cut.gif(readme,0,cut.duration(readme),OUT/'reshoot-readme.gif',fps=12,width=960)
    cut.write_srt([(0,span,'Your app changed. Your demo can too. Same storyboard. Fresh recording.')],readme.with_suffix('.srt'))
    save(OUT/'readme-edit.json',{'sources':[str(old.relative_to(ROOT)),str(new.relative_to(ROOT))],
        'speed':1,'end_hold_seconds':1.2,'layout':'side by side; beat boundaries aligned with end holds','beat_alignment':beat_alignment,
        'outputs':['reshoot-readme.mp4','reshoot-readme.gif']})
    save(FOLDER/'edit-result.json',{'social_seconds':cut.duration(social),'readme_seconds':cut.duration(readme),
        'terminal_last_change':last,'terminal_cut_ranges':[[0,first_end],[tail_start,tail_end]],
        'exports':str(OUT.relative_to(ROOT))})
    print(json.dumps(json.loads((FOLDER/'edit-result.json').read_text()),indent=2))


if __name__=='__main__':
    main()
