"""Read-only download bundles containing only a displayed run's final exports and subtitles."""
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import quote


def files(root, report):
    from reshoot.review import exports
    selected = exports(root, report)
    known = {row['path']: row['sha256'] for row in report.get('files', [])}
    selected += [name for path in selected if Path(path).suffix in ('.mp4', '.mov') and (name := str(Path(path).with_suffix('.srt'))) in known]
    selected = list(dict.fromkeys(selected))
    if not report.get('ok') or not selected or report.get('mode') == 'partial-preview':
        raise ValueError('Record a complete successful preview or final before downloading its exports.')
    names = [Path(path).name for path in selected]
    if len(set(names)) != len(names) or {'README.md', 'manifest.json'} & set(names):
        raise ValueError('Export names collide. Give each destination a different file name.')
    return [{'source': path, 'name': name, 'sha256': known[path]} for path, name in zip(selected, names)]


def bundle(root, report):
    from reshoot import review, screenshots, tours
    selected = files(root, report)
    binding = review.binding(root, report)
    descriptions = {Path(row['path']).name: row['alt'] for row in screenshots.listing(root, report)}
    tour_names = {Path(row['path']).name: row['title'] for row in tours.listing(root, report)}
    mode = report.get('mode', 'final')
    lines = ['# Your demo exports', '', f'Run: `{report["id"]}`', f'Format: {mode}',
             f'Review status: {report.get("review_status", "pending")}', '',
             'These are the shown recording\'s exports. Saved project edits may belong to a later recording.', '']
    for item in selected:
        name = item['name']
        alt = descriptions.get(name)
        if alt:
            alt = re.sub(r'([\\\[\]`*_<>])', r'\\\1', alt)
            lines += [f'![{alt}]({quote(name)})', '']
        else:
            label = 'Open offline walkthrough' if name in tour_names else name
            label = re.sub(r'([\\\[\]`*_<>])', r'\\\1', label)
            lines += [f'![The recorded demo]({quote(name)})' if name.endswith('.gif') else f'[{label}]({quote(name)})', '']
    lines += ['The HTML walkthrough works offline. GIFs have no sound. Subtitle files sit beside their video.',
              'Downloading does not accept or publish these files.']
    manifest = {'schema_version': 1, 'run_id': report['id'], 'binding': binding, 'mode': mode,
                'review_status': report.get('review_status', 'pending'), 'scan_status': report.get('scan_status', 'skipped'),
                'files': selected}
    output = tempfile.TemporaryFile()
    try:
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
            for item in selected:
                path = (root / item['source']).resolve()
                if not path.is_relative_to(root.resolve()) or not path.is_file():
                    raise ValueError('An export is missing or outside the shown run.')
                digest = hashlib.sha256()
                with path.open('rb') as source, archive.open(item['name'], 'w', force_zip64=True) as target:
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk); target.write(chunk)
                if digest.hexdigest() != item['sha256']:
                    raise ValueError('An export changed while preparing the download. Reload and review the recording.')
            archive.writestr('README.md', '\n'.join(lines) + '\n')
            archive.writestr('manifest.json', json.dumps(manifest, indent=2))
        output.seek(0)
        return output
    except BaseException:
        output.close()
        raise
