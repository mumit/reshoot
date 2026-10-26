"""Replay to a step, then collect an explicitly finished demonstration in an isolated browser."""
import asyncio
import json
import shlex
import time
from pathlib import Path

from reshoot import demonstration

HERE = Path(__file__).resolve().parent


async def capture(data, headless=False, drive=None):
    from playwright.async_api import async_playwright
    from reshoot import browser, web
    board, take, meta = data['board'], data['take'], data['meta']
    w, h, dpr = web.parse_size(take.get('size', board.get('size', '1280x720@1')))
    async with async_playwright() as pw:
        chrome = await pw.chromium.launch(executable_path=web.find_chrome(), headless=headless, args=web.chrome_flags())
        try:
            context = await chrome.new_context(viewport={'width':w, 'height':h}, device_scale_factor=dpr,
                                               locale='en-US', timezone_id='UTC',
                                               is_mobile=bool(take.get('mobile', board.get('mobile', False))),
                                               has_touch=bool(take.get('mobile', board.get('mobile', False))),
                                               color_scheme=take.get('theme', board.get('theme', 'dark')))
            await context.add_init_script((HERE / 'targets.js').read_text())
            await context.add_init_script('window.__reshootPostCaptions = true; window.__reshootBlur = ' +
                                          json.dumps(board.get('blur', [])) + '; window.__reshootSeed = ' +
                                          json.dumps(board.get('seed', 1)) + ';')
            await context.add_init_script((HERE / 'overlay.js').read_text())
            page = await context.new_page()
            page.set_default_timeout(10000)
            await page.goto(take.get('url', board['url']), wait_until='load')
            await page.evaluate('document.fonts.ready')
            events, root = [], data['board_path'].parent
            for entry in board.get('setup', []):
                await browser.action(page, entry, events, root)
            for beat in board['beat']:
                if beat['id'] == meta['beat'] and meta['mode'] != 'after':
                    break
                for entry in beat.get('action', []):
                    await browser.action(page, entry, events, root)
                for entry in beat.get('expect', []):
                    await browser.assertion(page, entry)
                if beat['id'] == meta['beat']:
                    break
            await page.evaluate('() => __demo.hide()')
            calls, done = [], asyncio.get_running_loop().create_future()
            total = 0
            def report(source, value):
                nonlocal total
                if done.done():
                    return
                event = json.loads(value) if isinstance(value, str) else value
                if source['frame'] != page.main_frame:
                    if event.get('kind') in ('page', 'changed'):
                        return
                    event = {'kind':'unsupported-frame', 'message':'Change iframe actions in the storyboard file.'}
                length = len(json.dumps(event))
                total += length
                if len(calls) >= 10000 or length > 262144 or total > 4 * 1024 * 1024:
                    done.set_exception(ValueError('This demonstration is too large. Show a shorter step.'))
                elif event.get('kind') == 'finish':
                    done.set_result(True)
                else:
                    calls.append((time.monotonic(), event))
            await context.expose_binding('__reshootRec', report)
            page.on('close', lambda: done.done() or done.set_result(False))
            context.on('page', lambda _: calls.append((time.monotonic(), {'kind':'unsupported-tab',
                               'message':'Demonstrate one page at a time; change popup actions in the story file.'})))
            script = 'window.__reshootToolbar = true; window.__reshootStepMode = ' + json.dumps(meta['mode']) + ';\n' + (HERE / 'rec.js').read_text()
            await context.add_init_script(script)
            for frame in page.frames:
                await frame.evaluate(script)
            if drive:
                await drive(page)
            if not await asyncio.wait_for(done, 900):
                raise ValueError('Demonstration cancelled. Your story is unchanged. Choose Done to save a draft.')
            return calls
        finally:
            await chrome.close()


def record(project, beat, mode='replace', headless=False, drive=None, draft_id=None, expected_revision=None):
    from reshoot import run
    data = demonstration.begin(project, beat, mode, draft_id, expected_revision)
    app = None
    try:
        if data['shoot'].get('app'):
            app = run.start_app({**data['shoot']['app'], 'cwd':str(data['folder'])}, data['root'] / 'app.log')
        calls = asyncio.run(capture(data, headless, drive))
        return demonstration.finish(data, calls)
    except BaseException as error:
        demonstration.fail(data, error)
        if isinstance(error, Exception):
            from reshoot.safety import redact
            raise ValueError(redact(str(error))) from error
        raise
    finally:
        if app:
            run.stop_app(app)


def main(args):
    try:
        if args.operation == 'record':
            ident = record(args.project, args.beat, args.mode, draft_id=args.draft_id, expected_revision=args.expected_revision)
            print(f'Demonstration saved: {ident}\nReview it in Studio or with reshoot step show {ident} --project {shlex.quote(args.project)}')
        elif args.operation == 'list':
            result = demonstration.latest(args.project)
            print(f"{result['id']} · {result['mode']} · {result['beat']} · {result['status']}\n{result['message']}"
                  if result else 'No pending step demonstration.')
        else:
            data = demonstration.read(args.project, args.draft)
            if args.operation == 'show':
                result = demonstration.model(data)
                print(result['message'] + '\n' + result['diff'])
            elif args.operation == 'apply':
                demonstration.apply(args.project, args.draft, data['binding'])
                print('Actions saved. Record a fresh preview to verify the whole task.')
            else:
                demonstration.discard(args.project, args.draft, data['binding'])
                print('Draft discarded. Your story is kept.')
        return 0
    except (ValueError, OSError, TimeoutError) as error:
        print(str(error))
        return 2
