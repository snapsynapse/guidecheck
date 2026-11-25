#!/usr/bin/env python3
"""Regressions for docs/first-guide.md: each step reaches the level the page shows.

The how-to builds a guide in three steps under released profile 2.0.0 and
quotes the verifier's output after each. These tests hold the step files to
those results so the page cannot drift from the verifier.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "guidecheck_verify.py"
STEPS = ROOT / "examples" / "first-guide"
GATE = ("--require-profile-version", "2.0.0", "--level", "3")


def verify(name: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(VERIFY), str(STEPS / name), *GATE],
        capture_output=True,
        text=True,
    )
    return result.returncode, json.loads(result.stdout)


def blocking(report: dict) -> set[str]:
    return {f["id"] for f in report["findings"] if f["severity"] == "error"}


class FirstGuideTests(unittest.TestCase):
    def test_step_1_reaches_level_2_without_blocking_findings(self):
        code, report = verify("step-1.txt")
        self.assertEqual(code, 1)
        self.assertEqual(report["guide"]["achieved_level"], 2)
        self.assertEqual(blocking(report), set())

    def test_step_2_is_blocked_only_by_the_missing_classification(self):
        code, report = verify("step-2.txt")
        self.assertEqual(code, 1)
        self.assertEqual(report["guide"]["achieved_level"], 2)
        self.assertEqual(blocking(report), {"content.required.action-classification"})

    def test_step_3_reaches_level_3(self):
        code, report = verify("step-3.txt")
        self.assertEqual(code, 0)
        self.assertEqual(report["verifier"]["version"], "2.0.0")
        self.assertEqual(report["guide"]["achieved_level"], 3)
        self.assertEqual(report["summary"]["blocking_findings"], 0)
        self.assertEqual(report["summary"]["warnings"], 0)

    def test_each_step_extends_the_one_before(self):
        one, two, three = ((STEPS / f"step-{n}.txt").read_text(encoding="ascii") for n in (1, 2, 3))
        self.assertTrue(two.startswith(one))
        self.assertIn("\nAction classification\n", three)
        self.assertNotIn("\nAction classification\n", two)


if __name__ == "__main__":
    unittest.main()
