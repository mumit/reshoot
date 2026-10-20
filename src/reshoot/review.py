"""Local review bundles and decisions bound to exact artifacts and policy."""
import hashlib
import html
import json
import shutil
from pathlib import Path
from urllib.parse import quote
from reshoot.artifacts import digest


def read(path):
    path = Path(path).resolve()
    if path.is_dir():
        path = path / 'run.json'
    report = json.loads(path.read_text())
    root = path.parent
    report.setdefault('id', 'legacy-' + digest(path)[:12])
    for item in report.get('files', []):
        p = (root / item['path']).resolve()
        if not p.is_relative_to(root) or not p.is_file() or digest(p) != item['sha256']:
            raise ValueError('missing, changed, or out-of-run artifact')
    return root, report


def policy(root):
    p = root / 'review' / 'report.json'
    report = json.loads(p.read_text()) if p.exists() else {}
    return {'findings': digest(root / 'review/flags.json') if (root / 'review/flags.json').exists() else None,
            'items': digest(root / 'review/key.json') if (root / 'review/key.json').exists() else None,
            'check': report.get('policy'), 'status': report.get('status'), 'scan': report.get('scan'), 'errors': report.get('errors', [])}


def binding(root, report):
    data = {'run_id': report['id'], 'files': report.get('files', []), 'policy': policy(root)}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def beats(root):
    result = {}
    for path in root.rglob('*.take.json'):
        take = json.loads(path.read_text())
        for beat in take.get('beats', []):
            key = take.get('story_id', path.stem) + '/' + beat['id']
            if key in result:
                raise ValueError('duplicate story/beat ID in comparison')
            video = take.get('video')
            shot = beat.get('screenshot')
            result[key] = {**beat,
                           'screenshot': str((path.parent / shot).resolve()) if shot else None,
                           'source_video': str((path.parent / video).resolve()) if video else None}
    # Legacy beats have timings but no verified result or captured evidence.
    if not result:
        for path in root.rglob('*.beats.json'):
            for name, start in json.loads(path.read_text()).items():
                result[path.stem + '/' + name] = {'id': name, 'start': start, 'status': 'unverified'}
    return result


def environment(root):
    return [{'story_id': data.get('story_id'), 'browser': data.get('browser'), 'capture': data.get('capture'),
             'story_sha256': data.get('story_sha256')}
            for path in sorted(root.rglob('*.take.json')) for data in [json.loads(path.read_text())]]


def decision_names(root):
    flags = root / 'review' / 'flags.json'
    findings = json.loads(flags.read_text()) if flags.exists() else {}
    return {'video', *beats(root), *('finding/' + label for label in findings)}


def compare(a):
    old_root, old = read(a.previous)
    new_root, new = read(a.current)
    before, after = beats(old_root), beats(new_root)
    rows = []
    for name in sorted(before.keys() | after.keys()):
        previous, current = before.get(name), after.get(name)
        state = 'added' if previous is None else 'removed' if current is None else 'matched'
        def frame_hash(beat):
            shot = beat.get('screenshot') if beat else None
            return digest(shot) if shot and Path(shot).is_file() else None
        previous_hash, current_hash = frame_hash(previous), frame_hash(current)
        def portable(beat, base):
            if beat is None:
                return None
            beat = dict(beat)
            for field in ('screenshot', 'source_video'):
                value = beat.get(field)
                if value:
                    p = Path(value).resolve()
                    beat[field] = str(p.relative_to(base)) if p.is_relative_to(base) else None
            return beat
        rows.append({'beat': name, 'change': state, 'previous': portable(previous, old_root), 'current': portable(current, new_root),
                     'definition_changed': previous.get('definition_sha256') != current.get('definition_sha256') if previous and current else None,
                     'duration_delta': round((current['end']-current['start'])-(previous['end']-previous['start']), 3) if previous and current and all(k in b for b in (previous,current) for k in ('start','end')) else None,
                     'evidence_changed': previous_hash != current_hash if previous_hash and current_hash else None,
                     'results_changed': [{k:v for k,v in x.items() if k != 'at'} for x in previous.get('expectations', [])] != [{k:v for k,v in x.items() if k != 'at'} for x in current.get('expectations', [])] if previous and current else None})
    result = {'schema_version': 1, 'previous': old['id'], 'current': new['id'], 'beats': rows,
              'inputs_changed': old.get('inputs') != new.get('inputs'),
              'previous_environment': environment(old_root), 'current_environment': environment(new_root),
              'note': 'Matched means the ID matched, not that pixels or results are equal.'}
    text = json.dumps(result, indent=2)
    if a.out:
        Path(a.out).write_text(text)
    else:
        print(text)
    return result


def main(a):
    root, report = read(a.run_path)
    token = binding(root, report)
    if a.import_decisions:
        decisions = json.loads(Path(a.import_decisions).read_text())
        if decisions.get('binding') != token or decisions.get('run_id') != report['id']:
            raise ValueError('decision belongs to another run, changed artifacts, or a changed policy')
        if not report.get('ok') or policy(root).get('status') == 'error':
            raise ValueError('cannot accept a failed run or failed check')
        choices = decisions.get('decisions', {})
        allowed = decision_names(root)
        if not choices or set(choices) - allowed or any(v not in ('accepted', 'rejected', 'pending') for v in choices.values()):
            raise ValueError('invalid review decisions')
        (root / 'decisions.json').write_text(json.dumps(decisions, indent=2))
        report['review_status'] = ('failed' if 'rejected' in choices.values() else
                                   'completed' if all(choices.get(name) == 'accepted' for name in allowed) else 'pending')
        (root / 'run.json').write_text(json.dumps(report, indent=2))
        print('Saved decisions for run', report['id'])
        return 0
    candidates = report.get('files', [])
    sections = []
    for item in candidates:
        name = item['path']
        src = html.escape(quote(name), quote=True)
        if Path(name).suffix in ('.mp4', '.mov'):
            content = f'<video controls preload="metadata" data-file="{src}" src="{src}"></video>'
        elif Path(name).suffix == '.gif':
            content = f'<img src="{src}" alt="Recorded GIF">'
        else:
            content = f'<a href="{src}">Open file</a>'
        sections.append('<article><h2>' + html.escape(name) + '</h2>' + content + '</article>')
    for take_path in root.rglob('*.take.json'):
        captured = json.loads(take_path.read_text())
        gaps = [r for r in captured.get('resources', []) if r.get('status') != 'saved']
        if gaps:
            sections.append('<article><h2>Resource capture gaps</h2><pre>' + html.escape(json.dumps(gaps, indent=2)) + '</pre></article>')
    all_beats = beats(root)
    for name, beat in all_beats.items():
        shot = beat.get('screenshot')
        image = ''
        if shot:
            p = Path(shot).resolve()
            if p.is_relative_to(root) and p.exists():
                image = f'<a href="{html.escape(quote(str(p.relative_to(root))), quote=True)}"><img alt="Original evidence frame" src="{html.escape(quote(str(p.relative_to(root))), quote=True)}"></a>'
        jump = ''
        source = beat.get('source_video')
        if source and Path(source).resolve().is_relative_to(root) and 'start' in beat:
            relative = quote(str(Path(source).resolve().relative_to(root)))
            jump = f'<button data-file="{html.escape(relative, quote=True)}" data-time="{float(beat["start"])}">Play this beat</button>'
        sections.append('<article><h2>' + html.escape(name) + '</h2><p>' + html.escape(beat.get('status', 'unverified')) + '</p>' + '<pre>' + html.escape(json.dumps(beat.get('expectations', []), indent=2)) + '</pre>' + jump + image + '</article>')
    scan_path = root / 'review' / 'report.json'
    scan_report = json.loads(scan_path.read_text()) if scan_path.exists() else {'status': 'not run'}
    keys_path = root / 'review' / 'key.json'
    keys = json.loads(keys_path.read_text()) if keys_path.exists() else {}
    flags_path = root / 'review' / 'flags.json'
    flags = json.loads(flags_path.read_text()) if flags_path.exists() else {}
    for label, (source, h) in keys.items():
        original = root / 'review' / 'originals' / (h + '.png')
        href = quote(str(original.relative_to(root)))
        sections.append('<article><h2>' + html.escape(label) + '</h2><p>' + html.escape(source) + '</p><p>' + html.escape(json.dumps(flags.get(label, []))) + '</p>' + (f'<a href="{href}">Open original frame</a>' if original.exists() else '') + '</article>')
    previous_panel = ''
    if a.previous:
        old_root, old = read(a.previous)
        result = compare(type('Args', (), {'previous': a.previous, 'current': a.run_path, 'out': str(root / 'comparison.json')})())
        # Copy the exact baseline into the local bundle so the HTML remains portable.
        baseline = root / 'baseline'
        baseline.mkdir(exist_ok=True)
        for item in old.get('files', []):
            if Path(item['path']).suffix in ('.mp4', '.gif'):
                target = baseline / item['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(old_root / item['path'], target)
                src = html.escape(quote(str(target.relative_to(root))), quote=True)
                previous_panel += f'<h2>Previous: {html.escape(item["path"])}</h2><video controls src="{src}"></video>'
        for row in result['beats']:
            previous_panel += '<article><h2>' + html.escape(row['beat']) + '</h2><div style="display:flex;gap:1rem">'
            for side, base in [('previous', old_root), ('current', root)]:
                beat = row.get(side)
                if not beat:
                    previous_panel += '<p>' + side + ': absent</p>'
                    continue
                shot = str((base / beat['screenshot']).resolve()) if beat.get('screenshot') else None
                previous_panel += '<div><p>' + side + ': ' + html.escape(beat.get('status', 'unverified')) + '</p>'
                if shot and Path(shot).is_file() and Path(shot).resolve().is_relative_to(base):
                    target = root / 'comparison-frames' / (side + '-' + hashlib.sha256(row['beat'].encode()).hexdigest()[:16] + '.png')
                    target.parent.mkdir(exist_ok=True)
                    shutil.copyfile(shot, target)
                    previous_panel += '<img alt="Beat evidence" src="' + quote(str(target.relative_to(root))) + '">'
                previous_panel += '</div>'
            previous_panel += '</div></article>'
        previous_panel += '<pre>' + html.escape(json.dumps(result, indent=2)) + '</pre>'
    initial = {'schema_version': 1, 'run_id': report['id'], 'binding': token, 'decisions': {name: 'pending' for name in sorted(decision_names(root))}}
    saved = root / 'decisions.json'
    if saved.exists():
        prior = json.loads(saved.read_text())
        if prior.get('binding') == token:
            initial = prior
    data = json.dumps(initial).replace('<', '\\u003c')
    document = '''<!doctype html><meta charset="utf-8"><title>Reshoot review</title>
<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem;background:#151515;color:#eee}video,img{max-width:100%;max-height:65vh}article{border-top:1px solid #777;padding:1rem 0}a{color:#add8ff}pre{white-space:pre-wrap;overflow-wrap:anywhere}select,button{font:inherit;margin:.5rem}</style>
<h1>Review this recording</h1><p>Execution and automatic scanning do not approve a video. Inspect the original frames and watch every final export.</p>'''
    document += '<pre>' + html.escape(json.dumps({'execution': report.get('ok'), 'expectations': report.get('expectations_status', 'unverified'), 'scan': scan_report}, indent=2)) + '</pre>'
    document += previous_panel + ''.join(sections) + '<h2>Your decisions</h2><div id="choices"></div><button id="save">Download decisions</button>'
    document += '<script>const result=' + data + '''; document.addEventListener('click', e=>{const b=e.target.closest('button[data-time]');if(!b)return;const v=[...document.querySelectorAll('video')].find(v=>v.dataset.file===b.dataset.file);if(v){v.currentTime=Number(b.dataset.time);v.scrollIntoView();v.play()}}); const box=document.getElementById('choices');
for(const [name,value] of Object.entries(result.decisions)){const label=document.createElement('label');label.textContent=name;const select=document.createElement('select');for(const v of ['pending','accepted','rejected']){const o=document.createElement('option');o.value=v;o.textContent=v;o.selected=v===value;select.append(o)}select.onchange=()=>result.decisions[name]=select.value;label.append(select);box.append(label,document.createElement('br'))}
document.getElementById('save').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));a.download='decisions.json';a.click();URL.revokeObjectURL(a.href)};</script>'''
    target = root / 'review.html'
    target.write_text(document)
    print(target)
    return 0
