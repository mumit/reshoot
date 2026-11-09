"""Shared project observations for the studio, CLI and coding agents. No page rendering."""
import hashlib
import json
from pathlib import Path

from reshoot.expectations import explain
from reshoot.journey import update_kind


def project(path):
    """The reshoot.toml for a project folder or the file itself, its folder and its first TOML web take."""
    path = Path(path)
    config = path if path.suffix == '.toml' else path / 'reshoot.toml'
    if not config.is_file():
        raise ValueError(f'no {config}: name the project folder, such as reshoot studio demo')
    from reshoot.config import read
    shoot, folder = read(config)
    if not shoot.get('schema_version'):
        raise ValueError('the studio needs a versioned project, with schema_version = 1 in reshoot.toml')
    take = next((t for t in shoot.get('take', []) if str(t.get('web', '')).endswith('.toml')), None)
    if not take:
        raise ValueError('the studio needs a take with a TOML storyboard, such as web = "storyboard.toml"')
    return config.resolve(), folder, take


def current(folder, partial=False):
    """The newest run that worked, as (root, report), or None. A partial preview, recorded from one beat on, is
    left out unless partial asks for one only."""
    from reshoot import review
    for root, report in review.runs(folder):
        if report.get('ok') and (report.get('mode') == 'partial-preview') == partial:
            try:
                return review.read(root)
            except (OSError, ValueError):
                continue
    return None


def failed(folder, take, config):
    """The newest failure, until a complete recording succeeds. Its media stays pinned like successful runs."""
    from reshoot import review
    from reshoot.artifacts import digest
    for root, report in review.runs(folder):
        if report.get('mode') == 'partial-preview' and report.get('ok'):
            continue
        if report.get('ok'):
            return None
        try:
            root, report = review.read(root)
            path = root / Path(take['out']).with_suffix('.take.json')
            meta = json.loads(path.read_text()) if path.exists() else {}
            failure = meta.get('failure') or {}
            board = Path(folder) / take['web']
            audit = root / 'repair.json'
            repair = json.loads(audit.read_text()) if audit.exists() else {}
            current_sha = digest(board)
            image = meta.get('failure_screenshot')
            check = None  # the result check that failed, said plainly, so the page can offer to remove it
            for beat in meta.get('beats', []):
                bad = next((i for i, x in enumerate(beat.get('expectations') or []) if x.get('status') == 'failed'), None)
                if bad is not None:
                    from reshoot import story
                    beats = story.load(board)['beat']
                    n = next((k for k, b in enumerate(beats) if b.get('id') == beat['id']), None)
                    expects = beats[n].get('expect', []) if n is not None else []
                    if n is not None and bad < len(expects):
                        error = beat['expectations'][bad].get('error', '')
                        check = {'beat': beat['id'], 'index': bad, 'expect': expects[bad], 'detail': error,
                                 'message': explain(n + 1, beat['id'], expects[bad], error)}
                    break
            return {'id': report['id'], 'binding': review.binding(root, report), 'check': check,
                    'message': meta.get('error') or '; '.join(report.get('errors', [])),
                    'image': str(Path(take['out']).parent / image) if image else None,
                    'repairable': failure.get('kind') in ('missing-target', 'ambiguous-target'), 'beat': failure.get('beat'),
                    'visual_repair': not failure.get('target', {}).get('frame'),
                    'candidates': failure.get('candidates', []),
                    'candidate_labels': failure.get('candidate_labels', []),
                    'repaired': repair.get('after') == current_sha,
                    'stale': (meta.get('story_sha256') is not None and meta['story_sha256'] != current_sha) or
                             (report.get('inputs', {}).get('config_sha256') is not None and report['inputs']['config_sha256'] != digest(config))}
        except (OSError, ValueError):
            continue
    return None


def describe(config, folder, take, run, context=None, session=None, job=None):
    from reshoot import create, journey, setup
    state = journey.state(config, run)
    if context is None:
        creation = create.load(folder)
        creating = bool(creation and creation['stage'] != 'done')
        context = {'creation_pending': creating,
                   'setup': setup.current(config),
                   'failure': failed(folder, take, config)}
    state = journey.workflow(state, creating=context.get('creation_pending', False), tools=context.get('setup'),
                             failure=context.get('failure'), session=session, has_run=bool(run), job=job,
                             mode=run[1].get('mode', 'final') if run else 'final')
    kind, reason = update_kind(folder, config, take, run)
    state.update(update_kind=kind, update_detail=reason)
    if state['phase'] == 'stopped':
        # The stopped step says what to fix; which saved files changed would only distract from it.
        state.update(changes=[], update_detail='')
    return state


def editable_paths(config):
    """The same source set for studio history, demonstrations and read-only status."""
    from reshoot.config import read
    data, folder = read(config)
    paths = [Path(config).resolve(), *dict.fromkeys((folder / item['web']).resolve()
             for item in data.get('take', []) if str(item.get('web', '')).endswith('.toml')),
             folder / 'styles.toml']
    if data.get('edit', {}).get('file'):
        paths.append((folder / data['edit']['file']).resolve())
    return paths


def inspect(path):
    """Observe durable browser-project state without probes, servers or checkpoint writes.

    Jobs and unsaved fields belong to each live studio. They cannot be inferred
    from disk; expose that limit rather than declaring the whole project idle.
    """
    import shlex
    from reshoot import create, demonstration, review, story
    from reshoot.run import shown
    from reshoot.session import Session
    config, folder, take = project(path)
    history = Session(config, editable_paths(config), read_only=True)
    revision = history.revision()
    run = current(folder)
    creation = create.load(folder)
    context = {'creation_pending': bool(creation and creation['stage'] != 'done'),
               'setup': None, 'failure': failed(folder, take, config)}
    state = describe(config, folder, take, run, context=context, session=history.info())
    target = shlex.quote(shown(folder))
    config_arg = shlex.quote(shown(config))
    commands = {'update': f'reshoot {state["update_kind"]} ' +
                          (shlex.quote(shown(run[0])) + ' --config ' + config_arg if state['update_kind'] == 'recut' else config_arg),
                'preview': 'reshoot preview ' + config_arg, 'run': 'reshoot run ' + config_arg,
                'create': create.resume_command(shown(folder)),
                'setup': 'reshoot doctor --probe --config ' + config_arg,
                'session': 'reshoot studio ' + target}
    if run:
        commands['review'] = 'reshoot review ' + shlex.quote(shown(run[0])) + ' --serve'
        commands['download'] = 'reshoot studio ' + target
    for kind, command in commands.items():
        state['actions'][kind]['command'] = command
    # action and continuation reference these same capability rows.
    failure = context['failure']
    draft = demonstration.latest(config)
    unresolved = [beat['id'] for beat in story.load(folder / take['web'])['beat'] if beat.get('recording_issue')]
    result = {'schema_version': 1, 'ok': True, 'project': shown(folder), 'revision': revision,
              'run': None if not run else {'id': run[1]['id'], 'path': shown(run[0]),
                    'binding': review.binding(*run), 'mode': run[1].get('mode', 'final'),
                    'execution': 'succeeded', 'expectations': run[1].get('expectations_status', 'unverified'),
                    'scan': run[1].get('scan_status', 'skipped'), 'review': run[1].get('review_status', 'pending')},
              'creation': creation['stage'] if creation else 'not_started',
              'failure': None if not failure else {key: failure.get(key) for key in
                           ('id', 'beat', 'repairable', 'repaired', 'stale')},
              'demonstration': None if not draft else {key: draft[key] for key in ('id', 'status', 'stale', 'can_apply')},
              'unresolved_steps': unresolved, 'workflow': state,
              'observation': {'tools': 'not_checked', 'live_jobs': 'not_observed', 'unsaved_fields': 'not_observed'}}
    if revision != history.revision() or history.version() != history.token:
        raise ValueError('The project or saved history changed while reading status. Run status again.')
    return result


def main(args):
    from reshoot.safety import redact
    try:
        result = inspect(args.project)
    except (ValueError, OSError) as error:
        result = {'schema_version': 1, 'ok': False, 'error': redact(str(error))}
    if args.json:
        print(json.dumps(result, indent=2))
    elif not result['ok']:
        print(result['error'])
    else:
        state = result['workflow']
        print(state['title'] + '\n' + state['detail'])
        print('Run: ' + (result['run']['id'] if result['run'] else 'none'))
        action = state['action']
        print('Next: ' + action['label'] + ('\n  ' + action['command'] if action.get('command') else ''))
        if result['unresolved_steps']:
            print('Unresolved steps: ' + ', '.join(result['unresolved_steps']))
        if result['demonstration']:
            print('A demonstrated action draft is waiting for review in the studio.')
        print('Recording tools, live studio jobs and unsaved fields were not checked.')
    return 0 if result['ok'] else 2
