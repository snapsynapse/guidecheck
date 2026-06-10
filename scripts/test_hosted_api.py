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
import guidecheck_constants as gc
import guidecheck_fetch as gf
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


def fetched(
    url: str,
    status: int,
    body: bytes,
    content_type: str = "text/plain; charset=utf-8",
    headers: dict[str, str] | None = None,
):
    response_headers = {
        "content-type": content_type,
        "x-content-type-options": "nosniff",
        "strict-transport-security": "max-age=31536000",
    }
    if headers is not None:
        response_headers = headers
    return SimpleNamespace(
        final_url=url,
        status=status,
        headers=response_headers,
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
    check("evaluated limitations", len(body.get("hosted_limitations", [])) == 4)


def test_evaluated_with_warnings() -> None:
    data = (ROOT / "fixtures" / "valid" / "prompterkit-level-3" / "guide.txt").read_bytes()
    url = "https://example.com/.well-known/assistant-guide.txt"
    request = run_post({"url": url}, lambda checked: fetched(checked, 200, data))
    body = request.body or {}
    check("evaluated warnings status", request.status == 200)
    check("evaluated warnings retained", body.get("summary", {}).get("warnings") == 4)
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
    check("level4 level5-ready", body.get("guide", {}).get("level5_ready") is True)
    check("level4 hash pinned", "Hash pinned: yes" in body.get("compact_report", ""))
    check("level4 manifest valid", body.get("manifest", {}).get("valid") is True)
    check("level4 manifest fetched", body.get("manifest", {}).get("fetched") is True)
    check(
        "level4 registry anchor",
        bool(anchors) and anchors[0].get("channel") == "package-registry"
        and anchors[0].get("status") == "present-matches",
    )


def test_level4_unrecognized_registry_host_not_independent() -> None:
    # A registry-url on a host the publisher can self-host provides no
    # independence. The attacker serves a matching hash, but the verifier must
    # not count it: Level 4 must fail with anchor.independent.missing and the
    # attacker URL must never be fetched.
    base = (ROOT / "fixtures" / "valid" / "level-4" / "guide.txt").read_text(encoding="utf-8")
    guide_url = "https://example.com/.well-known/assistant-guide.txt"
    manifest_url = "https://example.com/.well-known/assistant-guide-manifest.txt"
    registry_url = "https://attacker.example/fake-registry/example-verifier/1.0.0"
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

    def fake_fetch(checked):
        if checked == guide_url:
            return fetched(checked, 200, guide_data)
        if checked == manifest_url:
            return fetched(checked, 200, manifest)
        if checked == registry_url:
            raise AssertionError("unrecognized registry host must not be fetched")
        raise AssertionError(f"unexpected fetch {checked}")

    request = run_post({"url": guide_url, "requested_level": 4}, fake_fetch)
    body = request.body or {}
    blockers = [f["id"] for f in body.get("findings", []) if f["severity"] == "error"]
    warnings = [f["id"] for f in body.get("findings", []) if f["severity"] == "warning"]
    check("unrecognized-registry status", request.status == 200)
    check("unrecognized-registry not level4", body.get("guide", {}).get("achieved_level") == 3)
    check("unrecognized-registry anchor missing", "anchor.independent.missing" in blockers)
    check("unrecognized-registry warning", "anchor.registry.unrecognized-host" in warnings)


def test_package_registry_uses_assistant_guide_hash() -> None:
    # A package registry record can contain many sha256 fields. Only the hash
    # inside assistant-guide-specific metadata may satisfy the Level 4 anchor.
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
    wrong_sha = "0" * 64
    manifest = "\n".join(
        [
            "guide-path: /.well-known/assistant-guide.txt",
            "guide-version: 1.0.0",
            f"guide-sha256: {guide_sha}",
            f"guide-bytes: {len(guide_data)}",
            "immutable-release-url: https://example.com/org/example-verifier/releases/v1.0.0",
            "profile: human-verifiable-assistant-guide",
            "profile-version: 0.5.0",
            f"canonical-url: {guide_url}",
            "repository-url: https://example.com/org/example-verifier",
            "released-at: 2026-05-29T00:00:00Z",
            "",
        ]
    ).encode("utf-8")
    registry = (
        "{"
        f'"sha256":"{guide_sha}",'
        f'"assistantGuide":{{"url":"{guide_url}","sha256":"{wrong_sha}"}}'
        "}"
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
    blockers = [finding["id"] for finding in body.get("findings", []) if finding["severity"] == "error"]
    anchors = body.get("cross_channel_anchors", [])
    check("registry hash scoped status", request.status == 200)
    check("registry hash scoped not level4", body.get("guide", {}).get("achieved_level") == 3)
    check("registry hash scoped mismatch", "anchor.independent.mismatch" in blockers)
    check(
        "registry hash scoped observed assistantGuide",
        bool(anchors) and anchors[0].get("observed_sha256") == wrong_sha,
    )


def test_package_registry_url_mismatch_warns() -> None:
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
            "profile-version: 0.5.0",
            f"canonical-url: {guide_url}",
            "repository-url: https://example.com/org/example-verifier",
            "released-at: 2026-05-29T00:00:00Z",
            "",
        ]
    ).encode("utf-8")
    registry = json.dumps(
        {"assistantGuide": {"url": "https://evil.example/guide.txt", "sha256": guide_sha}},
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
    warnings = [finding["id"] for finding in body.get("findings", []) if finding["severity"] == "warning"]
    check("registry url mismatch status", request.status == 200)
    check("registry url mismatch still level4", body.get("guide", {}).get("achieved_level") == 4)
    check("registry url mismatch warning", "anchor.registry.url-mismatch" in warnings)


def test_evaluated_level4_not_level5_ready() -> None:
    base = (ROOT / "fixtures" / "valid" / "level-4-not-level5-ready" / "guide.txt").read_text(encoding="utf-8")
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
    warnings = [finding["id"] for finding in body.get("findings", []) if finding["severity"] == "warning"]
    check("level4 not level5-ready status", request.status == 200)
    check("level4 not level5-ready achieved", body.get("guide", {}).get("achieved_level") == 4)
    check("level4 not level5-ready flag", body.get("guide", {}).get("level5_ready") is False)
    check("level4 not level5-ready warning", "level5.runner.missing" in warnings)


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


def test_header_warnings() -> None:
    data = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_bytes()
    url = "https://example.com/.well-known/assistant-guide.txt"
    request = run_post(
        {"url": url},
        lambda checked: fetched(checked, 200, data, headers={"content-type": "text/plain"}),
    )
    body = request.body or {}
    warnings = [finding["id"] for finding in body.get("findings", []) if finding["severity"] == "warning"]
    check("header warnings status", request.status == 200)
    check("header content-type warning", "header.content-type.incompatible" in warnings)
    check("header nosniff warning", "header.x-content-type-options.missing" in warnings)
    check("header hsts warning", "header.hsts.missing" in warnings)


def test_content_variation_warning() -> None:
    first = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_bytes()
    second = first.replace(b"Assistant Guide: example-cli local install", b"Assistant Guide: changed-cli local install")
    url = "https://example.com/.well-known/assistant-guide.txt"
    calls = 0

    def fake_fetch(checked, request_profile="default"):
        nonlocal calls
        calls += 1
        return fetched(checked, 200, second if request_profile != "default" else first)

    request = run_post({"url": url}, fake_fetch)
    body = request.body or {}
    warnings = [finding["id"] for finding in body.get("findings", []) if finding["severity"] == "warning"]
    check("content variation status", request.status == 200)
    check("content variation refetched", calls >= 2)
    check("content variation warning", "fetch.content-variation" in warnings)


def test_content_variation_profile_unbranded() -> None:
    first = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_bytes()
    second = first.replace(b"Assistant Guide: example-cli local install", b"Assistant Guide: changed-cli local install")
    url = "https://example.com/.well-known/assistant-guide.txt"
    profiles: list[str] = []

    def fake_fetch(checked, request_profile="default"):
        profiles.append(request_profile)
        return fetched(checked, 200, second if request_profile != "default" else first)

    request = run_post({"url": url}, fake_fetch)
    body = request.body or {}
    warnings = [finding["id"] for finding in body.get("findings", []) if finding["severity"] == "warning"]
    variation_profiles = [profile for profile in profiles if profile != "default"]
    headers = [gf._request_headers(profile) for profile in variation_profiles]
    check("variation profile status", request.status == 200)
    check("variation profile selected", len(variation_profiles) == 1 and variation_profiles[0] in gf.VARIATION_PROFILES)
    check("variation profile unbranded", all("guidecheck" not in h["User-Agent"].lower() for h in headers))
    check("variation profile identity encoding", all(h["Accept-Encoding"] == "identity" for h in headers))
    check("variation profile detects bytes", "fetch.content-variation" in warnings)


def test_variation_profile_selection_contract() -> None:
    url = "https://example.com/.well-known/assistant-guide.txt"
    other_url = "https://other.example/.well-known/assistant-guide.txt"
    day = "2026-05-29"
    profile = gf.variation_request_profile(url, day)
    other_profile = gf.variation_request_profile(other_url, day)
    headers = gf._request_headers(profile)
    context = hv.HostedFetchContext(lambda checked, request_profile="default": fetched(checked, 200, b"x"))

    first = context.fetch(url, request_profile=profile)
    second = context.fetch(url, request_profile=profile)
    default = context.fetch(url)

    check("variation selection stable", gf.variation_request_profile(url, day) == profile)
    check("variation selection known", profile in gf.VARIATION_PROFILES)
    check("variation alternate known", other_profile in gf.VARIATION_PROFILES)
    check("variation selection unbranded", "guidecheck" not in headers["User-Agent"].lower())
    check("variation selection identity", headers["Accept-Encoding"] == "identity")
    check("variation cache same profile", first is second)
    check("variation cache separates default", default is not first)
    check("variation cache count", context.outbound_fetches == 2)


def test_fetch_budget_and_dedup() -> None:
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
            "profile-version: 0.5.0",
            f"canonical-url: {guide_url}",
            "repository-url: https://example.com/org/example-verifier",
            f"transparency-log-url: {registry_url}",
            "released-at: 2026-05-29T00:00:00Z",
            "",
        ]
    ).encode("utf-8")
    registry = json.dumps(
        {"assistantGuide": {"url": guide_url, "sha256": guide_sha}},
        sort_keys=True,
    ).encode("utf-8")
    calls: list[tuple[str, str]] = []

    def fake_fetch(checked, request_profile="default"):
        calls.append((checked, request_profile))
        if checked == guide_url:
            return fetched(checked, 200, guide_data)
        if checked == manifest_url:
            return fetched(checked, 200, manifest)
        if checked == registry_url:
            return fetched(checked, 200, registry, "application/json")
        raise AssertionError(f"unexpected fetch {checked}")

    request = run_post({"url": guide_url, "requested_level": 4}, fake_fetch)
    body = request.body or {}
    default_registry_calls = [call for call in calls if call == (registry_url, "default")]
    check("fetch budget status", request.status == 200)
    check("fetch budget capped", len(calls) <= hv.MAX_OUTBOUND_FETCHES, str(calls))
    check("fetch dedup registry transparency", len(default_registry_calls) == 1, str(calls))
    check("fetch budget level4", body.get("guide", {}).get("achieved_level") == 4)


def test_fetch_budget_exhaustion_evidence() -> None:
    findings: list = []
    context = hv.HostedFetchContext(lambda checked: fetched(checked, 200, b"x"), max_fetches=0)
    result = hv._fetch_text_evidence("https://example.com/manifest.txt", "manifest", findings, context)
    check("fetch budget manifest none", result is None)
    check(
        "fetch budget manifest evidence",
        bool(findings)
        and findings[0].id == "manifest.fetch-failed"
        and findings[0].evidence == "fetch-budget-exhausted",
    )

    findings = []
    context = hv.HostedFetchContext(lambda checked: fetched(checked, 200, b"x"), max_fetches=0)
    result = hv._fetch_text_evidence("https://example.com/anchor.txt", "package-registry anchor", findings, context)
    check("fetch budget anchor none", result is None)
    check(
        "fetch budget anchor evidence",
        bool(findings)
        and findings[0].id == "anchor.independent.unreachable"
        and findings[0].evidence == "fetch-budget-exhausted",
    )

    fetched_guide = fetched("https://example.com/.well-known/assistant-guide.txt", 200, b"Assistant Guide: X\n")
    context = hv.HostedFetchContext(lambda checked, request_profile="default": fetched_guide, max_fetches=0)
    variation_findings = hv._content_variation_findings(
        "https://example.com/.well-known/assistant-guide.txt",
        fetched_guide,
        context,
        hv.datetime(2026, 5, 29, tzinfo=hv.timezone.utc),
    )
    check(
        "fetch budget variation evidence",
        len(variation_findings) == 1
        and variation_findings[0].id == "fetch.content-variation.unchecked"
        and variation_findings[0].evidence == "fetch-budget-exhausted",
    )


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


def test_recommended_verifier_warnings() -> None:
    data = (ROOT / "fixtures" / "valid" / "level-3" / "guide.txt").read_text(encoding="utf-8")
    off_domain = data.replace(
        "recommended-verifier: https://guidecheck.org/verify",
        "recommended-verifier: https://verifier.example.net/verify",
    )
    standard = data
    off_findings, _level, _ready, _manifest, _anchors = hv.gv.evaluate_guide(off_domain.encode("utf-8"))
    standard_findings, _level, _ready, _manifest, _anchors = hv.gv.evaluate_guide(standard.encode("utf-8"))
    off_warnings = {finding.id for finding in off_findings if finding.severity == "warning"}
    standard_warnings = {finding.id for finding in standard_findings if finding.severity == "warning"}
    check("off-domain verifier warning", "metadata.recommended-verifier.off-domain" in off_warnings)
    check("standard verifier no warning", "metadata.recommended-verifier.off-domain" not in standard_warnings)


def test_version_constants() -> None:
    check("hosted version constant", hv.HOSTED_VERSION == gc.GUIDECHECK_VERSION)
    check("local version constant", hv.gv.VERIFIER_VERSION == gc.GUIDECHECK_VERSION)
    check("profile version constant", hv.gv.GUIDE_PROFILE_VERSION == gc.GUIDECHECK_VERSION)
    check("fetch user agent version", f"/{gc.GUIDECHECK_VERSION} " in gf.USER_AGENT)


def main() -> int:
    test_evaluated()
    test_evaluated_with_warnings()
    test_evaluated_level4_package_registry()
    test_level4_unrecognized_registry_host_not_independent()
    test_package_registry_uses_assistant_guide_hash()
    test_package_registry_url_mismatch_warns()
    test_evaluated_level4_not_level5_ready()
    test_evaluated_level4_missing_anchor()
    test_auto_resolved_origin()
    test_noncanonical_location_note()
    test_header_warnings()
    test_content_variation_warning()
    test_content_variation_profile_unbranded()
    test_variation_profile_selection_contract()
    test_fetch_budget_and_dedup()
    test_fetch_budget_exhaustion_evidence()
    test_not_found()
    test_not_a_guide()
    test_errors()
    test_rate_limit()
    test_recommended_verifier_warnings()
    test_version_constants()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
