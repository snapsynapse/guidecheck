#!/usr/bin/env python3
"""
Deterministic replay tests for guidecheck_fetch.safe_fetch.

The tests monkeypatch DNS, TLS, and HTTPSConnection so redirect and size-limit
behavior can be checked without network access.
"""

from __future__ import annotations

import sys
from pathlib import Path

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

    def getheader(self, name: str, default: str | None = None) -> str | None:
        return self.headers.get(name, default)

    def getheaders(self) -> list[tuple[str, str]]:
        return list(self.headers.items())

    def read(self, size: int | None = None) -> bytes:
        if size is None:
            return self.body
        return self.body[:size]


class FakeConnection:
    responses: list[FakeResponse] = []
    requests: list[tuple[str, int, str]] = []

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def request(self, method: str, path: str, headers: dict[str, str]) -> None:
        FakeConnection.requests.append((self.host, self.port, path))

    def getresponse(self) -> FakeResponse:
        if not FakeConnection.responses:
            raise OSError("no fake response queued")
        return FakeConnection.responses.pop(0)

    def close(self) -> None:
        return None


def with_fake_fetch(responses: list[FakeResponse], url: str):
    original_resolve = gf._resolve
    original_open_tls = gf._open_tls
    original_connection = gf.http.client.HTTPSConnection
    FakeConnection.responses = list(responses)
    FakeConnection.requests = []
    gf._resolve = lambda host, port: ["93.184.216.34"]
    gf._open_tls = lambda host, port, ip: object()
    gf.http.client.HTTPSConnection = FakeConnection
    try:
        return gf.safe_fetch(url)
    finally:
        gf._resolve = original_resolve
        gf._open_tls = original_open_tls
        gf.http.client.HTTPSConnection = original_connection
        FakeConnection.responses = []


def expect_error(name: str, responses: list[FakeResponse], url: str, code: str) -> None:
    try:
        with_fake_fetch(responses, url)
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
    test_content_variation_model()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
