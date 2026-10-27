#!/usr/bin/env python3
"""Frozen evaluator replay with explicit hosted security reporting corrections."""
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import check_reference_verifier as crv
import guidecheck_verify as gv
import test_hosted_api as hosted

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "fixtures/compatibility/legacy-baseline.json"
NOW = datetime(2026, 9, 5, 20, tzinfo=timezone.utc)


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz else NOW.replace(tzinfo=None)


def hosted_security_expected(results):
    """Apply only the reviewed SEC-001 hosted delta to historical expectations.

    Snapshots and all local reports remain unchanged. Do not normalize actual
    output: unexpected runtime changes must still fail the complete comparison.
    """
    expected = deepcopy(results)
    old_scope = "Hosted Level 4 supports package-registry, transparency-log, DNS TXT (resolved via DNS-over-HTTPS), and repository-file anchors. The repository-file allowlist is currently scoped to github.com; signed security.txt anchors are not fetched."
    new_scope = "Hosted Level 4 supports package-registry, DNS TXT (resolved via DNS-over-HTTPS), and repository-file anchors. The repository-file allowlist is currently scoped to github.com; transparency-log and signed security.txt anchors are not fetched. Transparency-log independence and append-only evidence are not verified."
    affected = 0
    for response in expected["hosted"]:
        body = response["body"]
        limitations = body["hosted_limitations"]
        assert limitations.count(old_scope) == 1
        limitations[limitations.index(old_scope)] = new_scope
        anchors = body.get("cross_channel_anchors", [])
        if any(a["channel"] == "transparency-log" for a in anchors):
            # The sole historical case aliases an independently valid registry
            # URL as a log. Its registry anchor and achieved level stay intact.
            assert body["guide"]["sha256"] == "3301cc097ccdf4f5ce7c5f11ac0d43d7edbbbd6b5c79cf7832cfc3e137317d26"
            assert [a["channel"] for a in anchors] == ["package-registry", "transparency-log"]
            body["cross_channel_anchors"] = anchors[:1]
            body["findings"].insert(1, {
                "id": "anchor.transparency-log.unverified",
                "severity": "info",
                "message": "transparency-log evidence is not fetched or counted toward Level 4; log independence and append-only evidence are not verified",
                "section": "verifier-conformance.23",
            })
            body["summary"]["infos"] += 1
            affected += 1
    return expected, affected


def capture():
    local = {}
    for path in crv.fixture_dirs():
        manifest = path / "manifest.txt"
        guide = path / "guide.txt"
        if not guide.exists():
            continue
        evaluation = gv.evaluate_local_file(
            guide, manifest if manifest.exists() else None,
            crv.fixture_anchor_paths(path), now=NOW,
        )
        local[str(path.relative_to(ROOT))] = gv.output_for(evaluation)
    responses = []
    original = hosted.run_post

    def record(*args, **kwargs):
        request = original(*args, **kwargs)
        responses.append({"status": request.status, "body": request.body})
        return request

    # Existing hosted scenarios exercise the real handler with replayed fetches.
    # Do not suppress assertion failures along with telemetry.
    old_counts = hosted.PASSED, hosted.FAILED
    hosted.PASSED = hosted.FAILED = 0
    try:
        with patch.object(hosted, "run_post", record), patch.object(hosted.hv, "datetime", FixedDateTime), redirect_stdout(io.StringIO()):
            for name in sorted(vars(hosted)):
                if name.startswith("test_") and name != "test_version_constants":
                    getattr(hosted, name)()
        if hosted.FAILED:
            raise AssertionError(f"{hosted.FAILED} hosted assertions failed during replay")
    finally:
        hosted.PASSED, hosted.FAILED = old_counts
    # Only machine-specific paths are normalized. Time is fixed at evaluation.
    return json.loads(json.dumps({"local": local, "hosted": responses}).replace(str(ROOT), "$ROOT"))


class DispatchCompatibilityTests(unittest.TestCase):
    def test_baseline_results_are_unchanged(self):
        expected, affected = hosted_security_expected(json.loads(SNAPSHOT.read_text())["results"])
        self.assertEqual(affected, 1)
        self.assertEqual(capture(), expected)


if __name__ == "__main__":
    unittest.main()
