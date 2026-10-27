"""Page-only footage, local speech, explicit wait edits and chaptered workshop exports."""
import asyncio
import base64
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import time

from PIL import Image, ImageDraw
from reshoot import cut, voice, web
from reshoot.artifacts import Frames

ENC = ['-r','30','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-color_range','tv']
BG, FG, MUTED, ACCENT = '#101a29', '#f2f5fa', '#acbed5', '#8ee9cc'
CURSOR = '''(() => {
 const install = () => {
  if (document.getElementById('tutorial-pointer')) return;
  const cursor=document.createElement('div'); cursor.id='tutorial-pointer';
  cursor.style.cssText='position:fixed;left:-50px;top:-50px;width:22px;height:22px;border:3px solid #2369ff;border-radius:50%;background:#ffffff88;pointer-events:none;z-index:2147483646;transform:translate(-50%,-50%);box-shadow:0 0 0 2px white';
  document.documentElement.append(cursor);
  addEventListener('mousemove', event => {cursor.style.left=event.clientX+'px';cursor.style.top=event.clientY+'px';},true);
  addEventListener('mousedown', () => {cursor.style.background='#2369ff';},true);
  addEventListener('mouseup', () => {cursor.style.background='#ffffff88';},true);
 }; if(document.readyState==='loading')addEventListener('DOMContentLoaded',install,{once:true});else install();
})();'''


def save(path, value):
    path = Path(path)
    pending = path.with_suffix(path.suffix + '.pending')
    pending.write_text(json.dumps(value, indent=2) + '\n')
    pending.replace(path)


def stamp(seconds, comma=False):
    value = round(seconds * 1000)
    hours, value = divmod(value, 3600000)
    minutes, value = divmod(value, 60000)
    seconds, millis = divmod(value, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{"," if comma else "."}{millis:03}'


def renarrate(source, target, lesson):
    """Start a separate narration edition, preserving the recorded inputs and evidence."""
    original = json.loads((source/'lesson.json').read_text())
    recording = json.loads((source/'recording.json').read_text())
    if recording.get('status') != 'recorded' or recording.get('mode') == 'rehearsal':
        raise ValueError('Use a completed, non-rehearsal tutorial recording.')
    if [s['id'] for s in original['scene']] != [s['id'] for s in lesson['scene']]:
        raise ValueError('Scene order changed; record fresh footage for the new lesson.')
    # Preserve commands and geometry from the captured version, including its app port.
    edition = {**original, 'voice':lesson['voice'],
               'scene':[{**old, 'text':new['text']} for old,new in zip(original['scene'],lesson['scene'])]}
    target.mkdir(parents=True)
    for name in ('raw','demo','app','before-app-change'):
        if (source/name).exists():shutil.copytree(source/name,target/name)
    (target/'exports').mkdir()
    shutil.copy2(source/'exports/notes-demo-exports.zip',target/'exports/notes-demo-exports.zip')
    save(target/'lesson.json',edition)
    save(target/'recording.json',{**recording,'renarrated_from':str(source),
         'narration_voice':edition['voice'],'narration_created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    return edition


def speech(folder, lesson):
    cache = folder / 'speech'
    cache.mkdir(exist_ok=True)
    result = {}
    for scene in lesson['scene']:
        target = cache / (scene['id'] + '.wav')
        signature = hashlib.sha256(('passage-v2\0' + lesson['voice'] + scene['text']).encode()).hexdigest()
        info = target.with_suffix('.json')
        if info.exists() and json.loads(info.read_text()).get('signature') == signature and target.exists():
            result[scene['id']] = json.loads(info.read_text()); continue
        neural = voice.engine_command(lesson['voice']).startswith('kokoro ')
        sentences = [scene['text']] if neural else re.split(r'(?<=[.!?])\s+', scene['text'])
        files, cues, at = [], [], .2
        for sentence in sentences:
            key = voice.cache_key(sentence, lesson['voice'])
            path = cache / (key + '.wav')
            length = cut.duration(path) if path.exists() else voice.speak(sentence, path, lesson['voice'])
            files.append(path)
            timing = path.with_suffix('.words.json')
            if neural and timing.exists():
                words = json.loads(timing.read_text())
                group = []
                for word in words:
                    group.append(word)
                    text = ''.join(item['text'] for item in group).strip()
                    if (len(text) >= 85 and word['text'][-1:].isspace()) or re.search(r'[.!?]$', text):
                        cues.append({'start':at+group[0]['start'], 'end':at+group[-1]['end'], 'text':text})
                        group = []
                if group:
                    cues.append({'start':at+group[0]['start'], 'end':at+group[-1]['end'],
                                 'text':''.join(item['text'] for item in group).strip()})
                at += length
                continue
            chunks, current = [], ''
            for word in sentence.split():
                if current and len(current) + len(word) > 116:
                    chunks.append(current); current = ''
                current += (' ' if current else '') + word
            if current: chunks.append(current)
            weight = sum(len(chunk) for chunk in chunks)
            start = at
            for chunk in chunks:
                end = start + length * len(chunk) / weight
                cues.append({'start':start, 'end':end, 'text':chunk})
                start = end
            at += length
        listing = cache / (scene['id'] + '.concat')
        listing.write_text(''.join(f"file '{path.as_posix()}'\n" for path in files))
        cut.ff('-f','concat','-safe','0','-i',listing,'-af','adelay=200,apad=pad_dur=0.8',
               '-ar','48000','-ac','1','-c:a','pcm_s16le',target)
        value = {'signature':signature,'seconds':cut.duration(target),'cues':cues}
        save(info, value); result[scene['id']] = value
        print('speech', scene['id'], round(value['seconds'],1), flush=True)
    save(folder / 'speech.json', result)
    return result


def draw_text(draw, xy, text, size, fill=FG, weight=600, width=None):
    font = cut.font(size, weight)
    if width:
        lines, current = [], ''
        for word in text.split():
            proposed = current + (' ' if current else '') + word
            if current and draw.textlength(proposed, font=font) > width:
                lines.append(current); current = word
            else: current = proposed
        if current: lines.append(current)
        text = '\n'.join(lines)
    draw.multiline_text(xy,text,font=font,fill=fill,spacing=12)


def plate(scene, chapter, detail=False):
    image = Image.new('RGB',(1920,1080),BG)
    draw = ImageDraw.Draw(image)
    draw_text(draw,(48,13),f'reshoot workshop  /  {chapter:02}  {scene["chapter"]}',25,ACCENT)
    if detail:
        draw_text(draw,(72,218),scene['title'],55,width=550)
        draw_text(draw,(72,450),scene['takeaway'],34,MUTED,width=550)
        draw_text(draw,(72,912),'Detail view · actual Studio footage',23,MUTED)
    else:
        draw_text(draw,(120,180),scene['title'],73,width=1640)
        if scene.get('command'):
            y = 400
            for line in scene['command'].splitlines():
                draw_text(draw,(120,y),line,35,ACCENT,500)
                y += 62
            y = max(y+55,670)
            draw_text(draw,(120,y),scene['takeaway'],37,MUTED,width=1630)
            draw_text(draw,(120,935),'Command / explanation graphic · Synthetic narration',23,MUTED)
        else:
            draw_text(draw,(120,435),scene['takeaway'],48,ACCENT,width=1580)
            draw_text(draw,(120,780),'Real notes app · Synthetic data · Synthetic narration',30,MUTED)
    return image


class Camera:
    def __init__(self, page):
        self.page, self.frames, self.offset = page, Frames(), None
        self.legacy = hasattr(page, 'cmd')
        self.tasks = set()

    async def start(self):
        self.began = time.monotonic()
        # Chrome emits no new screencast frame for an unchanged page. Capture
        # its actual state before starting, so every scene has a correct head.
        if self.legacy:
            shot=await self.page.cmd('Page.captureScreenshot',format='jpeg',quality=88)
        else:
            self.cdp = await self.page.context.new_cdp_session(self.page)
            shot=await self.cdp.send('Page.captureScreenshot',{'format':'jpeg','quality':88})
        self.frames.append((self.began,base64.b64decode(shot['data'])))
        if self.legacy:
            self.page.frames = self.frames; self.page.clock = None
            await self.page.cmd('Page.startScreencast',format='jpeg',quality=88,maxWidth=1440,maxHeight=810,everyNthFrame=2)
        else:
            def frame(event):
                at = event['metadata']['timestamp']
                if event['metadata']['deviceWidth']!=1440 or event['metadata']['deviceHeight']!=810:
                    self.bad_size=(event['metadata']['deviceWidth'],event['metadata']['deviceHeight'])
                if self.offset is None: self.offset = time.monotonic() - at
                self.frames.append((at+self.offset,base64.b64decode(event['data'])))
                task = asyncio.create_task(self.cdp.send('Page.screencastFrameAck',{'sessionId':event['sessionId']}))
                self.tasks.add(task); task.add_done_callback(self.tasks.discard)
            self.handler = frame
            self.cdp.on('Page.screencastFrame',frame)
            await self.cdp.send('Page.startScreencast',{'format':'jpeg','quality':88,'maxWidth':1440,'maxHeight':810,'everyNthFrame':2})
        await asyncio.sleep(.25)

    async def stop(self, path):
        await asyncio.sleep(.1)
        stopped = time.monotonic()
        if self.legacy:
            await self.page.cmd('Page.stopScreencast')
            self.page.frames = []
        else:
            await self.cdp.send('Page.stopScreencast')
            self.cdp.remove_listener('Page.screencastFrame',self.handler)
            if self.tasks: await asyncio.gather(*self.tasks)
            await self.cdp.detach()
        self.frames.append((stopped,None))
        if hasattr(self,'bad_size'):
            raise ValueError(f'Browser filming viewport was clipped: {self.bad_size}. Keep a 1440 by 810 window.')
        if len(self.frames) < 2: raise ValueError('No browser-page frames captured.')
        try:
            first, last = self.frames[0][0], self.frames[-1][0]
            save(path.with_suffix('.capture.json'),{'frames':len(self.frames)-1,'seconds':last-first,
                 'source':'headless browser page only','first_offset':first-self.began})
            await asyncio.to_thread(web.encode,self.frames,path,30,'1440:810',True)
            return first-self.began
        finally:
            self.frames.temp.cleanup()


class Shoot:
    def __init__(self, folder, lesson, spoken):
        self.folder, self.lesson, self.spoken = folder, lesson, spoken
        self.scenes = {scene['id']:scene for scene in lesson['scene']}
        self.raw = folder / 'raw'; self.raw.mkdir(exist_ok=True)
        self.active, self.events, self.wait = None, [], None

    def complete(self, key):
        return (self.raw / (key + '.json')).exists()

    def mark(self, kind, **data):
        self.events.append({'at':time.monotonic()-self.began,'kind':kind,**data})

    async def run(self, key, page=None, action=None):
        if self.complete(key): return
        self.active, self.events, self.wait = key, [], None
        self.began = time.monotonic()
        print('recording',key,flush=True)
        camera = Camera(page) if page else None
        if camera:
            await camera.start(); self.began = camera.began
        if action: await action(page)
        await asyncio.sleep(max(.35,self.spoken[key]['seconds']-(time.monotonic()-self.began)))
        offset = await camera.stop(self.raw / (key+'.mp4')) if camera else 0
        seconds = cut.duration(self.raw/(key+'.mp4')) if camera else self.spoken[key]['seconds']
        save(self.raw/(key+'.json'),{'id':key,'kind':'browser footage' if camera else 'instruction graphic',
             'seconds':seconds,'events':self.events,'wait':self.wait,'capture_offset':offset})
        print('recorded',key,round(seconds,1),flush=True)


def ranges(meta, audio_seconds):
    """Remove time only inside a recorded generation wait; native input keeps its original speed."""
    seconds, wait = meta['seconds'], meta.get('wait')
    extra = max(0,seconds-audio_seconds)
    if wait and extra > .8:
        offset = meta.get('capture_offset',0)
        start, end = wait[0]-offset+1, wait[1]-offset-1
        removed = min(extra,max(0,end-start))
        if removed > .8:
            return [(0,start),(start+removed,seconds)]
    return [(0,seconds)]


def compose(folder, lesson, spoken):
    work, exports = folder/'edit', folder/'exports'
    work.mkdir(exist_ok=True); exports.mkdir(exist_ok=True)
    chapters = list(dict.fromkeys(scene['chapter'] for scene in lesson['scene']))
    timeline, all_cues, at = [], [], 0
    for index, scene in enumerate(lesson['scene']):
        key = scene['id']; meta = json.loads((folder/'raw'/f'{key}.json').read_text())
        source=folder/'raw'/f'{key}.mp4'
        if key=='welcome':
            from reshoot import review
            native,report=review.read(folder/'demo/latest')
            source=native/next(name for name in review.exports(native,report) if name.endswith('.mp4'))
            native_seconds=cut.duration(source)
            begin=max(0,native_seconds-spoken[key]['seconds']-.1)
            meta={**meta,'kind':'finished demo export','seconds':spoken[key]['seconds'],
                  'source_file':str(source.relative_to(folder)),'source_start':begin,
                  'source_end':min(native_seconds,begin+spoken[key]['seconds']),
                  'hold_last_frame_seconds':max(0,spoken[key]['seconds']-(native_seconds-begin))}
        selected = ranges(meta,spoken[key]['seconds'])
        seconds = max(spoken[key]['seconds'],sum(end-start for start,end in selected))
        seconds = math.ceil(seconds*30)/30
        detail = scene.get('focus') == 'right' and meta['kind']=='browser footage'
        png = work/(key+'.png')
        image=plate(scene,chapters.index(scene['chapter'])+1,detail)
        if meta['kind'] in ('browser footage','finished demo export') and not detail:
            image=Image.new('RGB',(1920,1080),BG)
            draw_text(ImageDraw.Draw(image),(48,13),f'reshoot workshop  /  {chapters.index(scene["chapter"])+1:02}  {scene["chapter"]}',25,ACCENT)
        if key=='welcome':draw_text(ImageDraw.Draw(image),(1220,13),'Finished example · result held',25,ACCENT)
        if key=='done':draw_text(ImageDraw.Draw(image),(1260,13),'Preview generation wait omitted',25,ACCENT)
        elif len(selected)>1:draw_text(ImageDraw.Draw(image),(1330,13),'Recording wait shortened',25,ACCENT)
        image.save(png)
        target = work/(key+'.mp4')
        signature = hashlib.sha256(json.dumps([scene,meta,spoken[key],hashlib.sha256(Path(__file__).read_bytes()).hexdigest()],sort_keys=True).encode()).hexdigest()
        cache = target.with_suffix('.json')
        if not target.exists() or not cache.exists() or json.loads(cache.read_text())['signature'] != signature:
            inputs = ['-loop','1','-framerate','30','-i',png]
            filters = []
            if meta['kind'] in ('browser footage','finished demo export'):
                inputs += (['-ss',str(meta['source_start'])] if key=='welcome' else []) + ['-i',source]
                if len(selected)>1:
                    for n,(start,end) in enumerate(selected):
                        filters.append(f'[1:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[p{n}]')
                    filters.append('[p0][p1]concat=n=2:v=1:a=0[page]')
                else: filters.append('[1:v]setpts=PTS-STARTPTS[page]')
                if detail:
                    filters.append('[page]tpad=stop_mode=clone:stop_duration=60,crop=625:810:815:0,scale=-2:936:flags=lanczos[screen]')
                    filters.append('[0:v][screen]overlay=1070:60:shortest=1[v]')
                else:
                    filters.append('[page]tpad=stop_mode=clone:stop_duration=60,scale=1664:936:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,pad=1664:936:(ow-iw)/2:(oh-ih)/2:color=0x101a29[screen]')
                    filters.append('[0:v][screen]overlay=128:60:shortest=1[v]')
                visual = '[v]'
                audio_index=2
            else:
                visual='0:v';audio_index=1
            inputs += ['-i',folder/'speech'/f'{key}.wav']
            if filters: extra=['-filter_complex',';'.join(filters),'-map',visual]
            else: extra=['-map',visual]
            cut.ff(*inputs,*extra,'-map',f'{audio_index}:a','-af','volume=0.85,apad','-t',seconds,*ENC,
                   '-c:a','aac','-b:a','128k','-ar','48000','-ac','1','-movflags','+faststart',target)
            save(cache,{'signature':signature})
        row = {'id':key,'chapter':scene['chapter'],'title':scene['title'],'start':at,'end':at+seconds,
               'source':meta.get('source_file',f'raw/{key}.mp4' if meta['kind']=='browser footage' else 'authored instruction graphic'),
               'source_ranges':[(meta['source_start'],meta['source_end'])] if key=='welcome' else selected,
               'hold_last_frame_seconds':meta.get('hold_last_frame_seconds',0),
               'wait_shortened':len(selected)>1,'generation_wait_omitted':key=='done','detail_crop':detail}
        timeline.append(row)
        all_cues += [{**cue,'start':at+cue['start'],'end':at+cue['end']} for cue in spoken[key]['cues']]
        at += seconds
        print('composed',key,round(seconds,1),flush=True)
    save(folder/'timeline.json',timeline)
    save(folder/'captions.json',all_cues)
    export(folder,lesson,timeline,all_cues,'tutorial',timeline)
    excerpt = [row for row in timeline if row['id'] in ('command','write','save-check','search','search-check','done','first-preview')]
    export(folder,lesson,timeline,all_cues,'first-demo',excerpt)
    return timeline


def export(folder, lesson, timeline, cues, name, selected):
    listing = folder/'edit'/(name+'.concat')
    listing.write_text(''.join(f"file '{(folder/'edit'/(row['id']+'.mp4')).as_posix()}'\n" for row in selected))
    metadata = [';FFMETADATA1','title='+lesson['title'],'comment=Local synthetic narration; headless page recordings; pending owner review.']
    mapped, chapters, at = [], [], 0
    previous = None
    for row in selected:
        length = row['end']-row['start']
        if row['chapter'] != previous:
            chapters.append({'title':row['chapter'],'start':at,'end':at+length}); previous=row['chapter']
        else: chapters[-1]['end']=at+length
        mapped += [{**cue,'start':at+cue['start']-row['start'],'end':at+cue['end']-row['start']}
                   for cue in cues if row['start'] <= cue['start'] < row['end']]
        at += length
    for chapter in chapters:
        metadata += ['[CHAPTER]','TIMEBASE=1/1000',f'START={round(chapter["start"]*1000)}',
                     f'END={round(chapter["end"]*1000)}','title='+chapter['title']]
    meta = folder/'edit'/(name+'.ffmeta');meta.write_text('\n'.join(metadata)+'\n')
    srt = folder/'exports'/(name+'.srt')
    srt.write_text('\n\n'.join(f'{i}\n{stamp(c["start"],True)} --> {stamp(c["end"],True)}\n'+
                              '\n'.join(textwrap.wrap(c['text'],68)) for i,c in enumerate(mapped,1))+'\n')
    (folder/'exports'/(name+'.vtt')).write_text('WEBVTT\n\n'+re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})',r'\1.\2',srt.read_text()))
    audio_filter='aresample=async=1:first_pts=0'
    # Measure the exact edit, then normalize speech without changing its timing.
    normalizer='loudnorm=I=-18:TP=-2:LRA=11'
    measured=subprocess.run(['ffmpeg','-nostdin','-v','info','-f','concat','-safe','0','-i',str(listing),
                            '-vn','-af',normalizer+':print_format=json','-f','null','-'],
                            capture_output=True,text=True,check=True)
    levels=json.loads(re.search(r'\{\s*"input_i".*?\}',measured.stderr,re.S)[0])
    if math.isfinite(float(levels['input_i'])):
        fields={'measured_I':'input_i','measured_TP':'input_tp','measured_LRA':'input_lra',
                'measured_thresh':'input_thresh','offset':'target_offset'}
        audio_filter+=','+normalizer+':'+':'.join(key+'='+levels[value] for key,value in fields.items())
        save(folder/'exports'/(name+'-loudness.json'),{'target_lufs':-18,'true_peak_limit_db':-2,'measured':levels})
    cut.ff('-f','concat','-safe','0','-i',listing,'-i',meta,'-i',srt,'-map','0:v','-map','0:a','-map','2:0',
           '-map_metadata','1','-map_chapters','1','-c:v','copy','-c:a','aac','-b:a','160k',
           '-af',audio_filter,'-ar','48000','-c:s','mov_text','-movie_timescale','1000',
           '-movflags','+faststart',folder/'exports'/(name+'.mp4'))
    save(folder/'exports'/(name+'-chapters.json'),chapters)
    save(folder/'exports'/(name+'-captions.json'),mapped)
