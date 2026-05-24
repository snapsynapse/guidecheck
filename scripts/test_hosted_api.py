#!/usr/bin/env python3
"""
Offline contract tests for the hosted verifier API handler.

These tests call api.verify.handler.do_POST with a small fake request object and
stubbed fetch results. They do not open sockets or make outbound requests.
"""

from __future__ import annotations

import io
import json
import hashlib
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


def test_evaluated_level4_package_registry() -> None:
    base = (ROOT / "fixtures" / "valid" / "level-4" / "guide.txt").read_text(encoding="utf-8")
    guide_url = "https://example.com/.well-known/assistant-guide.txt"
    manifest_url = "https://example.com/.well-known/assistant-guide-manifest.txt"
    registry_url = "https://registry.npmjs.org/example-verifier/1.0.0"
    guide_text = base.replace(
        "manifest-url: https://example.com/.well-known/assistant-guide-manifest.txt",
        f"registry-url: {registry_url}\nmanifest-url: {manifest_url}",
    )
    guide_data = guide_text.encode("utf-8")
    guide_sha = hashlib.sha256(guide_data).hexdigest()
    manifest = "\n".join(
        [
            "guide-path: /.well-known/assistant-guide.txt",
            "guide-version: 1.0.0",
            f"guide-sha256: {guide_sha}",
            f"guide-bytes: {len(guide_data)}",
            "immutable-release-url: https://example.com/org/example-verifier/releases/v1.0.0",
            "profile: human-verifiable-assistant-guide",
            "profile-version: 0.2.0",
            f"canonical-url: {guide_url}",
            "repository-url: https://example.com/org/example-verifier",
            "released-at: 2026-05-21T00:00:00Z",
            "",
        ]
    ).encode("utf-8")
    registry = json.dumps(
        {"assistantGuide": {"url": guide_url, "sha256": guide_sha}},
        sort_keys=True,
    ).encode("utf-8")

    def fake_fetch(checked):
        if checked == guide_url:
            return fetched(checked, 200, guide_data)
        if checked == manifest_url:
            return fetched(checked, 200, manifest)
        if checked == registry_url:
            return fetched(checked, 200, registry, "application/json")
        raise AssertionError(f"unexpected fetch {checked}")

    request = run_post({"url": guide_url, "requested_level": 4}, fake_fetch)
    body = request.body or {}
    anchors = body.get("cross_channel_anchors", [])
    check("level4 status", request.status == 200)
    check("level4 achieved", body.get("guide", {}).get("achieved_level") == 4)
    check("level4 hash pinned", "Hash pinned: yes" in body.get("compact_report", ""))
    check("level4 manifest valid", body.get("manifest", {}).get("valid") is True)
    check("level4 manifest fetched", body.get("manifest", {}).get("fetched") is True)
    check(
        "level4 registry anchor",
        bool(anchors) and anchors[0].get("channel") == "package-registry"
        and anchors[0].get("status") == "present-matches",
    )


def test_evaluated_level4_missing_anchor() -> None:
    guide_url = "https://example.com/.well-known/assistant-guide.txt"
    manifest_url = "https://example.com/.well-known/assistant-guide-manifest.txt"
    guide = (ROOT / "fixtures" / "invalid" / "anchor-independent-missing" / "guide.txt").read_bytes()
    manifest = (ROOT / "fixtures" / "invalid" / "anchor-independent-missing" / "manifest.txt").read_bytes()

    def fake_fetch(checked):
        if checked == guide_url:
            return fetched(checked, 200, guide)
        if checked == manifest_url:
            return fetched(checked, 200, manifest)
        raise AssertionError(f"unexpected fetch {checked}")

    request = run_post({"url": guide_url, "requested_level": 4}, fake_fetch)
    body = request.body or {}
    blockers = [finding["id"] for finding in body.get("findings", []) if finding["severity"] == "error"]
    check("level4 missing anchor status", request.status == 200)
    check("level4 missing anchor level", body.get("guide", {}).get("achieved_level") == 3)
    check("level4 missing anchor blocker", "anchor.independent.missing" in blockers)
    check("level4 missing anchor no proceed", "Proceed? no" in body.get("compact_report", ""))


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
    test_evaluated_level4_package_registry()
    test_evaluated_level4_missing_anchor()
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
