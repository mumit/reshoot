"""Create a demo by showing a task, with guarded recovery after setup or preview failures."""
import json
import shlex
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit


def state_file(root):
    return Path(root) / 'takes/create.json'


def save(root, state):
    path = state_file(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix='.create-', delete=False) as out:
            temp = Path(out.name)
            json.dump(state, out)
        temp.replace(path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def load(root):
    path = state_file(root)
    if not path.is_file():
        return None
    try:
        if path.stat().st_size > 16384:
            raise ValueError('creation state exceeds 16 KB')
        state = json.loads(path.read_text())
        if (state['schema_version'] != 1 or state['stage'] not in ('record', 'preview', 'done')
                or not isinstance(state['size'], str) or not (state['url'] is None or isinstance(state['url'], str))):
            raise ValueError('invalid creation state')
        return state
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(f'Cannot resume this creation: {error}. Your files are kept; open reshoot studio instead.') from None


def resume_command(root):
    return 'reshoot create --resume --directory ' + shlex.quote(str(root))


def main(a):
    from reshoot import project, rec, run, setup, story, studio, web
    from reshoot.artifacts import digest
    root = Path(a.directory).resolve()
    config, board_path = root / 'reshoot.toml', root / 'storyboard.toml'
    existing = config.is_file() and not getattr(a, 'resume', False)
    persist = True
    if getattr(a, 'resume', False):
        state = load(root)
        if not state:
            raise ValueError('No saved create session here. Existing files are kept; use reshoot studio for an existing project.')
        if (a.url is not None and a.url != state['url']) or (a.size is not None and a.size != state['size']):
            raise ValueError('The URL or size differs from the saved creation. Resume without changing them, or use a new directory.')
        if state['stage'] == 'record' and any(digest(path) != state.get(key) for path, key in (
                (config, 'config_sha256'), (board_path, 'story_sha256'))):
            raise ValueError('The project changed after creation paused. Your draft is kept; open reshoot studio or record to a new storyboard file.')
        if state['stage'] == 'record' and story.load(board_path)['url'] != state['url']:
            raise ValueError('The saved target differs from the draft URL. Your files are kept; use a new directory for another app.')
    elif existing:
        print(f'Opening the project already in {root}. Its saved story is kept.', flush=True)
        if a.url:
            print('To demonstrate another task, use a new --directory or record into a separate draft.toml.', flush=True)
        state = load(root)
        persist = state is not None
        state = state or {'stage': 'preview', 'url': None, 'size': story.load(board_path).get('size', '960x540@1.5')}
    else:
        size = a.size or '960x540@1.5'
        if a.url and (urlsplit(a.url).scheme not in ('http', 'https') or not urlsplit(a.url).hostname):
            raise ValueError('Use the http:// or https:// address of your demo app.')
        web.parse_size(size)
        project.init(SimpleNamespace(directory=str(root), url=a.url, quiet=True, size=size))
        state = {'schema_version': 1, 'url': a.url, 'size': size, 'stage': 'record' if a.url else 'preview',
                 'config_sha256': digest(config), 'story_sha256': digest(board_path)}
        save(root, state)
        print(f'Created {root}. Checking the recording tools…', flush=True)
    if state['url'] and (urlsplit(state['url']).scheme not in ('http', 'https') or not urlsplit(state['url']).hostname):
        raise ValueError('The saved demo URL must use http:// or https://.')
    web.parse_size(state['size'])
    continuation = resume_command(root) if persist else 'reshoot create --directory ' + shlex.quote(str(root))
    if state['stage'] == 'done' or existing and studio.current(root):
        print('This creation is complete. Your saved project is kept.', flush=True)
        if a.no_studio:
            print('Continue with: reshoot studio ' + shlex.quote(str(root)))
            return 0
        return studio.serve(SimpleNamespace(project=str(root), port=None, no_open=a.no_open))
    print('Checking with a temporary made-up page, video and text; your app is not used for these checks.', flush=True)
    report = setup.check_project(config)
    if not report['ok']:
        print('Your project is saved. Run the fixes in a terminal, then continue with:\n  ' + continuation, flush=True)
        if a.no_studio:
            return 2
        return studio.serve(SimpleNamespace(project=str(root), port=None, no_open=a.no_open))
    if existing and state['stage'] == 'record':
        print('Creation is paused before demonstration. Continue with:\n  ' + resume_command(root), flush=True)
        if a.no_studio:
            return 2
        return studio.serve(SimpleNamespace(project=str(root), port=None, no_open=a.no_open))
    if state['stage'] == 'record':
        # A unique draft keeps external edits safe while the user demonstrates the task.
        original = {path: path.read_bytes() for path in (config, board_path)}
        if (digest(config), digest(board_path)) != (state['config_sha256'], state['story_sha256']):
            raise ValueError('The draft changed during tool checks. Your files are kept; reload the project before recording.')
        draft = root / ('recorded-' + uuid.uuid4().hex + '.toml')
        print('Show one task with demo data. Add a caption and check its result in the toolbar, then choose Done.', flush=True)
        rec.main(SimpleNamespace(url=state['url'], out=str(draft), size=state['size'], headless=False))
        from reshoot.workspace import save_many
        try:
            save_many({board_path: (draft.read_text(), story.load)}, original)
        except BaseException:
            print(f'Your recorded task is kept in {draft}. The existing project files were kept.', flush=True)
            raise
        draft.unlink()
        state.update(stage='preview', config_sha256=digest(config), story_sha256=digest(board_path))
        save(root, state)
    board = story.load(board_path)
    problems = [beat for beat in board['beat'] if beat.get('recording_issue')]
    code = 0
    if problems:
        print(f'Saved your story with {len(problems)} unresolved step(s). Repair the recording_issue entries before updating the preview.')
        code = 2
    else:
        try:
            run.preview(SimpleNamespace(config=str(config), from_beat=None))
        except (ValueError, SystemExit) as error:
            print(f'Your story is saved. The preview needs attention: {error}', flush=True)
            code = 2
        else:
            state['stage'] = 'done'
            if persist:
                save(root, state)
    print('Continue with: ' + (continuation if code else 'reshoot studio ' + shlex.quote(str(root))), flush=True)
    if a.no_studio:
        return code
    return studio.serve(SimpleNamespace(project=str(root), port=None, no_open=a.no_open))
