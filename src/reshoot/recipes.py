"""Purposeful starting pace, look and deliverables; task actions and checks stay intact."""
import copy
import re
import shlex
import tomllib
from pathlib import Path

from reshoot.workspace import block, put, quote, save_many, tables

CATALOG = {
    'feature': {'name': 'Feature highlight', 'description': 'One useful result, with a short opening and a clear result hold.',
                'target': 15, 'style': 'focus', 'minimum': .8, 'maximum': 4, 'cards': 0, 'exports': [{'preset': 'readme'}],
                'files': 'MP4 and README GIF'},
    'walkthrough': {'name': 'Task walkthrough', 'description': 'Explain several steps at a comfortable reading pace, with an opening and closing.',
                    'target': 45, 'style': 'paper', 'minimum': 2, 'maximum': 6, 'cards': 2.5, 'exports': [],
                    'files': 'MP4 and subtitles'},
    'release': {'name': 'Release update', 'description': 'Introduce what changed, demonstrate the task and finish on the result.',
                'target': 25, 'style': 'midnight', 'minimum': 1.2, 'maximum': 5, 'cards': 2, 'exports': [{'preset': 'readme'}],
                'files': 'MP4 and README GIF'},
}


def catalog():
    return [{'key': key, **copy.deepcopy(value)} for key, value in CATALOG.items()]


def _lines(raw):
    lines = raw.decode().splitlines(keepends=True)
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    return lines


def _action_seconds(action):
    kind = action['type']
    if kind == 'type':
        return len(action.get('text', '')) / 13 + .9
    return {'click': .9, 'scroll': .9, 'key': .1}.get(kind, .3)


def plan(project, key, title=None, expected=None):
    from reshoot import config as config_module, sequence, story, styles
    if not isinstance(key, str) or key not in CATALOG:
        raise ValueError('Choose feature, walkthrough or release.')
    recipe = CATALOG[key]
    if title is not None and (not isinstance(title, str) or not title.strip() or len(title) > 120):
        raise ValueError('Give the title 1 to 120 characters, or leave it out.')
    path = (Path(project) if Path(project).suffix == '.toml' else Path(project) / 'reshoot.toml').resolve()
    original = path.read_bytes()
    config, folder, boards, edit = styles.project(path)
    before = {p: p.read_bytes() if p.exists() else None for p in [config, *boards, edit, folder / 'styles.toml']}
    before[config] = original
    before.update(expected or {})
    raw = tomllib.loads(original.decode())
    if any(not str(take.get('web', '')).endswith('.toml') for take in raw['take']):
        raise ValueError('Starting recipes need TOML browser takes. Keep a mixed or custom capture recipe in its files.')
    data = [story.load(board) for board in boards]
    cut_lines = _lines(before[edit])
    cut = tomllib.loads(''.join(cut_lines))
    spec = copy.deepcopy(styles.BUILTINS[recipe['style']])
    title = ' '.join((title or data[0]['beat'][0].get('caption') or 'One useful task').split())
    existing_cards = any('card' in part for part in cut['part'])
    card_time = sum(part.get('duration', 2) for part in cut['part'] if 'card' in part)
    add_cards = bool(recipe['cards'] and not existing_cards)
    if add_cards:
        card_time += 2 * recipe['cards']
    actions = sum(_action_seconds(action) for board in data for beat in board['beat'] for action in beat.get('action', []))
    weighted = []
    for board in data:
        checked = [beat['id'] for beat in board['beat'] if beat.get('expect')]
        for beat in board['beat']:
            meaningful = bool(beat.get('action') or beat.get('expect') or beat.get('caption'))
            words = len(re.findall(r'\S+', beat.get('caption', '') + ' ' + beat.get('sub', '')))
            weight = max(1, words / 3) if meaningful else 0
            if checked and beat['id'] == checked[-1]:
                weight *= 1.5
            weighted.append(weight)
    budget = max(0, recipe['target'] - card_time - actions)
    total = sum(weighted) or 1
    holds = [round(min(recipe['maximum'], max(recipe['minimum'], budget * weight / total)), 1) if weight else 0
             for weight in weighted]
    changes, cursor = {}, 0
    for board_path, board in zip(boards, data):
        lines = _lines(before[board_path])
        styles.set_table(lines, '[caption]', spec['caption'])
        for beat in board['beat']:
            span = block(lines, '[[beat]]', lambda row: row.get('id') == beat['id'])
            holds[cursor] = max(holds[cursor], beat.get('min_reading', 0))
            put(lines, span, 'hold', holds[cursor], after='id')
            cursor += 1
        changes[board_path] = (''.join(lines), story.load)
    styles.set_table(cut_lines, '[style]', spec['card'])
    if spec['frame_enabled']:
        styles.set_table(cut_lines, '[frame]', spec['frame'])
    elif span := block(cut_lines, '[frame]'):
        del cut_lines[span[0] - 1:span[1]]
    for head, _, end in reversed(tables(cut_lines, '[[export]]')):
        del cut_lines[head:end]
    if add_cards:
        intro = ['[[part]]\n', f'card = {quote(title)}\n', f'duration = {recipe["cards"]}\n', '\n']
        at = tables(cut_lines, '[[part]]')[0][0]
        cut_lines[at:at] = intro
        cut_lines += ['\n', '[[part]]\n', 'card = "Try it yourself"\n', f'duration = {recipe["cards"]}\n']
    for profile in recipe['exports']:
        cut_lines += ['\n', '[[export]]\n', *[f'{name} = {quote(value)}\n' for name, value in profile.items()]]
    changed_cut = tomllib.loads(''.join(cut_lines))
    where = Path(raw['edit'].get('args', [raw['take'][0]['out']])[0]).parent
    old, new = sequence.outputs(cut, where), sequence.outputs(changed_cut, where)
    if (set(old) - set(new)) & set(raw.get('keep', {})):
        raise ValueError('This recipe removes an export used by [keep]. Update that delivery choice first.')
    config_lines = _lines(original)
    if raw.get('check'):
        listed = raw['check'].get('sources', [])
        selected = [name for name in listed if name not in old] + [name for name in new if name not in listed or name in old]
        put(config_lines, block(config_lines, '[check]'), 'sources', list(dict.fromkeys(selected)))
    changes[edit] = (''.join(cut_lines), sequence.check_cut)
    changes[config] = (''.join(config_lines), config_module.read)
    return {'before': before, 'changes': changes, 'recipe': recipe['name'],
            'estimate': round(actions + sum(holds) + card_time, 1), 'cards_added': add_cards,
            'note': 'Pacing is approximate; narration, waits and app responses can make the recording longer.'}


def apply(project, key, title=None, expected=None):
    prepared = plan(project, key, title, expected)
    save_many(prepared['changes'], prepared['before'])
    return {key: value for key, value in prepared.items() if key not in ('before', 'changes')}


def main(a):
    if a.operation == 'list':
        for recipe in catalog():
            print(f'{recipe["key"]:12} {recipe["name"]}: {recipe["files"]}. {recipe["description"]}')
        return 0
    result = plan(a.project, a.recipe, a.title) if a.dry_run else apply(a.project, a.recipe, a.title)
    print(f'{"Would apply" if a.dry_run else "Applied"} {result["recipe"]}; estimated {result["estimate"]:g} s before app/network delays.')
    print(result['note'])
    print('Task actions, result checks, the current cut and existing cards are kept. Export choices are replaced.')
    if not a.dry_run:
        from reshoot.run import shown
        config = Path(a.project) if Path(a.project).suffix == '.toml' else Path(a.project) / 'reshoot.toml'
        print('See it with: reshoot preview ' + shlex.quote(shown(config)))
    return 0
