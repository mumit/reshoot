"""Native-input Chromium driver for TOML storyboards. The overlay only draws."""
import asyncio
import base64
import json
import os
import time
from pathlib import Path
from reshoot import story, web, zoom
from reshoot.artifacts import Frames, digest
from reshoot.safety import redact


def locator(page, spec):
    scope = page.frame_locator(spec['frame']) if 'frame' in spec else page
    if 'test_id' in spec:
        return scope.get_by_test_id(spec['test_id'])
    if 'role' in spec:
        return scope.get_by_role(spec['role'], **({'name': spec['name'], 'exact': True} if 'name' in spec else {}))
    item = scope.locator(spec['css'])
    if 'text' in spec:
        import re
        item = item.filter(has_text=re.compile('^' + re.escape(spec['text']) + '$'))
    return item


async def action(page, entry, events, root):
    kind = entry['type']
    timeout = entry.get('timeout', 10000)
    if kind == 'navigate':
        await page.goto(entry['url'], timeout=timeout)
        return
    if kind == 'scroll':
        await page.mouse.wheel(0, entry.get('dy', 300))
        await page.wait_for_timeout(400)
        return
    item = locator(page, entry['target'])
    if kind == 'wait':
        await item.wait_for(state='visible', timeout=timeout)
        return
    if (found := await item.count()) != 1:
        target = ', '.join(f'{k} = {v!r}' for k, v in entry['target'].items())
        raise ValueError(f'{kind} target {{{target}}} matched {found} elements; it must match exactly one')
    await item.scroll_into_view_if_needed(timeout=timeout)
    box = await item.bounding_box()
    rect = [box[k] for k in ('x', 'y', 'width', 'height')] if box else None
    events.append((time.monotonic(), {'kind': 'act', 'phase': 'start', 'rect': rect}))
    if box:
        await page.evaluate('p => __demo.moveTo(p[0], p[1], 350)', [box['x'] + box['width']/2, box['y'] + box['height']/2])
    if kind == 'click':
        await item.click(timeout=timeout)
    elif kind == 'type':
        await item.click(timeout=timeout)
        if entry.get('clear', True):
            await item.fill('', timeout=timeout)
        await item.press_sequentially(entry['text'], delay=65, timeout=timeout)
    elif kind == 'key':
        await item.press(entry['key'], timeout=timeout)
    elif kind == 'upload':
        await item.set_input_files(str((root / entry['file']).resolve()), timeout=timeout)
    events.append((time.monotonic(), {'kind': 'act', 'phase': 'end', 'rect': rect}))


async def assertion(page, entry):
    from playwright.async_api import expect
    kind = entry['type']
    timeout = entry.get('timeout', 10000)
    if kind == 'url':
        import re
        await expect(page).to_have_url(re.compile(re.escape(entry['contains'])), timeout=timeout)
        return page.url
    item = locator(page, entry['target'])
    if kind == 'count':
        await expect(item).to_have_count(entry['count'], timeout=timeout)
        return await item.count()
    await expect(item).to_be_visible(timeout=timeout)
    if kind == 'text':
        await expect(item).to_contain_text(entry['contains'], timeout=timeout)
        return await item.inner_text()
    if kind == 'value':
        await expect(item).to_have_value(entry['value'], timeout=timeout)
        return await item.input_value()
    if kind == 'checked':
        await expect(item).to_be_checked(checked=entry.get('checked', True), timeout=timeout)
        return await item.is_checked()
    return True


async def capture(board, a, frames, out, metadata, spoken):
    from playwright.async_api import async_playwright
    w, h, dpr = web.parse_size(a.size or board.get('size', '1280x720@1'))
    if os.environ.get('RESHOOT_PREVIEW') == '1':
        dpr = min(dpr, 720 / max(w, h))
    z = zoom.settings(a.zoom if a.zoom is not None else board.get('zoom'))
    if board.get('caption'):
        z = z or {**zoom.DEFAULTS, 'scale': 1, 'watch': False}
        style = dict(board['caption'])
        if style.get('font'):
            style['font'] = str(Path(a.storyboard).resolve().parent / style['font'])
        z['caption_style'] = style
    cap_dpr = min(dpr * min(z['scale'], 2), 4) if z else dpr
    first = getattr(a, 'from_beat', None) or os.environ.get('RESHOOT_FROM_BEAT')
    ids = [b['id'] for b in board['beat']]
    metadata['mode'] = 'partial' if first else 'preview' if os.environ.get('RESHOOT_PREVIEW') else 'final'
    if first and first not in ids:
        raise ValueError('unknown starting beat')
    split = ids.index(first) if first else 0
    events, beats, pending, assets, resources = [], {}, [], [], []
    clock = None
    root = Path(a.storyboard).resolve().parent
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=web.find_chrome(), headless=True, args=web.chrome_flags())
        context = await browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=cap_dpr,
                                            color_scheme=a.theme or board.get('theme', 'dark'), locale='en-US', timezone_id='UTC',
                                            is_mobile=bool(a.mobile or board.get('mobile')), has_touch=bool(a.mobile or board.get('mobile')))
        page = await context.new_page()
        metadata['browser'] = browser.version
        errors = []
        page.on('pageerror', lambda e: errors.append(redact(str(e))))
        await page.expose_binding('__reshoot', lambda source, payload: events.append((time.monotonic(), json.loads(payload))))
        await page.add_init_script('window.__reshootPostCaptions = ' + json.dumps(bool(z)) + '; window.__reshootBlur = ' + json.dumps(board.get('blur', [])) + '; window.__reshootSeed = ' + str(board.get('seed', 1)) + ';')
        await page.add_init_script((web.HERE / 'overlay.js').read_text())
        asset_folder = out.with_suffix('.resources')
        asset_folder.mkdir(exist_ok=True)
        async def save_resource(response):
            if response.request.resource_type not in ('image', 'media'):
                return
            from reshoot.safety import describe
            record = {'source': describe(response.url), 'status': 'unavailable'}
            try:
                data = await response.body()
                import hashlib
                name = hashlib.sha256(data).hexdigest()
                target = asset_folder / name
                target.write_bytes(data)
                record.update(status='saved', file=str(target.relative_to(out.parent)), sha256=name, content_type=response.headers.get('content-type', ''))
                if response.request.resource_type == 'image':
                    from reshoot.check import open_image
                    if open_image(data) is not None:
                        assets.append(str(target))
                    else:
                        record['status'] = 'unsupported'
            except Exception:
                pass
            resources.append(record)
        resource_handler = lambda response: pending.append(asyncio.create_task(save_resource(response)))
        page.on('response', resource_handler)
        cdp = await context.new_cdp_session(page)
        # Playwright's virtual viewport can exceed Chrome's visible capture surface.
        # CDP screencasting needs both sizes, rather than stretching a clipped frame.
        await cdp.send('Emulation.setDeviceMetricsOverride', {'width': w, 'height': h, 'deviceScaleFactor': cap_dpr,
                       'mobile': bool(a.mobile or board.get('mobile')), 'screenWidth': w, 'screenHeight': h,
                       'dontSetVisibleSize': False})
        async def frame(event):
            nonlocal clock
            timestamp = event['metadata']['timestamp']
            if clock is None:
                clock = time.monotonic() - timestamp
            frames.append((timestamp + clock, base64.b64decode(event['data'])))
            await cdp.send('Page.screencastFrameAck', {'sessionId': event['sessionId']})
        frame_tasks = []
        frame_handler = lambda event: frame_tasks.append(asyncio.create_task(frame(event)))
        cdp.on('Page.screencastFrame', frame_handler)
        current = None
        try:
            await page.goto(a.url or board.get('url', 'http://localhost:8000/'), wait_until='load', timeout=30000)
            await page.evaluate('document.fonts.ready')
            for entry in board.get('setup', []):
                await action(page, entry, events, root)
            for previous in board['beat'][:split]:
                for entry in previous.get('action', []):
                    await action(page, entry, events, root)
                for entry in previous.get('expect', []):
                    await assertion(page, entry)
            metadata['replayed_before'] = ids[:split]
            events.clear()
            await cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 92, 'maxWidth': int(w*cap_dpr), 'maxHeight': int(h*cap_dpr)})
            for beat in board['beat'][split:]:
                current = beat['id']
                start = beats[current] = time.monotonic()
                result = {'id': current, 'purpose': beat.get('purpose'), 'caption': beat.get('caption'),
                          'definition_sha256': __import__('hashlib').sha256(json.dumps(beat, sort_keys=True).encode()).hexdigest(),
                          'status': 'running', 'expectations': []}
                metadata['beats'].append(result)
                await page.evaluate('p => __demo.caption(p[0], p[1])', [beat.get('caption'), beat.get('sub')])
                for entry in beat.get('action', []):
                    await action(page, entry, events, root)
                for entry in beat.get('expect', []):
                    try:
                        actual = await assertion(page, entry)
                    except Exception as error:
                        result['expectations'].append({'type': entry['type'], 'status': 'failed', 'error': redact(str(error))})
                        raise
                    result['expectations'].append({'type': entry['type'], 'status': 'passed', 'actual': redact(str(actual)), 'at': time.monotonic()})
                if errors:
                    raise RuntimeError('page error: ' + '; '.join(errors))
                result.update(verified_at=time.monotonic(), trim_wait=bool(beat.get('trim_wait')), min_reading=max(beat.get('min_reading', 0), board.get('caption', {}).get('min_seconds', 0)))
                shot = out.parent / (out.stem + '.evidence') / (current + '.png')
                shot.parent.mkdir(exist_ok=True)
                await page.screenshot(path=str(shot))
                result.update(status='passed' if beat.get('expect') else 'unverified', screenshot=str(shot.relative_to(out.parent)), start=start)
                await asyncio.sleep(max(beat.get('hold', 1), beat.get('min_reading', 0), board.get('caption', {}).get('min_seconds', 0) if beat.get('caption') else 0, spoken.get(current, ('', 0))[1] + .3 - (time.monotonic() - start)))
                result['end'] = time.monotonic()
            stop = time.monotonic()
            await cdp.send('Page.stopScreencast')
            cdp.remove_listener('Page.screencastFrame', frame_handler)
            page.remove_listener('response', resource_handler)
            if frame_tasks:
                await asyncio.gather(*frame_tasks)
            frames.append((stop, None))
            if pending:
                await asyncio.gather(*pending)
            if errors:
                raise RuntimeError('page error: ' + '; '.join(errors))
            metadata['status'] = 'completed'
        except Exception as e:
            if metadata['beats']:
                metadata['beats'][-1]['status'] = 'failed'
            failure = out.with_suffix('.failure.png')
            try:
                await page.screenshot(path=str(failure))
                metadata['failure_screenshot'] = str(failure.relative_to(out.parent))
            except Exception:
                pass
            raise RuntimeError(f'beat {current!r} failed: {redact(str(e))}') from None
        finally:
            cdp.remove_listener('Page.screencastFrame', frame_handler)
            page.remove_listener('response', resource_handler)
            if frame_tasks:
                await asyncio.gather(*frame_tasks, return_exceptions=True)
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            await context.close()
            await browser.close()
            metadata['resources'] = resources
    if not len(frames):
        raise ValueError('no frames captured')
    t0 = frames[0][0]
    for result in metadata['beats']:
        for key in ('start', 'end', 'verified_at'):
            if key in result:
                result[key] = max(0, result[key] - t0)
        for check in result['expectations']:
            check['at'] = max(0, check['at'] - t0)
    times = [t for t, _ in frames]
    metadata['capture'] = {'css_width': w, 'css_height': h, 'pixel_ratio': cap_dpr,
                           'frames': len(frames)-1, 'max_gap_seconds': max((b-a for a,b in zip(times,times[1:])), default=0), 'seed': board.get('seed', 1), 'locale': 'en-US', 'timezone': 'UTC',
                           'theme': a.theme or board.get('theme', 'dark'), 'mobile': bool(a.mobile or board.get('mobile'))}
    metadata['events'] = [{'t': max(0, t-t0), **event} for t, event in events]
    out.with_suffix('.beats.json').write_text(json.dumps({name: max(0, at-t0) for name, at in beats.items()}, indent=2))
    out.with_suffix('.events.json').write_text(json.dumps(metadata['events'], indent=2))
    out.with_suffix('.assets.json').write_text(json.dumps(sorted(set(assets)), indent=2))
    out.with_suffix('.voice.json').unlink(missing_ok=True)
    if spoken:
        spoken = {name: line for name, line in spoken.items() if name in beats}
        out.with_suffix('.voice.json').write_text(json.dumps([{'beat': name, 't': max(0, beats[name]-t0), 'file': f, 'seconds': seconds, 'text': board['voice'][name]} for name, (f, seconds) in spoken.items()], indent=2))
    temp = out.with_name(out.stem + '.partial.mp4')
    if z:
        zoom.render(frames, events, temp, w, h, int(w*dpr)//2*2, int(h*dpr)//2*2, z)
    else:
        web.encode(frames, temp, size=f'{int(w*dpr)//2*2}:{int(h*dpr)//2*2}')
    temp.replace(out)
    metadata['sha256'] = digest(out)


def main(a):
    board = story.load(a.storyboard)
    web.parse_size(a.size or board.get('size', '1280x720@1'))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    metadata = {'schema_version': 1, 'video': out.name, 'status': 'failed', 'story_id': board.get('id', Path(a.storyboard).stem), 'story_sha256': digest(a.storyboard), 'beats': []}
    from reshoot.voice import prepare
    spoken = prepare(board['voice'], os.environ.get('RESHOOT_VOICE_CACHE', out.with_suffix('.voice')), board.get('voice_engine')) if board.get('voice') else {}
    try:
        with Frames() as frames:
            asyncio.run(asyncio.wait_for(capture(board, a, frames, out, metadata, spoken), board.get('timeout', 600)))
    except (Exception, KeyboardInterrupt) as e:
        metadata['error'] = redact(str(e)) or type(e).__name__
        raise ValueError(metadata['error']) from None
    finally:
        out.with_suffix('.take.json').write_text(json.dumps(metadata, indent=2))
    print('wrote', out)
