"""Show a short, truthful summary of the actual CLI run, without host paths."""
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

BASE = Path(__file__).resolve().parent
folder = Path(sys.argv[2])
if sys.argv[1] == 'start':
    (folder / 'terminal-start.json').write_text(json.dumps({
        'before':[str(p) for p in BASE.glob('takes/runs/*/run.json')],
        'monotonic':time.monotonic(), 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    },indent=2)+'\n')
    print('Recording the updated app...',flush=True)
else:
    before = json.loads((folder / 'terminal-start.json').read_text())
    reports = set(BASE.glob('takes/runs/*/run.json')) - {Path(p) for p in before['before']}
    code = int(sys.argv[3])
    report_path = reports.pop() if len(reports) == 1 else None
    report = json.loads(report_path.read_text()) if report_path else {}
    ok = code == 0 and report.get('ok') and report.get('expectations_status') == 'passed' and report.get('expectations_count') == 6 and report.get('mode') == 'final'
    receipt = {'exit_code':code,'ok':bool(ok),'run_report':str(report_path) if report_path else None,
        'elapsed_seconds':round(time.monotonic()-before['monotonic'],3),
        'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'cli_log_sha256':hashlib.sha256((folder / 'terminal-cli.log').read_bytes()).hexdigest()}
    (folder / 'terminal-result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if ok:
        print('Recording ready.\n6 result checks passed.\nMP4 saved. Review pending.',flush=True)
    else:
        print('Recording failed. Evidence retained.',flush=True)
        raise SystemExit(code or 1)
