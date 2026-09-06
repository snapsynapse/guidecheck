#!/usr/bin/env python3
"""Keep baseline anchor behavior for existing profile declarations.

These are compatibility contracts against 3ceb30a, not reconstructions of
historical verifier releases or evidence that the future strict path works.
All fetches are replayed; no adopter files, DNS records, or servers are changed.
"""

from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
from pathlib import Path
import re
import unittest

import guidecheck_verify as gv
from test_hosted_api import fetched, run_post


ROOT = Path(__file__).resolve().parents[1]
# Deliberately pinned, never generated from the current tool version or tags.
LEGACY_VERSIONS = (
    "0.1.0", "0.2.0", "0.3.0", "0.3.1", "0.4.0", "0.5.0",
    "0.6.0", "0.7.0", "0.7.1",
)
GUIDE_URLS = (
    "https://snapsynapse.github.io/compat/.well-known/assistant-guide.txt",
    "https://compat.example.com/.well-known/assistant-guide.txt",
)
REPOSITORY = "https://github.com/snapsynapse/compat"
SOURCE = "/docs/.well-known/assistant-guide.txt"
RAW_URL = "https://raw.githubusercontent.com/snapsynapse/compat/HEAD" + SOURCE
NOW = datetime(2026, 9, 5, 20, tzinfo=timezone.utc)


def artifacts(version, guide_url):
    guide = (ROOT / "fixtures/valid/level-4/guide.txt").read_text()
    manifest_url = guide_url.replace("assistant-guide.txt", "assistant-guide-manifest.txt")
    for field, value in {
        "profile-version": version,
        "canonical-url": guide_url,
        "repository-url": REPOSITORY,
        "source-path": SOURCE,
        "manifest-url": manifest_url,
    }.items():
        guide = re.sub(r"^" + field + r": .*?$", field + ": " + value, guide, flags=re.M)
    data = guide.encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    manifest = "\n".join((
        "guide-path: /.well-known/assistant-guide.txt",
        "guide-version: 1.0.0",
        "guide-sha256: " + digest,
        "guide-bytes: " + str(len(data)),
        "immutable-release-url: https://example.com/releases/1.0.0",
        "profile: human-verifiable-assistant-guide",
        "profile-version: " + version,
        "canonical-url: " + guide_url,
        "repository-url: " + REPOSITORY,
        "",
    ))
    return data, manifest, manifest_url


class LegacyAnchorCompatibilityTests(unittest.TestCase):
    def test_repository_only_hosted_results_remain_level4(self):
        for version in LEGACY_VERSIONS:
            for guide_url in GUIDE_URLS:
                with self.subTest(version=version, guide_url=guide_url):
                    data, manifest, manifest_url = artifacts(version, guide_url)

                    def fake_fetch(url, request_profile="default", accept_override=None):
                        if url in (guide_url, RAW_URL):
                            return fetched(url, 200, data)
                        if url == manifest_url:
                            return fetched(url, 200, manifest.encode())
                        if url.startswith("https://cloudflare-dns.com/"):
                            return fetched(url, 200, b'{"Status":0}', "application/dns-json")
                        self.fail("unexpected fetch: " + url)

                    with redirect_stdout(io.StringIO()):
                        request = run_post({"url": guide_url, "requested_level": 4}, fake_fetch)
                    result = request.body
                    self.assertEqual(request.status, 200)
                    self.assertEqual(result["outcome"], "evaluated")
                    self.assertEqual(result["guide"]["achieved_level"], 4)
                    self.assertTrue(result["guide"]["level5_ready"])
                    self.assertEqual(result["summary"]["blocking_findings"], 0)
                    self.assertEqual(result["summary"]["warnings"], 0)
                    self.assertIn("Level: 4\n", result["compact_report"])
                    self.assertIn("Hash pinned: yes\nProceed? yes", result["compact_report"])
                    self.assertEqual(result["cross_channel_anchors"], [{
                        "channel": "repository-file",
                        "status": "present-matches",
                        "observed_sha256": hashlib.sha256(data).hexdigest(),
                    }])

    def test_local_cap_and_mismatch_blocking_remain(self):
        for version in LEGACY_VERSIONS:
            with self.subTest(version=version):
                data, manifest, _ = artifacts(version, GUIDE_URLS[0])
                repo_text = data.decode()
                findings, level, ready, _, _ = gv.evaluate_guide(
                    data, manifest, {"repository-file": repo_text}, now=NOW,
                )
                self.assertEqual(level, 3)
                self.assertFalse(ready)
                self.assertEqual([f.id for f in findings if f.severity == "error"], [])
                self.assertIn("level4.requires-fetch", [f.id for f in findings])
                for anchors in (
                    {"repository-file": repo_text + "\n"},
                    {"repository-file": repo_text, "dns-txt": "v=1; sha256=" + "0" * 64},
                    {},
                ):
                    findings, level, ready, _, _ = gv.evaluate_guide(
                        data, manifest, anchors, now=NOW, evidence_fetched=True,
                    )
                    self.assertEqual(level, 3)
                    self.assertFalse(ready)
                    errors = [f.id for f in findings if f.severity == "error"]
                    expected = "anchor.independent.mismatch" if anchors else "anchor.independent.missing"
                    self.assertEqual(errors, [expected])


if __name__ == "__main__":
    unittest.main()
