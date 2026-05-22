#!/usr/bin/env python3
"""
Offline contract tests for the hosted verifier API handler.

These tests call api.verify.handler.do_POST with a small fake request object and
stubbed fetch results. They do not open sockets or make outbound requests.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify as hv
from guidecheck_fetch import FetchError


ROOT = Path(__file__).resolve().parents[1]
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


class FakeRequest:
    def __init__(self, payload: object, ip: str = "203.0.113.10") -> None:
        if isinstance(payload, bytes):
            raw = payload
        else:
            raw = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Length": str(len(raw))}
        self.rfile = io.BytesIO(raw)
        self.client_address = (ip, 12345)
        self.status: int | None = None
        self.body: dict | None = None

    def _write_json(self, status: int, payload: dict) -> None:
        self.status = status
        self.body = payload

    def _error(self, status: int, code: str, message: str) -> None:
        self._write_json(
            status,
            {
                "error": {"code": code, "message": message},
                "hosted_limitations": list(hv.HOSTED_LIMITATIONS),
            },
        )


def fetched(url: str, status: int, body: bytes, content_type: str = "text/plain; charset=utf-8"):
    return SimpleNamespace(
        final_url=url,
        status=status,
        headers={"content-type": content_type},
        body=body,
        redirects=[],
        tls_valid=True,
    )


def run_post(payload: object, fake_fetch, ip: str = "203.0.113.10") -> FakeRequest:
    original_fetch = hv.safe_fetch
    hv.safe_fetch = fake_fetch
    hv._rate_hits.clear()
    request = FakeRequest(payload, ip=ip)
    try:
        hv.handler.do_POST(request)  # type: ignore[arg-type]
    finally:
        hv.safe_fetch = original_fetch
        hv._rate_hits.clear()
    return request


def test_evaluated() -> None:
    data = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_bytes()
    url = "https://example.com/.well-known/assistant-guide.txt"
    request = run_post({"url": url}, lambda checked: fetched(checked, 200, data))
    body = request.body or {}
    check("evaluated status", request.status == 200)
    check("evaluated outcome", body.get("outcome") == "evaluated")
    check("evaluated level", body.get("guide", {}).get("achieved_level") == 3)
    check("evaluated compact report", "SHA-256:" in body.get("compact_report", ""))
    check("evaluated limitations", len(body.get("hosted_limitations", [])) == 3)


def test_evaluated_with_warnings() -> None:
    data = (ROOT / "fixtures" / "valid" / "prompterkit-level-3" / "guide.txt").read_bytes()
    url = "https://example.com/.well-known/assistant-guide.txt"
    request = run_post({"url": url}, lambda checked: fetched(checked, 200, data))
    body = request.body or {}
    check("evaluated warnings status", request.status == 200)
    check("evaluated warnings retained", body.get("summary", {}).get("warnings") == 2)
    check("evaluated warnings still proceed", "Proceed? yes" in body.get("compact_report", ""))


def test_auto_resolved_origin() -> None:
    data = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_bytes()
    request = run_post({"url": "https://example.com/"}, lambda checked: fetched(checked, 200, data))
    body = request.body or {}
    check("origin auto-resolved", body.get("input", {}).get("auto_resolved") is True)
    check(
        "origin checked well-known",
        body.get("input", {}).get("url") == "https://example.com/.well-known/assistant-guide.txt",
    )


def test_noncanonical_location_note() -> None:
    data = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_bytes()
    url = "https://example.com/docs/guide.txt"
    request = run_post({"url": url}, lambda checked: fetched(checked, 200, data))
    body = request.body or {}
    check("noncanonical location note", "location_note" in body)


def test_not_found() -> None:
    request = run_post(
        {"url": "https://example.com/"},
        lambda checked: fetched(checked, 404, b"not found", "text/plain"),
    )
    body = request.body or {}
    check("not-found status", request.status == 200)
    check("not-found outcome", body.get("outcome") == "not-found")


def test_not_a_guide() -> None:
    request = run_post(
        {"url": "https://example.com/"},
        lambda checked: fetched(checked, 200, b"<!doctype html><html></html>", "text/html"),
    )
    body = request.body or {}
    check("not-a-guide status", request.status == 200)
    check("not-a-guide outcome", body.get("outcome") == "not-a-guide")


def test_errors() -> None:
    bad_json = run_post(b"{", lambda checked: None)
    check("bad json", bad_json.status == 400 and bad_json.body["error"]["code"] == "bad-request")

    bad_scheme = run_post({"url": "http://example.com/guide.txt"}, lambda checked: None)
    check("scheme rejected", bad_scheme.status == 400 and bad_scheme.body["error"]["code"] == "scheme")

    fetch_failed = run_post(
        {"url": "https://example.com/guide.txt"},
        lambda checked: (_ for _ in ()).throw(FetchError("dns-failed", "the host could not be resolved")),
    )
    check(
        "fetch error sanitized",
        fetch_failed.status == 400 and fetch_failed.body["error"]["code"] == "dns-failed",
    )


def test_rate_limit() -> None:
    original_fetch = hv.safe_fetch
    data = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_bytes()
    hv.safe_fetch = lambda checked: fetched(checked, 200, data)
    hv._rate_hits.clear()
    try:
        last = None
        for _ in range(hv._RATE_MAX + 1):
            request = FakeRequest({"url": "https://example.com/guide.txt"}, ip="203.0.113.20")
            hv.handler.do_POST(request)  # type: ignore[arg-type]
            last = request
        check("rate limit", last is not None and last.status == 429)
    finally:
        hv.safe_fetch = original_fetch
        hv._rate_hits.clear()


def main() -> int:
    test_evaluated()
    test_evaluated_with_warnings()
    test_auto_resolved_origin()
    test_noncanonical_location_note()
    test_not_found()
    test_not_a_guide()
    test_errors()
    test_rate_limit()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
