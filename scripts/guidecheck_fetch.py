#!/usr/bin/env python3
"""
SSRF-hardened public-web fetch for the GuideCheck hosted verifier.

The hosted verifier accepts a user-supplied guide URL. Fetching arbitrary
user-supplied URLs is the main risk surface, so this module enforces the
controls described in docs/vercel-migration-handoff.md:

- HTTPS only, plaintext HTTP rejected
- no cookies, authorization headers, or ambient credentials
- DNS resolved before connecting; private and metadata targets rejected
- resolved IP re-checked after every redirect
- response size capped before and during buffering
- connect, read, and total request deadlines enforced
- redirects limited and recorded; cross-registered-domain redirects rejected
- fetch errors sanitized before they reach the caller

Standard library only. Not a Vercel route. Imported by api/verify.py and
exercised by scripts/test_fetch_safety.py.
"""

from __future__ import annotations

import http.client
import hashlib
import ipaddress
import socket
import ssl
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit

from guidecheck_constants import HOSTED_USER_AGENT


MAX_BYTES = 256 * 1024
CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 8.0
TOTAL_DEADLINE = 12.0
MAX_REDIRECTS = 5
USER_AGENT = HOSTED_USER_AGENT
VARIATION_PROFILES = {
    "variation-browser": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "text/plain, application/octet-stream;q=0.8, */*;q=0.1",
    ),
    "variation-cli": (
        "curl/8.4.0",
        "text/plain;q=1.0, */*;q=0.2",
    ),
}
REPORT_HEADERS = {
    "content-type",
    "x-content-type-options",
    "strict-transport-security",
    "content-length",
}

# Best-effort multi-label public suffixes so a redirect from example.co.uk to
# evil.co.uk is treated as cross-domain. This is a curated subset, not the full
# Public Suffix List; the redirect policy is deliberately strict by default.
_MULTI_SUFFIXES = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "me.uk", "ltd.uk", "plc.uk",
    "co.jp", "or.jp", "ne.jp", "com.au", "net.au", "org.au", "edu.au",
    "co.nz", "org.nz", "co.za", "com.br", "com.mx", "co.in", "co.kr",
    "com.sg", "com.cn", "com.hk", "com.tw",
}


class FetchError(Exception):
    """A fetch failure whose message is safe to return to API clients.

    The message never contains resolved IP addresses or internal network
    detail. The code is a short stable token for the API error response.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class FetchResult:
    final_url: str
    status: int
    headers: dict[str, str]
    body: bytes
    redirects: list[dict[str, object]] = field(default_factory=list)
    tls_valid: bool = True


def registered_domain(host: str) -> str:
    """Approximate the registered domain (eTLD+1) for redirect-scope checks."""
    host = host.lower().strip(".")
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    if ".".join(labels[-2:]) in _MULTI_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def ip_is_blocked(ip: ipaddress._BaseAddress) -> bool:
    """Return True for any address the verifier must not connect to."""
    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
        or ip.is_reserved
    ):
        return True
    if not ip.is_global:
        return True
    if isinstance(ip, ipaddress.IPv4Address):
        # Carrier-grade NAT space is not global but is not flagged above.
        if ip in ipaddress.ip_network("100.64.0.0/10"):
            return True
    if isinstance(ip, ipaddress.IPv6Address):
        mapped = ip.ipv4_mapped
        if mapped is not None and ip_is_blocked(mapped):
            return True
    return False


def _resolve(host: str, port: int) -> list[str]:
    """Resolve a host and reject it if any address is non-public."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise FetchError("dns-failed", "the host could not be resolved")
    addrs = [info[4][0] for info in infos]
    if not addrs:
        raise FetchError("dns-failed", "the host could not be resolved")
    for addr in addrs:
        try:
            parsed = ipaddress.ip_address(addr)
        except ValueError:
            raise FetchError("blocked-target", "the host resolved to an invalid address")
        if ip_is_blocked(parsed):
            raise FetchError("blocked-target", "the host resolves to a non-public address")
    return addrs


def _open_tls(host: str, port: int, ip: str) -> ssl.SSLSocket:
    """Connect to a vetted IP and complete a TLS handshake verified for host."""
    raw = socket.create_connection((ip, port), timeout=CONNECT_TIMEOUT)
    context = ssl.create_default_context()
    try:
        return context.wrap_socket(raw, server_hostname=host)
    except Exception:
        raw.close()
        raise


def _request_headers(request_profile: str = "default") -> dict[str, str]:
    # No cookies, no authorization, no ambient credentials. Identity encoding
    # keeps the size cap exact and avoids decompression bombs.
    user_agent = USER_AGENT
    accept = "text/plain, */*;q=0.1"
    if request_profile == "variation":
        request_profile = "variation-browser"
    if request_profile in VARIATION_PROFILES:
        # The content-variation re-fetch deliberately does NOT identify itself as
        # GuideCheck. A host that cloaks against the verifier (serving benign
        # bytes whenever it sees a "guidecheck" user agent, malicious bytes to
        # real agents) would defeat the check if both fetches were branded. A
        # neutral profile makes verifier-targeted cloaking more visible.
        user_agent, accept = VARIATION_PROFILES[request_profile]
    return {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Encoding": "identity",
        "Connection": "close",
    }


def variation_request_profile(url: str, day: str) -> str:
    """Deterministically select one unbranded variation profile."""
    names = sorted(VARIATION_PROFILES)
    digest = hashlib.sha256(f"{url}\n{day}".encode("utf-8")).digest()
    return names[digest[0] % len(names)]


def safe_fetch(url: str, request_profile: str = "default") -> FetchResult:
    """Fetch a public guide URL with SSRF, size, redirect, and timeout limits.

    Raises FetchError with a sanitized message on any rejection or failure.
    """
    start = time.monotonic()
    current = url
    redirects: list[dict[str, object]] = []
    origin_domain: str | None = None

    for _ in range(MAX_REDIRECTS + 1):
        if time.monotonic() - start > TOTAL_DEADLINE:
            raise FetchError("timeout", "the request exceeded the time limit")

        parts = urlsplit(current)
        if parts.scheme != "https":
            raise FetchError("scheme", "only https guide URLs are accepted")
        host = parts.hostname
        if not host:
            raise FetchError("invalid-url", "the URL has no host")
        port = parts.port or 443

        domain = registered_domain(host)
        if origin_domain is None:
            origin_domain = domain
        elif domain != origin_domain:
            raise FetchError(
                "cross-domain-redirect",
                "the URL redirected to a different registered domain",
            )

        addrs = _resolve(host, port)
        path = parts.path or "/"
        if parts.query:
            path = f"{path}?{parts.query}"

        try:
            tls = _open_tls(host, port, addrs[0])
        except ssl.SSLError:
            raise FetchError("tls", "the TLS certificate could not be verified")
        except (socket.timeout, TimeoutError):
            raise FetchError("timeout", "the connection timed out")
        except OSError:
            raise FetchError("connect-failed", "the host could not be reached")

        conn = http.client.HTTPSConnection(host, port, timeout=READ_TIMEOUT)
        conn.sock = tls
        try:
            conn.request("GET", path, headers=_request_headers(request_profile))
            response = conn.getresponse()
            status = response.status

            if status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                response.read()
                if not location:
                    raise FetchError("bad-redirect", "a redirect response had no target")
                nxt = urljoin(current, location)
                redirects.append({"from": current, "to": nxt, "status": status})
                current = nxt
                continue

            length = response.getheader("Content-Length")
            if length and length.strip().isdigit() and int(length) > MAX_BYTES:
                raise FetchError("too-large", "the guide exceeds the size limit")
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise FetchError("too-large", "the guide exceeds the size limit")

            headers = {
                key.lower(): value
                for key, value in response.getheaders()
                if key.lower() in REPORT_HEADERS
            }
            return FetchResult(
                final_url=current,
                status=status,
                headers=headers,
                body=body,
                redirects=redirects,
                tls_valid=True,
            )
        except FetchError:
            raise
        except (socket.timeout, TimeoutError):
            raise FetchError("timeout", "the connection timed out")
        except OSError:
            raise FetchError("read-failed", "the response could not be read")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    raise FetchError("too-many-redirects", "the URL redirected too many times")
