#!/usr/bin/env python3
"""
Offline tests for the hosted verifier's public-web fetch and input handling.

These exercise scripts/guidecheck_fetch and api/verify without making outbound
network connections: scheme rejection, the IP blocklist, registered-domain
scope, rejection of localhost, loopback, private, link-local, and cloud
metadata targets, bare-origin URL resolution, and HTML-document detection.
Run with: make test-fetch-safety
"""

from __future__ import annotations

import ipaddress
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import guidecheck_fetch as gf
import verify as hv


PASSED = 0
FAILED = 0


def check(name: str, condition: bool) -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"PASS {name}")
    else:
        FAILED += 1
        print(f"FAIL {name}")


def expect_fetch_error(name: str, url: str, code: str) -> None:
    try:
        gf.safe_fetch(url)
    except gf.FetchError as exc:
        check(f"{name} -> {exc.code}", exc.code == code)
    except Exception as exc:  # noqa: BLE001
        check(name, False)
        print(f"     unexpected {type(exc).__name__}: {exc}")
    else:
        check(name, False)
        print("     expected FetchError, fetch returned a result")


def test_registered_domain() -> None:
    check("regdom plain", gf.registered_domain("example.com") == "example.com")
    check("regdom subdomain", gf.registered_domain("a.b.example.com") == "example.com")
    check("regdom co.uk", gf.registered_domain("shop.example.co.uk") == "example.co.uk")
    check("regdom bare host", gf.registered_domain("localhost") == "localhost")


def test_ip_blocklist() -> None:
    blocked = [
        "127.0.0.1", "10.0.0.1", "192.168.1.1", "172.16.0.1",
        "169.254.169.254", "169.254.0.1", "100.64.0.1",
        "0.0.0.0", "224.0.0.1", "::1", "fc00::1", "fe80::1",
        "::ffff:127.0.0.1", "::ffff:10.0.0.1",
    ]
    for addr in blocked:
        check(f"blocked {addr}", gf.ip_is_blocked(ipaddress.ip_address(addr)))
    allowed = ["8.8.8.8", "1.1.1.1", "2606:4700:4700::1111"]
    for addr in allowed:
        check(f"allowed {addr}", not gf.ip_is_blocked(ipaddress.ip_address(addr)))


def test_scheme_rejection() -> None:
    expect_fetch_error("http rejected", "http://example.com/guide.txt", "scheme")
    expect_fetch_error("ftp rejected", "ftp://example.com/guide.txt", "scheme")


def test_ssrf_targets() -> None:
    expect_fetch_error("localhost", "https://localhost/guide.txt", "blocked-target")
    expect_fetch_error("loopback ip", "https://127.0.0.1/guide.txt", "blocked-target")
    expect_fetch_error("private ip", "https://10.0.0.1/guide.txt", "blocked-target")
    expect_fetch_error(
        "metadata ip", "https://169.254.169.254/latest/meta-data/", "blocked-target"
    )
    expect_fetch_error("ipv6 loopback", "https://[::1]/guide.txt", "blocked-target")


def test_resolve_target_url() -> None:
    well_known = "https://example.com/.well-known/assistant-guide.txt"
    cases = [
        ("https://example.com/", well_known, True),
        ("https://example.com", well_known, True),
        ("https://example.com/docs/guide.txt", "https://example.com/docs/guide.txt", False),
        (well_known, well_known, False),
    ]
    for submitted, expect_url, expect_resolved in cases:
        url, resolved = hv.resolve_target_url(submitted)
        check(f"resolve {submitted}", url == expect_url and resolved == expect_resolved)


def test_looks_like_html() -> None:
    check("html doctype", hv.looks_like_html(b"<!DOCTYPE html>\n<html></html>"))
    check("html tag", hv.looks_like_html(b'  \n<html lang="en">'))
    check("plain guide", not hv.looks_like_html(b"Assistant Guide: Example\n\nTask scope\n"))
    check("empty body", not hv.looks_like_html(b""))


def main() -> int:
    test_registered_domain()
    test_ip_blocklist()
    test_scheme_rejection()
    test_ssrf_targets()
    test_resolve_target_url()
    test_looks_like_html()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
