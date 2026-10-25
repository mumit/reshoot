"""Create a demo by showing a task, then open its preview in the studio."""
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit


def main(a):
    from reshoot import project, rec, run, story, studio, web
    if a.url and (urlsplit(a.url).scheme not in ('http', 'https') or not urlsplit(a.url).hostname):
        raise ValueError('Use the http:// or https:// address of your demo app.')
    web.parse_size(a.size)
    root = Path(a.directory).resolve()
    project.init(SimpleNamespace(directory=str(root), url=a.url, quiet=True, size=a.size))
    print(f'Created {root}. Checking the recording tools…', flush=True)
    config = root / 'reshoot.toml'
    if project.doctor(SimpleNamespace(config=str(config), json=False)):
        raise ValueError('Install the missing tools, then continue with reshoot rec or reshoot studio. Your project is saved.')
    if a.url:
        print('Show one task with demo data. Add a caption and check its result in the toolbar, then choose Done.', flush=True)
        rec.main(SimpleNamespace(url=a.url, out=str(root / 'storyboard.toml'), size=a.size, headless=False))
    board = story.load(root / 'storyboard.toml')
    problems = [b for b in board['beat'] if b.get('recording_issue')]
    code = 0
    if problems:
        print(f'Saved your story with {len(problems)} unresolved step(s). Repair the recording_issue entries before updating the preview.')
        code = 2
    else:
        try:
            run.preview(SimpleNamespace(config=str(config), from_beat=None))
        except (ValueError, SystemExit) as e:
            print(f'Your story is saved. The preview needs attention: {e}', flush=True)
            code = 2
    if a.no_studio:
        print(f'Continue with: reshoot studio {root}')
        return code
    return studio.serve(SimpleNamespace(project=str(root), port=None, no_open=a.no_open))
