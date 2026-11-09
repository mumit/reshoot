"""Workflow contracts across users, HTTP clients and agents, with synthetic data."""
import itertools
import json
import threading
from types import SimpleNamespace

import pytest

from reshoot import create, jobs, journey, studio, workflow
from reshoot.session import Session
from test_journey import recording, setup


@pytest.mark.parametrize('creating,missing,recovering,busy', list(itertools.product([False, True], repeat=4)))
def test_recording_capabilities_and_next_action_agree(creating, missing, recovering, busy):
    base = {'phase': 'review', 'next': 'review', 'pending': False, 'title': 'Final', 'detail': ''}
    state = journey.workflow(base, creating=creating, tools={'ok': not missing},
                session={'title': 'Recover', 'detail': 'Choose history.'} if recovering else None,
                job={'running': True, 'state': 'running', 'cancelable': True} if busy else None,
                has_run=True)
    expected = 'cancel' if busy else 'session' if recovering else 'setup' if missing else 'create' if creating else 'review'
    assert state['next'] == expected and state['action']['enabled']
    for kind in ('update', 'run', 'preview', 'from', 'recut'):
        assert state['actions'][kind]['enabled'] == (not (creating or missing or recovering or busy))
        assert bool(state['actions'][kind]['reason']) != state['actions'][kind]['enabled']
    # Earlier evidence stays available even when recording or editing is blocked.
    assert state['actions']['download']['enabled']
    assert base['phase'] == 'review' and 'actions' not in base


def test_acceptance_is_separate_from_tools_and_recording_jobs():
    assert journey.permissions(has_run=True, tools={'ok': False})['accept']['enabled']
    for context in ({'pending': True}, {'mode': 'preview'}, {'session': {'title': 'Recover'}},
                    {'job': {'running': True}}):
        assert not journey.permissions(has_run=True, **context)['accept']['enabled']
    assert not journey.permissions()['accept']['enabled']


def tree(folder):
    return {str(path.relative_to(folder)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in folder.rglob('*') if path.is_file()}


def test_status_is_read_only_and_does_not_probe_or_render(tmp_path, monkeypatch, capsys):
    config, board, edit = setup(tmp_path)
    run = recording(tmp_path, config, board, edit, mode='final')
    original = tree(tmp_path)
    monkeypatch.setattr('reshoot.setup.inspect', lambda *a, **k: pytest.fail('status must not probe tools'))
    monkeypatch.setattr('reshoot.cut.probe', lambda *a, **k: pytest.fail('status must not inspect video'))
    from reshoot.cli import main
    with pytest.raises(SystemExit) as result:
        main(['status', str(tmp_path), '--json'])
    assert result.value.code == 0
    data = json.loads(capsys.readouterr().out)
    assert data['schema_version'] == 1 and data['ok']
    assert data['run']['id'] == run[0].name and data['run']['review'] == 'pending'
    assert data['workflow']['next'] == 'review'
    assert run[0].name in data['workflow']['action']['command']
    assert data['workflow']['states']['tools'] == 'unknown'
    assert data['observation']['live_jobs'] == 'not_observed'
    actions = data['workflow']['actions']
    # Only actions with something to act on are offered, and those that wait for a person say so.
    assert not actions['repair']['enabled'] and 'No stopped step' in actions['repair']['reason']
    assert not actions['audition']['enabled'] and 'narration' in actions['audition']['reason']
    assert not actions['recut']['enabled'] and actions['recut']['reason'].startswith('A re-cut only applies')
    assert actions['review']['waits_for_person'] and actions['download']['waits_for_person']
    assert not actions['run']['waits_for_person'] and actions['from']['command'].endswith('--from STEP')
    assert tree(tmp_path) == original
    assert not (tmp_path / 'takes/studio').exists()


def test_status_and_studio_use_the_same_source_and_update_decision(tmp_path):
    config, board, edit = setup(tmp_path)
    run = recording(tmp_path, config, board, edit)
    studio.edit(board, {'beat': 'search', 'caption': 'A clearer caption'})
    status = workflow.inspect(tmp_path)['workflow']
    state = studio.workflow(config, tmp_path, studio.project(config)[2], run,
                            context={'creation_pending': False, 'setup': None, 'failure': None})
    assert status['phase'] == state['phase'] == 'pending'
    assert status['update_kind'] == state['update_kind'] == 'recut'
    assert status['actions']['accept']['enabled'] is False
    studio.edit(board, {'beat': 'search', 'hold': 7})
    assert workflow.inspect(config)['workflow']['update_kind'] == 'preview'


def test_tools_remain_blocked_in_live_status_after_a_successful_run(tmp_path, monkeypatch):
    config, board, edit = setup(tmp_path)
    run = recording(tmp_path, config, board, edit)
    monkeypatch.setattr('reshoot.setup.current', lambda _: {'ok': False})
    state = workflow.describe(config, tmp_path, workflow.project(config)[2], run)
    assert state['next'] == 'setup' and not state['actions']['run']['enabled']
    # Disk-only observation explicitly leaves tool readiness unknown instead.
    assert workflow.inspect(config)['workflow']['states']['tools'] == 'unknown'


def test_status_preserves_history_and_explains_recovery(tmp_path):
    config, board, _ = setup(tmp_path)
    history = Session(config, workflow.editable_paths(config))
    with history.transaction():
        history.change(lambda: studio.edit(board, {'beat': 'search', 'caption': 'Saved caption'}))
    board.write_text(board.read_text() + '# external edit\n')
    original = tree(tmp_path)
    status = workflow.inspect(config)
    assert status['workflow']['next'] == 'session'
    assert not status['workflow']['actions']['update']['enabled']
    assert tree(tmp_path) == original
    observer = Session(config, workflow.editable_paths(config), read_only=True)
    for operation in (lambda: observer.recover('fresh', observer.token),
                      lambda: observer.change(lambda: board.write_text('wrong')),
                      lambda: observer.move('undo')):
        with pytest.raises(ValueError, match='read-only'):
            operation()
    assert tree(tmp_path) == original


def test_status_reports_pending_creation_and_malformed_state_without_writing(tmp_path, capsys):
    setup(tmp_path)
    create.save(tmp_path, {'schema_version': 1, 'stage': 'preview', 'url': None, 'size': '640x360@1'})
    original = tree(tmp_path)
    result = workflow.inspect(tmp_path)
    assert result['creation'] == 'preview' and result['workflow']['next'] == 'create'
    assert not result['workflow']['actions']['run']['enabled']
    assert tree(tmp_path) == original
    create.state_file(tmp_path).write_text('{broken')
    original = tree(tmp_path)
    assert workflow.main(SimpleNamespace(project=tmp_path, json=True)) == 2
    assert json.loads(capsys.readouterr().out)['ok'] is False
    assert tree(tmp_path) == original


def test_job_cannot_be_cancelled_after_success_or_during_result_application(tmp_path):
    import sys
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    def apply():
        entered.set()
        assert release.wait(5)
        finished.set()
    job = jobs.Job()
    job.start('repair', [sys.executable, '-c', 'print("repaired")'], tmp_path, on_done=apply,
              result={'saved': True})
    try:
        assert entered.wait(5)
        snapshot = job.json()
        assert snapshot['state'] == 'finishing' and snapshot['running'] and not snapshot['cancelable']
        assert job.cancel(snapshot['n']) is False
        with pytest.raises(ValueError, match='still running'):
            job.start('run', [], tmp_path)
    finally:
        release.set()
    wait_done(job)
    assert finished.is_set() and job.json()['state'] == 'succeeded'
    assert job.json()['saved'] and job.code == 0
    assert job.cancel(job.n) is False and not job.cancelled


def wait_done(job):
    import time
    deadline = time.monotonic() + 5
    while job.running() and time.monotonic() < deadline:
        threading.Event().wait(.01)
    assert not job.running()


def test_stale_cancel_cannot_stop_a_new_job_and_cancel_before_spawn_is_retained(tmp_path, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    killed, applied = [], []
    class Process:
        stdout = ()
        def poll(self): return None
        def wait(self): return -2  # ended by the cancel's SIGINT, as a real command is
    def spawn(*a, **k):
        entered.set()
        assert release.wait(5)
        return Process()
    monkeypatch.setattr(jobs.subprocess, 'Popen', spawn)
    monkeypatch.setattr(jobs.Job, '_stop', staticmethod(lambda proc: killed.append(proc)))
    job = jobs.Job()
    job.start('preview', [], tmp_path, on_done=lambda: applied.append(True), result={'saved': True})
    try:
        assert entered.wait(5)
        with pytest.raises(ValueError, match='active job changed'):
            job.cancel(job.n - 1)
        assert not job.cancelled and job.json()['state'] == 'starting'
        assert job.cancel(job.n)
        assert job.json()['state'] == 'cancelling'
    finally:
        release.set()
    wait_done(job)
    assert killed and not applied
    assert job.code == 130 and job.json()['state'] == 'cancelled' and 'saved' not in job.json()


def test_work_that_finishes_despite_a_late_cancel_succeeds_and_applies_its_result(tmp_path):
    import sys
    applied = []
    job = jobs.Job()
    # Ignores the cancel's SIGINT, as a repair does once it has saved the story, then finishes normally.
    script = 'import signal, time; signal.signal(signal.SIGINT, signal.SIG_IGN); print("saved", flush=True); time.sleep(1)'
    job.start('repair', [sys.executable, '-c', script], tmp_path, on_done=lambda: applied.append(True))
    deadline = __import__('time').monotonic() + 5
    while not job.json()['lines'] and __import__('time').monotonic() < deadline:
        threading.Event().wait(.01)
    assert job.cancel(job.n)
    wait_done(job)
    assert job.json()['state'] == 'succeeded' and applied and not job.cancelled


def test_settle_reconciles_a_cancelled_or_failed_job_before_another_can_start(tmp_path):
    import sys
    settled = []
    job = jobs.Job()
    def settle():
        settled.append(job.running())  # still counts as running, so no other job can start in between
    job.start('repair', [sys.executable, '-c', 'raise SystemExit(3)'], tmp_path, on_done=lambda: settled.append('done'),
              settle=settle)
    wait_done(job)
    assert settled == [True] and job.json()['state'] == 'failed' and job.code == 3
    def broken(): raise ValueError('could not record the repair in Undo')
    job.start('repair', [sys.executable, '-c', 'raise SystemExit(4)'], tmp_path, settle=broken)
    wait_done(job)
    assert job.json()['state'] == 'failed' and 'could not record the repair in Undo' in job.json()['lines']


def test_a_result_step_that_hangs_ends_the_job_instead_of_holding_the_studio(tmp_path):
    import sys
    release = threading.Event()
    job = jobs.Job()
    job.finish_timeout = .2
    job.start('repair', [sys.executable, '-c', 'pass'], tmp_path, on_done=lambda: release.wait(5))
    try:
        wait_done(job)
        assert job.json()['state'] == 'failed' and any('taking too long' in line for line in job.json()['lines'])
        job.start('preview', [sys.executable, '-c', 'pass'], tmp_path)  # the studio can go on
        wait_done(job)
        assert job.json()['state'] == 'succeeded'
    finally:
        release.set()


def test_failed_result_application_is_failed_and_allows_another_job(tmp_path):
    import sys
    def fail(): raise ValueError('Could not remember the repaired source')
    job = jobs.Job()
    job.start('repair', [sys.executable, '-c', 'pass'], tmp_path, on_done=fail)
    wait_done(job)
    assert job.json()['state'] == 'failed' and job.code == 1
    job.start('preview', [sys.executable, '-c', 'pass'], tmp_path)
    wait_done(job)
    assert job.json()['state'] == 'succeeded' and job.n == 2


def test_latest_failure_does_not_replace_the_last_successful_run(tmp_path):
    config, board, edit = setup(tmp_path)
    root, report = recording(tmp_path, config, board, edit, mode='final')
    failure = root.parent / ('b' * 32)
    failure.mkdir()
    (failure / 'run.json').write_text(json.dumps({'id': failure.name, 'ok': False, 'mode': 'preview',
                  'finished_at': '2099-01-01T00:00:00+00:00', 'errors': ['synthetic stopped step'], 'files': []}))
    result = workflow.inspect(config)
    assert result['run']['id'] == root.name and result['run']['execution'] == 'succeeded'
    assert result['failure']['id'] == failure.name
    assert result['workflow']['phase'] == 'stopped' and result['workflow']['next'] == 'update'
    # A stop without a missing control is not something a locator repair can fix.
    assert not result['workflow']['actions']['repair']['enabled']


def test_status_offers_repair_only_for_a_stopped_step_with_a_missing_control(tmp_path, monkeypatch):
    config, board, edit = setup(tmp_path)
    recording(tmp_path, config, board, edit, mode='final')
    stopped = {'id': 'c' * 32, 'beat': 'search', 'repairable': True, 'repaired': False, 'stale': False}
    monkeypatch.setattr('reshoot.workflow.failed', lambda *args: stopped)
    repair = workflow.inspect(config)['workflow']['actions']['repair']
    assert repair['enabled'] and repair['command'].endswith('takes/runs/' + 'c' * 32)
    assert not repair['waits_for_person']
    stopped['repaired'] = True  # the control was updated; the next step is recording again, not another repair
    assert not workflow.inspect(config)['workflow']['actions']['repair']['enabled']


def test_http_status_guards_jobs_and_stale_cancellation_with_the_same_capabilities(tmp_path, monkeypatch):
    import sys
    import urllib.parse
    import urllib.request
    from reshoot.workspace import History
    config, _, _ = setup(tmp_path)
    monkeypatch.setattr('reshoot.setup.current', lambda _: {'ok': True})
    server, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    job = server.reshoot_job
    try:
        job.start('preview', [sys.executable, '-c', 'import time; time.sleep(30)'], tmp_path)
        revision = History(workflow.editable_paths(config)).revision()
        with urllib.request.urlopen(url + 'state.json?' + urllib.parse.urlencode({'revision': revision})) as response:
            state = json.load(response)
        assert state['phase'] == 'busy' and state['next'] == 'cancel'
        assert not state['actions']['preview']['enabled']
        def post(action, values):
            request = urllib.request.Request(url + action, data=json.dumps({'revision': revision, **values}).encode(),
                                             headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request) as response:
                return json.load(response)
        assert post('job', {'kind': 'preview'})['error'] == state['actions']['preview']['reason']
        assert 'active job changed' in post('cancel', {'job_n': job.n - 1})['error']
        assert job.running() and not job.cancelled
        assert post('cancel', {'job_n': job.n})['ok']
        wait_done(job)
        assert job.json()['state'] == 'cancelled'
        late = post('cancel', {'job_n': job.n})
        assert not late['ok'] and 'no longer be cancelled' in late['error']
    finally:
        job.cancel()
        server.shutdown()
        server.server_close()


@pytest.mark.browser
def test_reopening_during_a_job_then_cancelling_restores_controls_and_explanations(tmp_path, monkeypatch):
    import sys
    from playwright.sync_api import expect, sync_playwright
    from reshoot import web
    config, _, _ = setup(tmp_path)
    monkeypatch.setattr('reshoot.setup.current', lambda _: {'ok': True, 'checks': []})
    server, url, _ = studio.server(SimpleNamespace(project=str(tmp_path), port=None))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    job = server.reshoot_job
    try:
        job.start('preview', [sys.executable, '-c', 'import time; time.sleep(30)'], tmp_path)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=web.find_chrome(), headless=True)
            page = browser.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            final = page.locator('[data-job=run]')
            expect(final).to_be_disabled()
            expect(final).to_have_attribute('title', 'An update is running. Wait for it or cancel before changing the project.')
            page.screenshot(path=str(tmp_path / 'job-running.png'))
            page.click('#cancel')
            expect(page.locator('#job-title')).to_contain_text('cancelled')
            expect(page.locator('#job-title')).to_contain_text('Your saved story is kept.')
            expect(final).to_be_enabled()
            expect(final).to_have_attribute('title', 'Record the full-size video for review')
            # The editing panel the server sent locked for the job is usable again without a reload.
            page.wait_for_function("() => !document.querySelector('fieldset.side-fields').disabled", timeout=5000)
            assert not errors and job.json()['state'] == 'cancelled'
            page.screenshot(path=str(tmp_path / 'job-cancelled.png'))
            browser.close()
    finally:
        job.cancel()
        server.shutdown()
        server.server_close()
