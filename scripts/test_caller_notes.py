#!/usr/bin/env python3
"""Regressions for the local CLI's caller notes and the Level 4 contract gate.

The report on stdout and the native exit status are a released contract. The
notes tested here go to stderr only and exist because the exit status and the
report's last line say less than a reader tends to assume: the guide's author
chooses the evaluator, a run without --level requires no level, and
'Proceed?' counts blocking findings only.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "guidecheck_verify.py"
LEGACY = ROOT / "examples" / "level-3-assistant-guide.txt"
MODERN = ROOT / "fixtures" / "profiles" / "2.0.0" / "local-consistency" / "guide.txt"
UNBOUNDED = ROOT / "fixtures" / "profiles" / "2.0.0" / "corrected-bound-unpinned" / "guide.txt"
NOTE = "guidecheck_verify: note: "


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(VERIFY), *args], capture_output=True, text=True)


def notes(result: subprocess.CompletedProcess) -> list[str]:
    return [line[len(NOTE):] for line in result.stderr.splitlines() if line.startswith(NOTE)]


class CallerNoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix="guidecheck-caller-notes-")
        scratch = Path(cls.scratch.name)
        modern = re.sub(r"^manifest-url:.*\n", "", MODERN.read_text(), flags=re.M)
        # A clean Level 3 guide under the current profile.
        cls.modern_level3 = scratch / "modern-level-3.txt"
        cls.modern_level3.write_text(modern)
        # The same guide with its action fences made unrecognizable and the
        # invocation heading renamed, so no Level 3 check is triggered.
        lowered = modern.replace("[action]", "[action 2]").replace("[/action]", "[/action 2]")
        lowered = lowered.replace("Assistant invocation prompt", "Assistant prompt")
        cls.modern_level2 = scratch / "modern-level-2.txt"
        cls.modern_level2.write_text(lowered)
        # The README's rejected fixture, with only its declared version lowered.
        downgraded = re.sub(r"^manifest-url:.*\n", "", UNBOUNDED.read_text(), flags=re.M)
        cls.downgraded = scratch / "declared-legacy.txt"
        cls.downgraded.write_text(downgraded.replace("profile-version: 2.0.0", "profile-version: 0.7.1"))

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def report(self, result):
        self.assertNotIn("note:", result.stdout)
        return json.loads(result.stdout)

    def test_preconditions_still_hold(self):
        # If these fail, the fixtures moved and the tests below prove nothing.
        level3 = self.report(run(str(self.modern_level3)))
        self.assertEqual((level3["guide"]["achieved_level"], level3["summary"]["blocking_findings"]), (3, 0))
        level2 = self.report(run(str(self.modern_level2)))
        self.assertEqual((level2["guide"]["achieved_level"], level2["summary"]["blocking_findings"]), (2, 0))
        self.assertTrue(level2["compact_report"].endswith("Proceed? yes"))

    def test_current_profile_at_level_3_is_silent(self):
        for extra in ((), ("--level", "3"), ("--require-profile-version", "2.0.0", "--level", "3", "--fail-on-warning")):
            with self.subTest(extra):
                result = run(str(self.modern_level3), *extra)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")

    def test_author_selected_older_policy_is_named(self):
        for path, policy in ((LEGACY, "0.7.1"), (self.downgraded, "0.7.1")):
            with self.subTest(path.name):
                result = run(str(path), "--level", "3")
                self.assertEqual(result.returncode, 0)  # the released exit status is unchanged
                found = notes(result)
                self.assertEqual(len(found), 1)
                self.assertIn(f"evaluated under the {policy} policy", found[0])
                self.assertIn("--require-profile-version 2.0.0", found[0])
                self.report(result)

    def test_downgraded_guide_is_refused_once_the_caller_requires_the_profile(self):
        result = run(str(self.downgraded), "--level", "3", "--require-profile-version", "2.0.0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("profile-version-requirement-mismatch", result.stderr)
        self.assertEqual(notes(result), [])

    def test_requiring_the_declared_older_policy_is_a_deliberate_choice(self):
        result = run(str(LEGACY), "--level", "3", "--require-profile-version", "0.7.1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(notes(result), [])

    def test_exit_zero_below_level_3_says_no_level_was_required(self):
        result = run(str(self.modern_level2), "--require-profile-version", "2.0.0")
        self.assertEqual(result.returncode, 0)
        found = notes(result)
        self.assertEqual(len(found), 1)
        self.assertIn("exit status 0 at achieved Level 2", found[0])
        self.assertIn("--level 3", found[0])

    def test_unmet_level_explains_the_proceed_line(self):
        result = run(str(self.modern_level2), "--require-profile-version", "2.0.0", "--level", "3", "--format", "text")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.rstrip().endswith("Proceed? yes"))  # frozen report text
        found = notes(result)
        self.assertEqual(len(found), 1)
        self.assertIn("achieved Level 2 is below the requested Level 3", found[0])
        self.assertIn("'Proceed?' line counts blocking findings only", found[0])

    def test_blocking_findings_need_no_gate_note(self):
        result = run(str(UNBOUNDED), "--level", "3")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(notes(result), [])

    def test_stdout_is_byte_identical_with_and_without_notes(self):
        noted = run(str(LEGACY), "--format", "text")
        quiet = run(str(LEGACY), "--format", "text", "--require-profile-version", "0.7.1")
        self.assertTrue(notes(noted))
        self.assertEqual(notes(quiet), [])
        self.assertEqual(noted.stdout, quiet.stdout)

    def test_help_does_not_promise_level_4(self):
        text = run("--help").stdout
        self.assertNotIn("through GuideCheck Level 4", text)
        self.assertIn("Levels 1 through 3", text)


class ContractLevelFourGateTests(unittest.TestCase):
    """posix-json-v1: --level 4 is inconclusive only for a Level 3 result."""

    @classmethod
    def setUpClass(cls):
        CallerNoteTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def gate(self, path: Path, level: str):
        result = run(str(path), "--contract", "posix-json-v1", "--level", level)
        return result.returncode, json.loads(result.stdout)["gate"]["status"], result.stderr

    def test_level_3_result_is_inconclusive_for_level_4(self):
        self.assertEqual(self.gate(self.modern_level3, "4"), (3, "inconclusive", ""))

    def test_result_below_level_3_is_rejected_for_level_4(self):
        self.assertEqual(self.gate(self.modern_level2, "4"), (2, "rejected", ""))
        self.assertEqual(self.gate(self.modern_level2, "3"), (2, "rejected", ""))

    def test_contract_mode_prints_no_notes(self):
        self.assertEqual(self.gate(LEGACY, "3"), (0, "accepted", ""))


if __name__ == "__main__":
    unittest.main()
