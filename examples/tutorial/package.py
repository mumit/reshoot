"""Prepare a portable workshop bundle and publishing drafts. Never uploads anything."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPO = 'https://github.com/mumit/reshoot'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f'{minutes:02}:{seconds:02}'


def package(attempt, destination, commit):
    exports = attempt/'exports'
    audit = json.loads((attempt/'audit.json').read_text())
    names = ['tutorial','first-demo']
    required = ['transcript.md'] + [name+suffix for name in names for suffix in ('.mp4','.srt','.vtt','-chapters.json')]
    # Check before making a package, so a stale audit cannot describe changed media.
    for name in names:
        if sha(exports/(name+'.mp4')) != audit['exports'][name]['sha256']:
            raise ValueError('The video changed since its audit. Audit the attempt again before packaging.')
    for name in required:
        if not (exports/name).is_file():raise ValueError('Missing export: '+name)
    if audit['scan']['status'] != 'completed' or audit['scan']['flagged']:
        raise ValueError('Complete the scan and resolve its findings before packaging.')
    destination.mkdir(parents=True)
    bundle = destination/'reshoot-workshop';bundle.mkdir()
    for name in required:shutil.copy2(exports/name,bundle/name)
    source = REPO+'/blob/'+commit
    sections = []
    for name,title in [('tutorial','Full workshop'),('first-demo','Make your first demo')]:
        frame=attempt/'review'/('welcome.png' if name=='tutorial' else 'write.png')
        poster=''
        if frame.is_file():
            shutil.copy2(frame,bundle/(name+'-poster.png'))
            poster=f' poster="{name}-poster.png"'
        chapters = json.loads((bundle/(name+'-chapters.json')).read_text())
        buttons = ''.join(f'<li><button data-video="{name}" data-seek="{row["start"]:.3f}">'
                          f'{timestamp(row["start"])} · {html.escape(row["title"])}</button></li>' for row in chapters)
        sections.append(f'<section><h2>{title}</h2><video id="{name}" controls preload="metadata" src="{name}.mp4"{poster}>'
                        f'<track default kind="captions" srclang="en" label="English" src="{name}.vtt"></video>'
                        f'<p><a href="{name}.mp4" download>Download MP4</a> · '
                        f'<a href="{name}.srt">SRT captions</a></p><ol>{buttons}</ol></section>')
        chapter_text = '\n'.join(timestamp(row['start'])+' '+row['title'] for row in chapters)
        (destination/(name+'-upload.txt')).write_text(
            ('Make a web app demo, then keep it current | Reshoot workshop' if name=='tutorial'
             else 'Make your first web app demo with Reshoot')+'\n\n'
            'Record a useful task in a web app, then turn it into a demo you can refresh when the UI changes. '
            'This walkthrough uses the made-up notes app and synthetic data. Narration: local Kokoro Heart.\n\n'
            'Follow along: '+source+'/guide/video-workshop.md\n'
            'Source and rebuild instructions: '+source+'/examples/tutorial/README.md\n\n'
            'Chapters / navigation timestamps\n'+chapter_text+'\n')
    (bundle/'watch.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width"><title>Reshoot workshop</title>'
        '<style>body{font:18px/1.6 system-ui;background:#101a29;color:#f2f5fa;max-width:1040px;margin:auto;padding:28px}'
        'video{width:100%;background:black}a{color:#8ee9cc}section{margin:48px 0}'
        'button{font:inherit;color:inherit;background:#1b2b43;border:1px solid #acbed5;border-radius:6px;padding:8px;cursor:pointer}'
        'ol{list-style:none;padding:0}li{margin:8px 0}button:focus-visible,a:focus-visible{outline:3px solid #8ee9cc}</style>'
        '<h1>Make a web app demo, then keep it current</h1><p>Real notes app · Synthetic data · Kokoro Heart narration</p>'
        f'<p><a href="{source}/guide/video-workshop.md">Follow along</a> · '
        f'<a href="transcript.md">Workshop transcript</a> · <a href="{source}/examples/tutorial/README.md">Rebuild from source</a></p>'
        '<p>Play the short introduction first, or use the chapters to explore the full workshop. '
        'For caption tracks when watching locally, follow README.md.</p>'
        +''.join(reversed(sections))+
        '<script>document.querySelectorAll("button[data-seek]").forEach(b=>b.onclick=()=>{'
        'const v=document.getElementById(b.dataset.video);document.querySelectorAll("video").forEach(other=>{if(other!==v)other.pause()});'
        'v.currentTime=Number(b.dataset.seek);v.play();v.scrollIntoView({behavior:"smooth",block:"center"})});</script></html>')
    (bundle/'README.md').write_text('# Reshoot workshop\n\n'
        'Open `first-demo.mp4` for the short introduction or `tutorial.mp4` for the full workshop. '
        'No Reshoot, Kokoro or Python installation is needed to play the MP4 files.\n\n'
        '`watch.html` adds chapter buttons. Browser caption tracks work most reliably through a local server. '
        'If Python is installed, run this from the extracted folder:\n\n'
        '```bash\npython3 -m http.server 8000 --bind 127.0.0.1\n```\n\n'
        'Open http://127.0.0.1:8000/watch.html. Ctrl-C stops the server. '
        'Alternatively, load the matching SRT file in a video player that supports subtitles.\n\n'
        'The complete timestamped transcript is in `transcript.md`. Each video also has SRT, VTT '
        'and chapter JSON files. The recordings use synthetic notes data and local Kokoro Heart narration.\n\n'
        'Follow along: '+source+'/guide/video-workshop.md\n\n'
        'Rebuild instructions: '+source+'/examples/tutorial/README.md\n')
    (destination/'release-notes.md').write_text('# Draft: Reshoot web app workshop\n\n'
        'Learn to record a useful task, shape its story, repair it after a UI change and export a current demo.\n\n'
        '- Full chaptered workshop, about 15 minutes.\n- First-demo introduction, about 2½ minutes.\n'
        '- English captions, timestamped transcript and a portable chapter player.\n'
        '- Synthetic notes data and local Kokoro Heart narration.\n\n'
        'Download and extract `reshoot-workshop-heart.zip`. Start with `README.md` or open either MP4 directly.\n\n'
        'Follow-along guide: '+source+'/guide/video-workshop.md\n\n'
        'Publishing checklist for the owner: watch both final edits, upload MP4s with their matching SRT files, '
        'and use the adjacent upload descriptions. The short introduction has only two navigation timestamps. '
        'For a standalone GitHub video release, use a `workshop-*` tag; this repository uses `v*` tags '
        'to start its Python package release workflow.\n')
    files = {p.name:sha(p) for p in sorted(bundle.iterdir()) if p.is_file()}
    (bundle/'manifest.json').write_text(json.dumps({'source_commit':commit,'source_url':REPO+'/tree/'+commit,
        'source_review_status':audit['review_status'],'files':files},indent=2)+'\n')
    archive = destination/'reshoot-workshop-heart.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(bundle.iterdir()):output.write(path,'reshoot-workshop/'+path.name)
    (destination/'SHA256SUMS').write_text(sha(archive)+'  '+archive.name+'\n')
    return archive


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt',type=Path,required=True)
    parser.add_argument('--out',type=Path,help='new local destination; default: ATTEMPT/distribution')
    args=parser.parse_args()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    print(package(args.attempt.resolve(),(args.out or args.attempt/'distribution').resolve(),commit))


if __name__=='__main__':main()
