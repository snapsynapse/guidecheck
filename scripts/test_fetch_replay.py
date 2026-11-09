#!/usr/bin/env python3
"""
Deterministic replay tests for guidecheck_fetch.safe_fetch.

The tests monkeypatch DNS, TLS, and HTTPSConnection so redirect and size-limit
behavior can be checked without network access.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import guidecheck_fetch as gf


PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"PASS {name}")
    else:
        FAILED += 1
        print(f"FAIL {name}")
        if detail:
            print(f"     {detail}")


class FakeResponse:
    def __init__(self, status: int, headers: dict[str, str] | None = None, body: bytes = b"") -> None:
        self.status = status
        self.headers = headers or {}
        self.body = body
        self.closed = False

    def getheader(self, name: str, default: str | None = None) -> str | None:
        return self.headers.get(name, default)

    def getheaders(self) -> list[tuple[str, str]]:
        return list(self.headers.items())

    def read(self, size: int | None = None) -> bytes:
        if size is None:
            return self.body
        return self.body[:size]

    def close(self) -> None:
        self.closed = True


class UnreadRedirect(FakeResponse):
    """Fail immediately if an ignored redirect body is consumed."""

    def __init__(self, status: int, headers: dict[str, str]) -> None:
        super().__init__(status, headers)
        self.read_calls = 0

    def read(self, size: int | None = None) -> bytes:
        self.read_calls += 1
        raise AssertionError("redirect body must not be read")


class FakeConnection:
    responses: list[FakeResponse] = []
    requests: list[tuple[str, int, str]] = []
    instances: list[FakeConnection] = []

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.closed = False
        self.response = None
        # A new hop must not open before the previous connection closes.
        if self.instances:
            previous = self.instances[-1]
            if not previous.closed:
                raise AssertionError("previous connection is still open")
            if previous.response is not None and not previous.response.closed:
                raise AssertionError("previous redirect response is still open")
        self.instances.append(self)

    def request(self, method: str, path: str, headers: dict[str, str]) -> None:
        FakeConnection.requests.append((self.host, self.port, path))

    def getresponse(self) -> FakeResponse:
        if not FakeConnection.responses:
            raise OSError("no fake response queued")
        self.response = FakeConnection.responses.pop(0)
        return self.response

    def close(self) -> None:
        self.closed = True


def with_fake_fetch(responses: list[FakeResponse], url: str, resolver=None):
    original_resolve = gf._resolve
    original_open_tls = gf._open_tls
    original_connection = gf.http.client.HTTPSConnection
    FakeConnection.responses = list(responses)
    FakeConnection.requests = []
    FakeConnection.instances = []
    gf._resolve = resolver or (lambda host, port: ["93.184.216.34"])
    gf._open_tls = lambda host, port, ip: object()
    gf.http.client.HTTPSConnection = FakeConnection
    try:
        return gf.safe_fetch(url)
    finally:
        gf._resolve = original_resolve
        gf._open_tls = original_open_tls
        gf.http.client.HTTPSConnection = original_connection
        FakeConnection.responses = []


def expect_error(name: str, responses: list[FakeResponse], url: str, code: str, resolver=None) -> None:
    try:
        with_fake_fetch(responses, url, resolver)
    except gf.FetchError as exc:
        check(name, exc.code == code, f"expected {code}, got {exc.code}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"unexpected {type(exc).__name__}: {exc}")
    else:
        check(name, False, "expected FetchError")


def test_success() -> None:
    result = with_fake_fetch(
        [FakeResponse(200, {"Content-Type": "text/plain; charset=utf-8"}, b"Assistant Guide: X\n")],
        "https://example.com/.well-known/assistant-guide.txt",
    )
    check("success status", result.status == 200)
    check("success body", result.body == b"Assistant Guide: X\n")
    check("success content-type", result.headers["content-type"] == "text/plain; charset=utf-8")


def test_header_capture() -> None:
    result = with_fake_fetch(
        [
            FakeResponse(
                200,
                {
                    "Content-Type": "text/plain; charset=utf-8",
                    "Content-Length": "18",
                    "Set-Cookie": "session=secret",
                },
                b"Assistant Guide: X\n",
            )
        ],
        "https://example.com/.well-known/assistant-guide.txt",
    )
    check(
        "headers capture content-type",
        result.headers == {"content-type": "text/plain; charset=utf-8", "content-length": "18"},
    )


def test_same_domain_redirect() -> None:
    result = with_fake_fetch(
        [
            FakeResponse(302, {"Location": "https://docs.example.com/guide.txt"}),
            FakeResponse(200, {"Content-Type": "text/plain"}, b"ok"),
        ],
        "https://example.com/.well-known/assistant-guide.txt",
    )
    check("same-domain redirect final", result.final_url == "https://docs.example.com/guide.txt")
    check("same-domain redirect recorded", len(result.redirects) == 1)


def test_cross_domain_redirect() -> None:
    expect_error(
        "cross-domain redirect",
        [FakeResponse(302, {"Location": "https://example.net/guide.txt"})],
        "https://example.com/.well-known/assistant-guide.txt",
        "cross-domain-redirect",
    )


def test_bad_redirect() -> None:
    expect_error(
        "redirect without location",
        [FakeResponse(302)],
        "https://example.com/.well-known/assistant-guide.txt",
        "bad-redirect",
    )


def test_too_many_redirects() -> None:
    responses = [
        FakeResponse(302, {"Location": f"https://example.com/guide-{idx}.txt"})
        for idx in range(gf.MAX_REDIRECTS + 1)
    ]
    expect_error(
        "too many redirects",
        responses,
        "https://example.com/.well-known/assistant-guide.txt",
        "too-many-redirects",
    )


def test_size_limits() -> None:
    expect_error(
        "content-length too large",
        [FakeResponse(200, {"Content-Length": str(gf.MAX_BYTES + 1)}, b"")],
        "https://example.com/.well-known/assistant-guide.txt",
        "too-large",
    )
    expect_error(
        "streamed body too large",
        [FakeResponse(200, {}, b"x" * (gf.MAX_BYTES + 1))],
        "https://example.com/.well-known/assistant-guide.txt",
        "too-large",
    )
    for headers in ({}, {"Content-Length": "invalid"}, {"Content-Length": "0"}):
        result = with_fake_fetch(
            [FakeResponse(200, headers, b"x" * gf.MAX_BYTES)],
            "https://example.com/guide.txt",
        )
        check(f"final body exact limit {headers}", len(result.body) == gf.MAX_BYTES)
        expect_error(
            f"final body overflow {headers}",
            [FakeResponse(200, headers, b"x" * (gf.MAX_BYTES + 1))],
            "https://example.com/guide.txt",
            "too-large",
        )


def check_redirect_cleanup(name: str, responses: list[UnreadRedirect]) -> None:
    check(f"{name} bodies unread", all(r.read_calls == 0 for r in responses))
    check(f"{name} responses closed", all(r.closed for r in responses))
    check(f"{name} connections closed", all(c.closed for c in FakeConnection.instances))


def test_redirect_bodies() -> None:
    framings = ({"Content-Length": str(gf.MAX_BYTES + 1)}, {}, {"Transfer-Encoding": "chunked"})
    for status in (301, 302, 303, 307, 308):
        for framing in framings:
            name = f"redirect {status} {framing}"
            response = UnreadRedirect(status, {"Location": "/next", **framing})
            try:
                result = with_fake_fetch(
                    [response, FakeResponse(200, {"Content-Type": "text/plain"}, b"ok")],
                    "https://example.com/guide.txt",
                )
                check(name, result.body == b"ok" and result.final_url == "https://example.com/next")
                check(f"{name} history", result.redirects == [{
                    "from": "https://example.com/guide.txt",
                    "to": "https://example.com/next", "status": status,
                }])
            except Exception as exc:
                check(name, False, str(exc))
            check_redirect_cleanup(name, [response])

        for headers in ({}, {"Location": ""}):
            name = f"redirect {status} missing/empty target {headers}"
            response = UnreadRedirect(status, headers)
            expect_error(name, [response], "https://example.com/guide.txt", "bad-redirect")
            check_redirect_cleanup(name, [response])
            check(f"{name} no next request", len(FakeConnection.requests) == 1)


def test_redirect_rejections() -> None:
    for target, code in (("ftp://example.com/next", "scheme"),
                         ("https://example.net/next", "cross-domain-redirect")):
        response = UnreadRedirect(302, {"Location": target})
        expect_error(code, [response], "https://example.com/guide.txt", code)
        check_redirect_cleanup(code, [response])
        check(f"{code} no target request", len(FakeConnection.requests) == 1)

    # Keep the real per-hop address validator; replace only system DNS.
    def addresses(host, port, **kwargs):
        ip = "93.184.216.34" if host == "example.com" else "127.0.0.1"
        return [(gf.socket.AF_INET, gf.socket.SOCK_STREAM, 6, "", (ip, port))]

    response = UnreadRedirect(302, {"Location": "https://private.example.com/next"})
    with patch.object(gf.socket, "getaddrinfo", side_effect=addresses):
        expect_error("private redirect", [response], "https://example.com/guide.txt",
                     "blocked-target", resolver=gf._resolve)
    check_redirect_cleanup("private redirect", [response])
    check("private redirect no target request", len(FakeConnection.requests) == 1)


def test_redirect_chains() -> None:
    for hops in (gf.MAX_REDIRECTS, gf.MAX_REDIRECTS + 1):
        responses = [UnreadRedirect(302, {"Location": f"/hop-{i}"}) for i in range(hops)]
        if hops > gf.MAX_REDIRECTS:
            expect_error("unread chain exhausted", responses, "https://example.com/start",
                         "too-many-redirects")
        else:
            try:
                result = with_fake_fetch(responses + [FakeResponse(200, {}, b"ok")],
                                         "https://example.com/start")
                expected = [{"from": "https://example.com/start" if i == 0 else f"https://example.com/hop-{i-1}",
                             "to": f"https://example.com/hop-{i}", "status": 302}
                            for i in range(hops)]
                check("maximum allowed chain", result.body == b"ok" and result.redirects == expected)
            except Exception as exc:
                check("maximum allowed chain", False, str(exc))
        check_redirect_cleanup(f"chain {hops}", responses)


def test_redirect_failures() -> None:
    class FailingBody(FakeResponse):
        def read(self, size=None):
            raise failure

    for failure, code in ((gf.socket.timeout(), "timeout"), (OSError(), "read-failed")):
        response = UnreadRedirect(302, {"Location": "/next"})
        expect_error(f"final {code}", [response, FailingBody(200)],
                     "https://example.com/start", code)
        check_redirect_cleanup(f"final {code}", [response])

    def failing_resolver(host, port):
        if host == "next.example.com":
            raise gf.FetchError("dns-failed", "the host could not be resolved")
        return ["93.184.216.34"]

    response = UnreadRedirect(302, {"Location": "https://next.example.com/next"})
    expect_error("next-hop DNS failure", [response], "https://example.com/start",
                 "dns-failed", resolver=failing_resolver)
    check_redirect_cleanup("next-hop DNS failure", [response])


def test_http_response_stream_closure() -> None:
    class HeaderOnlyStream(io.BytesIO):
        forbid_body = False

        def read(self, size=-1):
            raise AssertionError("HTTPResponse must not read the redirect body")

        def readline(self, size=-1):
            if self.forbid_body:
                raise AssertionError("HTTPResponse must not read redirect chunks")
            return super().readline(size)

    class FakeSocket:
        def makefile(self, mode):
            return stream

    for framing in (b"Content-Length: 262145\r\n", b"", b"Transfer-Encoding: chunked\r\n"):
        stream = HeaderOnlyStream(b"HTTP/1.1 302 Found\r\nLocation: /next\r\n" + framing + b"\r\n")
        response = gf.http.client.HTTPResponse(FakeSocket())
        response.begin()
        stream.forbid_body = True
        try:
            result = with_fake_fetch([response, FakeResponse(200, {}, b"ok")],
                                     "https://example.com/start")
            check(f"stdlib redirect {framing!r}", result.body == b"ok")
        except Exception as exc:
            check(f"stdlib redirect {framing!r}", False, str(exc))
        check(f"stdlib stream closed {framing!r}", stream.closed)
        check(f"stdlib connections closed {framing!r}", all(c.closed for c in FakeConnection.instances))
        response.close()


def test_content_variation_model() -> None:
    first = with_fake_fetch(
        [FakeResponse(200, {"Content-Type": "text/plain"}, b"Assistant Guide: A\n")],
        "https://example.com/.well-known/assistant-guide.txt",
    )
    second = with_fake_fetch(
        [FakeResponse(200, {"Content-Type": "text/plain"}, b"Assistant Guide: B\n")],
        "https://example.com/.well-known/assistant-guide.txt",
    )
    check("content variation detectable", first.body != second.body)


def main() -> int:
    test_success()
    test_header_capture()
    test_same_domain_redirect()
    test_cross_domain_redirect()
    test_bad_redirect()
    test_too_many_redirects()
    test_size_limits()
    test_redirect_bodies()
    test_redirect_rejections()
    test_redirect_chains()
    test_redirect_failures()
    test_http_response_stream_closure()
    test_content_variation_model()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
