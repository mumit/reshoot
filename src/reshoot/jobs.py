"""One studio job, with explicit transitions and cancellation bound to its generation."""
import os
import signal
import subprocess
import threading
from enum import Enum


class Phase(str, Enum):
    IDLE = 'idle'
    STARTING = 'starting'
    RUNNING = 'running'
    CANCELLING = 'cancelling'
    FINISHING = 'finishing'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


ACTIVE = {Phase.STARTING, Phase.RUNNING, Phase.CANCELLING, Phase.FINISHING}
TRANSITIONS = {
    Phase.IDLE: {Phase.STARTING},
    Phase.STARTING: {Phase.RUNNING, Phase.CANCELLING, Phase.FAILED},
    Phase.RUNNING: {Phase.CANCELLING, Phase.FINISHING, Phase.FAILED},
    Phase.CANCELLING: {Phase.CANCELLED},
    Phase.FINISHING: {Phase.SUCCEEDED, Phase.FAILED},
    Phase.SUCCEEDED: {Phase.STARTING},
    Phase.FAILED: {Phase.STARTING},
    Phase.CANCELLED: {Phase.STARTING},
}


class Job:
    def __init__(self):
        self.kind, self.lines, self.code, self.n, self.beat = None, [], None, 0, None
        self.lock = threading.RLock()
        self.proc, self.cancelled, self.result = None, False, None
        self.phase = Phase.IDLE

    def _transition(self, phase):
        if phase not in TRANSITIONS[self.phase]:
            raise RuntimeError(f'invalid job transition: {self.phase.value} to {phase.value}')
        self.phase = phase

    def running(self):
        with self.lock:
            return self.phase in ACTIVE

    def start(self, kind, cmd, cwd, beat=None, on_done=None, result=None):
        with self.lock:
            if self.running():
                raise ValueError(f'a {self.kind} is still running')
            self._transition(Phase.STARTING)
            self.kind, self.lines, self.code, self.n, self.beat = kind, [], None, self.n + 1, beat
            self.proc, self.cancelled, self.result = None, False, result

        def go():
            from reshoot.safety import redact
            try:
                proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, start_new_session=True)
                with self.lock:
                    self.proc = proc
                    cancelled = self.cancelled
                    if not cancelled:
                        self._transition(Phase.RUNNING)
                if cancelled:
                    self._stop(proc)
                for line in proc.stdout:
                    with self.lock:
                        self.lines.append(redact(line.rstrip()).replace(str(cwd) + '/', ''))
                code = proc.wait()
                with self.lock:
                    if self.cancelled:
                        self.code = 130
                        self._transition(Phase.CANCELLED)
                        return
                    if code:
                        self.code = code
                        self._transition(Phase.FAILED)
                        return
                    # The process completed. Applying its result is an indivisible
                    # finishing step: a late cancel must not label a saved repair cancelled.
                    self._transition(Phase.FINISHING)
                if on_done:
                    on_done()
                with self.lock:
                    self.code = 0
                    self._transition(Phase.SUCCEEDED)
            except Exception as error:
                with self.lock:
                    self.lines.append(redact(str(error)))
                    self.code = 130 if self.cancelled else 1
                    self._transition(Phase.CANCELLED if self.cancelled else Phase.FAILED)

        threading.Thread(target=go, daemon=True).start()

    @staticmethod
    def _stop(proc):
        if proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, signal.SIGINT)
        except ProcessLookupError:
            return

        def stop():
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        timer = threading.Timer(12, stop)
        timer.daemon = True
        timer.start()

    def cancel(self, expected=None):
        with self.lock:
            if expected is not None and (type(expected) is not int or expected != self.n):
                raise ValueError('The active job changed. Reload before cancelling it.')
            if self.phase not in (Phase.STARTING, Phase.RUNNING):
                return False
            self.cancelled = True
            self._transition(Phase.CANCELLING)
            proc = self.proc
        if proc:
            self._stop(proc)
        return True

    def json(self):
        with self.lock:
            return {'n': self.n, 'kind': self.kind, 'beat': self.beat, 'running': self.running(),
                    'state': self.phase.value, 'code': self.code, 'lines': self.lines[-400:],
                    'cancelled': self.cancelled,
                    'cancelable': self.phase in (Phase.STARTING, Phase.RUNNING),
                    **(self.result if self.phase == Phase.SUCCEEDED and self.result else {})}
