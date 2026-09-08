#!/usr/bin/env python3
"""Replay complete released 1.0.0 reports, independently of current policy code."""
from contextlib import redirect_stdout
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import check_reference_verifier as fixtures
import guidecheck_verify as verifier
import test_hosted_api as hosted
from test_legacy_anchor_compatibility import artifacts, GUIDE_URLS, RAW_URL, NOW

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "1bd5f3d6e31f79ca6125e7da03ec1746934eb6b5"


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz else NOW.replace(tzinfo=None)


def capture():
    local = {}
    for path in sorted((ROOT / "fixtures/profiles/1.0.0").iterdir()):
        if not (path / "guide.txt").is_file():
            continue
        manifest = path / "manifest.txt"
        evaluation = verifier.evaluate_local_file(
            path / "guide.txt", manifest if manifest.exists() else None,
            fixtures.fixture_anchor_paths(path), now=NOW,
        )
        local[path.name] = verifier.output_for(evaluation)
    responses = []
    for dns in (False, True):
        data, manifest, manifest_url = artifacts("1.0.0", GUIDE_URLS[0])

        def fetch(url, request_profile="default", accept_override=None):
            if url in (GUIDE_URLS[0], RAW_URL):
                return hosted.fetched(url, 200, data)
            if url == manifest_url:
                return hosted.fetched(url, 200, manifest.encode())
            if url.startswith("https://cloudflare-dns.com/"):
                record = {"Status": 0}
                if dns:
                    record.update(AD=True, Answer=[{"type": 16, "data":
                        '"v=1; sha256=' + hashlib.sha256(data).hexdigest() + '"'}])
                return hosted.fetched(url, 200, json.dumps(record).encode(), "application/dns-json")
            raise AssertionError(url)

        with patch.object(hosted.hv, "datetime", FixedDateTime), redirect_stdout(io.StringIO()):
            request = hosted.run_post({"url": GUIDE_URLS[0]}, fetch)
        responses.append({"dns": dns, "status": request.status, "body": request.body})
    # Evaluation time is fixed. Only checkout-specific paths are normalized.
    return json.loads(json.dumps({"local": local, "hosted": responses}).replace(str(ROOT), "$ROOT"))


class StrictCompatibilityTests(unittest.TestCase):
    def test_complete_released_reports_are_unchanged(self):
        baseline = json.loads((ROOT / "fixtures/compatibility/strict-1.0.0-baseline.json").read_text())
        self.assertEqual(baseline["source_commit"], SOURCE_COMMIT)
        self.assertEqual(capture(), baseline["results"])


if __name__ == "__main__":
    unittest.main()
