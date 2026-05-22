"""
GuideCheck hosted verifier API.

POST /api/verify with a JSON body { "url": "https://..." } and the function
fetches the guide over the public web, runs the GuideCheck Level 1-3 checks,
and returns verifier JSON plus a compact report.

This hosted verifier evaluates Levels 1 through 3 only. It does not fetch
sidecar manifests, check independent provenance anchors (Level 4), or evaluate
runtime conformance (Level 5). The response always carries an explicit
hosted_limitations field saying so.

Check logic is shared with the local reference verifier via
scripts/guidecheck_verify.evaluate_guide, so hosted and local results agree.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_ROOT, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import guidecheck_verify as gv  # noqa: E402
from guidecheck_fetch import FetchError, safe_fetch  # noqa: E402


HOSTED_NAME = "guidecheck-hosted"
HOSTED_VERSION = "0.1.0"
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


def build_response(url, fetched, findings, achieved_level, now):
    """Assemble the hosted verifier response. Achieved level is capped at 3."""
    data = fetched.body
    blocking = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    infos = sum(1 for f in findings if f.severity == "info")
    result: dict = {
        "verifier": {
            "name": HOSTED_NAME,
            "version": HOSTED_VERSION,
            "verifier_profile": gv.VERIFIER_PROFILE,
            "verifier_profile_version": gv.VERIFIER_PROFILE_VERSION,
            "guide_profile": gv.GUIDE_PROFILE,
            "guide_profile_version": gv.GUIDE_PROFILE_VERSION,
        },
        "input": {
            "evaluation_mode": "public-web",
            "url": url,
        },
        "fetch": {
            "final_url": fetched.final_url,
            "fetched_at": now.isoformat().replace("+00:00", "Z"),
            "http_status": fetched.status,
            "headers": fetched.headers,
            "redirects": fetched.redirects,
            "tls_valid": fetched.tls_valid,
        },
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

        try:
            fetched = safe_fetch(url)
        except FetchError as exc:
            self._error(400, exc.code, exc.message)
            return
        except Exception:
            self._error(502, "fetch-failed", "the guide could not be fetched")
            return

        if fetched.status != 200:
            self._error(
                400,
                "http-status",
                f"the guide URL returned HTTP {fetched.status}",
            )
            return

        now = datetime.now(timezone.utc)
        findings, achieved_level, _ = gv.evaluate_guide(fetched.body, None, now)
        self._write_json(200, build_response(url, fetched, findings, achieved_level, now))
