"""Build a real, local notes workshop. Records pages only; never accepts or publishes."""
import argparse
import asyncio
from functools import partial
import hashlib
import http.server
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import tomllib
from types import SimpleNamespace
import urllib.request
import uuid

from reshoot import create, demonstrate, rec, review, story, studio, web
from media import CURSOR, Shoot, compose, save, speech

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


async def click(page, selector):
    item = page.locator(selector)
    await item.scroll_into_view_if_needed()
    box = await item.bounding_box()
    await page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2,steps=12)
    await asyncio.sleep(.35)
    await item.click()
    await asyncio.sleep(.45)


async def field(page, selector, value, save_field=True):
    await click(page,selector)
    await page.locator(selector).fill('')
    await page.locator(selector).press_sequentially(str(value),delay=48)
    if save_field:
        await page.locator(selector).press('Tab')
        await page.wait_for_function('!document.querySelector("[data-unsaved]")')
    await asyncio.sleep(.5)


async def nav_click(page, selector):
    async with page.expect_navigation(wait_until='load'):
        await click(page,selector)
    await asyncio.sleep(.7)


async def legacy_click(page, selector, toolbar=False):
    js = ('document.querySelector("reshoot-recorder").shadowRoot' if toolbar else 'document')
    coords = await page.run('const el='+js+'.querySelector('+json.dumps(selector)+'); '
                            'const r=el.getBoundingClientRect(); return [r.x+r.width/2,r.y+r.height/2]')
    x,y=coords
    await page.cmd('Input.dispatchMouseEvent',type='mouseMoved',x=x,y=y)
    await asyncio.sleep(.3)
    for kind in ('mousePressed','mouseReleased'):
        await page.cmd('Input.dispatchMouseEvent',type=kind,x=x,y=y,button='left',clickCount=1)
    await asyncio.sleep(.5)


async def legacy_type(page, value):
    for ch in value:
        await page.cmd('Input.insertText',text=ch); await asyncio.sleep(.055)
    await asyncio.sleep(.4)


async def recorder_tour(page, shoot):
    for _ in range(80):
        if await page.run('return !!document.querySelector("reshoot-recorder")'): break
        await asyncio.sleep(.1)
    await page.run(CURSOR)
    async def write(_):
        await asyncio.sleep(2)
        await legacy_click(page,'#text'); await legacy_type(page,'Pick up the bikes')
        for kind in ('keyDown','keyUp'):
            await page.cmd('Input.dispatchKeyEvent',type=kind,key='Enter',code='Enter',windowsVirtualKeyCode=13,
                           **({'text':'\r'} if kind=='keyDown' else {}))
    async def check(_):
        await asyncio.sleep(2); await legacy_click(page,'[data-do=check]',True)
        await legacy_click(page,'#list li')
    async def search(_):
        await asyncio.sleep(2); await legacy_click(page,'#q'); await legacy_type(page,'bike')
        await legacy_click(page,'[data-do=caption]',True)
        await legacy_click(page,'input[name=caption]',True); await legacy_type(page,'Find the matching note')
        await legacy_click(page,'form button',True)
    async def done(_):
        await asyncio.sleep(2); await legacy_click(page,'[data-do=done]',True)
    for key, action in [('write',write),('save-check',check),('search',search),('search-check',check),('done',done)]:
        await shoot.run(key,page,action)
    assert not page.errors,page.errors


def start_app(folder, state):
    app = folder/'app';app.mkdir(exist_ok=True)
    for name in ('index.html','about.html'):
        target=app/name
        if not target.exists(): shutil.copyfile(ROOT/'src/reshoot/templates'/name,target)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    port = state.get('app_port',8765)
    try:
        httpd=http.server.ThreadingHTTPServer(('127.0.0.1',port),partial(Quiet,directory=str(app)))
    except OSError:
        if state.get('app_port'): raise
        httpd=http.server.ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(app)))
    threading.Thread(target=httpd.serve_forever,daemon=True).start()
    state['app_port']=httpd.server_port
    return httpd,f'http://127.0.0.1:{httpd.server_port}/'


async def prelude(folder, lesson, shoot, app_url):
    from playwright.async_api import async_playwright
    await shoot.run('welcome')
    async with async_playwright() as pw:
        chrome=await pw.chromium.launch(executable_path=web.find_chrome(),headless=True,args=web.chrome_flags())
        try:
            context=await chrome.new_context(viewport={'width':1440,'height':810},locale='en-US',timezone_id='UTC')
            await context.add_init_script(CURSOR)
            page=await context.new_page(); await page.goto(app_url)
            await shoot.run('app',page)
        finally: await chrome.close()
    await shoot.run('command')


class Workshop:
    def __init__(self, folder, shoot, state, url):
        self.folder,self.shoot,self.state,self.url=folder,shoot,state,url
        self.config=folder/'demo/reshoot.toml'
        self.search=state['search']

    async def select(self,page):
        await click(page,f'[data-select-step="{self.search}"]')
        await page.locator(f'.beat[data-beat="{self.search}"]').scroll_into_view_if_needed()

    async def jump(self,page,target):
        if target in ('compare-panel','audio-panel','recipe-panel'):
            if not await page.locator('.more-tools').evaluate('el=>el.open'):
                await click(page,'.more-tools > summary')
        await click(page,f'.section-nav [data-jump="{target}"]')

    async def job(self,page,selector,expected=0,audition=False):
        def status():
            with urllib.request.urlopen(self.url+'job.json') as response:return json.load(response)
        previous=await asyncio.to_thread(status)
        await click(page,selector)
        start=time.monotonic()-self.shoot.began
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            value=await asyncio.to_thread(status)
            if value.get('n',0)>previous.get('n',0) and not value['running']: break
            await asyncio.sleep(.5)
        else: raise TimeoutError('The recorded Studio job did not finish in four minutes.')
        if expected is None: assert value['code'] != 0,value
        else: assert value['code']==expected,value
        if not audition:
            await page.wait_for_function('n => Number(document.body.dataset.seen)>=n',arg=value['n'],timeout=30000)
        self.shoot.wait=[start,time.monotonic()-self.shoot.began]
        save(self.folder/('job-'+str(value['n'])+'.json'),value)
        return value

    async def play(self,page,selected=False):
        if selected:
            await self.select(page); await click(page,'#play-selected')
        else:
            await self.jump(page,'preview-panel')
            await page.locator('#video').evaluate('el=>{el.muted=true;el.currentTime=0;el.play()}')
        await page.locator('#video').scroll_into_view_if_needed()

    async def run(self,page):
        row=f'.beat[data-beat="{self.search}"]'
        async def preview(p):await self.play(p)
        await self.shoot.run('first-preview',page,preview)
        await self.select(page)
        await self.shoot.run('proof',page)
        await self.shoot.run('story-files')
        async def selection(p):
            await self.jump(p,'story-panel'); await p.locator('#step-strip').scroll_into_view_if_needed()
            await click(p,'#step-choice-0'); await asyncio.sleep(2)
            await self.select(p)
        await self.shoot.run('selection',page,selection)
        await self.select(page)
        async def caption(p):
            await asyncio.sleep(2); await field(p,row+' [name=caption]','A note found in a moment')
        await self.shoot.run('caption',page,caption)
        async def hold(p):
            await asyncio.sleep(2); await field(p,row+' [name=hold]','3')
        await self.shoot.run('hold',page,hold)
        async def undo(p):
            await nav_click(p,'[data-history=undo]');await asyncio.sleep(2)
            await nav_click(p,'[data-history=redo]');await self.select(p)
        await self.shoot.run('undo',page,undo)
        await self.shoot.run('update',page,lambda p:self.job(p,'[data-job=update]'))
        await self.shoot.run('play-step',page,lambda p:self.play(p,True))
        async def shape(p):
            await self.jump(p,'look-panel')
            form=p.locator('.export-framing').first
            await form.scroll_into_view_if_needed();await asyncio.sleep(2)
            await form.locator('[name=fit]').select_option('crop')
            await form.locator('[name=display_width]').fill('390')
            await click(p,'.export-framing button[type=submit]');await asyncio.sleep(1)
            await self.jump(p,'preview-panel')
        await self.shoot.run('shape',page,shape)
        await self.select(page)
        async def replace(p):
            if not await p.locator(row+' .demonstrate-controls').evaluate('el=>el.open'):
                await click(p,row+' .demonstrate-controls > summary')
            await asyncio.sleep(2)
            await click(p,row+' [data-demonstrate][data-mode=replace]')
        await self.shoot.run('replace-intro',page,replace)
        # The Studio job runs the real demonstrated draft workflow in a child,
        # with native headless input and a camera on that page.
        if not self.shoot.complete('replace-review') and not self.shoot.complete('replace-show'):
            deadline=time.monotonic()+180
            while time.monotonic()<deadline:
                job=await page.evaluate('fetch("job.json").then(r=>r.json())')
                if not job['running']:
                    if job['code']!=0:raise RuntimeError(job)
                    break
                await asyncio.sleep(.5)
            else:raise TimeoutError('Demonstrated replacement did not finish.')
        if not self.shoot.complete('replace-review'):
            await page.wait_for_selector('#demonstration-panel',timeout=45000)
            await page.locator('#demonstration-panel').scroll_into_view_if_needed()
        async def use(p):
            await asyncio.sleep(5); await nav_click(p,'[data-demonstration=apply]')
        await self.shoot.run('replace-review',page,use)
        await self.shoot.run('replace-verify',page,lambda p:self.job(p,'[data-job=update]'))
        async def style(p):
            await self.jump(p,'look-panel')
            await p.locator('[data-style=midnight]').scroll_into_view_if_needed()
            await asyncio.sleep(2);await nav_click(p,'[data-style=midnight]')
            await self.jump(p,'preview-panel')
        await self.shoot.run('style',page,style)
        await self.select(page)
        async def narration(p):
            if not await p.locator(row+' .narration').evaluate('el=>el.open'):
                await click(p,row+' .narration > summary')
            await field(p,row+' .narration-form textarea','Find the note you saved by typing one of its words.',False)
            await click(p,row+' .narration-form button[type=submit]')
            await p.wait_for_function('!document.querySelector("[data-unsaved]")')
        await self.shoot.run('voice',page,narration)
        async def audition(p):
            await self.job(p,f'[data-audition="{self.search}"]',audition=True)
            await p.locator('#audition-player').evaluate('el=>{el.muted=true;el.pause()}')
            await p.locator('#audition-player').scroll_into_view_if_needed()
        await self.shoot.run('audition',page,audition)
        async def card(p):
            await self.jump(p,'look-panel')
            await nav_click(p,'[data-add-card=start]')
            await self.jump(p,'look-panel')
            await field(p,'.card input[name=text]','Find a note in seconds')
        await self.shoot.run('card',page,card)
        async def polished(p):
            await self.job(p,'[data-job=update]');await self.play(p)
            self.state['polished_run']=p and await p.locator('body').get_attribute('data-run')
            save(self.folder/'recording.json',self.state)
        await self.shoot.run('polished',page,polished)
        if 'polished_run' not in self.state:
            self.state['polished_run']=review.read(self.folder/'demo/latest')[1]['id']
        await self.shoot.run('data')
        await self.shoot.run('change')
        app=self.folder/'app/index.html'
        if 'id="q"' in app.read_text():
            snapshot=self.folder/'before-app-change';snapshot.mkdir(exist_ok=True)
            shutil.copy2(app,snapshot/'index.html')
            for name in ('reshoot.toml','storyboard.toml','edit.toml'):
                shutil.copy2(self.folder/'demo'/name,snapshot/name)
            app.write_text(app.read_text().replace('id="q"','id="note-search"').replace('querySelector("#q")','querySelector("#note-search")').replace('<h1>Notes ','<h1>Notes, refreshed '))
        async def refresh(p):
            await click(p,'details.advanced > summary')
            await self.job(p,'[data-job=preview]',expected=None)
        await self.shoot.run('refresh',page,refresh)
        if not self.shoot.complete('failure'):
            await page.locator('.failure').scroll_into_view_if_needed()
        await self.shoot.run('failure',page)
        async def repair(p):await self.job(p,'[data-repair=apply]')
        await self.shoot.run('repair',page,repair)
        async def verify(p):
            await self.job(p,'[data-job=update]');await self.play(p)
        await self.shoot.run('verify',page,verify)
        async def compare(p):
            await self.jump(p,'compare-panel')
            await p.locator('#comparison-source').select_option(self.state['polished_run'])
            await p.locator('.compare-playback').wait_for()
            await p.get_by_role('button',name='Play both',exact=True).wait_for(state='visible')
            await click(p,'.compare-playback button:has-text("Play both")')
            await p.locator('.compare-pair').first.scroll_into_view_if_needed()
        await self.shoot.run('compare',page,compare)
        await self.shoot.run('final',page,lambda p:self.job(p,'[data-job=run]'))
        await self.jump(page,'review-panel')
        await self.shoot.run('review',page)
        async def sheets(p):
            await click(p,'.scan > summary')
            image=p.locator('.scan a').first
            href=await image.get_attribute('href')
            await p.goto(self.url+href)
        await self.shoot.run('sheets',page,sheets)
        await page.goto(self.url)
        async def download(p):
            await self.jump(p,'download-panel')
            async with p.expect_download() as download:
                await click(p,'[data-bundle]')
            result=await download.value
            target=self.folder/'exports/notes-demo-exports.zip';target.parent.mkdir(exist_ok=True)
            await result.save_as(target)
        await self.shoot.run('download',page,download)
        await self.shoot.run('own-app')
        await self.shoot.run('close')


def record(folder, lesson, rehearse=False):
    state=read(folder/'recording.json')
    spoken=speech(folder,lesson)
    print('narration minutes',round(sum(row['seconds'] for row in spoken.values())/60,2),flush=True)
    if rehearse:
        state['mode']='rehearsal'
        spoken={key:{**value,'seconds':1} for key,value in spoken.items()}
    shoot=Shoot(folder,lesson,spoken)
    app,app_url=start_app(folder,state)
    lesson['scene'][2]['command']=lesson['scene'][2]['command'].replace('8765',str(app.server_port))
    save(folder/'lesson.json',lesson);save(folder/'recording.json',state)
    try:
        asyncio.run(prelude(folder,lesson,shoot,app_url))
        if not (folder/'demo/latest').exists():
            original=rec.session
            async def driven(url,w,h,calls,**kwargs):
                return await original(url,w,h,calls,headless=True,toolbar=True,drive=lambda page:recorder_tour(page,shoot))
            rec.session=driven
            try:
                code=create.main(SimpleNamespace(url=app_url,directory=str(folder/'demo'),size='1440x810@1',
                                                 no_studio=True,no_open=True,recipe=None,title=None))
                if code:raise RuntimeError('URL-based creation failed. Inspect the retained logs and draft.')
            finally:rec.session=original
        board=story.load(folder/'demo/storyboard.toml')
        if 'search' not in state:
            state['search']=next(row['id'] for row in board['beat'] if any(a.get('target',{}).get('css')=='#q' for a in row.get('action',[])))
        save(folder/'recording.json',state)
        original_start=studio.Job.start
        def start(self,kind,command,cwd,*args,**kwargs):
            if kind=='demonstrate':
                get=lambda flag:command[command.index(flag)+1]
                command=[sys.executable,str(BASE/'build.py'),'demonstrate','--attempt',str(folder),'--project',get('--project'),
                         '--beat',command[5],'--draft-id',get('--draft-id'),'--expected-revision',get('--expected-revision')]
            return original_start(self,kind,command,cwd,*args,**kwargs)
        studio.Job.start=start
        httpd,url,_=studio.server(SimpleNamespace(project=str(folder/'demo'),port=None))
        threading.Thread(target=httpd.serve_forever,daemon=True).start()
        async def studio_tour():
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                chrome=await pw.chromium.launch(executable_path=web.find_chrome(),headless=True,args=web.chrome_flags())
                try:
                    context=await chrome.new_context(viewport={'width':1440,'height':810},accept_downloads=True,locale='en-US',timezone_id='UTC')
                    await context.add_init_script(CURSOR)
                    page=await context.new_page(); page.set_default_timeout(20000)
                    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                    await page.goto(url)
                    await Workshop(folder,shoot,state,url).run(page)
                    assert not errors,errors
                finally:await chrome.close()
        try:asyncio.run(studio_tour())
        finally:
            httpd.reshoot_job.cancel();httpd.shutdown();httpd.server_close();studio.Job.start=original_start
        state.update(status='recorded',native_run=review.read(folder/'demo/latest')[1]['id'])
        save(folder/'recording.json',state)
    finally:app.shutdown();app.server_close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['record','compose','audit','demonstrate'])
    parser.add_argument('--attempt',type=Path)
    parser.add_argument('--reuse-speech',type=Path,help='reuse local cached speech from an earlier tutorial attempt')
    parser.add_argument('--rehearse',action='store_true',help='exercise the real workflow quickly; not a candidate video')
    parser.add_argument('--project');parser.add_argument('--beat');parser.add_argument('--draft-id');parser.add_argument('--expected-revision')
    args=parser.parse_args()
    lesson=tomllib.loads((BASE/'lesson.toml').read_text())
    if args.attempt:
        folder=args.attempt.resolve()
        if not folder.is_relative_to((ROOT/'takes/tutorial').resolve()):raise ValueError('Use an attempt under takes/tutorial/.')
    else:
        if args.operation!='record':parser.error('--attempt is required for an existing recording')
        folder=ROOT/'takes/tutorial'/('attempt-'+uuid.uuid4().hex[:12]);folder.mkdir(parents=True)
        sources=folder/'source';sources.mkdir()
        for path in BASE.glob('*'):
            if path.is_file():shutil.copy2(path,sources/path.name)
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        save(folder/'recording.json',{'status':'recording','created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
             'commit':commit,'capture':'headless browser pages only; native input; synthetic notes; local synthetic narration',
             'owner_review':'pending','accepted_media':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'docs/demo').glob('*') if p.is_file()}})
        if args.reuse_speech:
            previous=args.reuse_speech.resolve()
            if not previous.is_relative_to((ROOT/'takes/tutorial').resolve()):raise ValueError('Reuse speech only from a local tutorial attempt.')
            shutil.copytree(previous/'speech',folder/'speech')
    print('attempt',folder,flush=True)
    invocation=folder/'invocations'/('run-'+uuid.uuid4().hex[:10]);invocation.mkdir(parents=True)
    for source in BASE.glob('*'):
        if source.is_file():shutil.copy2(source,invocation/source.name)
    class Tee:
        def __init__(self,first,second):self.first,self.second=first,second
        def write(self,value):self.first.write(value);self.second.write(value);self.flush()
        def flush(self):self.first.flush();self.second.flush()
    log=(invocation/'process.log').open('w',buffering=1)
    sys.stdout=Tee(sys.stdout,log);sys.stderr=Tee(sys.stderr,log)
    if args.operation=='record':record(folder,lesson,args.rehearse)
    elif args.operation=='compose':compose(folder,read(folder/'lesson.json'),read(folder/'speech.json'))
    elif args.operation=='demonstrate':
        spoken=read(folder/'speech.json')
        if read(folder/'recording.json').get('mode')=='rehearsal':
            spoken={key:{**value,'seconds':1} for key,value in spoken.items()}
        shoot=Shoot(folder,lesson,spoken)
        async def drive(page):
            await page.evaluate(CURSOR)
            async def act(p):
                await asyncio.sleep(2);await field(p,'#q','bikes',False)
                await click(p,'reshoot-recorder [data-do=done]')
            await shoot.run('replace-show',page,act)
        ident=demonstrate.record(args.project,args.beat,headless=True,drive=drive,
                                draft_id=args.draft_id,expected_revision=args.expected_revision)
        print('Separate draft saved',ident,flush=True)
    else:
        from audit import audit
        audit(folder)


if __name__=='__main__':main()
