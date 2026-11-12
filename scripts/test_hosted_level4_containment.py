#!/usr/bin/env python3
"""Offline regressions: the hosted verifier does not award Level 4.

Every hosted anchor location (DNS name, registry record, repository file) is
taken from fields inside the guide bytes, so whoever writes the guide chooses
where the "independent" evidence comes from. Until an anchor is bound to the
checked host by something the web host cannot rewrite, the hosted path
reports anchor evidence as unverified and caps every profile at Level 3.

All fetches are mocked. No network, DNS, registry, or repository is touched.
"""

from contextlib import redirect_stdout
import hashlib
import io
import json
import re
import unittest

from test_hosted_api import fetched, run_post
from test_legacy_anchor_compatibility import LEGACY_VERSIONS, artifacts, GUIDE_URLS

PROFILES = (*LEGACY_VERSIONS, "1.0.0", "2.0.0")
VICTIM_URL = "https://victim.example/.well-known/assistant-guide.txt"
FOREIGN_CANONICAL = GUIDE_URLS[0]  # snapsynapse.github.io, not the victim
ATTACKER_REGISTRY = "https://registry.npmjs.org/attacker-owned-pkg/1.0.0"
ATTACKER_REPOSITORY = "https://github.com/attacker/throwaway"
SOURCE = "/docs/.well-known/assistant-guide.txt"
ATTACKER_RAW = "https://raw.githubusercontent.com/attacker/throwaway/HEAD" + SOURCE
NXDOMAIN = json.dumps({"Status": 3}).encode()


def set_field(data: bytes, field: str, value: str) -> bytes:
    text = data.decode()
    pattern = r"^" + re.escape(field) + r": .*?$"
    if re.search(pattern, text, flags=re.M):
        text = re.sub(pattern, field + ": " + value, text, flags=re.M)
    else:
        text = text.replace("manifest-url:", f"{field}: {value}\nmanifest-url:", 1)
    return text.encode()


def rehash(manifest: str, old: bytes, new: bytes) -> str:
    return manifest.replace(
        "guide-sha256: " + hashlib.sha256(old).hexdigest(),
        "guide-sha256: " + hashlib.sha256(new).hexdigest(),
    ).replace("guide-bytes: " + str(len(old)), "guide-bytes: " + str(len(new)))


def dns_answer(digest: str, url: str) -> bytes:
    return json.dumps({"Status": 0, "Answer": [
        {"type": 16, "data": f'"v=1; sha256={digest}; url={url}"'}]}).encode()


class HostedLevel4ContainmentTests(unittest.TestCase):
    def post(self, data, routes):
        calls = []

        def fetch(url, request_profile="default", accept_override=None):
            calls.append(url)
            if url == VICTIM_URL:
                return fetched(url, 200, data)
            for prefix, response in routes.items():
                if url == prefix or (prefix.endswith("/") and url.startswith(prefix)):
                    return response(url)
            self.fail("unexpected fetch: " + url)

        with redirect_stdout(io.StringIO()):
            request = run_post({"url": VICTIM_URL, "requested_level": 4}, fetch)
        self.assertEqual(request.status, 200)
        self.assertEqual(request.body["outcome"], "evaluated")
        return request.body, calls

    def assert_contained(self, body, version, channel):
        guide = body["guide"]
        self.assertEqual(guide["achieved_level"], 3)
        self.assertFalse(guide["level5_ready"])
        self.assertIn("Level: 3\n", body["compact_report"])
        self.assertIn("Hash pinned: no\n", body["compact_report"])
        finding = next(f for f in body["findings"] if f["id"] == "anchor.hosted.unverified")
        self.assertEqual(finding["severity"], "info")
        anchors = {a["channel"]: a for a in body.get("cross_channel_anchors", [])}
        # The evidence is still reported, marked unverified on the hosted path.
        self.assertEqual(anchors[channel]["status"], "present-matches")
        for anchor in anchors.values():
            self.assertEqual(anchor["hosted_verification"], "unverified")
            if version in {"1.0.0", "2.0.0"}:
                self.assertFalse(anchor["qualifies_for_level4"])
        if version in {"1.0.0", "2.0.0"}:
            self.assertEqual(body["qualifying_anchor_count"], 0)
            self.assertIn("Qualifying anchors: 0\n", body["compact_report"])
        self.assertTrue(any("Levels 1 through 3" in s for s in body["hosted_limitations"]))

    def test_foreign_domain_dns_anchor(self):
        """Audit reproduction 1: canonical-url names a host the victim does not control."""
        for version in PROFILES:
            with self.subTest(version=version):
                data, manifest, manifest_url = artifacts(version, FOREIGN_CANONICAL)
                digest = hashlib.sha256(data).hexdigest()
                body, calls = self.post(data, {
                    manifest_url: lambda u: fetched(u, 200, manifest.encode()),
                    "https://raw.githubusercontent.com/": lambda u: fetched(u, 404, b""),
                    "https://cloudflare-dns.com/": lambda u: fetched(
                        u, 200, dns_answer(digest, FOREIGN_CANONICAL), "application/dns-json"),
                })
                self.assertTrue(any("_assistant-guide.snapsynapse.github.io" in c for c in calls))
                self.assert_contained(body, version, "dns-txt")

    def test_attacker_named_registry_package(self):
        """Audit reproduction 2: registry-url names a package the attacker owns."""
        for version in PROFILES:
            with self.subTest(version=version):
                original, manifest, manifest_url = artifacts(version, VICTIM_URL)
                data = set_field(original, "registry-url", ATTACKER_REGISTRY)
                manifest = rehash(manifest, original, data)
                digest = hashlib.sha256(data).hexdigest()
                registry = json.dumps({"assistantGuide": {"sha256": digest, "url": VICTIM_URL}}).encode()
                body, calls = self.post(data, {
                    manifest_url: lambda u: fetched(u, 200, manifest.encode()),
                    ATTACKER_REGISTRY: lambda u: fetched(u, 200, registry, "application/json"),
                    "https://raw.githubusercontent.com/": lambda u: fetched(u, 404, b""),
                    "https://cloudflare-dns.com/": lambda u: fetched(u, 200, NXDOMAIN, "application/dns-json"),
                })
                self.assertIn(ATTACKER_REGISTRY, calls)
                self.assert_contained(body, version, "package-registry")

    def test_attacker_repository_any_profile(self):
        """Audit reproduction 3: the guide names an attacker repository and picks the profile."""
        for version in PROFILES:
            with self.subTest(version=version):
                original, manifest, manifest_url = artifacts(version, VICTIM_URL)
                data = set_field(original, "repository-url", ATTACKER_REPOSITORY)
                manifest = rehash(manifest, original, data)
                body, calls = self.post(data, {
                    manifest_url: lambda u: fetched(u, 200, manifest.encode()),
                    ATTACKER_RAW: lambda u: fetched(u, 200, data),
                    "https://cloudflare-dns.com/": lambda u: fetched(u, 200, NXDOMAIN, "application/dns-json"),
                })
                self.assertIn(ATTACKER_RAW, calls)
                self.assert_contained(body, version, "repository-file")

    def test_every_anchor_at_once_stays_level3(self):
        """Mixed anchors: DNS, registry, and repository all present and matching."""
        for version in PROFILES:
            with self.subTest(version=version):
                original, manifest, manifest_url = artifacts(version, VICTIM_URL)
                data = set_field(set_field(original, "registry-url", ATTACKER_REGISTRY),
                                 "repository-url", ATTACKER_REPOSITORY)
                manifest = rehash(manifest, original, data)
                digest = hashlib.sha256(data).hexdigest()
                registry = json.dumps({"assistantGuide": {"sha256": digest, "url": VICTIM_URL}}).encode()
                body, _ = self.post(data, {
                    manifest_url: lambda u: fetched(u, 200, manifest.encode()),
                    ATTACKER_REGISTRY: lambda u: fetched(u, 200, registry, "application/json"),
                    ATTACKER_RAW: lambda u: fetched(u, 200, data),
                    "https://cloudflare-dns.com/": lambda u: fetched(
                        u, 200, dns_answer(digest, VICTIM_URL), "application/dns-json"),
                })
                self.assert_contained(body, version, "dns-txt")
                self.assertEqual(
                    sorted(a["channel"] for a in body["cross_channel_anchors"]),
                    ["dns-txt", "package-registry", "repository-file"],
                )

    # Adversarial re-test: other routes back to hosted Level 4.

    def test_redirect_to_canonical_host_stays_level3(self):
        """A redirect that lands on the canonical host does not bind the anchor."""
        for version in PROFILES:
            with self.subTest(version=version):
                data, manifest, manifest_url = artifacts(version, FOREIGN_CANONICAL)
                digest = hashlib.sha256(data).hexdigest()

                def landed(url):
                    response = fetched(FOREIGN_CANONICAL, 200, data)
                    response.redirects = [{"status": 301, "location": FOREIGN_CANONICAL}]
                    return response

                body = self.post_landing(data, landed, {
                    manifest_url: lambda u: fetched(u, 200, manifest.encode()),
                    "https://raw.githubusercontent.com/": lambda u: fetched(u, 404, b""),
                    "https://cloudflare-dns.com/": lambda u: fetched(
                        u, 200, dns_answer(digest, FOREIGN_CANONICAL), "application/dns-json"),
                })
                self.assert_contained(body, version, "dns-txt")

    def post_landing(self, data, landed, routes):
        def fetch(url, request_profile="default", accept_override=None):
            if url == VICTIM_URL:
                return landed(url)
            for prefix, response in routes.items():
                if url == prefix or (prefix.endswith("/") and url.startswith(prefix)):
                    return response(url)
            self.fail("unexpected fetch: " + url)

        with redirect_stdout(io.StringIO()):
            request = run_post({"url": VICTIM_URL, "requested_level": 4}, fetch)
        self.assertEqual(request.status, 200)
        return request.body

    def test_host_bound_dns_anchor_stays_level3(self):
        """Even a DNS anchor on the checked host is not awarded Level 4 here."""
        for version in PROFILES:
            with self.subTest(version=version):
                data, manifest, manifest_url = artifacts(version, VICTIM_URL)
                digest = hashlib.sha256(data).hexdigest()
                body, calls = self.post(data, {
                    manifest_url: lambda u: fetched(u, 200, manifest.encode()),
                    "https://raw.githubusercontent.com/": lambda u: fetched(u, 404, b""),
                    "https://cloudflare-dns.com/": lambda u: fetched(
                        u, 200, dns_answer(digest, VICTIM_URL), "application/dns-json"),
                })
                self.assertTrue(any("_assistant-guide.victim.example" in c for c in calls))
                self.assert_contained(body, version, "dns-txt")
                self.assertEqual(body["summary"]["blocking_findings"], 0)
                self.assertIn("Proceed? yes", body["compact_report"])

    def test_manifest_fields_cannot_name_anchors(self):
        """Anchor fields placed in the manifest are not fetched or counted."""
        for version in PROFILES:
            with self.subTest(version=version):
                data, manifest, manifest_url = artifacts(version, VICTIM_URL)
                manifest += (f"registry-url: {ATTACKER_REGISTRY}\n"
                             f"repository-url: {ATTACKER_REPOSITORY}\n"
                             f"canonical-url: {FOREIGN_CANONICAL}\n")
                body, calls = self.post(data, {
                    manifest_url: lambda u: fetched(u, 200, manifest.encode()),
                    "https://raw.githubusercontent.com/": lambda u: fetched(u, 404, b""),
                    "https://cloudflare-dns.com/": lambda u: fetched(u, 200, NXDOMAIN, "application/dns-json"),
                })
                self.assertNotIn(ATTACKER_REGISTRY, calls)
                self.assertNotIn(ATTACKER_RAW, calls)
                self.assertLessEqual(body["guide"]["achieved_level"], 3)
                self.assertFalse(body["guide"]["level5_ready"])

    def test_required_profile_version_cannot_restore_level4(self):
        """A caller profile assertion never reinterprets guide bytes into Level 4."""
        for version in PROFILES:
            for required in ("0.7.1", "1.0.0", "2.0.0"):
                with self.subTest(version=version, required=required):
                    data, manifest, manifest_url = artifacts(version, FOREIGN_CANONICAL)
                    digest = hashlib.sha256(data).hexdigest()

                    def fetch(url, request_profile="default", accept_override=None):
                        if url == VICTIM_URL:
                            return fetched(url, 200, data)
                        if url == manifest_url:
                            return fetched(url, 200, manifest.encode())
                        if url.startswith("https://raw.githubusercontent.com/"):
                            return fetched(url, 404, b"")
                        if url.startswith("https://cloudflare-dns.com/"):
                            return fetched(url, 200, dns_answer(digest, FOREIGN_CANONICAL), "application/dns-json")
                        self.fail("unexpected fetch: " + url)

                    with redirect_stdout(io.StringIO()):
                        request = run_post({"url": VICTIM_URL, "requested_level": 4,
                                            "required_profile_version": required}, fetch)
                    if request.status == 200:
                        self.assertEqual(request.body["guide"]["achieved_level"], 3)
                        self.assertFalse(request.body["guide"]["level5_ready"])
                    else:
                        self.assertEqual(request.status, 400)


if __name__ == "__main__":
    unittest.main()
