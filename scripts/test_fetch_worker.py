"""Offline tests for the unactivated SEC-003 worker candidate."""
import inspect
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

import guidecheck_fetch as gf
import guidecheck_fetch_worker as worker

FIXTURE = Path(__file__).with_name('test_fetch_worker_child.py')


def fd_count():
    return len(os.listdir('/dev/fd' if sys.platform == 'darwin' else '/proc/self/fd'))


class TransportBoundaryTests(unittest.TestCase):
    def test_public_entrypoint_forwards_arguments_and_result(self):
        result = gf.FetchResult('https://example.com/final', 200, {'content-type': 'text/plain'}, b'ok')
        with (
            patch.object(worker.subprocess, 'Popen', side_effect=AssertionError('public fetch must not spawn')),
            patch.object(gf, '_fetch_in_process', return_value=result) as transport,
        ):
            self.assertIs(gf.safe_fetch('https://example.com/'), result)
            transport.assert_called_once_with('https://example.com/', request_profile='default', accept_override=None)
            transport.reset_mock()
            self.assertIs(gf.safe_fetch('https://example.com/', 'variation-cli', 'application/dns-json'), result)
            transport.assert_called_once_with('https://example.com/', request_profile='variation-cli',
                                              accept_override='application/dns-json')
            transport.reset_mock()
            self.assertIs(gf.safe_fetch('https://example.com/', request_profile='variation-browser',
                                        accept_override='text/plain'), result)
            transport.assert_called_once_with('https://example.com/', request_profile='variation-browser',
                                              accept_override='text/plain')

    def test_public_entrypoint_preserves_fetch_error(self):
        error = gf.FetchError('blocked-target', 'the host resolves to a non-public address')
        with (
            patch.object(worker.subprocess, 'Popen', side_effect=AssertionError('public fetch must not spawn')),
            patch.object(gf, '_fetch_in_process', side_effect=error),
        ):
            with self.assertRaises(gf.FetchError) as raised:
                gf.safe_fetch('https://example.com/')
        self.assertIs(raised.exception, error)

    def test_public_entrypoint_stays_synchronous_without_spawning(self):
        signature = inspect.signature(gf.safe_fetch)
        self.assertEqual(list(signature.parameters), ['url', 'request_profile', 'accept_override'])
        self.assertEqual(signature.parameters['request_profile'].default, 'default')
        self.assertIsNone(signature.parameters['accept_override'].default)
        self.assertFalse(inspect.iscoroutinefunction(gf.safe_fetch))
        with patch.object(worker.subprocess, 'Popen', side_effect=AssertionError('public fetch must not spawn')):
            with self.assertRaises(gf.FetchError) as raised:
                gf.safe_fetch('ftp://example.com/')
        self.assertEqual(raised.exception.code, 'scheme')


@unittest.skipUnless(os.name == 'posix', 'experimental POSIX worker candidate')
class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.supervisor = worker._Supervisor(FIXTURE, capacity=1)
        self.before = fd_count()
        self.children = []
        self.real_popen = subprocess.Popen

    def launch(self, *args, **kwargs):
        proc = self.real_popen(*args, **kwargs)
        self.children.append(proc)
        return proc

    def tearDown(self):
        self.assertTrue(self.supervisor.close())
        self.assertFalse(self.supervisor.active)
        for proc in self.children:
            self.assertIsNotNone(proc.returncode)
            self.assertTrue(proc.stdin.closed and proc.stdout.closed)
            with self.assertRaises(ChildProcessError):
                os.waitpid(proc.pid, os.WNOHANG)
        self.assertEqual(fd_count(), self.before)

    def fetch(self, path, **kwargs):
        with patch.object(worker.subprocess, 'Popen', side_effect=self.launch):
            return self.supervisor.fetch('https://example.com' + path, **kwargs)

    def test_binary_and_request_variations_roundtrip(self):
        self.assertEqual(self.fetch('/binary').body, b'\x00\xff\n')
        result = self.fetch('/echo', request_profile='variation-cli', accept_override='application/dns-json')
        self.assertEqual(json.loads(result.body), {'url': 'https://example.com/echo',
                         'request_profile': 'variation-cli', 'accept_override': 'application/dns-json'})

    def test_large_input_uses_bounded_nonblocking_writes(self):
        path = '/echo?' + 'x' * 60000
        self.assertEqual(json.loads(self.fetch(path).body)['url'], 'https://example.com' + path)

    def test_actual_transport_blocking_stages_cancel(self):
        with tempfile.TemporaryDirectory(prefix='guidecheck-worker-stages-') as directory:
            for path in ('/dns-block', '/tls-block', '/write-block', '/headers-block', '/body-block', '/chunk-block'):
                with self.subTest(path=path):
                    marker = Path(directory) / path.lstrip('/')
                    start = time.monotonic()
                    with self.assertRaises(gf.FetchError) as raised:
                        self.fetch(path + '?' + urlencode({'marker': str(marker)}), deadline=start + 0.30)
                    self.assertEqual(raised.exception.code, 'timeout')
                    self.assertLess(time.monotonic() - start, 1.2)
                    self.assertEqual(marker.read_text(), path, 'must reach the named stage before cancellation')
                    self.assertFalse(self.supervisor.active)

    def test_ignore_term_escalates_to_kill(self):
        with self.assertRaises(gf.FetchError) as raised:
            self.fetch('/ignore-term', deadline=time.monotonic() + 0.35)
        self.assertEqual(raised.exception.code, 'timeout')
        self.assertEqual(self.children[-1].returncode, -9)

    def test_incomplete_or_crashed_workers_never_succeed(self):
        for path, code in (('/crash', 'fetch-failed'), ('/bad-first', 'fetch-failed'),
                           ('/wrong-pid', 'fetch-failed'),
                           ('/result-hang', 'timeout'), ('/eof-hang', 'timeout'),
                           ('/oversized', 'fetch-failed')):
            with self.subTest(path=path):
                with self.assertRaises(gf.FetchError) as raised:
                    self.fetch(path, deadline=time.monotonic() + 0.25)
                self.assertEqual(raised.exception.code, code)

    def test_error_message_is_parent_owned(self):
        with self.assertRaises(gf.FetchError) as raised:
            self.fetch('/tls-error')
        self.assertEqual(raised.exception.code, 'tls')
        self.assertNotIn('SECRET', str(raised.exception))

    def test_protocol_and_body_limits_are_validated(self):
        pid = os.getpid()
        ready = {'event': 'ready', 'pid': pid}
        value = {'final_url': 'https://example.com/', 'status': 200, 'headers': {},
                 'body': '', 'redirects': [], 'tls_valid': True}
        def packet(first=ready, body=value, result_pid=pid):
            return (json.dumps(first) + '\n' + json.dumps({
                'event': 'result', 'pid': result_pid, 'fetch': body}) + '\n').encode()
        self.assertEqual(worker._decode(packet(), pid).body, b'')
        for raw in (packet(first=[]), packet(first={'event': 'other', 'pid': pid}),
                    packet(result_pid=pid + 1), packet(body={**value, 'status': True}),
                    packet(body={**value, 'body': '!not-base64!'}),
                    packet(body={**value, 'body': 'A' * (4 * ((gf.MAX_BYTES + 2) // 3) + 4)}),
                    packet(body={**value, 'headers': {'set-cookie': 'secret'}}),
                    packet(body={**value, 'redirects': [{}]})):
            with self.subTest(raw=raw[:70]):
                with self.assertRaises(ValueError):
                    worker._decode(raw, pid)

    def test_expired_or_oversized_request_starts_no_worker(self):
        with patch.object(worker.subprocess, 'Popen', side_effect=AssertionError('must not spawn')):
            with self.assertRaises(gf.FetchError) as raised:
                self.supervisor.fetch('https://example.com/', deadline=time.monotonic() - 1)
            self.assertEqual(raised.exception.code, 'timeout')
            with self.assertRaises(gf.FetchError):
                self.supervisor.fetch('https://example.com/' + 'x' * worker.MAX_INPUT)

    def test_validation_cannot_accept_a_late_result(self):
        original = worker._decode
        clock = [0.0]
        def decode(*args):
            result = original(*args)
            clock[0] = 1.0
            return result
        with patch.object(worker.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(worker, '_decode', side_effect=decode):
            with self.assertRaises(gf.FetchError) as raised:
                self.fetch('/echo', deadline=0.5)
        self.assertEqual(raised.exception.code, 'timeout')

    def test_terminate_failure_does_not_skip_cleanup(self):
        def launch(*args, **kwargs):
            proc = self.launch(*args, **kwargs)
            proc.terminate = lambda: (_ for _ in ()).throw(OSError('fixture failure'))
            return proc
        with patch.object(worker.subprocess, 'Popen', side_effect=launch):
            with self.assertRaises(gf.FetchError) as raised:
                self.supervisor.fetch('https://example.com/body-block', deadline=time.monotonic() + 0.20)
        self.assertEqual(raised.exception.code, 'timeout')
        self.assertFalse(self.supervisor.active)
        self.assertEqual(self.children[-1].returncode, -9)

    def test_stream_failure_retains_admission_until_recovery(self):
        original = None
        def launch(*args, **kwargs):
            nonlocal original
            proc = self.launch(*args, **kwargs)
            original = proc.stdout.close
            proc.stdout.close = lambda: (_ for _ in ()).throw(OSError('fixture failure'))
            return proc
        try:
            with patch.object(worker.subprocess, 'Popen', side_effect=launch):
                with self.assertRaises(gf.FetchError) as raised:
                    self.supervisor.fetch('https://example.com/echo')
            self.assertEqual(raised.exception.code, 'fetch-failed')
            self.assertEqual(len(self.supervisor.active), 1)
            with self.assertRaises(gf.FetchError) as raised:
                self.fetch('/echo', deadline=time.monotonic() + 0.03)
            self.assertEqual(raised.exception.code, 'timeout')
        finally:
            if original:
                self.children[-1].stdout.close = original
        self.assertTrue(self.supervisor.close())
        self.assertEqual(self.fetch('/echo').status, 200)

    def test_caller_interruption_survives_incomplete_cleanup(self):
        interruption = KeyboardInterrupt('fixture caller cancellation')
        original = None
        def launch(*args, **kwargs):
            nonlocal original
            proc = self.launch(*args, **kwargs)
            original = proc.stdout.close
            proc.stdout.close = lambda: (_ for _ in ()).throw(OSError('fixture failure'))
            return proc
        try:
            with patch.object(worker.subprocess, 'Popen', side_effect=launch), patch.object(
                    worker.selectors.DefaultSelector, 'select', side_effect=interruption):
                with self.assertRaises(KeyboardInterrupt) as raised:
                    self.supervisor.fetch('https://example.com/body-block')
            self.assertIs(raised.exception, interruption)
            proc, = self.children
            self.assertIsNotNone(proc.returncode)
            self.assertTrue(proc.stdin.closed)
            self.assertFalse(proc.stdout.closed)
            self.assertIs(self.supervisor.active[proc.pid], proc)
            with patch.object(worker.subprocess, 'Popen', side_effect=AssertionError('must not spawn')):
                with self.assertRaises(gf.FetchError) as raised:
                    self.supervisor.fetch('https://example.com/echo', deadline=time.monotonic() + 0.03)
            self.assertEqual(raised.exception.code, 'timeout')
        finally:
            if original:
                self.children[0].stdout.close = original
            self.assertTrue(self.supervisor.close())
        self.assertFalse(self.supervisor.active)
        self.assertEqual(self.fetch('/echo').status, 200)

    def test_admission_is_shared_across_calls(self):
        ready = threading.Event()
        original = worker._frame
        def frame(*args):
            value = original(*args)
            if value['event'] == 'ready':
                ready.set()
            return value
        outcomes = []
        def holder():
            try:
                self.supervisor.fetch('https://example.com/body-block', deadline=time.monotonic() + 0.5)
            except gf.FetchError as exc:
                outcomes.append(exc.code)
        with patch.object(worker, '_frame', side_effect=frame), patch.object(worker.subprocess, 'Popen', side_effect=self.launch):
            thread = threading.Thread(target=holder)
            thread.start()
            try:
                self.assertTrue(ready.wait(0.4))
                with self.assertRaises(gf.FetchError) as raised:
                    self.supervisor.fetch('https://example.com/echo', deadline=time.monotonic() + 0.03)
                self.assertEqual(raised.exception.code, 'timeout')
                self.assertEqual(len(self.children), 1)
            finally:
                thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcomes, ['timeout'])

    def test_default_entrypoint_imports_without_checkout_path(self):
        with self.assertRaises(gf.FetchError) as raised:
            worker.supervised_fetch('ftp://example.com/')
        self.assertEqual(raised.exception.code, 'scheme')

    def test_default_child_binds_private_transport_without_public_recursion(self):
        result = gf.FetchResult('https://example.com/final', 200, {'content-type': 'text/plain'}, b'\x00\xff',
                                [{'from': 'https://example.com/', 'to': 'https://example.com/final', 'status': 302}])
        for profile, accept in (('default', None), ('variation-cli', 'application/dns-json')):
            request = {'url': 'https://example.com/', 'request_profile': profile, 'accept_override': accept}
            with self.subTest(profile=profile), io.TextIOWrapper(io.BytesIO(json.dumps(request).encode())) as stdin:
                with (
                    patch.object(gf, 'safe_fetch', side_effect=AssertionError('must not recurse through public fetch')) as public,
                    patch.object(gf, '_fetch_in_process', return_value=result) as transport,
                    patch.object(worker.sys, 'stdin', stdin),
                    patch.object(worker, '_emit') as emit,
                ):
                    worker._serve()
                public.assert_not_called()
                transport.assert_called_once_with(**request)
                raw = b'\n'.join(json.dumps(call.args[0]).encode() for call in emit.call_args_list)
                self.assertEqual(worker._decode(raw, os.getpid()), result)

    def test_default_child_preserves_private_error_category(self):
        request = {'url': 'https://example.com/', 'request_profile': 'default', 'accept_override': None}
        error = gf.FetchError('tls', 'SECRET diagnostic')
        with io.TextIOWrapper(io.BytesIO(json.dumps(request).encode())) as stdin:
            with (
                patch.object(gf, 'safe_fetch', side_effect=AssertionError('must not call public fetch')) as public,
                patch.object(gf, '_fetch_in_process', side_effect=error) as transport,
                patch.object(worker.sys, 'stdin', stdin),
                patch.object(worker, '_emit') as emit,
            ):
                worker._serve()
        public.assert_not_called()
        transport.assert_called_once_with(**request)
        raw = b'\n'.join(json.dumps(call.args[0]).encode() for call in emit.call_args_list)
        result = worker._decode(raw, os.getpid())
        self.assertIsInstance(result, gf.FetchError)
        self.assertEqual(result.code, 'tls')
        self.assertNotIn('SECRET', str(result))


if __name__ == '__main__':
    unittest.main(verbosity=2)
