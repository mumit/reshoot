"""Local review bundles and decisions bound to exact artifacts and policy."""
import hashlib
import html
import json
import shlex
import shutil
from pathlib import Path
from urllib.parse import quote
from reshoot.artifacts import digest


# Run aliases: the last part of a run path picks the newest run that matches.
ALIASES = {'latest': lambda report: bool(report.get('ok')),
           'accepted': lambda report: report.get('review_status') == 'completed'}


def runs_folder(path):
    """The takes/runs folder for a project folder, its reshoot.toml, or the runs folder itself."""
    path = Path(path).resolve()
    if path.suffix == '.toml' or path.is_file():
        path = path.parent
    return path if path.name == 'runs' else path / 'takes' / 'runs'


def runs(path):
    """Every run report under the folder, newest first, as (folder, report)."""
    found = []
    for report_path in runs_folder(path).glob('*/run.json'):
        try:
            report = json.loads(report_path.read_text())
        except (OSError, ValueError):
            continue
        # Older runs have no finish time; their event log was last written as they finished.
        events = report_path.parent / 'events.jsonl'
        mtime = (events if events.exists() else report_path).stat().st_mtime
        from datetime import datetime, timezone
        report.setdefault('finished_at', datetime.fromtimestamp(mtime, timezone.utc).isoformat(timespec='seconds'))
        found.append((report_path.parent, report))
    return sorted(found, key=lambda run: run[1]['finished_at'], reverse=True)


def resolve(path):
    """A run folder, with `latest` (newest successful run) or `accepted` (newest accepted run) as its last part."""
    path = Path(path)
    marker = path / 'run.json'
    if marker.is_file() and (report := json.loads(marker.read_text())).get('record'):
        # A committed record stands in for its run; use the run itself, with its media, when it is still here.
        full = runs_folder(path.parent) / report['id']
        return full if (full / 'run.json').is_file() else path
    if path.name not in ALIASES or path.exists():
        return path
    for folder, report in runs(path.parent):
        if ALIASES[path.name](report):
            import sys
            print(f'{path.name} is run {folder.name}', file=sys.stderr)
            return folder
    raise ValueError(f'no {"successful" if path.name == "latest" else "accepted"} run in {runs_folder(path.parent)}')


def listing(a):
    found = runs(a.project)
    if not found:
        print(f'no runs in {runs_folder(a.project)}')
        return 0
    newest = {name: next((f.name for f, r in found if test(r)), None) for name, test in ALIASES.items()}
    print(f'{"run":32}  {"finished (UTC)":19}  {"mode":15}  {"result":6}  {"review":9}')
    for folder, report in found:
        tags = ' '.join(name for name, id in newest.items() if id == folder.name)
        print(f'{folder.name:32}  {report["finished_at"][:19].replace("T", " "):19}  {report.get("mode", "final"):15}  '
              f'{"ok" if report.get("ok") else "failed":6}  {report.get("review_status", "pending"):9}  {tags}'.rstrip())
    return 0


def read(path):
    path = resolve(path).resolve()
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
    if getattr(a, 'markdown', None):
        Path(a.markdown).write_text(summary(result, new, new_root))
    text = json.dumps(result, indent=2)
    if not a.out:
        print(text)
        return result
    Path(a.out).write_text(text)
    if not getattr(a, 'quiet', False):
        counts = {}
        for row in result['beats']:
            counts[row['change']] = counts.get(row['change'], 0) + 1
        print(f"Compared run {new['id']} with {old['id']}. Beats: " + ', '.join(f'{n} {s}' for s, n in sorted(counts.items())) + '.')
        changed = False
        for row in result['beats']:
            what = [w for w, key in (('steps', 'definition_changed'), ('results', 'results_changed')) if row[key]]
            if row['change'] != 'matched' or what:
                changed = True
                print(f"  {row['beat']}: {row['change']}" + (', changed ' + ' and '.join(what) if what else ''))
        if not changed:
            print('No beat changed its steps or results.')
        print(f"Result checks {old.get('expectations_status', 'unverified')} before, "
              f"{new.get('expectations_status', 'unverified')} now. Wrote {a.out}.")
    return result


def exports(root, report):
    """The videos a person watches: raw web takes sit beside their .take.json, the rest are exports."""
    return [f['path'] for f in report.get('files', []) if Path(f['path']).suffix in ('.mp4', '.mov', '.gif')
            and not (root / f['path']).with_suffix('.take.json').exists()]


def status(root, report):
    """One line on what a run showed: its result checks, its scan, and whether it is accepted."""
    from reshoot.check import load
    count, state = report.get('expectations_count', 0), report.get('expectations_status', 'unverified')
    checks = (f'{count} of {count} result checks passed' if state == 'passed' else
              'result checks failed' if state == 'failed' else 'result checks not verified')
    scan, flags = load(root / 'review' / 'report.json', None), load(root / 'review' / 'flags.json', {})
    scanned = ('no scan' if scan is None else
               f'scan: {len(load(root / "review" / "key.json", {}))} items, {len(flags)} flagged')
    verdict = {'completed': 'accepted', 'failed': 'rejected'}.get(report.get('review_status'), 'not accepted yet')
    return ' · '.join((checks, scanned, verdict))


def accept(a):
    """Record the owner's verdict in one step: the exports, every beat and every scan item, bound to the exact run."""
    import sys
    from datetime import datetime, timezone
    from reshoot.check import load
    root, report = read(a.run_path)
    if report.get('record'):
        raise ValueError('this is a run record without its media; accept the run itself')
    sheets = root / 'review'
    if not report.get('ok') or policy(root).get('status') == 'error':
        raise ValueError('cannot accept a failed run or failed check')
    if report.get('mode', 'final') != 'final' and not a.preview:
        raise ValueError(f'run {report["id"]} is a {report["mode"]}, made smaller and quicker than a final: record '
                         'one with `reshoot run`, or pass --preview to accept this one anyway')
    key, flags = load(sheets / 'key.json', {}), load(sheets / 'flags.json', {})
    failed = set(load(sheets / 'failed.json', []))
    named = set(a.flagged or []) | set(a.reject or [])
    if unknown := sorted(named - set(key)):
        raise ValueError('not on the current sheets: ' + ' '.join(unknown))
    if a.reject:
        (sheets / 'failed.json').write_text(json.dumps(sorted(failed | {key[label][1] for label in a.reject}), indent=1))
        print('Rejected. Take these out of the demo data or story, then record a new run:')
        for label in a.reject:
            print(f'  {label}  {key[label][0]}')
        decide(root, report, {name: 'rejected' if name in {'finding/' + label for label in a.reject} else 'pending'
                              for name in decision_names(root)}, 'failed')
        return 1
    if failed & {h for _, h in key.values()}:
        raise ValueError('items on these sheets were rejected; record a new run')
    if unnamed := [label for label in flags if label not in named]:
        print('The scan flagged these. Inspect each at full size first:')
        for label in unnamed:
            print(f'  {label}  {key[label][0]}: ' + '; '.join(f'{why} {part}' for why, part in flags[label]))
        print('Then name each one you accept with --flagged, or reject it with --reject.')
        return 1
    videos = exports(root, report)
    beat_names = sorted(beats(root))
    print(f'Accepting run {report["id"]} ({report.get("mode", "final")}):')
    for path in videos:
        print('  export  ' + path)
    print(f'  {len(beat_names)} beats, expectations {report.get("expectations_status", "unverified")}')
    if key:
        from reshoot.run import shown
        print(f'  {len(key)} scan items on the sheets in {shown(sheets)}' + (f', including {len(flags)} flagged' if flags else ''))
    if not a.yes:
        if not sys.stdin.isatty():
            raise ValueError('accepting needs the owner: run it in a terminal, or pass --yes for the owner')
        try:
            answer = input('Have you watched these and looked at every scan item? [y/N] ')
        except (EOFError, KeyboardInterrupt):
            answer = ''
        if answer.strip().lower() not in ('y', 'yes'):
            print('Nothing recorded.')
            return 1
    if key:
        checked = load(sheets / 'checked.json', {})
        scan_report = load(sheets / 'report.json', {})
        today = datetime.now(timezone.utc).date().isoformat()
        checked |= {h: {'source': src, 'checked': today, 'policy': scan_report.get('policy')} for src, h in key.values()}
        (sheets / 'checked.json').write_text(json.dumps(checked, indent=1, sort_keys=True))
        if scan_report:
            scan_report['review'] = 'completed'
            (sheets / 'report.json').write_text(json.dumps(scan_report, indent=2))
    decide(root, report, {name: 'accepted' for name in decision_names(root)}, 'completed')
    print('Accepted. Publishing is still up to you.')
    if root.parent.name == 'runs' and root.parent.parent.name == 'takes':
        target = record(root, report, root.parent.parent.parent / 'accepted')
        from reshoot.run import shown
        print(f'Wrote {shown(target)}: commit it with the demo source, so CI and fresh checkouts compare against this run.')
        print(f'To copy the video and GIF for a README: reshoot export {shlex.quote(shown(target))} --directory docs/demo')
    return 0


def record(root, report, target):
    """Write a run's small record: its report, beat results and evidence frames, without the media. Committed beside
    the demo source, it lets a fresh checkout, such as CI, compare a new run with this one."""
    target = Path(target).resolve()
    if target.exists():
        marker = target / 'run.json'
        if not (marker.exists() and json.loads(marker.read_text()).get('record')):
            raise ValueError(f'{target} exists and is not a run record; choose another folder')
    keep = [f for f in report.get('files', []) if f['path'].endswith('.take.json') or '.evidence/' in f['path']]
    staging = target.with_name(target.name + '.partial')
    shutil.rmtree(staging, ignore_errors=True)
    for item in keep:
        (staging / item['path']).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / item['path'], staging / item['path'])
    staging.mkdir(parents=True, exist_ok=True)
    if (root / 'decisions.json').exists():
        shutil.copyfile(root / 'decisions.json', staging / 'decisions.json')
    (staging / 'run.json').write_text(json.dumps({**report, 'files': keep, 'record': True}, indent=2))
    shutil.rmtree(target, ignore_errors=True)
    staging.rename(target)
    return target


def decide(root, report, choices, status):
    from datetime import datetime, timezone
    decisions = {'schema_version': 1, 'run_id': report['id'], 'binding': binding(root, report),
                 'decisions': dict(sorted(choices.items())), 'recorded_by': 'reshoot accept',
                 'recorded_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    (root / 'decisions.json').write_text(json.dumps(decisions, indent=2))
    report['review_status'] = status
    (root / 'run.json').write_text(json.dumps(report, indent=2))


def summary(result, report, root):
    """A short Markdown account of a comparison, for a pull request or a chat message."""
    from reshoot.check import load
    scan, flags = load(root / 'review' / 'report.json', {}), load(root / 'review' / 'flags.json', {})
    counts = {}
    for row in result['beats']:
        counts[row['change']] = counts.get(row['change'], 0) + 1
    def yes(value):
        return '' if value is None else 'changed' if value else 'same'
    lines = [f"Run `{result['current']}` compared with `{result['previous']}`.", '',
             f"- Result checks: {report.get('expectations_status', 'unverified')} ({report.get('expectations_count', 0)})",
             f"- Beats: " + ', '.join(f'{n} {state}' for state, n in sorted(counts.items())),
             f"- Scan: {scan.get('status', 'not run')}, {scan.get('unchecked') or 0} items to look at, {len(flags)} flagged",
             f"- Inputs changed: {'yes' if result['inputs_changed'] else 'no'}", '',
             '| Beat | Change | Definition | Duration | Frame pixels | Results |', '|---|---|---|---|---|---|']
    for row in result['beats']:
        delta = row['duration_delta']
        lines.append(f"| `{row['beat']}` | {row['change']} | {yes(row['definition_changed'])} | "
                     f"{'' if delta is None else f'{delta:+.2f} s' if abs(delta) >= .005 else '0'} | {yes(row['evidence_changed'])} | {yes(row['results_changed'])} |")
    lines += ['', result['note'] + ' Frame pixels change with small things such as the cursor; watch the video.']
    return '\n'.join(lines) + '\n'


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
        checks = beat.get('expectations', [])
        passed = sum(x.get('status') == 'passed' for x in checks)
        line = beat.get('status', 'unverified') + (f', {passed} of {len(checks)} result checks passed' if checks else '')
        detail = ('<details><summary>Check data</summary><pre>' + html.escape(json.dumps(checks, indent=2)) + '</pre></details>') if checks else ''
        sections.append('<article><h2>' + html.escape(name) + '</h2><p>' + html.escape(line) + '</p>' + detail + jump + image + '</article>')
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
        result = compare(type('Args', (), {'previous': a.previous, 'current': a.run_path, 'out': str(root / 'comparison.json'),
                                           'quiet': True})())
        # Copy the exact baseline into the local bundle so the HTML remains portable.
        baseline = root / 'baseline'
        baseline.mkdir(exist_ok=True)
        for item in old.get('files', []):
            if Path(item['path']).suffix in ('.mp4', '.gif'):
                target = baseline / item['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(old_root / item['path'], target)
                src = html.escape(quote(str(target.relative_to(root))), quote=True)
                if target.suffix == '.gif':
                    content = f'<img src="{src}" alt="Previous GIF">'
                else:
                    content = f'<video controls src="{src}"></video>'
                previous_panel += f'<h2>Previous: {html.escape(item["path"])}</h2>' + content
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
        previous_panel += '<details><summary>Comparison data</summary><pre>' + html.escape(json.dumps(result, indent=2)) + '</pre></details>'
    initial = {'schema_version': 1, 'run_id': report['id'], 'binding': token, 'decisions': {name: 'pending' for name in sorted(decision_names(root))}}
    saved = root / 'decisions.json'
    if saved.exists():
        prior = json.loads(saved.read_text())
        if prior.get('binding') == token:
            initial = prior
    data = json.dumps(initial).replace('<', '\\u003c')
    document = '''<!doctype html><meta charset="utf-8"><title>Reshoot review</title>
<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem;background:#151515;color:#eee}video,img{max-width:100%;max-height:65vh}article{border-top:1px solid #777;padding:1rem 0}a{color:#add8ff}pre{white-space:pre-wrap;overflow-wrap:anywhere}select,button{font:inherit;margin:.5rem}</style>
<h1>Review this recording</h1>'''
    document += '<p><strong>' + html.escape(status(root, report)) + '</strong></p>'
    command = 'reshoot accept ' + shlex.quote(str(root)) + ''.join(' --flagged ' + shlex.quote(label) for label in flags)
    document += ('<p><strong>To accept:</strong> watch every export below and look at the scan items, flagged ones first. '
                 'Then run <code>' + html.escape(command) + '</code>. Name a failed item with <code>--reject LABEL</code> instead.</p>')
    document += ('<details><summary>Run data</summary><pre>' + html.escape(json.dumps({'execution': report.get('ok'), 'expectations': report.get('expectations_status', 'unverified'), 'scan': scan_report}, indent=2))
                 + '</pre></details>')
    document += previous_panel + ''.join(sections) + '<h2>Your decisions</h2><div id="choices"></div><button id="save">Download decisions</button>'
    document += '<script>const result=' + data + '''; document.addEventListener('click', e=>{const b=e.target.closest('button[data-time]');if(!b)return;const v=[...document.querySelectorAll('video')].find(v=>v.dataset.file===b.dataset.file);if(v){v.currentTime=Number(b.dataset.time);v.scrollIntoView();v.play()}}); const box=document.getElementById('choices');
for(const [name,value] of Object.entries(result.decisions)){const label=document.createElement('label');label.textContent=name;const select=document.createElement('select');for(const v of ['pending','accepted','rejected']){const o=document.createElement('option');o.value=v;o.textContent=v;o.selected=v===value;select.append(o)}select.onchange=()=>result.decisions[name]=select.value;label.append(select);box.append(label,document.createElement('br'))}
document.getElementById('save').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));a.download='decisions.json';a.click();URL.revokeObjectURL(a.href)};</script>'''
    target = root / 'review.html'
    target.write_text(document)
    if not getattr(a, 'quiet', False):
        print(target)
    return 0
