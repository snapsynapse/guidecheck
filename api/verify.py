"""
GuideCheck hosted verifier API.

POST /api/verify with { "url": "https://..." }. The function resolves the
target, fetches it over the public web with SSRF protections, classifies the
outcome, and for a real guide artifact runs the GuideCheck Level 1-3 checks.

A bare origin (no path) is resolved to the standard guide location at
/.well-known/assistant-guide.txt, so a user can paste a site URL and still
get a useful answer.

Outcomes (HTTP 200, body carries "outcome"):
- evaluated    a plain-text guide was fetched and checked
- not-found    the target returned a non-200 status
- not-a-guide  the target returned an HTML page, not a plain-text guide

Genuine failures (bad request, https/SSRF rejection, DNS, timeout, rate
limit) return HTTP 4xx with an {"error": ...} body.

This hosted verifier evaluates Levels 1 through 3 only and always returns a
hosted_limitations field. Check logic is shared with the local reference
verifier via scripts/guidecheck_verify.evaluate_guide.
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
HOSTED_VERSION = "0.1.0"
WELL_KNOWN_PATH = "/.well-known/assistant-guide.txt"
MAX_REQUEST_BODY = 4096
HOSTED_LIMITATIONS = [
    "This verifier evaluates Levels 1 through 3 only.",
    "Level 4 provenance and independent anchors are not implemented.",
    "Level 5 runtime conformance is not evaluated.",
]

# Best-effort per-IP rate limit. Serverless instances are ephemeral, so this
# only constrains a warm instance; it is a first line, not the whole control.
_RATE_WINDOW = 60.0
_RATE_MAX = 12
_rate_hits: dict[str, list[float]] = {}


def _rate_ok(client_ip: str) -> bool:
    now = time.monotonic()
    hits = [t for t in _rate_hits.get(client_ip, []) if now - t < _RATE_WINDOW]
    if len(hits) >= _RATE_MAX:
        _rate_hits[client_ip] = hits
        return False
    hits.append(now)
    _rate_hits[client_ip] = hits
    return True


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
            "Hash pinned: no",
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


def build_evaluated(submitted, checked, auto_resolved, fetched, findings, achieved_level, now) -> dict:
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
            "achieved_level": min(achieved_level, 3),
            "level5_ready": False,
        },
        "summary": {
            "blocking_findings": blocking,
            "warnings": warnings,
            "infos": infos,
        },
        "findings": [f.as_dict() for f in findings],
        "hosted_limitations": list(HOSTED_LIMITATIONS),
    }
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
        forwarded = self.headers.get("x-forwarded-for", "")
        client_ip = forwarded.split(",")[0].strip() or self.client_address[0]
        if not _rate_ok(client_ip):
            self._error(429, "rate-limited", "too many requests; try again shortly")
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_REQUEST_BODY:
            self._error(400, "bad-request", "the request body is missing or too large")
            return

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw)
            url = payload["url"]
        except (json.JSONDecodeError, KeyError, TypeError):
            self._error(400, "bad-request", "the body must be JSON with a string url field")
            return
        if not isinstance(url, str) or not url.strip():
            self._error(400, "bad-request", "the body must be JSON with a string url field")
            return
        url = url.strip()

        if not url.lower().startswith("https://"):
            self._error(400, "scheme", "the guide URL must use https")
            return

        checked_url, auto_resolved = resolve_target_url(url)

        try:
            fetched = safe_fetch(checked_url)
        except FetchError as exc:
            self._error(400, exc.code, exc.message)
            return
        except Exception:
            self._error(502, "fetch-failed", "the guide could not be fetched")
            return

        now = datetime.now(timezone.utc)
        if fetched.status != 200:
            self._write_json(200, build_not_found(url, checked_url, auto_resolved, fetched, now))
            return
        if looks_like_html(fetched.body):
            self._write_json(200, build_not_a_guide(url, checked_url, auto_resolved, fetched, now))
            return

        findings, achieved_level, _ = gv.evaluate_guide(fetched.body, None, now)
        self._write_json(
            200,
            build_evaluated(url, checked_url, auto_resolved, fetched, findings, achieved_level, now),
        )
