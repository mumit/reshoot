"""Record, compose and check the local reshoot promotion. Never publishes."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import time
import uuid

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUTPUT = ROOT / 'takes/promo'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def cli():
    local = Path(sys.executable).parent / 'reshoot'
    found = str(local) if local.exists() else shutil.which('reshoot')
    if not found:
        raise RuntimeError('Install reshoot and run this script in its Python environment')
    return found


def execute(args, folder, name, timeout=200):
    began = time.monotonic()
    with (folder / (name+'.stdout')).open('w') as out, (folder / (name+'.stderr')).open('w') as err:
        result = subprocess.run(list(map(str,args)), cwd=ROOT, stdout=out, stderr=err, timeout=timeout)
    save(folder / (name+'.command.json'),{'command':list(map(str,args)),'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-began,3)})
    if result.returncode:
        detail='\n'.join((folder/(name+'.stderr')).read_text().splitlines()[-12:])
        raise RuntimeError(f'{name} failed ({result.returncode}); logs retained in {folder}\n{detail}')


def capture(config, mode, folder, name):
    before = set(BASE.glob('takes/runs/*/run.json'))
    execute([cli(),mode,str(BASE/config)],folder,name)
    added = set(BASE.glob('takes/runs/*/run.json'))-before
    assert len(added)==1, 'Expected one isolated native run'
    path = added.pop()
    report=json.loads(path.read_text())
    assert report['ok'] and report['expectations_status']=='passed' and report['expectations_count']==6
    return str(path.relative_to(ROOT))


def record():
    if not shutil.which('vhs'):
        raise RuntimeError('VHS is needed to record the real command')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    folder=OUTPUT/('attempt-'+uuid.uuid4().hex[:12]);folder.mkdir()
    source_files=[p for p in BASE.rglob('*') if p.is_file() and 'takes' not in p.relative_to(BASE).parts and '__pycache__' not in p.parts]
    save(folder/'inputs.json',{str(p.relative_to(ROOT)):sha(p) for p in source_files})
    for source in source_files:
        target=folder/'source-recipe'/source.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    originals=folder/'original-docs';originals.mkdir()
    for name in ('notes.mp4','notes.gif'):
        shutil.copyfile(ROOT/'docs/demo'/name,originals/name)
    state={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':platform.platform(),
        'capture':'headless browser pages and clean VHS terminal only; synthetic notes',
        'source_inputs_sha256':sha(folder/'inputs.json'),'runs':{},'status':'recording'}
    save(folder/'recording.json',state)
    execute([cli(),'--version'],folder,'version')
    execute([cli(),'doctor','--config',str(BASE/'release-v1.toml'),'--json'],folder,'doctor')
    for key,config,mode in [('v1-preview','release-v1.toml','preview'),('v1','release-v1.toml','run'),('v2-preview','release-v2.toml','preview')]:
        state['runs'][key]=capture(config,mode,folder,key)
        save(folder/'recording.json',state)
        print(key,'passed',flush=True)
    # Only the real command and a result-derived summary are displayed. Raw CLI
    # logs retain diagnostic paths off-screen. No host prompt/history is shown.
    shell=folder/'terminal-shell.sh'
    summary=shlex.quote(str(BASE/'terminal-result.py'))
    dest=shlex.quote(str(folder));python=shlex.quote(sys.executable)
    shell.write_text(f'''cd {shlex.quote(str(ROOT))}
PS1='$ '
PATH={shlex.quote(str(Path(sys.executable).parent)+':/opt/homebrew/bin:/usr/bin:/bin')}
export PATH PS1
reshoot() {{
  {python} {summary} start {dest}
  {shlex.quote(cli())} "$@" > {shlex.quote(str(folder/'terminal-cli.log'))} 2>&1
  promo_code=$?
  {python} {summary} finish {dest} "$promo_code"
  return "$promo_code"
}}
clear
''')
    tape=folder/'command.tape'
    bootstrap="env -i PATH=/opt/homebrew/bin:/usr/bin:/bin TERM=xterm-256color LANG=en_US.UTF-8 bash --noprofile --norc"
    tape.write_text(f'''Output {json.dumps(str(folder/'terminal-full.mp4'))}
Set Shell "bash"
Set FontFamily "monospace"
Set FontSize 23
Set Width 960
Set Height 360
Set Padding 26
Set Framerate 30
Set TypingSpeed 45ms
Set Theme "Catppuccin Mocha"
Hide
Type {json.dumps(bootstrap)} Enter
Type {json.dumps('source '+shlex.quote(str(shell)))} Enter
Sleep 500ms
Show
Sleep 400ms
Type "reshoot run examples/promo/release-v2.toml" Enter
Sleep 55s
''')
    execute(['vhs',str(tape)],folder,'vhs',timeout=160)
    result=json.loads((folder/'terminal-result.json').read_text())
    assert result['ok'] and result['exit_code']==0
    state['runs']['v2']=str(Path(result['run_report']).relative_to(ROOT))
    execute([cli(),'compare',str((ROOT/state['runs']['v1']).parent),str((ROOT/state['runs']['v2']).parent),'--out',str(folder/'comparison.json')],folder,'compare')
    comparison=json.loads((folder/'comparison.json').read_text())
    assert len(comparison['beats'])==4 and all(b['change']=='matched' and not b['definition_changed'] for b in comparison['beats'])
    state['status']='recorded';state['terminal_elapsed_seconds']=result['elapsed_seconds']
    save(folder/'recording.json',state)
    print('Recordings retained:',folder,flush=True)
    return folder


def selected(path):
    if path:
        return Path(path).resolve()
    attempts=sorted(OUTPUT.glob('attempt-*/recording.json'))
    if len(attempts)!=1:
        raise RuntimeError('Specify --attempt when more than one attempt exists')
    return attempts[0].parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['record','compose','audit','all'],nargs='?',default='all')
    parser.add_argument('--attempt')
    args=parser.parse_args()
    folder=record() if args.action in ('record','all') else selected(args.attempt)
    if args.action in ('compose','all'):
        edit_recipe=folder/('edit-recipe-'+uuid.uuid4().hex[:8]);edit_recipe.mkdir()
        for name in ('render.py','audit.py'):
            shutil.copyfile(BASE/name,edit_recipe/name)
        save(edit_recipe/'inputs.json',{name:sha(edit_recipe/name) for name in ('render.py','audit.py')})
        execute([sys.executable,str(BASE/'render.py'),str(folder)],folder,'compose',timeout=300)
        print('Composed social MP4 and README loop.',flush=True)
    if args.action in ('audit','all'):
        execute([sys.executable,str(BASE/'audit.py'),str(folder)],folder,'audit',timeout=300)
        print('Media and native-result audit passed.',flush=True)
    print(folder,flush=True)


if __name__=='__main__':
    main()
