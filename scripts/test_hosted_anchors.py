#!/usr/bin/env python3
"""Unit tests for scripts/guidecheck_hosted_anchors.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import guidecheck_hosted_anchors as gha


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


def test_derive_repository_file_url_github() -> None:
    url, reason = gha.derive_repository_file_url(
        "https://github.com/snapsynapse/guidecheck",
        "/docs/.well-known/assistant-guide.txt",
    )
    check(
        "github raw url",
        url == "https://raw.githubusercontent.com/snapsynapse/guidecheck/HEAD/docs/.well-known/assistant-guide.txt",
        f"got {url!r}",
    )
    check("github reason empty", reason is None)


def test_derive_repository_file_url_github_strip_dot_git() -> None:
    url, _ = gha.derive_repository_file_url(
        "https://github.com/owner/repo.git",
        "guide.txt",
    )
    check(
        "github strips .git suffix",
        url == "https://raw.githubusercontent.com/owner/repo/HEAD/guide.txt",
        f"got {url!r}",
    )


def test_derive_repository_file_url_github_tree_ref() -> None:
    url, _ = gha.derive_repository_file_url(
        "https://github.com/owner/repo/tree/release/v1",
        "/docs/guide.txt",
    )
    check(
        "github tree ref used",
        url == "https://raw.githubusercontent.com/owner/repo/release/v1/docs/guide.txt",
        f"got {url!r}",
    )


def test_derive_repository_file_url_github_commit_ref() -> None:
    sha = "0123456789abcdef0123456789abcdef01234567"
    url, _ = gha.derive_repository_file_url(
        f"https://github.com/owner/repo/commit/{sha}",
        "/docs/guide.txt",
    )
    check(
        "github commit ref used",
        url == f"https://raw.githubusercontent.com/owner/repo/{sha}/docs/guide.txt",
        f"got {url!r}",
    )


def test_derive_repository_file_url_rejects_non_allowlisted() -> None:
    url, reason = gha.derive_repository_file_url(
        "https://gitlab.com/owner/repo",
        "/guide.txt",
    )
    check("gitlab url is None", url is None)
    check("gitlab reason names host", reason == "gitlab.com")

    url, reason = gha.derive_repository_file_url(
        "https://attacker.example/owner/repo",
        "/guide.txt",
    )
    check("self-hosted url is None", url is None)
    check("self-hosted reason names host", reason == "attacker.example")


def test_derive_repository_file_url_requires_inputs() -> None:
    url, reason = gha.derive_repository_file_url(None, "/guide.txt")
    check("missing repository-url returns nothing", url is None and reason is None)

    url, reason = gha.derive_repository_file_url("https://github.com/owner/repo", None)
    check("missing source-path returns nothing", url is None and reason is None)


def test_derive_repository_file_url_rejects_http() -> None:
    url, reason = gha.derive_repository_file_url(
        "http://github.com/owner/repo",
        "/guide.txt",
    )
    check("http repository-url rejected", url is None)
    check("http reason recorded", reason == "repository-url not https")


def test_derive_repository_file_url_path_encoding() -> None:
    url, _ = gha.derive_repository_file_url(
        "https://github.com/owner/repo",
        "/docs/has space/guide.txt",
    )
    check(
        "path encoded for raw URL",
        url == "https://raw.githubusercontent.com/owner/repo/HEAD/docs/has%20space/guide.txt",
        f"got {url!r}",
    )


def test_derive_dns_txt_query_url() -> None:
    url, host = gha.derive_dns_txt_query_url("https://guidecheck.org/.well-known/assistant-guide.txt")
    expected = "https://cloudflare-dns.com/dns-query?name=_assistant-guide.guidecheck.org&type=TXT"
    check("doh query url for bare host", url == expected, f"got {url!r}")
    check("doh host bare", host == "guidecheck.org")


def test_derive_dns_txt_query_url_strips_www() -> None:
    url, host = gha.derive_dns_txt_query_url("https://www.example.com/.well-known/assistant-guide.txt")
    check("doh host www stripped", host == "example.com")
    check("doh url name www stripped", "_assistant-guide.example.com" in (url or ""))


def test_parse_doh_txt_response_valid() -> None:
    body = json.dumps(
        {
            "Status": 0,
            "AD": True,
            "Answer": [
                {"type": 16, "data": "\"v=1; sha256=abc; url=https://example.com/guide\""}
            ],
        }
    ).encode("utf-8")
    parsed = gha.parse_doh_txt_response(body)
    check("doh parse ok", parsed is not None)
    if parsed:
        records, dnssec = parsed
        check("doh records extracted", records == ["v=1; sha256=abc; url=https://example.com/guide"], str(records))
        check("doh ad bit reported", dnssec is True)


def test_parse_doh_txt_response_joins_quoted_strings() -> None:
    # DNS TXT records longer than 255 bytes are split into multiple quoted
    # strings on the wire; DoH preserves the multi-string encoding.
    body = json.dumps(
        {
            "Status": 0,
            "AD": False,
            "Answer": [
                {"type": 16, "data": "\"first \" \"second\""}
            ],
        }
    ).encode("utf-8")
    parsed = gha.parse_doh_txt_response(body)
    check("doh joins parts", parsed is not None and parsed[0] == ["first second"], str(parsed))
    check("doh ad false reported", parsed is not None and parsed[1] is False)


def test_parse_doh_txt_response_skips_non_txt() -> None:
    body = json.dumps(
        {
            "Status": 0,
            "Answer": [
                {"type": 5, "data": "cname.example.com."},
                {"type": 16, "data": "\"v=1; sha256=abc\""},
            ],
        }
    ).encode("utf-8")
    parsed = gha.parse_doh_txt_response(body)
    check("doh skips cname", parsed is not None and parsed[0] == ["v=1; sha256=abc"], str(parsed))


def test_parse_doh_txt_response_rejects_nxdomain() -> None:
    body = json.dumps({"Status": 3}).encode("utf-8")
    check("doh nxdomain returns None", gha.parse_doh_txt_response(body) is None)


def test_parse_doh_txt_response_rejects_bad_json() -> None:
    check("doh bad json returns None", gha.parse_doh_txt_response(b"not json") is None)


def test_select_dns_txt_record_prefers_matching_url() -> None:
    records = [
        "v=1; sha256=aaa; url=https://other.example/g",
        "v=1; sha256=bbb; url=https://guidecheck.org/.well-known/assistant-guide.txt",
        "v=2; foo=bar",
    ]
    chosen = gha.select_dns_txt_record(records, "https://guidecheck.org/.well-known/assistant-guide.txt")
    check(
        "select prefers matching url",
        chosen == "v=1; sha256=bbb; url=https://guidecheck.org/.well-known/assistant-guide.txt",
        f"got {chosen!r}",
    )


def test_select_dns_txt_record_falls_back_to_first_v1() -> None:
    records = ["v=2; foo=bar", "v=1; sha256=aaa"]
    chosen = gha.select_dns_txt_record(records, None)
    check("select falls back to first v=1", chosen == "v=1; sha256=aaa", f"got {chosen!r}")


def test_select_dns_txt_record_no_fallback_when_url_mismatches() -> None:
    records = [
        "v=1; sha256=aaa; url=https://other.example/g",
        "v=1; sha256=bbb",
    ]
    chosen = gha.select_dns_txt_record(records, "https://guidecheck.org/.well-known/assistant-guide.txt")
    check("select no fallback on url mismatch", chosen is None, f"got {chosen!r}")


def test_select_dns_txt_record_returns_none_when_no_v1() -> None:
    records = ["v=2; foo=bar"]
    check("select no v=1 returns None", gha.select_dns_txt_record(records, "https://x") is None)


def main() -> int:
    test_derive_repository_file_url_github()
    test_derive_repository_file_url_github_strip_dot_git()
    test_derive_repository_file_url_github_tree_ref()
    test_derive_repository_file_url_github_commit_ref()
    test_derive_repository_file_url_rejects_non_allowlisted()
    test_derive_repository_file_url_requires_inputs()
    test_derive_repository_file_url_rejects_http()
    test_derive_repository_file_url_path_encoding()
    test_derive_dns_txt_query_url()
    test_derive_dns_txt_query_url_strips_www()
    test_parse_doh_txt_response_valid()
    test_parse_doh_txt_response_joins_quoted_strings()
    test_parse_doh_txt_response_skips_non_txt()
    test_parse_doh_txt_response_rejects_nxdomain()
    test_parse_doh_txt_response_rejects_bad_json()
    test_select_dns_txt_record_prefers_matching_url()
    test_select_dns_txt_record_falls_back_to_first_v1()
    test_select_dns_txt_record_no_fallback_when_url_mismatches()
    test_select_dns_txt_record_returns_none_when_no_v1()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
