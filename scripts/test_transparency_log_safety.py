#!/usr/bin/env python3
"""Offline regressions for unestablished hosted transparency-log evidence."""

from contextlib import redirect_stdout
import hashlib
import io
import json
import unittest

from test_hosted_api import fetched, run_post
from test_legacy_anchor_compatibility import LEGACY_VERSIONS, artifacts, GUIDE_URLS, RAW_URL


class TransparencyLogSafetyTests(unittest.TestCase):
    def verify(self, version, log_url, independent=None):
        guide_url = GUIDE_URLS[0]
        data, manifest, manifest_url = artifacts(version, guide_url)
        registry_url = "https://registry.npmjs.org/example-verifier/1.0.0"
        if independent == "package-registry":
            original_data = data
            data = data.replace(b"manifest-url:", f"registry-url: {registry_url}\nmanifest-url:".encode())
            manifest = manifest.replace(
                "guide-sha256: " + hashlib.sha256(original_data).hexdigest(),
                "guide-sha256: " + hashlib.sha256(data).hexdigest(),
            ).replace("guide-bytes: " + str(len(original_data)),
                      "guide-bytes: " + str(len(data)))
        digest = hashlib.sha256(data).hexdigest()
        manifest += f"transparency-log-url: {log_url}\n"
        calls = []

        def fetch(url, request_profile="default", accept_override=None):
            calls.append(url)
            if url == guide_url:
                return fetched(url, 200, data)
            if url == manifest_url:
                return fetched(url, 200, manifest.encode())
            if url == registry_url:
                return fetched(url, 200, json.dumps({"assistantGuide": {
                    "sha256": digest, "url": guide_url}}).encode(), "application/json")
            if url == log_url:
                # Even matching text must never be fetched/qualified as a log.
                return fetched(url, 200, f"guide-sha256: {digest}".encode())
            if url == RAW_URL:
                return fetched(url, 404, b"")
            if url.startswith("https://cloudflare-dns.com/"):
                response = {"Status": 0}
                if independent == "dns-txt":
                    response["Answer"] = [{"type": 16, "data":
                        f'"v=1; sha256={digest}; url={guide_url}"'}]
                return fetched(url, 200, json.dumps(response).encode(), "application/dns-json")
            self.fail("unexpected fetch: " + url)

        with redirect_stdout(io.StringIO()):
            request = run_post({"url": guide_url, "requested_level": 4}, fetch)
        self.assertEqual(request.status, 200)
        body = request.body
        self.assertEqual(body["outcome"], "evaluated")
        self.assertTrue(body["manifest"]["valid"])
        self.assertNotIn(log_url, calls)
        self.assertNotIn("transparency-log", [a["channel"] for a in body.get("cross_channel_anchors", [])])
        finding = next(f for f in body["findings"] if f["id"] == "anchor.transparency-log.unverified")
        self.assertEqual(finding["severity"], "info")
        self.assertTrue(any("transparency-log" in s and "not fetched" in s for s in body["hosted_limitations"]))
        return body

    def test_arbitrary_log_cannot_establish_level4_for_any_profile(self):
        for version in (*sorted(LEGACY_VERSIONS), "1.0.0", "2.0.0"):
            for url in (
                "https://snapsynapse.github.io/compat/.well-known/self-asserted-log.txt",
                "https://different.example/log-entry.txt",
            ):
                with self.subTest(version=version, url=url):
                    body = self.verify(version, url)
                    self.assertEqual(body["guide"]["achieved_level"], 3)
                    self.assertFalse(body["guide"]["level5_ready"])
                    self.assertIn("anchor.independent.missing", [f["id"] for f in body["findings"]])
                    self.assertIn("Proceed? no", body["compact_report"])
                    if version in {"1.0.0", "2.0.0"}:
                        self.assertEqual(body["qualifying_anchor_count"], 0)

    def test_supported_independent_anchor_still_establishes_level4(self):
        for version in ("0.7.1", "1.0.0", "2.0.0"):
            for channel in ("dns-txt", "package-registry"):
                with self.subTest(version=version, channel=channel):
                    body = self.verify(version, "https://different.example/log-entry.txt", channel)
                    self.assertEqual(body["guide"]["achieved_level"], 4)
                    self.assertEqual(body["summary"]["blocking_findings"], 0)
                    self.assertIn("Proceed? yes", body["compact_report"])
                    self.assertEqual([a["channel"] for a in body["cross_channel_anchors"]], [channel])
                    if version != "0.7.1":
                        self.assertEqual(body["qualifying_anchor_count"], 1)


if __name__ == "__main__":
    unittest.main()
