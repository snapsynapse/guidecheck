"""Experimental SEC-003 worker boundary; not wired into the API or scanner.

POSIX candidate only. A fixed child runs the existing transport. The parent
bounds admission, IPC, completion and cleanup; no guide commands are executed.
"""
from __future__ import annotations

import base64
import json
import math
import os
from pathlib import Path
import selectors
import subprocess
import sys
import threading
import time

# -I omits the script directory. Bootstrap only this installed/bundled sibling
# directory, never cwd or PYTHONPATH. The worker is also tested outside checkout.
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from guidecheck_fetch import FetchError, FetchResult, MAX_BYTES, MAX_REDIRECTS, REPORT_HEADERS, TOTAL_DEADLINE

MAX_INPUT = 64 * 1024
# Body base64 (~350 KiB), four bounded HTTP header fields, redirect/URL metadata.
# This is a separate IPC envelope cap, not a profile or guide-size change.
MAX_OUTPUT = 2 * 1024 * 1024
TERM_GRACE = 0.05
KILL_GRACE = 0.5
_MESSAGES = {
    'scheme': 'only https guide URLs are accepted',
    'invalid-url': 'the URL is invalid',
    'dns-failed': 'the host could not be resolved',
    'blocked-target': 'the host resolves to a non-public address',
    'cross-domain-redirect': 'the URL redirected to a different registered domain',
    'tls': 'the TLS certificate could not be verified',
    'timeout': 'the request exceeded the time limit',
    'connect-failed': 'the host could not be reached',
    'bad-redirect': 'a redirect response had no target',
    'too-large': 'the guide exceeds the size limit',
    'read-failed': 'the response could not be read',
    'too-many-redirects': 'the URL redirected too many times',
    'fetch-failed': 'the fetch worker could not complete the request',
}


def _error(code='fetch-failed'):
    return FetchError(code, _MESSAGES[code])


def _frame(raw, event, pid):
    value = json.loads(raw)
    if (not isinstance(value, dict) or value.get('event') != event
            or type(value.get('pid')) is not int or value['pid'] != pid):
        raise ValueError('invalid worker frame')
    return value


def _decode(raw, pid):
    lines = raw.splitlines()
    if len(lines) != 2:
        raise ValueError('invalid worker framing')
    _frame(lines[0], 'ready', pid)
    last = json.loads(lines[1])
    if isinstance(last, dict) and last.get('event') == 'error':
        last = _frame(lines[1], 'error', pid)
        code = last.get('code')
        if code not in _MESSAGES:
            raise ValueError('unknown worker error')
        return _error(code)
    last = _frame(lines[1], 'result', pid)
    value = last.get('fetch')
    if not isinstance(value, dict) or set(value) != {'final_url', 'status', 'headers', 'body', 'redirects', 'tls_valid'}:
        raise ValueError('invalid worker result')
    if not isinstance(value['final_url'], str) or len(value['final_url']) > MAX_INPUT:
        raise ValueError('invalid final URL')
    if type(value['status']) is not int or not 100 <= value['status'] <= 599:
        raise ValueError('invalid status')
    headers = value['headers']
    if (not isinstance(headers, dict) or not set(headers) <= REPORT_HEADERS
            or not all(isinstance(v, str) for v in headers.values())):
        raise ValueError('invalid headers')
    encoded = value['body']
    if not isinstance(encoded, str) or len(encoded) > 4 * ((MAX_BYTES + 2) // 3):
        raise ValueError('invalid body encoding')
    body = base64.b64decode(encoded, validate=True)
    if len(body) > MAX_BYTES:
        raise ValueError('invalid body size')
    redirects = value['redirects']
    if not isinstance(redirects, list) or len(redirects) > MAX_REDIRECTS:
        raise ValueError('invalid redirects')
    for hop in redirects:
        if (not isinstance(hop, dict) or set(hop) != {'from', 'to', 'status'}
                or type(hop['status']) is not int or hop['status'] not in (301, 302, 303, 307, 308)
                or not all(isinstance(hop[k], str) and len(hop[k]) <= MAX_INPUT for k in ('from', 'to'))):
            raise ValueError('invalid redirect')
    if type(value['tls_valid']) is not bool:
        raise ValueError('invalid TLS result')
    return FetchResult(value['final_url'], value['status'], headers, body, redirects, value['tls_valid'])


class _Supervisor:
    def __init__(self, entrypoint=None, capacity=2):
        self.entrypoint = Path(entrypoint or __file__).resolve()
        self.gate = threading.BoundedSemaphore(capacity)
        self.lock = threading.Lock()
        self.active = {}

    def _cleanup(self, proc, force=False):
        def attempt(call):
            try:
                call()
            except (OSError, ValueError, subprocess.TimeoutExpired):
                pass
        try:
            attempt(proc.poll)
            if proc.returncode is None:
                if not force:
                    attempt(proc.terminate)
                    attempt(lambda: proc.wait(timeout=TERM_GRACE))
                if proc.returncode is None:
                    attempt(proc.kill)
                    attempt(lambda: proc.wait(timeout=KILL_GRACE))
        finally:
            try:
                attempt(proc.stdin.close)
            finally:
                attempt(proc.stdout.close)
        clean = proc.returncode is not None and proc.stdin.closed and proc.stdout.closed
        if clean:
            with self.lock:
                removed = self.active.pop(proc.pid, None)
            if removed is not None:
                self.gate.release()
        return clean

    def close(self):
        """Retry this supervisor's retained resources only; no background pool."""
        with self.lock:
            children = list(self.active.values())
        return all([self._cleanup(proc, force=True) for proc in children])

    def fetch(self, url, request_profile='default', accept_override=None, *, deadline=None):
        start = time.monotonic()
        if deadline is not None and (not isinstance(deadline, (int, float)) or not math.isfinite(deadline)):
            raise _error('timeout')
        expires = min(start + TOTAL_DEADLINE, deadline) if deadline is not None else start + TOTAL_DEADLINE
        def remaining():
            return max(0.0, expires - time.monotonic())
        if os.name != 'posix':
            raise _error()
        for value in (url, request_profile, accept_override):
            if value is not None and (not isinstance(value, str) or len(value) > MAX_INPUT):
                raise _error('invalid-url')
        if not isinstance(url, str) or not isinstance(request_profile, str):
            raise _error('invalid-url')
        request = json.dumps({'url': url, 'request_profile': request_profile,
                              'accept_override': accept_override}).encode('utf-8')
        if len(request) > MAX_INPUT:
            raise _error('invalid-url')
        if not remaining() or not self.gate.acquire(timeout=remaining()):
            raise _error('timeout')
        proc = None
        selector = None
        pending_error = False
        try:
            if not remaining():
                raise _error('timeout')
            env = {'PATH': os.defpath}
            for name in ('SSL_CERT_FILE', 'SSL_CERT_DIR'):
                if name in os.environ:
                    env[name] = os.environ[name]
            proc = subprocess.Popen([sys.executable, '-I', '-u', str(self.entrypoint)],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, bufsize=0, close_fds=True,
                                    start_new_session=True, env=env)
            with self.lock:
                self.active[proc.pid] = proc
            if not remaining():
                raise _error('timeout')
            os.set_blocking(proc.stdin.fileno(), False)
            os.set_blocking(proc.stdout.fileno(), False)
            selector = selectors.DefaultSelector()
            selector.register(proc.stdin, selectors.EVENT_WRITE)
            selector.register(proc.stdout, selectors.EVENT_READ)
            sent = 0
            raw = bytearray()
            ready = False
            eof = False
            while not eof:
                if not remaining():
                    raise _error('timeout')
                for key, _ in selector.select(remaining()):
                    if key.fileobj is proc.stdin:
                        try:
                            sent += os.write(key.fd, request[sent:sent + 4096])
                        except BlockingIOError:
                            continue
                        if sent == len(request):
                            selector.unregister(proc.stdin)
                            proc.stdin.close()
                    else:
                        try:
                            chunk = os.read(key.fd, min(65536, MAX_OUTPUT + 1 - len(raw)))
                        except BlockingIOError:
                            continue
                        if not chunk:
                            eof = True
                            selector.unregister(proc.stdout)
                            break
                        raw.extend(chunk)
                        if len(raw) > MAX_OUTPUT:
                            raise _error()
                        if not ready and b'\n' in raw:
                            _frame(raw.split(b'\n', 1)[0], 'ready', proc.pid)
                            ready = True
            if not remaining():
                raise _error('timeout')
            proc.wait(timeout=remaining())
            if proc.returncode:
                raise _error()
            result = _decode(raw, proc.pid)
            if not remaining():
                raise _error('timeout')
            if isinstance(result, FetchError):
                raise result
            return result
        except subprocess.TimeoutExpired:
            pending_error = True
            raise _error('timeout') from None
        except (OSError, ValueError, RecursionError, TypeError):
            pending_error = True
            raise _error() from None
        except BaseException:
            pending_error = True
            raise
        finally:
            try:
                if selector:
                    selector.close()
            finally:
                if proc is None:
                    self.gate.release()
                # Cleanup must block success without replacing caller failures
                # or cancellation. Retained resources still require recovery.
                elif not self._cleanup(proc) and not pending_error:
                    raise _error() from None


_SUPERVISOR = _Supervisor()


def supervised_fetch(url, request_profile='default', accept_override=None, *, deadline=None):
    """Candidate entrypoint; callers must opt in explicitly during local testing."""
    return _SUPERVISOR.fetch(url, request_profile, accept_override, deadline=deadline)


def _emit(value):
    sys.stdout.buffer.write(json.dumps(value).encode('utf-8') + b'\n')
    sys.stdout.buffer.flush()


def _serve(fetcher=None):
    """Fixed child protocol. Injection is for trusted test entrypoints only."""
    if fetcher is None:
        from guidecheck_fetch import safe_fetch
        fetcher = safe_fetch
    pid = os.getpid()
    _emit({'event': 'ready', 'pid': pid})
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise _error()
        request = json.loads(raw)
        if (not isinstance(request, dict) or set(request) != {'url', 'request_profile', 'accept_override'}
                or not isinstance(request['url'], str) or not isinstance(request['request_profile'], str)
                or (request['accept_override'] is not None and not isinstance(request['accept_override'], str))):
            raise _error()
        fetched = fetcher(**request)
        if len(fetched.body) > MAX_BYTES:
            raise _error('too-large')
        _emit({'event': 'result', 'pid': pid, 'fetch': {
            'final_url': fetched.final_url, 'status': fetched.status, 'headers': fetched.headers,
            'body': base64.b64encode(fetched.body).decode('ascii'),
            'redirects': fetched.redirects, 'tls_valid': fetched.tls_valid}})
    except FetchError as exc:
        _emit({'event': 'error', 'pid': pid, 'code': exc.code if exc.code in _MESSAGES else 'fetch-failed'})
    except Exception:
        _emit({'event': 'error', 'pid': pid, 'code': 'fetch-failed'})


if __name__ == '__main__':
    _serve()
