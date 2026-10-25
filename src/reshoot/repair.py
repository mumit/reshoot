"""Inspect or explicitly repair a missing storyboard target. Checks and actions never change automatically."""
import asyncio
import hashlib
import json
import shlex
import tempfile
from pathlib import Path

from reshoot.artifacts import digest

HERE = Path(__file__).resolve().parent


async def compatible(item, entry):
    kind = entry['type']
    if not await item.is_visible():
        return False
    if kind in ('click', 'type', 'select', 'check', 'key', 'upload') and not await item.is_enabled():
        return False
    return await item.evaluate('''(el, kind) => {
      if (kind === 'type') return el.isContentEditable || (!el.readOnly && (el.tagName === 'TEXTAREA' ||
        (el.tagName === 'INPUT' && !['button','submit','reset','checkbox','radio','file','hidden','range','color'].includes(el.type))));
      if (kind === 'select') return el.tagName === 'SELECT';
      if (kind === 'check' || kind === 'checked') return el.matches('input[type=checkbox],input[type=radio],[role=checkbox],[role=radio],[role=switch]');
      if (kind === 'upload') return el.matches('input[type=file]');
      if (kind === 'value') return 'value' in el;
      return true;
    }''', kind)


async def diagnose(page, entry):
    """Bound optional diagnosis so a stale iframe cannot hide or indefinitely delay the original failure."""
    try:
        return await asyncio.wait_for(_diagnose(page, entry), timeout=2)
    except asyncio.TimeoutError:
        return ({'kind': 'missing-target', 'target': entry['target'], 'candidates': [], 'ambiguous': False}
                if entry.get('target') and entry['type'] != 'count' else None)


async def _diagnose(page, entry):
    """Suggest only visible alternatives that agree on one element. Never execute or substitute a target."""
    from reshoot.browser import locator
    if not entry.get('target') or entry['type'] == 'count':
        return None
    try:
        count = await locator(page, entry['target']).count()
        if count == 1:
            return None
        if count > 1:
            return {'kind': 'ambiguous-target', 'target': entry['target'], 'candidates': [], 'ambiguous': True}
        found, labels, identities = [], [], set()
        for alternative in entry.get('fallbacks', []):
            spec = dict(alternative)
            if entry['target'].get('frame') and 'frame' not in spec:
                spec['frame'] = entry['target']['frame']
            item = locator(page, spec)
            if await item.count() != 1 or not await compatible(item, entry):
                continue
            identity = await item.evaluate('''el => {
              const state = window.__reshootRepairIdentity || (window.__reshootRepairIdentity = {ids: new WeakMap(), next: 0});
              if (!state.ids.has(el)) state.ids.set(el, ++state.next);
              return state.ids.get(el);
            }''')
            identities.add((spec.get('frame'), identity))
            if spec not in found:
                found.append(spec)
                labels.append(await item.evaluate("el => (el.getAttribute('aria-label') || el.getAttribute('placeholder') || (el.labels && el.labels[0] ? el.labels[0].innerText : '') || el.innerText || el.tagName).trim().replace(/\\s+/g, ' ').slice(0,100)"))
        return {'kind': 'missing-target', 'target': entry['target'],
                'candidates': found[:1] if len(identities) == 1 else [],
                'candidate_labels': labels[:1] if len(identities) == 1 else [], 'ambiguous': len(identities) > 1}
    except Exception:
        # Failure diagnosis must not hide the original recording error.
        return {'kind': 'missing-target', 'target': entry['target'], 'candidates': [], 'ambiguous': False}


def load(run_path, config=None):
    """A hash-verified failed run and its unchanged storyboard, never a guessed source path."""
    from reshoot import review, story
    from reshoot.config import read
    root, report = review.read(run_path)
    if report.get('ok'):
        raise ValueError('Choose the failed run printed by the recording command.')
    config = Path(config).resolve() if config else root.parent.parent.parent / 'reshoot.toml'
    shoot, folder = read(config)
    if report.get('inputs', {}).get('config_sha256') and report['inputs']['config_sha256'] != digest(config):
        raise ValueError('Project settings changed since this failure. Record a new preview before repairing it.')
    if not shoot.get('schema_version'):
        raise ValueError('Repair needs a versioned browser project.')
    for take in shoot.get('take', []):
        path = root / Path(take.get('out', '')).with_suffix('.take.json')
        if not str(take.get('web', '')).endswith('.toml') or not path.is_file():
            continue
        meta = json.loads(path.read_text())
        failure = meta.get('failure')
        if not failure or failure.get('kind') not in ('missing-target', 'ambiguous-target'):
            continue
        board_path = (folder / take['web']).resolve()
        if digest(board_path) != meta.get('story_sha256'):
            raise ValueError('The storyboard changed since this failure. Record a new preview before repairing it.')
        board = story.load(board_path)
        beat = next((b for b in board['beat'] if b['id'] == failure['beat']), None)
        if beat is None or failure['section'] not in ('action', 'expect', 'setup'):
            raise ValueError('The failed operation no longer matches this story.')
        entries = board.get('setup', []) if failure['section'] == 'setup' else beat.get(failure['section'], [])
        index = failure['index'] - 1
        if not 0 <= index < len(entries) or entries[index].get('target') != failure['target']:
            raise ValueError('The failed target no longer matches this story.')
        return {'root': root, 'report': report, 'config': config, 'folder': folder, 'take': take, 'meta': meta,
                'board': board, 'board_path': board_path, 'failure': failure, 'entry': entries[index]}
    raise ValueError('This run has no repairable control diagnosis. Result mismatches need the app or demo data fixed.')


def apply(data, target, alternatives=()):
    """Change just one target, preserving its operation, expected values, other checks and comments."""
    from reshoot import story
    from reshoot.workspace import read_lines, tables, put, save
    story.target(target)
    if digest(data['board_path']) != data['meta']['story_sha256']:
        raise ValueError('The storyboard changed during the repair. Your edits were kept.')
    failure, board = data['failure'], data['board']
    lines = read_lines(data['board_path'])
    if failure['section'] == 'setup':
        spans = tables(lines, '[[setup]]')
    else:
        heads = [head for head, _, _ in tables(lines, '[[beat]]')]
        index = next(n for n, b in enumerate(board['beat']) if b['id'] == failure['beat'])
        start, end = heads[index], heads[index + 1] if index + 1 < len(heads) else len(lines)
        spans = [(head + start, a + start, b + start) for head, a, b in
                 tables(lines[start:end], f'[[beat.{failure["section"]}]]')]
    head, start, end = spans[failure['index'] - 1]
    put(lines, (start, end), 'target', target)
    # Add alternatives when absent; preserve existing lists and their comments.
    others = []
    for spec in [data['entry']['target'], *alternatives, *data['entry'].get('fallbacks', [])]:
        if spec != target and spec not in others:
            others.append(spec)
    # Recompute the span after inserting a missing target line.
    end = next((n for n in range(head + 1, len(lines)) if lines[n].lstrip().startswith('[')), len(lines))
    if not data['entry'].get('fallbacks'):
        put(lines, (head + 1, end), 'fallbacks', others[:12] or None)
    expected_after = hashlib.sha256(''.join(lines).encode()).hexdigest()
    record = {'schema_version': 1, 'before': data['meta']['story_sha256'], 'after': expected_after,
              'beat': failure['beat'], 'section': failure['section'], 'index': failure['index'],
              'previous_target': data['entry']['target'], 'target': target}
    with tempfile.NamedTemporaryFile(mode='w', dir=data['root'], prefix='.repair-', suffix='.json', delete=False) as f:
        json.dump(record, f, indent=2)
        pending = Path(f.name)
    try:
        save(data['board_path'], lines, story.load, expected_sha256=data['meta']['story_sha256'])
        if digest(data['board_path']) != expected_after:
            raise ValueError('The storyboard changed after repair. External edits were kept; record a fresh preview.')
        pending.replace(data['root'] / 'repair.json')
    finally:
        pending.unlink(missing_ok=True)
    return record


async def replay(page, data):
    """Replay only the prefix needed to see the broken step. The broken operation is never executed."""
    from reshoot.browser import action, assertion
    board, failure, events = data['board'], data['failure'], []
    root = data['board_path'].parent
    for i, entry in enumerate(board.get('setup', []), 1):
        if failure['section'] == 'setup' and failure['index'] == i:
            return
        await action(page, entry, events, root)
    for beat in board['beat']:
        for section, operation in [('action', action), ('expect', assertion)]:
            for i, entry in enumerate(beat.get(section, []), 1):
                if beat['id'] == failure['beat'] and section == failure['section'] and failure['index'] == i:
                    return
                if section == 'action':
                    await operation(page, entry, events, root)
                else:
                    await operation(page, entry)
    raise ValueError('The failed operation is absent from this storyboard.')


async def choose(data, pick=False, headless=False, drive=None):
    """Revalidate on the current app. A visual choice needs an explicit Use this control confirmation."""
    from playwright.async_api import async_playwright
    from reshoot import browser, web
    board = data['board']
    if pick and data['entry']['target'].get('frame'):
        raise ValueError('Visual repair currently selects controls on the main page. Repair iframe targets in the storyboard.')
    w, h, dpr = web.parse_size(data['take'].get('size', board.get('size', '1280x720@1')))
    async with async_playwright() as pw:
        chrome = await pw.chromium.launch(executable_path=web.find_chrome(), headless=not pick or headless,
                                          args=web.chrome_flags())
        try:
            context = await chrome.new_context(viewport={'width': w, 'height': h}, locale='en-US', timezone_id='UTC',
                                               device_scale_factor=dpr,
                                               is_mobile=bool(data['take'].get('mobile') or board.get('mobile')),
                                               has_touch=bool(data['take'].get('mobile') or board.get('mobile')),
                                               color_scheme=data['take'].get('theme', board.get('theme', 'dark')))
            await context.add_init_script((HERE / 'targets.js').read_text())
            await context.add_init_script((HERE / 'overlay.js').read_text())
            page = await context.new_page()
            await page.goto(data['take'].get('url', board.get('url')), wait_until='load')
            await page.evaluate('document.fonts.ready')
            await replay(page, data)
            await page.evaluate('() => __demo.hide()')
            if not pick:
                fresh = await diagnose(page, data['entry'])
                candidates = (fresh or {}).get('candidates', [])
                old = data['failure'].get('candidates', [])
                if len(candidates) != 1 or candidates[0] not in old:
                    raise ValueError('The suggested control changed or is ambiguous. Choose a replacement in the app.')
                return candidates[0], []
            selected = asyncio.get_running_loop().create_future()
            def answer(source, value):
                if source['frame'] == page.main_frame and not selected.done():
                    selected.set_result(value)
            await page.expose_binding('__reshootChoose', answer)
            page.on('close', lambda: selected.done() or selected.set_result(None))
            await page.evaluate('kind => window.__reshootRepairOperation = kind', data['entry']['type'])
            await page.evaluate((HERE / 'repair.js').read_text())
            if drive:
                await drive(page)
            value = await selected
            if not value:
                raise ValueError('Repair cancelled. The storyboard is unchanged.')
            target = value['target']
            from reshoot.story import target as validate
            validate(target)
            item = browser.locator(page, target)
            if await item.count() != 1 or not await compatible(item, data['entry']):
                raise ValueError('The selected control moved or is ambiguous. Choose it again.')
            return target, value.get('fallbacks', [])
        finally:
            await chrome.close()


def main(a):
    from reshoot import run
    from reshoot.config import read
    from reshoot.safety import redact
    from reshoot.workspace import History
    data = load(a.run_path, a.config)
    failure = data['failure']
    print(f'Control needs repair: beat {failure["beat"]}, {failure["section"]} {failure["index"]}.')
    if not (a.apply or a.pick):
        for target in failure.get('candidates', []):
            print('Suggested replacement: ' + redact(json.dumps(target)))
            print('Apply after checking the failure frame:\n  reshoot repair ' + shlex.quote(str(data['root'])) + ' --apply')
        print('Or choose the replacement in the app:\n  reshoot repair ' + shlex.quote(str(data['root'])) + ' --pick')
        return 0
    shoot, folder = read(data['config'])
    paths = [data['config'], data['board_path']]
    if shoot.get('edit', {}).get('file'):
        paths.append(folder / shoot['edit']['file'])
    history = History(paths)
    revision, app = history.revision(), None
    try:
        if shoot.get('app'):
            app = run.start_app({**shoot['app'], 'cwd': str(folder)}, data['root'] / 'repair-app.log')
        target, alternatives = asyncio.run(choose(data, pick=a.pick, headless=getattr(a, 'headless', False)))
        history.check(revision)
        apply(data, target, alternatives)
    finally:
        run.stop_app(app)
    print('Updated only the locator. Actions and expected result values were preserved. Record a fresh preview to verify:\n'
          '  reshoot preview ' + shlex.quote(str(data['config'])))
    return 0
