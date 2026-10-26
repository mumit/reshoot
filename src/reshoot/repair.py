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


# What a control was when a take last used it: compared with the page when the control has gone, so a renamed link
# or button can still be found. Positions are in page coordinates, as the page was scrolled to the control.
FINGERPRINT = """el => {
  const r = el.getBoundingClientRect();
  return {tag: el.tagName.toLowerCase(), href: el.getAttribute('href'), id: el.id || null, name: el.getAttribute('name'),
          test_id: el.getAttribute('data-testid'), rect: [r.x + scrollX, r.y + scrollY, r.width, r.height]};
}"""

# Every visible control, scored against a fingerprint: the same link, id or test id is the same control; the same kind
# of element where the old one was is probably it. Only a single best match is offered.
MATCH = """before => {
  const seen = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const centre = r => [r[0] + r[2] / 2, r[1] + r[3] / 2];
  const [bx, by] = centre(before.rect || [0, 0, 0, 0]);
  const scored = [];
  for (const el of document.querySelectorAll('a,button,input,select,textarea,summary,[role],[tabindex],[data-testid]')) {
    if (!seen(el)) continue;
    const r = el.getBoundingClientRect(), [x, y] = centre([r.x + scrollX, r.y + scrollY, r.width, r.height]);
    const href = el.getAttribute('href'), tag = el.tagName.toLowerCase();
    let score = 0, reason = '';
    if (before.href && before.href !== '#' && href === before.href) { score = 3; reason = 'goes to the same place'; }
    else if (before.id && el.id === before.id) { score = 3; reason = 'has the same id'; }
    else if (before.test_id && el.getAttribute('data-testid') === before.test_id) { score = 3; reason = 'has the same test id'; }
    else if (before.name && el.getAttribute('name') === before.name) { score = 2; reason = 'has the same name'; }
    else if (before.rect && tag === before.tag && Math.hypot(x - bx, y - by) < 48) { score = 1; reason = 'is where it was'; }
    if (score) scored.push({el, score, reason});
  }
  scored.sort((a, b) => b.score - a.score);
  if (!scored.length || (scored[1] && scored[1].score === scored[0].score)) return null;
  document.querySelectorAll('[data-reshoot-candidate]').forEach(el => el.removeAttribute('data-reshoot-candidate'));
  scored[0].el.setAttribute('data-reshoot-candidate', '');
  const el = scored[0].el;
  return {reason: scored[0].reason, tag: el.tagName.toLowerCase(), href: el.getAttribute('href'), id: el.id || null,
          label: (el.getAttribute('aria-label') || (el.labels && el.labels[0] ? el.labels[0].innerText : '') || el.innerText ||
                  el.getAttribute('placeholder') || '').trim().replace(/\\s+/g, ' ').slice(0, 100)};
}"""

LABEL = "el => (el.getAttribute('aria-label') || (el.labels && el.labels[0] ? el.labels[0].innerText : '') || el.innerText || el.getAttribute('placeholder') || '').trim().replace(/\\s+/g, ' ').slice(0, 60)"

KINDS = {'link': 'link', 'button': 'button', 'textbox': 'text box', 'combobox': 'list', 'checkbox': 'checkbox',
         'radio': 'option', 'tab': 'tab', 'menuitem': 'menu item', 'switch': 'switch', 'searchbox': 'search box'}


async def fingerprint(page, entry):
    """The control an action is about to use, or None when it can't be told apart."""
    from reshoot.browser import locator
    try:
        item = locator(page, entry['target'])
        return await asyncio.wait_for(item.evaluate(FINGERPRINT), 1) if await item.count() == 1 else None
    except Exception:
        return None


def earlier(out):
    """The controls an earlier take of this story used: the last good run's and the accepted run's when recording in a
    run, or the previous take at the same path."""
    import os
    paths = []
    if (run_dir := os.environ.get('RESHOOT_RUN_DIR')) and Path(out).resolve().is_relative_to(Path(run_dir).resolve()):
        relative = Path(out).resolve().relative_to(Path(run_dir).resolve())
        paths += [Path(root) / relative for root in os.environ.get('RESHOOT_EARLIER', '').split(os.pathsep) if root]
    paths.append(Path(out))
    for path in paths:
        try:
            targets = json.loads(path.with_suffix('.take.json').read_text()).get('targets')
        except (OSError, ValueError):
            continue
        if targets:
            return targets
    return []


def plain(entry, failure, present=()):
    """What a missing or ambiguous control means, in a person's words."""
    target = entry['target']
    kind = KINDS.get(target.get('role'), target.get('role') or 'control')
    if target.get('name'):
        named = f'the {kind} "{target["name"]}"'
    elif target.get('role'):
        named = f'the {kind}'
    elif target.get('test_id'):
        named = f'the control with test id "{target["test_id"]}"'
    else:
        named = f'the control matching {target.get("css")}' + (f' with the text "{target["text"]}"' if target.get('text') else '')
    if failure['kind'] == 'ambiguous-target':
        return f'found more than one control that could be {named}. Give the target something that tells them apart, such as a name or a test id.'
    if failure.get('candidate_labels') and failure.get('reason'):
        return f"couldn't find {named}. It's probably \"{failure['candidate_labels'][0]}\" now: that one {failure['reason']}."
    message = f"couldn't find {named}."
    if present:
        message += f' The {kind}s on the page now: ' + ', '.join(f'"{label}"' for label in present) + '.'
    return message


async def present(page, entry):
    """Up to eight controls of the same kind that the page shows now, by their words."""
    from reshoot.browser import locator
    target = entry['target']
    if not target.get('role'):
        return []
    try:
        items = locator(page, {k: v for k, v in target.items() if k in ('role', 'frame')})
        labels = []
        for n in range(min(await items.count(), 30)):
            item = items.nth(n)
            if await item.is_visible() and (label := await item.evaluate(LABEL)) and label not in labels:
                labels.append(label)
        return labels[:8]
    except Exception:
        return []


async def diagnose(page, entry, before=None):
    """Bound optional diagnosis so a stale iframe cannot hide or indefinitely delay the original failure."""
    try:
        found = await asyncio.wait_for(_diagnose(page, entry, before), timeout=2)
    except asyncio.TimeoutError:
        found = ({'kind': 'missing-target', 'target': entry['target'], 'candidates': [], 'ambiguous': False}
                 if entry.get('target') and entry['type'] != 'count' else None)
    from reshoot.story import EXPECT
    if found and entry['type'] not in EXPECT:  # a failed result check is explained by the studio, with its values
        others = []
        if not (found.get('candidates') or found.get('ambiguous')):
            try:
                others = await asyncio.wait_for(present(page, entry), 2)
            except asyncio.TimeoutError:
                pass
        found['message'] = plain(entry, found, others)
    return found


async def _guess(page, entry, before):
    """A replacement for a missing control, from what the control was when a take last used it."""
    from reshoot.browser import locator
    if not before or entry['target'].get('frame'):
        return None
    match = await page.evaluate(MATCH, before)
    if not match:
        return None
    try:
        target, specs = entry['target'], []
        if target.get('role') and match['label']:
            specs.append({'role': target['role'], 'name': match['label']})
        if match['href']:
            specs.append({'css': f'{match["tag"]}[href={json.dumps(match["href"])}]'})
        if match['id']:
            specs.append({'css': f'#{match["id"]}'})
        for spec in specs:
            item = locator(page, spec)
            if (await item.count() == 1 and await item.evaluate("el => el.hasAttribute('data-reshoot-candidate')")
                    and await compatible(item, entry)):
                return {'candidates': [spec], 'candidate_labels': [match['label'] or match['tag']], 'reason': match['reason']}
        return None
    finally:
        await page.evaluate("() => document.querySelectorAll('[data-reshoot-candidate]').forEach(el => el.removeAttribute('data-reshoot-candidate'))")


async def _diagnose(page, entry, before=None):
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
        if not found and (guess := await _guess(page, entry, before)):
            return {'kind': 'missing-target', 'target': entry['target'], 'ambiguous': False, 'before': before, **guess}
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
                fresh = await diagnose(page, data['entry'], data['failure'].get('before'))
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
    print(f"Step {failure['beat']!r} stopped: it {failure['message']}" if failure.get('message') else
          f'Control needs repair: beat {failure["beat"]}, {failure["section"]} {failure["index"]}.')
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
    print(f"Changed only which control step {failure['beat']!r} uses; its actions and result checks are as they were. "
          'Record a preview to check it:\n  reshoot preview ' + shlex.quote(run.shown(data['config'])))
    return 0
