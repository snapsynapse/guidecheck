#!/usr/bin/env python3
"""
Helpers for hosted-verifier Level 4 anchor fetching.

The hosted verifier resolves the following independent channels by fetching
external evidence:

- package-registry  (existing, see api/verify.py)
- transparency-log  (existing, see api/verify.py)
- repository-file   (this module, github.com only in 0.6.0)
- dns-txt           (this module, DoH via Cloudflare in 0.6.0)

This module owns the URL derivation and DoH response parsing for the two new
channels. It does no network IO itself; api/verify.py supplies a fetcher that
applies the SSRF-hardened safe_fetch plus the hosted fetch budget.

The repository-file allowlist is intentionally small in 0.6.0. The roadmap
tracks expansion to gitlab.com, codeberg.org, bitbucket.org, and git.sr.ht.
Self-hosted code-host instances cannot be allowlisted generically and are
deferred to a future per-instance opt-in.
"""

from __future__ import annotations

import json
from urllib.parse import urlsplit, quote

GITHUB_HOST = "github.com"
ALLOWED_REPO_HOSTS = frozenset({GITHUB_HOST})

DOH_PROVIDER_NAME = "cloudflare-dns.com"
DOH_ENDPOINT = "https://cloudflare-dns.com/dns-query"
DOH_ACCEPT = "application/dns-json"

DNS_TXT_PREFIX = "_assistant-guide."
DNS_TXT_VERSION = "v=1"


def derive_repository_file_url(repository_url: str | None, source_path: str | None) -> tuple[str | None, str | None]:
    """Return (raw URL, reason) for a repository-file anchor fetch.

    Returns (url, None) on success. Returns (None, reason) when the channel
    does not apply or the host is not allowlisted. The reason is a short token
    suitable for an evidence field on a warning finding.
    """
    if not repository_url or not source_path:
        return None, None
    parts = urlsplit(repository_url)
    if parts.scheme != "https" or not parts.hostname:
        return None, "repository-url not https"
    host = parts.hostname.lower()
    if host not in ALLOWED_REPO_HOSTS:
        return None, host
    segments = [seg for seg in parts.path.split("/") if seg]
    if len(segments) < 2:
        return None, "repository-url missing owner or repo"
    owner, repo = segments[0], segments[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    clean_path = source_path.lstrip("/")
    if not clean_path:
        return None, "source-path empty"
    if host == GITHUB_HOST:
        ref = _github_ref_from_segments(segments)
        encoded = "/".join(quote(p, safe="") for p in clean_path.split("/"))
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{quote(ref, safe='/')}/{encoded}", None
    return None, host


def _github_ref_from_segments(segments: list[str]) -> str:
    """Return the GitHub ref named by repository_url, or HEAD for repo roots."""
    if len(segments) >= 4 and segments[2] in {"tree", "blob"}:
        return "/".join(segments[3:])
    if len(segments) >= 4 and segments[2] == "commit":
        return segments[3]
    return "HEAD"


def derive_dns_txt_query_url(canonical_url: str | None) -> tuple[str | None, str | None]:
    """Return (DoH query URL, host) for the DNS TXT anchor.

    canonical-url's hostname is used as the registered-domain proxy; the spec
    locates the TXT record at `_assistant-guide.<registered-domain>` but the
    hosted verifier treats the canonical host as authoritative. A future
    improvement could resolve the registered domain explicitly.
    """
    if not canonical_url:
        return None, None
    parts = urlsplit(canonical_url)
    if not parts.hostname:
        return None, None
    host = parts.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    qname = f"{DNS_TXT_PREFIX}{host}"
    url = f"{DOH_ENDPOINT}?name={quote(qname, safe='')}&type=TXT"
    return url, host


def parse_doh_txt_response(body: bytes) -> tuple[list[str], bool] | None:
    """Return (TXT strings, DNSSEC-validated bool) from a DoH JSON response.

    Returns None if the body is not valid DoH JSON or NXDOMAIN. DNSSEC
    validation is taken from the AD bit reported by the resolver; the hosted
    verifier trusts the resolver's chain check in 0.6.0. A future
    client-side DNSSEC validator is on the roadmap.
    """
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    status = data.get("Status")
    if not isinstance(status, int) or status != 0:
        return None
    answers = data.get("Answer")
    if not isinstance(answers, list):
        return [], bool(data.get("AD"))
    records: list[str] = []
    for ans in answers:
        if not isinstance(ans, dict):
            continue
        rtype = ans.get("type")
        # TXT = 16. Some DoH providers also return CNAMEs (type 5); skip them.
        if rtype != 16:
            continue
        raw = ans.get("data")
        if not isinstance(raw, str):
            continue
        records.append(_strip_txt_quotes(raw))
    return records, bool(data.get("AD"))


def _strip_txt_quotes(raw: str) -> str:
    """Strip surrounding TXT quoting and join concatenated TXT strings."""
    pieces: list[str] = []
    buf: list[str] = []
    in_quote = False
    escape = False
    for ch in raw:
        if escape:
            buf.append(ch)
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            if in_quote:
                pieces.append("".join(buf))
                buf = []
                in_quote = False
            else:
                in_quote = True
            continue
        if in_quote:
            buf.append(ch)
    if buf and in_quote:
        pieces.append("".join(buf))
    if pieces:
        return "".join(pieces)
    return raw.strip()


def select_dns_txt_record(records: list[str], expected_canonical_url: str | None) -> str | None:
    """Choose the GuideCheck TXT record from a TXT RRset.

    Picks the first `v=1; sha256=...; url=<canonical-url>` record whose url
    matches expected_canonical_url. Falls back to the first record beginning
    with `v=1` when no url comparison is possible.
    """
    candidates = [r for r in records if r.lstrip().startswith(DNS_TXT_VERSION)]
    if not candidates:
        return None
    if expected_canonical_url:
        for record in candidates:
            if _txt_url_field(record) == expected_canonical_url:
                return record
        return None
    return candidates[0]


def _txt_url_field(record: str) -> str | None:
    for chunk in record.split(";"):
        chunk = chunk.strip()
        if chunk.startswith("url="):
            return chunk[len("url="):].strip()
    return None
