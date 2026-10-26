"""Native-input Chromium driver for TOML storyboards. The overlay only draws."""
import asyncio
import base64
import json
import os
import time
from pathlib import Path
from reshoot import captions, story, web, zoom
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


async def action(page, entry, events, root, hand=None):
    """One storyboard action. While recording, hand is how the cursor and typing look: the [cursor] settings and a
    seeded random rhythm. Setup and replayed actions, which are not in the video, leave it out and run quickly."""
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
        # While recording, the glide takes longer for longer trips, as the Python route's does.
        await page.evaluate('p => __demo.moveTo(p[0], p[1], p[2])', [box['x'] + box['width']/2,
                            box['y'] + box['height']/2, None if hand else 350])
    if hand and box and kind in ('click', 'type', 'select', 'check'):
        await page.evaluate('() => __demo.tap()')
    if kind == 'click':
        await item.click(timeout=timeout)
    elif kind == 'type':
        await item.click(timeout=timeout)
        if entry.get('clear', True):
            await item.fill('', timeout=timeout)
        if not hand:
            await item.press_sequentially(entry['text'], delay=65, timeout=timeout)
        else:  # an uneven rhythm, a little longer after a space
            for ch in entry['text']:
                await page.keyboard.type(ch)
                await page.wait_for_timeout(1000 / hand['typing'] * (0.55 + hand['random']() * 0.9) + (70 if ch == ' ' else 0))
    elif kind == 'select':
        if not hand:
            await page.wait_for_timeout(250)  # let the cursor rest on the control before the choice changes
        await item.select_option(entry['option'], timeout=timeout)
    elif kind == 'check':
        await item.set_checked(entry.get('checked', True), timeout=timeout)
    elif kind == 'key':
        await item.press(entry['key'], timeout=timeout)
    elif kind == 'upload':
        await item.set_input_files(str((root / entry['file']).resolve()), timeout=timeout)
    events.append((time.monotonic(), {'kind': 'act', 'phase': 'end', 'rect': rect}))


async def evidence(page, frames, shot):
    """Save the beat's evidence: the last frame the video shows, at the end of its hold. A screenshot taken during
    capture can take the frame that shows a result, and a still page sends no other, so the video would show the old
    page through the whole hold."""
    last = frames[-1][1] if len(frames) else None
    if last is not None:
        import io
        from PIL import Image
        Image.open(io.BytesIO(last)).save(shot)
    else:
        await page.screenshot(path=str(shot))


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


async def layout(page, beat):
    """Optional, bounded geometry-only feedback. A measurement failure never changes a result check."""
    async def collect():
        data = await page.evaluate((web.HERE / 'layout.js').read_text())
        data['checked'] = []
        for check in beat.get('expect', [])[:12]:
            if check.get('target'):
                items = locator(page, check['target'])
                for i in range(min(await items.count(), 12)):
                    box = await items.nth(i).bounding_box(timeout=100)
                    if box:
                        text_box = None
                        if check['type'] == 'text' and not check['target'].get('frame'):
                            text_box = await items.nth(i).evaluate('''(el, expected) => {
                              const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
                              let node, visited = 0;
                              while ((node = walker.nextNode()) && visited++ < 2000) {
                                const at = node.textContent.indexOf(expected);
                                if (at < 0 || !expected.length) continue;
                                const range = document.createRange(); range.setStart(node, at); range.setEnd(node, at + expected.length);
                                const box = range.getBoundingClientRect();
                                if (box.width && box.height && box.right > 0 && box.bottom > 0 && box.left < innerWidth && box.top < innerHeight)
                                  return [box.x, box.y, box.width, box.height];
                              }
                              return null;
                            }''', check['contains'])
                        data['checked'].append(text_box or [box[k] for k in ('x', 'y', 'width', 'height')])
        return data
    try:
        return await asyncio.wait_for(collect(), timeout=1)
    except Exception:
        return {'schema_version': 1, 'unavailable': True}


async def capture(board, a, frames, out, metadata, spoken):
    from playwright.async_api import async_playwright
    w, h, dpr = web.parse_size(a.size or board.get('size', '1280x720@1'))
    if os.environ.get('RESHOOT_PREVIEW') == '1':
        dpr = min(dpr, 720 / max(w, h))
    z = zoom.settings(a.zoom if a.zoom is not None else board.get('zoom'))
    if z:
        z['captions'] = False  # drawn afterwards, from the storyboard (captions.py)
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
        try:
            # Without these flags the screencast sends frames at the page's CSS size whatever the pixel ratio, so @2
            # was only scaled up, and the first frames come from a window shorter than the page.
            sharp = [f'--force-device-scale-factor={cap_dpr:g}', f'--window-size={w},{h}']
            browser = await pw.chromium.launch(executable_path=web.find_chrome(), headless=True,
                                               args=web.chrome_flags() + sharp)
        except Exception as e:
            raise RuntimeError(f'Chrome could not start: {redact(str(e).splitlines()[0])}. If this runs inside an agent\'s '
                               'sandbox, such as Codex\'s, Chrome is usually what the sandbox blocks: run the reshoot '
                               'command outside it, with the harness\'s approval') from None
        context = await browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=cap_dpr,
                                            color_scheme=a.theme or board.get('theme', 'dark'), locale='en-US', timezone_id='UTC',
                                            is_mobile=bool(a.mobile or board.get('mobile')), has_touch=bool(a.mobile or board.get('mobile')))
        page = await context.new_page()
        metadata['browser'] = browser.version
        errors = []
        page.on('pageerror', lambda e: errors.append(redact(str(e))))
        await page.expose_binding('__reshoot', lambda source, payload: events.append((time.monotonic(), json.loads(payload))))
        cursor = board.get('cursor', {})
        hand = {'typing': cursor.get('typing', 13), 'random': __import__('random').Random(board.get('seed', 1)).random}
        await page.add_init_script('window.__reshootPostCaptions = true; window.__reshootBlur = ' + json.dumps(board.get('blur', [])) + '; window.__reshootSeed = ' + str(board.get('seed', 1)) + '; window.__reshootCursor = ' + json.dumps({k: cursor[k] for k in ('size', 'ripple') if k in cursor}) + ';')
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
            # Chrome stamps each frame with the wall-clock time it was painted. Map that onto the beats' clock with
            # an offset measured directly, not from when a frame arrives: large frames arrive late, and an offset
            # taken from a late first frame would shift the whole video behind the actions.
            timestamp = event['metadata'].get('timestamp')
            painted = timestamp + clock if timestamp else time.monotonic()
            frames.append((painted, base64.b64decode(event['data'])))
            started.set()
            await cdp.send('Page.screencastFrameAck', {'sessionId': event['sessionId']})
        started = asyncio.Event()
        frame_tasks = []
        frame_handler = lambda event: frame_tasks.append(asyncio.create_task(frame(event)))
        cdp.on('Page.screencastFrame', frame_handler)
        current = None
        async def perform(entry, section, index, beat_id, hand=None):
            try:
                return (await assertion(page, entry)) if section == 'expect' else await action(page, entry, events, root, hand)
            except Exception:
                from reshoot.repair import diagnose
                diagnosis = await diagnose(page, entry)
                if diagnosis:
                    metadata['failure'] = {**diagnosis, 'beat': beat_id, 'section': section, 'index': index}
                raise
        try:
            await page.goto(a.url or board.get('url', 'http://localhost:8000/'), wait_until='load', timeout=30000)
            await page.evaluate('document.fonts.ready')
            for index, entry in enumerate(board.get('setup', []), 1):
                await perform(entry, 'setup', index, ids[0])
            for previous in board['beat'][:split]:
                if previous.get('recording_issue'):
                    raise ValueError(f'Unresolved step {previous["id"]}: {previous["recording_issue"]}')
                for index, entry in enumerate(previous.get('action', []), 1):
                    await perform(entry, 'action', index, previous['id'])
                for index, entry in enumerate(previous.get('expect', []), 1):
                    await perform(entry, 'expect', index, previous['id'])
            metadata['replayed_before'] = ids[:split]
            # Force the first composition before capture starts. Without this Chrome can begin the take with a
            # blank frame even though the DOM and fonts are ready. Screenshots remain off camera; during capture
            # evidence must continue to come from the screencast itself.
            await page.screenshot()
            events.clear()
            clock = time.monotonic() - time.time()
            await cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 92, 'maxWidth': int(w*cap_dpr), 'maxHeight': int(h*cap_dpr)})
            # The video starts at the first frame, so wait for it before the first beat: on a slow machine it came
            # a third of a second late, and the start of the take was cut from the video.
            try:
                await asyncio.wait_for(started.wait(), 5)
            except asyncio.TimeoutError:
                pass  # a page that never paints still records; the first frame then starts the video, as before
            for beat in board['beat'][split:]:
                current = beat['id']
                if beat.get('recording_issue'):
                    raise ValueError(f'Unresolved step {current}: {beat["recording_issue"]}. Repair it in the storyboard before recording.')
                start = beats[current] = time.monotonic()
                result = {'id': current, 'purpose': beat.get('purpose'), 'caption': beat.get('caption'),
                          'definition_sha256': __import__('hashlib').sha256(json.dumps(beat, sort_keys=True).encode()).hexdigest(),
                          'status': 'running', 'expectations': []}
                metadata['beats'].append(result)
                await page.evaluate('p => __demo.caption(p[0], p[1])', [beat.get('caption'), beat.get('sub')])
                for index, entry in enumerate(beat.get('action', []), 1):
                    await perform(entry, 'action', index, current, hand)
                for index, entry in enumerate(beat.get('expect', []), 1):
                    try:
                        actual = await perform(entry, 'expect', index, current)
                    except Exception as error:
                        result['expectations'].append({'type': entry['type'], 'status': 'failed', 'error': redact(str(error))})
                        raise
                    result['expectations'].append({'type': entry['type'], 'status': 'passed', 'actual': redact(str(actual)), 'at': time.monotonic()})
                if errors:
                    raise RuntimeError('page error: ' + '; '.join(errors))
                result.update(verified_at=time.monotonic(), trim_wait=bool(beat.get('trim_wait')), min_reading=max(beat.get('min_reading', 0), board.get('caption', {}).get('min_seconds', 0)))
                shot = out.parent / (out.stem + '.evidence') / (current + '.png')
                shot.parent.mkdir(exist_ok=True)
                result.update(status='passed' if beat.get('expect') else 'unverified', screenshot=str(shot.relative_to(out.parent)), start=start)
                await asyncio.sleep(max(beat.get('hold', 1), beat.get('min_reading', 0), board.get('caption', {}).get('min_seconds', 0) if beat.get('caption') else 0, spoken.get(current, ('', 0))[1] + .3 - (time.monotonic() - start)))
                result['layout'] = await layout(page, beat)
                result['end'] = time.monotonic()
                await evidence(page, frames, shot)
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
            where = f'beat {current!r}' if current else 'opening the storyboard url'
            hint = ''
            if 'ERR_UNSAFE_PORT' in str(e):
                hint = ('. Chrome refuses some ports, such as 5060 and 6000: run the app on another port, or set '
                        'RESHOOT_CHROME_FLAGS=--explicitly-allowed-ports=PORT')
            raise RuntimeError(f'{where} failed: {redact(str(e))}{hint}') from None
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
    metadata['capture'] = {'css_width': w, 'css_height': h, 'pixel_ratio': cap_dpr, 'zoom': bool(z),
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
    # The take is recorded without captions, then the storyboard's are drawn on it, as a re-cut draws them again.
    by_id = {b['id']: b for b in board['beat']}
    shown = captions.timing([(e['t'], e) for e in metadata['events']], [b['id'] for b in metadata['beats']])
    out.with_suffix('.captions.json').write_text(json.dumps({'schema_version': 1, 'css_width': w, 'captions': [
        {**row, 'recorded': by_id[row['beat']].get('caption') or None, 'recorded_sub': by_id[row['beat']].get('sub') or None}
        for row in shown]}, indent=2))
    clean = out.with_suffix('.clean.mp4')
    if z:
        zoom.render(frames, events, clean, w, h, int(w*dpr)//2*2, int(h*dpr)//2*2, z, master=True)
    else:
        web.encode(frames, clean, size=f'{int(w*dpr)//2*2}:{int(h*dpr)//2*2}', master=True)
    captions.draw(out, board, a.storyboard)
    metadata['sha256'] = digest(out)


def main(a):
    board = story.load(a.storyboard)
    web.parse_size(a.size or board.get('size', '1280x720@1'))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    metadata = {'schema_version': 1, 'video': out.name, 'status': 'failed', 'story_id': board.get('id', Path(a.storyboard).stem), 'story_sha256': digest(a.storyboard), 'beats': [],
                'recording_settings_sha256': __import__('hashlib').sha256(json.dumps(
                    story.recording_settings(board), sort_keys=True).encode()).hexdigest()}
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
