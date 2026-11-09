"""Trusted no-network child fixtures; never selected by production input."""
import ctypes
import io
import json
import os
from pathlib import Path
import signal
import sys
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guidecheck_fetch as gf
import guidecheck_fetch_worker as worker

MARKER = None
STAGE = None


def block():
    if MARKER:
        Path(MARKER).write_text(STAGE)
    ctypes.CDLL(None).sleep(60)


def fetcher(url, request_profile='default', accept_override=None):
    mode = urlsplit(url).path
    if mode in ('/echo', '/binary'):
        body = b'\x00\xff\n' if mode == '/binary' else json.dumps({
            'url': url, 'request_profile': request_profile, 'accept_override': accept_override}).encode()
        return gf.FetchResult(url, 200, {'content-type': 'text/plain'}, body)
    if mode == '/tls-error':
        raise gf.FetchError('tls', 'SECRET diagnostic must not reach the parent')
    if mode == '/ignore-term':
        block()
    if mode == '/oversized':
        sys.stdout.buffer.write(b'x' * (worker.MAX_OUTPUT + 1))
        sys.stdout.buffer.flush()
        block()
    if mode == '/crash':
        os._exit(7)
    if mode == '/result-hang':
        worker._emit({'event': 'result', 'pid': os.getpid(), 'fetch': {
            'final_url': url, 'status': 200, 'headers': {}, 'body': '',
            'redirects': [], 'tls_valid': True}})
        block()
    if mode == '/eof-hang':
        os.close(sys.stdout.fileno())
        block()

    # Drive the actual existing transport to a named blocking stage, with no
    # real DNS or network. The parent must cancel the opaque operation.
    def resolve(host, port):
        if mode == '/dns-block':
            block()
        return ['93.184.216.34']
    def tls(host, port, ip):
        if mode == '/tls-block':
            block()
        return object()
    class Response:
        status = 200
        def getheader(self, name):
            return None
        def getheaders(self):
            return []
        def read(self, count):
            if mode == '/body-block':
                block()
            return b'ok'
    class Connection:
        def __init__(self, *args, **kwargs):
            self.sock = None
        def request(self, *args, **kwargs):
            if mode == '/write-block':
                block()
        def getresponse(self):
            if mode == '/headers-block':
                block()
            if mode == '/chunk-block':
                headers = b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'
                class Stream(io.BytesIO):
                    def readline(self, size=-1):
                        if self.tell() >= len(headers):
                            block()
                        return super().readline(size)
                class Socket:
                    def makefile(self, mode):
                        return Stream(headers)
                response = gf.http.client.HTTPResponse(Socket())
                response.begin()
                return response
            return Response()
        def close(self):
            pass
    gf._resolve = resolve
    gf._open_tls = tls
    gf.http.client.HTTPSConnection = Connection
    return gf._fetch_in_process(url, request_profile, accept_override)


if __name__ == '__main__':
    # Read only the bounded trusted fixture request so first-frame faults can
    # be emitted before _serve's real ready message. No production test switch.
    raw = sys.stdin.buffer.read(worker.MAX_INPUT + 1)
    parts = urlsplit(json.loads(raw)['url'])
    mode = parts.path
    MARKER = parse_qs(parts.query).get('marker', [None])[0]
    STAGE = mode
    if mode == '/bad-first':
        print('{broken', flush=True)
        block()
    elif mode == '/wrong-pid':
        worker._emit({'event': 'ready', 'pid': os.getpid() + 1})
        block()
    else:
        if mode == '/ignore-term':
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        sys.stdin = io.TextIOWrapper(io.BytesIO(raw))
        worker._serve(fetcher)
