#!/usr/bin/env python3
"""Frozen evaluator replay with explicit hosted security reporting corrections."""
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
import re
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


# Hosted replay results that the frozen snapshot records at Level 4.
SEC015_CAPPED_HOSTED_RESULTS = 8
SEC015_OLD_LEVELS = "This verifier evaluates Levels 1 through 4 when supported Level 4 evidence is available."
SEC015_NEW_LEVELS = "This verifier evaluates Levels 1 through 3. It does not award Level 4."
SEC015_NEW_SCOPE = "Declared package-registry, DNS TXT (resolved via DNS-over-HTTPS), and repository-file anchors are fetched and reported as unverified evidence: their locations are named by the guide itself and are not bound to the checked host, so they do not count toward Level 4. The repository-file allowlist is currently scoped to github.com; transparency-log and signed security.txt anchors are not fetched. Transparency-log independence and append-only evidence are not verified."
SEC015_FINDING = {
    "id": "anchor.hosted.unverified",
    "severity": "info",
    "message": "the hosted verifier reports declared anchor evidence but does not verify it: "
               "anchor locations are named by the guide and are not bound to the checked host, "
               "so Level 4 is not awarded here",
    "section": "verifier-conformance.23",
}


def _apply_sec015(body, declared_manifest):
    """The reviewed SEC-015 hosted delta: no hosted result reaches Level 4."""
    limitations = body["hosted_limitations"]
    assert limitations.count(SEC015_OLD_LEVELS) == 1
    limitations[limitations.index(SEC015_OLD_LEVELS)] = SEC015_NEW_LEVELS
    old_scope = next(s for s in limitations if s.startswith("Hosted Level 4 supports "))
    limitations[limitations.index(old_scope)] = SEC015_NEW_SCOPE
    if body.get("outcome") != "evaluated":
        return False
    guide, summary = body["guide"], body["summary"]
    was_level4 = guide["achieved_level"] >= 4
    if was_level4:
        # Level 5 readiness is evaluated only for Level 4 results.
        dropped = [f for f in body["findings"] if f["id"].startswith("level5.")]
        body["findings"] = [f for f in body["findings"] if not f["id"].startswith("level5.")]
        for finding in dropped:
            key = {"error": "blocking_findings", "warning": "warnings", "info": "infos"}[finding["severity"]]
            summary[key] -= 1
    guide["achieved_level"] = min(guide["achieved_level"], 3)
    guide["level5_ready"] = False
    if declared_manifest:
        body["findings"].append(dict(SEC015_FINDING))
        summary["infos"] += 1
    for anchor in body.get("cross_channel_anchors", []):
        if "qualifies_for_level4" in anchor:
            anchor["qualifies_for_level4"] = False
        anchor["hosted_verification"] = "unverified"
    if "qualifying_anchor_count" in body:
        body["qualifying_anchor_count"] = 0
    lines = []
    for line in body["compact_report"].split("\n"):
        key = line.split(":", 1)[0]
        line = {
            "Qualifying anchors": "Qualifying anchors: 0",
            "Level": f"Level: {guide['achieved_level']}",
            "Blocking findings": f"Blocking findings: {summary['blocking_findings']}",
            "Warnings": f"Warnings: {summary['warnings']}",
            "Hash pinned": "Hash pinned: no",
        }.get(key, line)
        if line.startswith("Proceed? "):
            line = f"Proceed? {'yes' if summary['blocking_findings'] == 0 else 'no'}"
        lines.append(line)
    body["compact_report"] = "\n".join(lines)
    return was_level4


def hosted_security_expected(results, declared_manifest):
    """Apply only the reviewed SEC-001 and SEC-015 hosted deltas to historical expectations.

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
    capped = sum(
        _apply_sec015(response["body"], declared_manifest(index))
        for index, response in enumerate(expected["hosted"])
    )
    return expected, affected, capped


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
    declared = []
    original = hosted.run_post

    def record(payload, fake_fetch, *args, **kwargs):
        # Record only an input fact (does the guide declare manifest-url?),
        # never anything derived from the response under test.
        guide_bytes = []

        def spy(url, *fetch_args, **fetch_kwargs):
            response = fake_fetch(url, *fetch_args, **fetch_kwargs)
            if not guide_bytes:
                guide_bytes.append(getattr(response, "body", b""))
            return response

        request = original(payload, spy, *args, **kwargs)
        responses.append({"status": request.status, "body": request.body})
        declared.append(bool(guide_bytes) and re.search(rb"^manifest-url:", guide_bytes[0], re.M) is not None)
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
    results = json.loads(json.dumps({"local": local, "hosted": responses}).replace(str(ROOT), "$ROOT"))
    return results, declared


class DispatchCompatibilityTests(unittest.TestCase):
    def test_baseline_results_are_unchanged(self):
        actual, declared = capture()
        expected, affected, capped = hosted_security_expected(
            json.loads(SNAPSHOT.read_text())["results"], declared.__getitem__,
        )
        self.assertEqual(affected, 1)
        self.assertEqual(capped, SEC015_CAPPED_HOSTED_RESULTS)
        self.maxDiff = None
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
