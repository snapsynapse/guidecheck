#!/usr/bin/env python3
"""Regressions for the README "Try it" lesson: fail, repair, pass, one profile.

The README reproduces a released 2.0.0 fixture that is rejected for an
unbounded action, then verifies a repaired copy of the same guide under the
same gate. These tests hold both halves, and hold the repair to the three
changes the README names, so the lesson cannot drift from the files.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "guidecheck_verify.py"
FAILING = ROOT / "fixtures" / "profiles" / "2.0.0" / "corrected-bound-unpinned" / "guide.txt"
REPAIRED = ROOT / "examples" / "2.0.0-corrected-bound-inline" / "guide.txt"
GATE = ("--require-profile-version", "2.0.0", "--level", "3")


def verify(path: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(VERIFY), str(path), *GATE],
        capture_output=True,
        text=True,
    )
    return result.returncode, json.loads(result.stdout)


class ReadmeTrialTests(unittest.TestCase):
    def test_failing_fixture_is_rejected_for_the_unbounded_action(self):
        code, report = verify(FAILING)
        self.assertEqual(code, 1)
        self.assertEqual(report["guide"]["achieved_level"], 2)
        blocking = {f["id"] for f in report["findings"] if f["severity"] == "error"}
        self.assertEqual(blocking, {"action.exec-unbounded", "anchor.independent.missing"})

    def test_repaired_guide_passes_the_same_gate_under_the_same_profile(self):
        code, report = verify(REPAIRED)
        self.assertEqual(code, 0)
        self.assertEqual(report["verifier"]["version"], "2.0.0")
        self.assertEqual(report["profile_selection"]["evaluated_policy"], "2.0.0")
        self.assertEqual(report["guide"]["achieved_level"], 3)
        self.assertEqual(report["summary"]["blocking_findings"], 0)
        self.assertEqual(report["summary"]["warnings"], 0)

    def test_repair_changes_only_what_the_readme_describes(self):
        before = FAILING.read_text(encoding="ascii").splitlines()
        after = REPAIRED.read_text(encoding="ascii").splitlines()
        removed = {l[1:] for l in difflib.unified_diff(before, after, lineterm="", n=0)
                   if l.startswith("-") and not l.startswith("---")}
        added = {l[1:] for l in difflib.unified_diff(before, after, lineterm="", n=0)
                 if l.startswith("+") and not l.startswith("+++")}
        self.assertIn("command: npm --prefix subdir run check", removed)
        self.assertIn("command: example-verifier --version", added)
        self.assertTrue(any(l.startswith("manifest-url:") for l in removed))
        self.assertFalse(any(l.startswith("manifest-url:") for l in added))
        self.assertLessEqual(len(removed), 9)


if __name__ == "__main__":
    unittest.main()
