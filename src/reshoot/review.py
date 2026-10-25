"""Local review bundles and decisions bound to exact artifacts and policy."""
import hashlib
import html
import json
import re
import shlex
import shutil
from pathlib import Path
from urllib.parse import quote
from reshoot.artifacts import digest


ACCEPTED = '<div id="to-accept"><p><strong>Accepted.</strong> Publishing is still up to you.</p></div>'

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


def named(root, report):
    """The run's files by the opaque name the scan gives each source, which keeps paths out of its logs."""
    from reshoot.safety import describe
    return {describe(path).split(' source ', 1)[1]: item['path'] for item in report.get('files', [])
            for path in {str(root / item['path']), str((root / item['path']).resolve())}}


def where(text, names):
    """'local source ed36b587c98c@4.7s' as 'takes/demo-final.mp4 at 4.7 s', when it names one of the run's files."""
    m = re.fullmatch(r'local source ([0-9a-f]{12})(?:@([0-9.]+)s)?(.*)', text, re.S)
    if not m or m[1] not in names:
        return text
    return names[m[1]] + (f' at {float(m[2]):g} s' if m[2] else '') + m[3]


def frame(root, label):
    """A label's cell of its scan sheet, with the red box round what was found, or None for a text finding."""
    m = re.fullmatch(r'(\d+)-([1-4])', label)
    sheet = root / 'review' / f'{int(m[1]):02}.jpg' if m else None
    if not sheet or not sheet.exists():
        return None
    from PIL import Image, ImageChops
    j = int(m[2]) - 1
    x, y = (j % 2) * 1010, (j // 2) * 790
    cell = Image.open(sheet).convert('RGB').crop((x, y + 31, x + 1000, y + 787))  # below the label, with the box
    ink = ImageChops.difference(cell, Image.new('RGB', cell.size, 'white')).convert('L').point(lambda v: 255 if v > 40 else 0)
    box = ink.getbbox()
    return cell.crop(box) if box else None


def shared(root, report, copied, findings_dir, link=None):
    """Markdown for a pull request or a README: the copied GIF and video, and each finding with its frame. With a
    link, such as https://github.com/OWNER/REPO/blob/BRANCH/, paths become URLs a pull request can show."""
    from reshoot.check import findings, load, span
    from reshoot.run import shown
    def url(path, image=False):
        path = shown(path)
        return link.rstrip('/') + '/' + quote(path) + ('?raw=true' if image else '') if link else quote(path)
    gifs = [p for p in copied if p.suffix == '.gif']
    videos = [p for p in copied if p.suffix in ('.mp4', '.mov')]
    lines = []
    if gifs:
        image = f'![The recorded demo]({url(gifs[0], True)})'
        lines += [f'[{image}]({url(videos[0])})' if videos else image, '']
    lines += [f'[Watch {p.name}]({url(p)})' for p in videos]
    keys, flags = load(root / 'review' / 'key.json', {}), load(root / 'review' / 'flags.json', {})
    if keys:
        groups, names = findings(flags), named(root, report)
        lines += ['', '### What the scan found', '',
                  f"{len(keys)} items scanned, {len(groups)} finding{'s' if len(groups) != 1 else ''}. The scan points at "
                  "likely problems; it cannot prove a frame is safe, so watch the video too."]
        for name, (found, members) in groups.items():
            lines += ['', f'**{name}** {found}: {span(members)}. The first is {where(keys[members[0]][0], names)}.']
            picture = Path(findings_dir) / f'{name}.jpg' if findings_dir else None
            if picture and picture.exists():
                lines += ['', f'![Finding {name}, frame {members[0]}]({url(picture, True)})']
            else:
                lines += ['', 'Its frame is in the review page, in the run\'s files.']
    return '\n'.join(lines).strip() + '\n'


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
    """The videos a person watches: raw web takes sit beside their .take.json, with their captionless .clean.mp4,
    and the rest are exports."""
    return [f['path'] for f in report.get('files', []) if Path(f['path']).suffix in ('.mp4', '.mov', '.gif')
            and not (root / f['path']).with_suffix('.take.json').exists()
            and not (f['path'].endswith('.clean.mp4') and (root / f['path'][:-10]).with_suffix('.take.json').exists())]


def status(root, report):
    """One line on what a run showed: its result checks, its scan, and whether it is accepted."""
    from reshoot.check import load
    count, state = report.get('expectations_count', 0), report.get('expectations_status', 'unverified')
    checks = (f'{count} of {count} result checks passed' if state == 'passed' else
              'result checks failed' if state == 'failed' else 'result checks not verified')
    scan, flags = load(root / 'review' / 'report.json', None), load(root / 'review' / 'flags.json', {})
    from reshoot.check import findings
    groups = len(findings(flags))
    scanned = ('no scan' if scan is None else
               f'scan: {len(load(root / "review" / "key.json", {}))} items, ' +
               (f'{groups} finding{"s" if groups > 1 else ""} in {len(flags)} of them' if flags else '0 flagged'))
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
    from reshoot.check import findings, span
    groups = findings(flags)
    # A finding's ID, such as F1, stands for every frame it was found in.
    def labels(names):
        return [label for name in names or [] for label in (groups[name][1] if name in groups else [name])]
    a.flagged, a.reject = labels(a.flagged) or None, labels(a.reject) or None
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
        print('The scan found these. Inspect each at full size first:')
        for name, (found, members) in groups.items():
            if left := [label for label in members if label in unnamed]:
                print(f'  {name}  {found}: {span(left)}')
        print('Then accept each with --flagged, such as --flagged F1, or reject it with --reject.')
        return 1
    videos = exports(root, report)
    beat_names = sorted(beats(root))
    print(f'Accepting run {report["id"]} ({report.get("mode", "final")}):')
    for path in videos:
        print('  export  ' + path)
    print(f'  {len(beat_names)} beats, result checks {report.get("expectations_status", "unverified")}')
    if key:
        from reshoot.run import shown
        print(f'  {len(key)} scan items on the sheets in {shown(sheets)}' +
              (f', including {len(groups)} finding{"s" if len(groups) > 1 else ""} in {len(flags)}' if flags else ''))
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
    if (page := root / 'review.html').exists():  # so the page says so too, keeping any comparison on it
        page.write_text(re.sub(r'<div id="to-accept">.*?</div>', lambda m: ACCEPTED, page.read_text(), count=1, flags=re.S))
    if root.parent.name == 'runs' and root.parent.parent.name == 'takes':
        target = record(root, report, root.parent.parent.parent / 'accepted')
        from reshoot.run import shown
        print(f'Wrote {shown(target)}: commit it with the demo source, so CI and fresh checkouts compare against this run.')
        print(f'To copy the video and GIF for a README: reshoot export {shlex.quote(shown(target))} --directory docs/demo')
    return 0


def record(root, report, target, shared=()):
    """Write a run's small record: its report, beat results and evidence frames, without the media. Committed beside
    the demo source, it lets a fresh checkout, such as CI, compare a new run with this one. For the files in shared,
    which are being copied out with it, it also keeps the first frame of each finding in them, as findings/F1.jpg,
    so a pull request can show it: those frames are already in the shared files."""
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
    from reshoot.check import findings, load
    keys, names = load(root / 'review' / 'key.json', {}), named(root, report)
    for name, (_, members) in findings(load(root / 'review' / 'flags.json', {})).items():
        first = next((label for label in members if where(keys.get(label, [''])[0], names).split(' at ')[0] in shared), None)
        if first and (picture := frame(root, first)):
            (staging / 'findings').mkdir(exist_ok=True)
            picture.save(staging / 'findings' / f'{name}.jpg', quality=88)
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
    from reshoot.check import findings, load
    scan, flags = load(root / 'review' / 'report.json', {}), load(root / 'review' / 'flags.json', {})
    counts = {}
    for row in result['beats']:
        counts[row['change']] = counts.get(row['change'], 0) + 1
    def yes(value):
        return '' if value is None else 'changed' if value else 'same'
    lines = [f"Run `{result['current']}` compared with `{result['previous']}`.", '',
             f"- Result checks: {report.get('expectations_status', 'unverified')} ({report.get('expectations_count', 0)})",
             f"- Beats: " + ', '.join(f'{n} {state}' for state, n in sorted(counts.items())),
             f"- Scan: {scan.get('status', 'not run')}, {scan.get('unchecked') or 0} items to look at, "
             + (f"{len(findings(flags))} finding{'s' if len(findings(flags)) != 1 else ''} in {len(flags)} of them" if flags else 'nothing flagged'),
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
    # The page reads top to bottom as the review goes: the exports, what the scan found, the scan sheets, then each
    # beat with its original take, and the run's other files folded away at the end.
    watched = exports(root, report)
    named_files = {item['path'] for item in report.get('files', [])}
    media, sections, scanned, other = [], [], [], []
    for item in report.get('files', []):
        name = item['path']
        src = html.escape(quote(name), quote=True)
        if Path(name).suffix in ('.mp4', '.mov', '.gif'):
            content = (f'<img src="{src}" alt="Recorded GIF">' if name.endswith('.gif') else
                       f'<video controls preload="metadata" data-file="{src}" src="{src}"></video>')
            feedback = ''
            sidecar = str(Path(name).with_suffix('.readability.json'))
            if name in watched and sidecar in named_files:
                quality = json.loads((root / sidecar).read_text())
                feedback = '<details><summary>Framing and readability at ' + str(int(quality['display_width'])) + ' px viewing width</summary>'
                feedback += '<p>Editing hints, not a readability verdict. Inspect the actual export at its intended size.</p><ul>'
                feedback += ''.join('<li>' + html.escape(item['message']) + '</li>' for item in quality['issues'])
                feedback += '</ul>' + ''.join('<p>' + html.escape(note) + '</p>' for note in quality['notes']) + '</details>'
            (media if name in watched else sections).append(
                '<article><h2>' + ('' if name in watched else 'Original take: ') + html.escape(name) + '</h2>' + content + feedback + '</article>')
        else:
            other.append(f'<li><a href="{src}">{html.escape(name)}</a></li>')
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
    names = named(root, report)
    keys = {label: [where(found, names), h] for label, (found, h) in keys.items()}
    def original(label):
        path = root / 'review' / 'originals' / (keys[label][1] + '.png')
        return quote(str(path.relative_to(root))) if path.exists() else None
    # Flagged items first, each with its frame and what the scan found; then the sheets of everything else.
    from reshoot.check import findings, span
    groups = findings(flags)
    for name, (found, members) in groups.items():
        href = original(members[0])
        others = ''.join(f'<li><a href="{h}">{html.escape(label)}</a>: {html.escape(keys[label][0])}</li>' if (h := original(label))
                         else f'<li>{html.escape(label)}</li>' for label in members)
        scanned.append('<article class="flagged"><h2>Finding ' + html.escape(name) + ': ' + html.escape(found) + '</h2><p>'
                        + html.escape(span(members)) + '. The first is ' + html.escape(keys[members[0]][0]) + '.</p>'
                        + (f'<a href="{href}"><img alt="Flagged frame {html.escape(members[0])}" src="{href}"></a>' if href else '')
                        + (f'<details><summary>Every frame it was found in</summary><ul>{others}</ul></details>' if len(members) > 1 else '')
                        + '</article>')
    pages = sorted((root / 'review').glob('[0-9]*.jpg'))
    if keys:
        rest = len(keys) - len(flags)
        sheet_images = ''.join(f'<a href="{quote(str(p.relative_to(root)))}"><img alt="Scan sheet {p.stem}" src="{quote(str(p.relative_to(root)))}"></a>'
                               for p in pages)
        items = ''.join(f'<li>{html.escape(label)}: ' + (f'<a href="{href}">' if (href := original(label)) else '')
                        + html.escape(keys[label][0]) + ('</a>' if href else '') + '</li>' for label in keys)
        scanned.append(f'<article><h2>Scan sheets</h2><p>{len(keys)} items on {len(pages)} sheets'
                        + (f', flagged ones first. {rest} more the scan found nothing in.' if flags else '. The scan found nothing in them.')
                        + ' Look over them for what a scan can miss, such as a name in a picture or a face on Linux.</p>'
                        + f'<div class="sheets">{sheet_images}</div><details><summary>Each item at full size</summary><ul>{items}</ul></details></article>')
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
<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem;background:#151515;color:#eee}video,img{max-width:100%;max-height:65vh}article{border-top:1px solid #777;padding:1rem 0}a{color:#add8ff}.sheets{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:.5rem}.sheets img{width:100%}.flagged{border-left:4px solid #e33;padding-left:1rem}pre{white-space:pre-wrap;overflow-wrap:anywhere}select,button{font:inherit;margin:.5rem}</style>
<h1>Review this recording</h1>'''
    document += '<p><strong>' + html.escape(status(root, report)) + '</strong></p>'
    command = 'reshoot accept ' + shlex.quote(str(root)) + (' --flagged ' + ' '.join(groups) if groups else '')
    if report.get('review_status') == 'completed':
        document += ACCEPTED
    else:
        document += ('<div id="to-accept"><p><strong>To accept:</strong> watch every export below and look at the scan '
                     'items, flagged ones first. Then run <code>' + html.escape(command) + '</code>, or accept it on '
                     'this page with <code>reshoot review ' + html.escape(shlex.quote(str(root))) + ' --serve</code>. '
                     'Name a finding that must not be shared with <code>--reject</code> instead, such as '
                     '<code>--reject F1</code>.</p></div>')
    document += ('<details><summary>Run data</summary><pre>' + html.escape(json.dumps({'execution': report.get('ok'), 'expectations': report.get('expectations_status', 'unverified'), 'scan': scan_report}, indent=2))
                 + '</pre></details>')
    files = f'<article><details><summary>Other files in the run ({len(other)})</summary><ul>{"".join(other)}</ul></details></article>' if other else ''
    document += previous_panel + ''.join(media + scanned + sections) + files + '<h2>Your decisions</h2><div id="choices"></div><button id="save">Download decisions</button>'
    document += '<script>const result=' + data + '''; document.addEventListener('click', e=>{const b=e.target.closest('button[data-time]');if(!b)return;const v=[...document.querySelectorAll('video')].find(v=>v.dataset.file===b.dataset.file);if(v){v.currentTime=Number(b.dataset.time);v.scrollIntoView();v.play()}}); const box=document.getElementById('choices');
for(const [name,value] of Object.entries(result.decisions)){const label=document.createElement('label');label.textContent=name;const select=document.createElement('select');for(const v of ['pending','accepted','rejected']){const o=document.createElement('option');o.value=v;o.textContent=v;o.selected=v===value;select.append(o)}select.onchange=()=>result.decisions[name]=select.value;label.append(select);box.append(label,document.createElement('br'))}
document.getElementById('save').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));a.download='decisions.json';a.click();URL.revokeObjectURL(a.href)};</script>'''
    target = root / 'review.html'
    target.write_text(document)
    if not getattr(a, 'quiet', False):
        print(target)
    return 0


def panel(root, report, *, final_action='reshoot run'):
    """The accept panel for a served review page: a choice for each finding, a promise to have watched, a button."""
    from reshoot.check import findings, load
    if report.get('review_status') == 'completed':
        return ACCEPTED
    if not report.get('ok') or policy(root).get('status') == 'error':
        return ('<div id="to-accept"><p><strong>This run failed, so it cannot be accepted.</strong> Fix it and record a '
                'new run.</p></div>')
    if report.get('mode', 'final') != 'final':
        return ('<div id="to-accept"><p><strong>This is a preview,</strong> smaller and quicker than a final. Record a '
                f'final with <strong>{html.escape(final_action)}</strong> and accept that.</p></div>')
    rows = ''.join(
        f'<fieldset data-finding="{html.escape(name)}"><legend>{html.escape(name)}: {html.escape(found)}, '
        f'{len(members)} frame{"s" if len(members) != 1 else ""}</legend>'
        f'<label><input type="radio" name="{html.escape(name)}" value="flagged"> May be shared</label> '
        f'<label><input type="radio" name="{html.escape(name)}" value="reject"> Must not be shared</label></fieldset>'
        for name, (found, members) in findings(load(root / 'review' / 'flags.json', {})).items())
    ask = ' Then say whether each finding may be shared.' if rows else ''
    return (f'<div id="to-accept" class="flagged" data-run="{html.escape(report["id"])}" '
            f'data-binding="{binding(root, report)}"><h2>Accept this run</h2><p>Watch every export to the end and '
            'look at the scan items, findings first.' + ask + '</p>' + rows + PANEL + '</div>' + PANEL_SCRIPT)


PANEL = '''<p><label><input type="checkbox" id="watched"> I watched every export to the end and looked at every scan
item</label></p><button id="accept" disabled>Accept the run</button><pre id="outcome"></pre>'''

PANEL_SCRIPT = '''<script>(() => {
  const box = document.getElementById('to-accept'), button = document.getElementById('accept');
  const choices = () => [...box.querySelectorAll('fieldset')].map(f => [f.dataset.finding, (f.querySelector('input:checked') || {}).value]);
  box.addEventListener('change', () => {
    const c = choices();
    button.textContent = c.some(([, v]) => v === 'reject') ? 'Reject the run' : 'Accept the run';
    button.disabled = !document.getElementById('watched').checked || c.some(([, v]) => !v);
  });
  button.onclick = async () => {
    if (document.querySelector('[data-unsaved]')) {
      document.getElementById('outcome').textContent = 'Fix the unsaved field before accepting.';
      return;
    }
    button.disabled = true;
    const c = choices();
    const body = {run_id: box.dataset.run, binding: box.dataset.binding, revision: document.body.dataset.revision,
                  flagged: c.filter(([, v]) => v === 'flagged').map(([n]) => n),
                  reject: c.filter(([, v]) => v === 'reject').map(([n]) => n)};
    const r = await fetch('accept', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const out = await r.json();
    document.getElementById('outcome').textContent = out.output;
    if (out.code === 0 || body.reject.length) box.querySelectorAll('input').forEach(i => i.disabled = true);
    else button.disabled = false;
  };
})();</script>'''


def reply(handler, code, body, kind='text/html; charset=utf-8', extra=()):
    """A response from a page server on this computer: never cached, with the body unless it was a HEAD."""
    handler.send_response(code)
    handler.send_header('Content-Type', kind)
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    for k, v in extra:
        handler.send_header(k, v)
    handler.end_headers()
    if handler.command != 'HEAD':
        handler.wfile.write(body)


def send_file(handler, root, name):
    """A file from inside root, with byte ranges, so a video can seek; anything outside it is not found."""
    import mimetypes
    file = (root / name).resolve()
    if not file.is_relative_to(root.resolve()) or not file.is_file():
        return reply(handler, 404, b'not found', 'text/plain')
    data = file.read_bytes()
    kind = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
    if m := re.fullmatch(r'bytes=(\d*)-(\d*)', handler.headers.get('Range', '')):
        start = int(m[1]) if m[1] else max(0, len(data) - int(m[2] or 0))
        end = min(int(m[2]), len(data) - 1) if m[1] and m[2] else len(data) - 1
        return reply(handler, 206, data[start:end + 1], kind,
                     [('Content-Range', f'bytes {start}-{end}/{len(data)}'), ('Accept-Ranges', 'bytes')])
    reply(handler, 200, data, kind, [('Accept-Ranges', 'bytes')])


def from_page(handler, path):
    """Whether a POST came from the page this server sent: to path, which holds the token, at this host and port,
    as JSON, which another site's page cannot send here without the browser asking first. Returns its body, or
    None after refusing it."""
    host = f'127.0.0.1:{handler.server.server_address[1]}'
    if (handler.path != path or handler.headers.get('Host') != host
            or handler.headers.get('Origin') not in (None, 'http://' + host)
            or not handler.headers.get('Content-Type', '').startswith('application/json')):
        reply(handler, 403, b'not from this review page', 'text/plain')
        return None
    try:
        body = json.loads(handler.rfile.read(int(handler.headers.get('Content-Length') or 0)) or b'{}')
    except ValueError:
        body = None
    if not isinstance(body, dict):
        reply(handler, 400, b'not a JSON object', 'text/plain')
        return None
    return body


def accept_from_page(run_path, body):
    """The page's decision, recorded as `reshoot accept` records it: (exit code, what it printed)."""
    import contextlib, io
    from types import SimpleNamespace
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            root, report = read(run_path)
            if body.get('run_id') != report['id'] or body.get('binding') != binding(root, report):
                raise ValueError('This recording or its scan changed. Reload and review it before accepting.')
            code = accept(SimpleNamespace(run_path=run_path, flagged=body.get('flagged') or None,
                                          reject=body.get('reject') or None, yes=True, preview=False))
        return code, out.getvalue()
    except ValueError as e:
        return 2, str(e)


def serve(a):
    """Serve the run's review page on this computer only, with a panel that accepts or rejects the run, as
    `reshoot accept` does. The address has a random token, and the server takes decisions only from its own page."""
    import http.server, secrets, threading, time, webbrowser
    from types import SimpleNamespace
    from urllib.parse import unquote
    root, _ = read(a.run_path)
    main(SimpleNamespace(run_path=str(root), previous=a.previous, import_decisions=None, quiet=True))
    token = secrets.token_urlsafe(16)
    done = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):  # the terminal shows the outcome, not each request
            pass

        def do_GET(self):
            prefix, path = f'/{token}/', self.path.split('?', 1)[0]
            if not path.startswith(prefix):
                return reply(self, 404, b'not found', 'text/plain')
            name = unquote(path[len(prefix):]) or 'review.html'
            if name == 'review.html':
                page = re.sub(r'<div id="to-accept">.*?</div>', lambda m: panel(*read(root)),
                              (root / 'review.html').read_text(), count=1, flags=re.S)
                return reply(self, 200, page.encode())
            send_file(self, root, name)

        do_HEAD = do_GET

        def do_POST(self):
            body = from_page(self, f'/{token}/accept')
            if body is None:
                return
            code, text = accept_from_page(str(root), body)
            print(text.rstrip(), flush=True)
            reply(self, 200, json.dumps({'code': code, 'output': text}).encode(), 'application/json')
            if code == 0 or (code == 1 and body.get('reject')):
                done.set()

    server = http.server.ThreadingHTTPServer(('127.0.0.1', a.port or 0), Handler)
    url = f'http://127.0.0.1:{server.server_address[1]}/{token}/'
    print(f'The review page is at {url}\nAccept or reject the run there, or press Ctrl-C to stop.', flush=True)
    if not a.no_open:
        webbrowser.open(url)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        done.wait()
        time.sleep(0.5)  # let the page show the outcome
    except KeyboardInterrupt:
        print('Stopped; nothing more recorded.')
    finally:
        server.shutdown()
    return 0
