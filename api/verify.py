"""
GuideCheck hosted verifier API.

POST /api/verify with { "url": "https://..." }. The function resolves the
target, fetches it over the public web with SSRF protections, classifies the
outcome, and for a real guide artifact runs the GuideCheck Level 1-4 checks
where supported public-web provenance evidence is available.

A bare origin (no path) is resolved to the standard guide location at
/.well-known/assistant-guide.txt, so a user can paste a site URL and still
get a useful answer.

Outcomes (HTTP 200, body carries "outcome"):
- evaluated    a plain-text guide was fetched and checked
- not-found    the target returned a non-200 status
- not-a-guide  the target returned an HTML page, not a plain-text guide

Genuine failures (bad request, https/SSRF rejection, DNS, timeout, rate
limit) return HTTP 4xx with an {"error": ...} body.

This hosted verifier evaluates Levels 1 through 4, with a scoped Level 4
anchor set, and always returns a hosted_limitations field. Check logic is
shared with the local reference verifier via
scripts/guidecheck_verify.evaluate_guide.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit, urlunsplit

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_ROOT, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import guidecheck_verify as gv  # noqa: E402
from guidecheck_fetch import FetchError, safe_fetch  # noqa: E402


HOSTED_NAME = "guidecheck-hosted"
HOSTED_VERSION = "0.2.1"
WELL_KNOWN_PATH = "/.well-known/assistant-guide.txt"
MAX_REQUEST_BODY = 4096
ANALYTICS_EVENT = "guidecheck_verify"
HOSTED_LIMITATIONS = [
    "This verifier evaluates Levels 1 through 4 when supported Level 4 evidence is available.",
    "Hosted Level 4 currently supports package-registry and transparency-log anchors; DNS TXT, repository-file, and signed security.txt anchors are not fetched.",
    "Level 5 runtime conformance is not evaluated.",
]

# Best-effort per-IP rate limit. Serverless instances are ephemeral, so this
# only constrains a warm instance; it is a first line, not the whole control.
_RATE_WINDOW = 60.0
_RATE_MAX = 12
_rate_hits: dict[str, list[float]] = {}

AGENT_CHOICES = {
    "unspecified": ("unspecified", "unspecified"),
    "chatgpt": ("openai", "chatgpt"),
    "codex": ("openai", "codex"),
    "claude": ("anthropic", "claude"),
    "gemini": ("google", "gemini"),
    "cursor": ("cursor", "cursor"),
    "copilot": ("github", "copilot"),
    "local": ("local", "local"),
    "other": ("other", "other"),
}


def _rate_ok(client_ip: str) -> bool:
    now = time.monotonic()
    hits = [t for t in _rate_hits.get(client_ip, []) if now - t < _RATE_WINDOW]
    if len(hits) >= _RATE_MAX:
        _rate_hits[client_ip] = hits
        return False
    hits.append(now)
    _rate_hits[client_ip] = hits
    return True


def _day(now: datetime) -> str:
    return now.date().isoformat()


def _duration_bucket(ms: int) -> str:
    if ms < 500:
        return "under-500ms"
    if ms < 1000:
        return "500ms-1s"
    if ms < 3000:
        return "1-3s"
    if ms < 10000:
        return "3-10s"
    if ms < 30000:
        return "10-30s"
    return "over-30s"


def _target_info(url: str | None) -> dict:
    if not url:
        return {
            "target_host": "unknown",
            "target_path_kind": "unknown",
            "target_scheme": "unknown",
        }
    parts = urlsplit(url)
    path = parts.path or "/"
    if path == WELL_KNOWN_PATH:
        path_kind = "well-known"
    elif path in ("", "/"):
        path_kind = "root"
    else:
        path_kind = "custom"
    host = (parts.hostname or "unknown").lower()
    if host.startswith("www."):
        host = host[4:]
    return {
        "target_host": host,
        "target_path_kind": path_kind,
        "target_scheme": parts.scheme or "unknown",
    }


def _analytics_context(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        payload = {}
    raw_agent = payload.get("agent")
    agent_key = raw_agent if isinstance(raw_agent, str) else "unspecified"
    agent_key = agent_key.strip().lower()
    if agent_key not in AGENT_CHOICES:
        agent_key = "unspecified"
    provider, family = AGENT_CHOICES[agent_key]

    raw_level = payload.get("requested_level")
    requested_level = raw_level if isinstance(raw_level, int) and raw_level in (1, 2, 3, 4) else None
    return {
        "agent_provider": provider,
        "agent_model_family": family,
        "requested_level": requested_level,
    }


def _failure_category(outcome: str, findings: list[gv.Finding] | None = None, error_code: str | None = None) -> str:
    if error_code:
        if error_code in {"scheme", "bad-request"}:
            return "request_invalid"
        if error_code == "rate-limited":
            return "rate_limited"
        return "fetch_failed"
    if outcome == "not-found":
        return "not_found"
    if outcome == "not-a-guide":
        return "not_plain_text"
    if outcome != "evaluated":
        return outcome
    blocker_ids = [f.id for f in findings or [] if f.severity == "error"]
    if not blocker_ids:
        return "none"
    if any(fid.startswith("byte-profile.") or fid.startswith("construct.") for fid in blocker_ids):
        return "byte_profile"
    if any(fid.startswith("metadata.") for fid in blocker_ids):
        return "metadata"
    if any(fid.startswith("action.") for fid in blocker_ids):
        return "actions"
    if any(fid.startswith("content.") for fid in blocker_ids):
        return "required_content"
    if any(fid.startswith("manifest.") or fid.startswith("anchor.") for fid in blocker_ids):
        return "provenance"
    return "other_blocking_findings"


def _log_product_event(
    *,
    now: datetime,
    started: float,
    status: int,
    outcome: str,
    payload: dict | None = None,
    checked_url: str | None = None,
    auto_resolved: bool | None = None,
    achieved_level: int | None = None,
    findings: list[gv.Finding] | None = None,
    error_code: str | None = None,
) -> None:
    payload_context = _analytics_context(payload)
    event = {
        "event": ANALYTICS_EVENT,
        "day": _day(now),
        "route": "/api/verify",
        "status": status,
        "outcome": outcome,
        "failure_category": _failure_category(outcome, findings, error_code),
        "duration_bucket": _duration_bucket(int((time.monotonic() - started) * 1000)),
        "auto_resolved": bool(auto_resolved),
        "achieved_level": achieved_level,
        "conformance_delta": (
            achieved_level - payload_context["requested_level"]
            if achieved_level is not None and payload_context["requested_level"] is not None
            else None
        ),
    }
    event.update(payload_context)
    if (
        event["outcome"] == "evaluated"
        and event["failure_category"] == "none"
        and isinstance(event["conformance_delta"], int)
        and event["conformance_delta"] < 0
    ):
        event["failure_category"] = "below_requested_level"
    event.update(_target_info(checked_url))
    print(json.dumps(event, sort_keys=True), flush=True)


def resolve_target_url(submitted: str) -> tuple[str, bool]:
    """Resolve the URL to fetch.

    A bare origin (empty path or '/') is rewritten to the well-known guide
    location. Returns (url_to_fetch, auto_resolved).
    """
    parts = urlsplit(submitted)
    if parts.path in ("", "/") and not parts.query:
        resolved = urlunsplit((parts.scheme, parts.netloc, WELL_KNOWN_PATH, "", ""))
        return resolved, True
    return submitted, False


def looks_like_html(body: bytes) -> bool:
    """True if the body is an HTML document rather than a plain-text guide."""
    head = body[:1024].lstrip().lower()
    return b"<!doctype html" in head or b"<html" in head


def well_known_for(url: str) -> str:
    """Return the canonical guide URL for the origin of the given URL."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, WELL_KNOWN_PATH, "", ""))


def _guide_metadata(body: bytes) -> dict[str, str]:
    blocks, _ = gv.parse_key_block(
        gv.decode_text(body),
        "[assistant-guide-metadata]",
        "[/assistant-guide-metadata]",
    )
    return blocks[0] if len(blocks) == 1 else {}


def _body_text(body: bytes) -> str:
    return body.decode("utf-8", errors="replace")


def _fetch_text_evidence(url: str, evidence_kind: str, findings: list[gv.Finding]) -> str | None:
    try:
        fetched = safe_fetch(url)
    except FetchError as exc:
        severity = "error" if evidence_kind == "manifest" else "warning"
        fid = "manifest.fetch-failed" if evidence_kind == "manifest" else "anchor.independent.unreachable"
        findings.append(
            gv.Finding(
                fid,
                severity,
                f"{evidence_kind} could not be fetched",
                section="verifier-conformance.22" if evidence_kind == "manifest" else "verifier-conformance.23",
                evidence=exc.code,
            )
        )
        return None
    except Exception:
        severity = "error" if evidence_kind == "manifest" else "warning"
        fid = "manifest.fetch-failed" if evidence_kind == "manifest" else "anchor.independent.unreachable"
        findings.append(
            gv.Finding(
                fid,
                severity,
                f"{evidence_kind} could not be fetched",
                section="verifier-conformance.22" if evidence_kind == "manifest" else "verifier-conformance.23",
            )
        )
        return None

    if fetched.status != 200:
        severity = "error" if evidence_kind == "manifest" else "warning"
        fid = "manifest.fetch-failed" if evidence_kind == "manifest" else "anchor.independent.unreachable"
        findings.append(
            gv.Finding(
                fid,
                severity,
                f"{evidence_kind} returned HTTP {fetched.status}",
                section="verifier-conformance.22" if evidence_kind == "manifest" else "verifier-conformance.23",
            )
        )
        return None
    if looks_like_html(fetched.body):
        severity = "error" if evidence_kind == "manifest" else "warning"
        fid = "manifest.fetch-failed" if evidence_kind == "manifest" else "anchor.independent.unreachable"
        findings.append(
            gv.Finding(
                fid,
                severity,
                f"{evidence_kind} returned HTML instead of plain text evidence",
                section="verifier-conformance.22" if evidence_kind == "manifest" else "verifier-conformance.23",
            )
        )
        return None
    return _body_text(fetched.body)


def _hosted_level4_evidence(body: bytes) -> tuple[str | None, dict[str, str], list[gv.Finding]]:
    metadata = _guide_metadata(body)
    manifest_url = metadata.get("manifest-url")
    extra_findings: list[gv.Finding] = []
    anchor_texts: dict[str, str] = {}
    manifest_text: str | None = None

    if not manifest_url:
        return None, anchor_texts, extra_findings

    manifest_text = _fetch_text_evidence(manifest_url, "manifest", extra_findings)
    if manifest_text is None:
        return None, anchor_texts, extra_findings

    registry_url = metadata.get("registry-url")
    if registry_url:
        registry_text = _fetch_text_evidence(registry_url, "package-registry anchor", extra_findings)
        if registry_text is not None:
            anchor_texts["package-registry"] = registry_text

    manifest = gv.parse_manifest(manifest_text)
    transparency_url = manifest.get("transparency-log-url")
    if transparency_url:
        transparency_text = _fetch_text_evidence(transparency_url, "transparency-log anchor", extra_findings)
        if transparency_text is not None:
            anchor_texts["transparency-log"] = transparency_text

    return manifest_text, anchor_texts, extra_findings


def _verifier_block() -> dict:
    return {
        "name": HOSTED_NAME,
        "version": HOSTED_VERSION,
        "verifier_profile": gv.VERIFIER_PROFILE,
        "verifier_profile_version": gv.VERIFIER_PROFILE_VERSION,
        "guide_profile": gv.GUIDE_PROFILE,
        "guide_profile_version": gv.GUIDE_PROFILE_VERSION,
    }


def _input_block(submitted: str, checked: str, auto_resolved: bool) -> dict:
    return {
        "evaluation_mode": "public-web",
        "url": checked,
        "submitted_url": submitted,
        "auto_resolved": auto_resolved,
    }


def _fetch_block(fetched, now: datetime) -> dict:
    return {
        "final_url": fetched.final_url,
        "fetched_at": now.isoformat().replace("+00:00", "Z"),
        "http_status": fetched.status,
        "headers": fetched.headers,
        "redirects": fetched.redirects,
        "tls_valid": fetched.tls_valid,
        "bytes": len(fetched.body),
    }


def _compact_report(result: dict) -> str:
    guide = result["guide"]
    summary = result["summary"]
    return "\n".join(
        [
            f"Verifier: {result['verifier']['name']} {result['verifier']['version']}",
            f"Guide: {result['input']['url']}",
            f"Level: {guide['achieved_level']}",
            f"SHA-256: {guide['sha256']}",
            f"Blocking findings: {summary['blocking_findings']}",
            f"Warnings: {summary['warnings']}",
            f"Hash pinned: {'yes' if guide['achieved_level'] >= 4 else 'no'}",
            f"Proceed? {'yes' if summary['blocking_findings'] == 0 else 'no'}",
        ]
    )


def _location_note(checked: str) -> str | None:
    """Guidance when a guide was verified at a non-canonical path."""
    if urlsplit(checked).path == WELL_KNOWN_PATH:
        return None
    return (
        f"This guide was verified at {checked}, which is not the standard "
        f"location. A conformant guide must be named assistant-guide.txt and "
        f"served at {well_known_for(checked)} so assistants can discover it. "
        f"Move or copy the file there."
    )


def build_not_found(submitted, checked, auto_resolved, fetched, now) -> dict:
    well_known = well_known_for(checked)
    if checked == well_known:
        message = (
            f"No assistant-guide.txt was found at {checked} (HTTP "
            f"{fetched.status}). That is the standard location GuideCheck "
            f"checks. If this site publishes an install guide under another "
            f"name or path, rename it to assistant-guide.txt and serve it there."
        )
    else:
        message = (
            f"No file was found at {checked} (HTTP {fetched.status}). A "
            f"conformant guide is served at {well_known}."
        )
    return {
        "verifier": _verifier_block(),
        "input": _input_block(submitted, checked, auto_resolved),
        "outcome": "not-found",
        "fetch": _fetch_block(fetched, now),
        "message": message,
        "hosted_limitations": list(HOSTED_LIMITATIONS),
    }


def build_not_a_guide(submitted, checked, auto_resolved, fetched, now) -> dict:
    content_type = fetched.headers.get("content-type", "unknown")
    message = (
        f"{checked} returned an HTML web page (content-type: {content_type}), "
        f"not a plain-text assistant-guide.txt. A conformant guide is a plain "
        f"ASCII .txt file, not HTML. If this site has an install guide, publish "
        f"it as plain text named assistant-guide.txt at {well_known_for(checked)}."
    )
    return {
        "verifier": _verifier_block(),
        "input": _input_block(submitted, checked, auto_resolved),
        "outcome": "not-a-guide",
        "fetch": _fetch_block(fetched, now),
        "message": message,
        "hosted_limitations": list(HOSTED_LIMITATIONS),
    }


def build_evaluated(
    submitted,
    checked,
    auto_resolved,
    fetched,
    findings,
    achieved_level,
    level5_ready,
    now,
    manifest_evidence=None,
    cross_channel_anchors=None,
) -> dict:
    data = fetched.body
    blocking = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    infos = sum(1 for f in findings if f.severity == "info")
    result: dict = {
        "verifier": _verifier_block(),
        "input": _input_block(submitted, checked, auto_resolved),
        "outcome": "evaluated",
        "fetch": _fetch_block(fetched, now),
        "guide": {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "achieved_level": achieved_level,
            "level5_ready": level5_ready,
        },
        "summary": {
            "blocking_findings": blocking,
            "warnings": warnings,
            "infos": infos,
        },
        "findings": [f.as_dict() for f in findings],
        "hosted_limitations": list(HOSTED_LIMITATIONS),
    }
    if manifest_evidence is not None:
        result["manifest"] = manifest_evidence.as_dict()
    if cross_channel_anchors:
        result["cross_channel_anchors"] = [
            anchor.as_dict() for anchor in cross_channel_anchors
        ]
    note = _location_note(checked)
    if note:
        result["location_note"] = note
    result["compact_report"] = _compact_report(result)
    return result


class handler(BaseHTTPRequestHandler):
    # Vercel's Python runtime dispatches to this class per request.

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, code: str, message: str) -> None:
        self._write_json(
            status,
            {
                "error": {"code": code, "message": message},
                "hosted_limitations": list(HOSTED_LIMITATIONS),
            },
        )

    def log_message(self, *args) -> None:  # noqa: D401
        # Suppress default request logging; submitted guide URLs may be
        # sensitive and must not land in stdout request logs.
        return

    def do_GET(self) -> None:
        self._error(405, "method-not-allowed", "send a POST request with a JSON body")

    def do_POST(self) -> None:
        started = time.monotonic()
        payload: dict | None = None
        checked_url: str | None = None
        auto_resolved: bool | None = None

        def fail(status: int, code: str, message: str) -> None:
            _log_product_event(
                now=datetime.now(timezone.utc),
                started=started,
                status=status,
                outcome="error",
                payload=payload,
                checked_url=checked_url,
                auto_resolved=auto_resolved,
                error_code=code,
            )
            self._error(status, code, message)

        forwarded = self.headers.get("x-forwarded-for", "")
        client_ip = forwarded.split(",")[0].strip() or self.client_address[0]
        if not _rate_ok(client_ip):
            fail(429, "rate-limited", "too many requests; try again shortly")
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_REQUEST_BODY:
            fail(400, "bad-request", "the request body is missing or too large")
            return

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw)
            url = payload["url"]
        except (json.JSONDecodeError, KeyError, TypeError):
            fail(400, "bad-request", "the body must be JSON with a string url field")
            return
        if not isinstance(url, str) or not url.strip():
            fail(400, "bad-request", "the body must be JSON with a string url field")
            return
        url = url.strip()

        if not url.lower().startswith("https://"):
            checked_url = url
            fail(400, "scheme", "the guide URL must use https")
            return

        checked_url, auto_resolved = resolve_target_url(url)

        try:
            fetched = safe_fetch(checked_url)
        except FetchError as exc:
            fail(400, exc.code, exc.message)
            return
        except Exception:
            fail(502, "fetch-failed", "the guide could not be fetched")
            return

        now = datetime.now(timezone.utc)
        if fetched.status != 200:
            _log_product_event(
                now=now,
                started=started,
                status=200,
                outcome="not-found",
                payload=payload,
                checked_url=checked_url,
                auto_resolved=auto_resolved,
            )
            self._write_json(200, build_not_found(url, checked_url, auto_resolved, fetched, now))
            return
        if looks_like_html(fetched.body):
            _log_product_event(
                now=now,
                started=started,
                status=200,
                outcome="not-a-guide",
                payload=payload,
                checked_url=checked_url,
                auto_resolved=auto_resolved,
            )
            self._write_json(200, build_not_a_guide(url, checked_url, auto_resolved, fetched, now))
            return

        manifest_text, anchor_texts, hosted_evidence_findings = _hosted_level4_evidence(fetched.body)
        findings, achieved_level, level5_ready, manifest_evidence, cross_channel_anchors = gv.evaluate_guide(
            fetched.body,
            manifest_text,
            anchor_texts,
            now=now,
        )
        if manifest_evidence is not None:
            manifest_evidence.fetched = True
        findings.extend(hosted_evidence_findings)
        _log_product_event(
            now=now,
            started=started,
            status=200,
            outcome="evaluated",
            payload=payload,
            checked_url=checked_url,
            auto_resolved=auto_resolved,
            achieved_level=achieved_level,
            findings=findings,
        )
        self._write_json(
            200,
            build_evaluated(
                url,
                checked_url,
                auto_resolved,
                fetched,
                findings,
                achieved_level,
                level5_ready,
                now,
                manifest_evidence,
                cross_channel_anchors,
            ),
        )
