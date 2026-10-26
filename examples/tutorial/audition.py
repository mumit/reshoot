"""Compare local Kokoro voices on the same passage and existing notes footage."""
import argparse
import hashlib
import html
from pathlib import Path
import uuid

from reshoot import cut
from reshoot.kokoro import VOICES, settings
from media import ENC, export, save, speech

PASSAGES = [
    {'id': 'app', 'title': 'Choose one useful task', 'chapter': 'Start with a result',
     'text': "Let's make a demo of this little notes app. We'll save a note, then find it by searching for bike. "
             "That's our whole story: one useful task, with a result you can see. We're using made-up data, "
             "so we can repeat the same task whenever the app changes."},
    {'id': 'first-preview', 'title': 'Shape the first preview', 'chapter': 'Make it yours',
     'text': "Here's the recorded preview in reshoot. The cursor and caption help the viewer follow along. "
             "From here, we can change the words, give the result more time, or choose a different look. "
             "The story stays beside the app, ready to record again. Start small, watch the result, and improve one moment at a time."},
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=Path, required=True, help='existing tutorial attempt with raw notes footage')
    parser.add_argument('--voice', action='append', help='repeat for each English Kokoro voice ID')
    args = parser.parse_args()
    source = args.attempt.resolve()
    names = args.voice or ['af_heart', 'af_bella', 'am_michael']
    for name in names:
        settings('kokoro --voice ' + name)
    for scene in PASSAGES:
        if not (source/'raw'/f'{scene["id"]}.mp4').is_file():
            parser.error('Use a completed tutorial recording with app and first-preview footage.')
    root = Path('takes')/('kokoro-audition-'+uuid.uuid4().hex[:12])
    root = root.resolve(); root.mkdir(parents=True)
    links, results = [], []
    for name in names:
        folder = root/name; folder.mkdir()
        (folder/'edit').mkdir(); (folder/'exports').mkdir()
        lesson = {'title':'Reshoot · Kokoro voice audition', 'voice':'kokoro --voice '+name, 'scene':PASSAGES}
        save(folder/'lesson.json', lesson)
        spoken = speech(folder, lesson)
        timeline, cues, at = [], [], 0
        for scene in PASSAGES:
            key = scene['id']; seconds = spoken[key]['seconds']
            raw = source/'raw'/f'{key}.mp4'
            # Retain ordinary action speed, holding only the last actual frame.
            seconds = max(seconds, cut.duration(raw))
            cut.ff('-i',raw,'-i',folder/'speech'/f'{key}.wav',
                   '-map','0:v','-map','1:a','-vf','tpad=stop_mode=clone:stop_duration=60',
                   '-af','apad','-t',seconds,*ENC,'-c:a','aac','-b:a','128k',folder/'edit'/f'{key}.mp4')
            seconds = cut.duration(folder/'edit'/f'{key}.mp4')
            timeline.append({'id':key,'title':scene['title'],'chapter':scene['chapter'],'start':at,'end':at+seconds})
            cues += [{**cue,'start':at+cue['start'],'end':at+cue['end']} for cue in spoken[key]['cues']]
            at += seconds
        save(folder/'timeline.json',timeline)
        export(folder,lesson,timeline,cues,'audition',timeline)
        (folder/'exports/transcript.md').write_text('\n\n'.join(scene['text'] for scene in PASSAGES)+'\n')
        results.append({'voice':name,'seconds':at,'file':f'{name}/exports/audition.mp4'})
        links.append(f'<section><h2>{html.escape(VOICES.get(name,name))}</h2><p>{name} · speed 1</p>'
                     f'<video controls preload="metadata" src="{name}/exports/audition.mp4">'
                     f'<track kind="captions" src="{name}/exports/audition.vtt" srclang="en" label="English"></video>'
                     f'<p><a href="{name}/exports/audition.mp4">Download video</a> · '
                     f'<a href="{name}/exports/transcript.md">Transcript</a></p></section>')
    save(root/'audition.json',{'status':'pending listening review','source_attempt':str(source),
         'source_sha256':{scene['id']:hashlib.sha256((source/'raw'/f'{scene["id"]}.mp4').read_bytes()).hexdigest()
                          for scene in PASSAGES},'results':results})
    (root/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width"><title>Reshoot voice audition</title>'
        '<style>body{font:18px/1.6 system-ui;background:#101a29;color:#f2f5fa;max-width:960px;margin:auto;padding:28px}'
        'video{width:100%;background:black}a{color:#8ee9cc}section{margin:48px 0}</style>'
        '<h1>Choose a voice for the workshop</h1><p>Three local synthetic voices, the same spoken script and '
        'actual notes footage. Listen for clarity, natural pauses, pronunciation and whether you would '
        'want to hear it for a whole tutorial. Captions use model word timings. Pending listening review.</p>'
        + ''.join(links) + '</html>')
    print(root/'index.html',flush=True)


if __name__ == '__main__':
    main()
