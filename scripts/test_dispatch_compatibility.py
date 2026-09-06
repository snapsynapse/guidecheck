#!/usr/bin/env python3
"""Differential contract captured from 3ceb30a before dispatch implementation."""
from contextlib import redirect_stdout
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
        self.assertEqual(capture(), json.loads(SNAPSHOT.read_text())["results"])


if __name__ == "__main__":
    unittest.main()
